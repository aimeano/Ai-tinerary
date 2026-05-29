import os
import requests
from dotenv import load_dotenv
from math import radians, sin, cos, sqrt, atan2

import numpy as np
from sklearn.cluster import DBSCAN

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Session-scoped cache: "kota kinabalu|malaysia" → {"kota kinabalu", "sabah", ...}
# Avoids repeated geocoding API calls for the same city within one run.
_city_token_cache: dict[str, set[str]] = {}


def resolve_city_tokens(city: str, country: str) -> set[str]:
    """
    Dynamically resolve all location tokens (city name + state/province
    short and long names) by geocoding the city itself.

    This replaces any hardcoded city→state map and works for any city
    worldwide — Malaysia, Indonesia, or beyond.

    Example:
        resolve_city_tokens("Kota Kinabalu", "Malaysia")
        → {"kota kinabalu", "sabah"}

        resolve_city_tokens("Yogyakarta", "Indonesia")
        → {"yogyakarta", "special region of yogyakarta", "di yogyakarta"}

        resolve_city_tokens("Denpasar", "Indonesia")
        → {"denpasar", "bali"}
    """
    cache_key = f"{city.lower().strip()}|{country.lower().strip()}"
    if cache_key in _city_token_cache:
        return _city_token_cache[cache_key]

    # Always include the raw city name as a fallback
    tokens: set[str] = {city.lower().strip()}

    if not GOOGLE_MAPS_API_KEY:
        _city_token_cache[cache_key] = tokens
        return tokens

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": f"{city}, {country}",
                "key": GOOGLE_MAPS_API_KEY,
            },
            timeout=30,
        )
        data = response.json()

        if data.get("status") == "OK":
            result = data["results"][0]
            for component in result.get("address_components", []):
                component_types = component.get("types", [])
                # Capture city, district, and state/province level names.
                # Skip postal_code, country, plus_code etc. — they are too
                # broad or irrelevant for address matching.
                if any(t in component_types for t in (
                    "locality",
                    "administrative_area_level_1",
                    "administrative_area_level_2",
                    "sublocality",
                    "sublocality_level_1",
                )):
                    tokens.add(component.get("long_name", "").lower())
                    tokens.add(component.get("short_name", "").lower())

            tokens.discard("")
            print(f"[resolve_city_tokens] '{city}' → {tokens}")

    except Exception as exc:
        print(f"[resolve_city_tokens] Warning for '{city}': {exc}")

    _city_token_cache[cache_key] = tokens
    return tokens


def geocode_pois(pois: list[str], city_hint: str = "") -> list[dict]:
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Missing GOOGLE_MAPS_API_KEY in .env")

    geocoded = []

    for poi in pois:
        query = f"{poi}, {city_hint}" if city_hint and city_hint.lower() not in poi.lower() else poi

        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": query,
                "key": GOOGLE_MAPS_API_KEY
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            print(f"Skipping {poi}: {data.get('status')}")
            continue

        result = data["results"][0]
        location = result["geometry"]["location"]

        geocoded.append({
            "name": poi,
            "formatted_address": result.get("formatted_address"),
            "lat": location["lat"],
            "lng": location["lng"],
            "types": result.get("types", [])
        })

    return geocoded


def validate_geocoded_pois(
    geocoded: list[dict],
    cities: list[str],
    country: str,
) -> list[dict]:
    """
    Keep only POIs whose Google-returned formatted_address actually belongs
    to one of the target cities (or their state/province).

    Each surviving POI gets a 'city' field so the prompt can group places
    by city — preventing the LLM from mixing e.g. KL landmarks into a
    Penang day.

    Accepted tokens are resolved dynamically via the Geocoding API — no
    hardcoded city→state mapping needed.  Works for Malaysia, Indonesia,
    or any country.
    """
    # Build a per-city token set so we can tag which city a POI belongs to.
    city_tokens: dict[str, set[str]] = {
        city: resolve_city_tokens(city, country)
        for city in cities
    }

    valid = []
    for poi in geocoded:
        address = poi.get("formatted_address", "").lower()
        matched_city = None

        for city, tokens in city_tokens.items():
            if any(token in address for token in tokens):
                matched_city = city
                break

        if matched_city:
            valid.append({**poi, "city": matched_city})
        else:
            all_tokens = set().union(*city_tokens.values())
            print(
                f"[validate] Dropped '{poi['name']}' — "
                f"geocoded to '{poi.get('formatted_address')}' "
                f"(expected tokens: {all_tokens})"
            )

    return valid


def haversine_km(lat1, lng1, lat2, lng2):
    radius_km = 6371

    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return radius_km * c


def build_local_distance_matrix(geocoded_pois: list[dict]) -> list[dict]:
    matrix = []

    for i, origin in enumerate(geocoded_pois):
        for j, destination in enumerate(geocoded_pois):
            if i == j:
                continue

            distance_km = haversine_km(
                origin["lat"],
                origin["lng"],
                destination["lat"],
                destination["lng"]
            )

            matrix.append({
                "from": origin["name"],
                "to": destination["name"],
                "distance_km": round(distance_km, 2)
            })

    return matrix


def cluster_pois(geocoded_pois: list[dict], radius_km: float = 2.5) -> list[dict]:
    if not geocoded_pois:
        return []

    coords = np.array([
        [poi["lat"], poi["lng"]]
        for poi in geocoded_pois
    ])

    coords_rad = np.radians(coords)

    earth_radius_km = 6371
    epsilon = radius_km / earth_radius_km

    clustering = DBSCAN(
        eps=epsilon,
        min_samples=1,
        metric="haversine"
    ).fit(coords_rad)

    clusters = {}

    for poi, label in zip(geocoded_pois, clustering.labels_):
        label = int(label)
        clusters.setdefault(label, []).append(poi)

    return [
        {
            "cluster_id": label,
            "places": places
        }
        for label, places in clusters.items()
    ]