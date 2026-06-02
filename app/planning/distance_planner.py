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

# Session-scoped cache: "kota kinabalu|malaysia" → {"north": ..., "south": ..., ...}
# Populated as a side-effect of resolve_city_tokens; used in validate_geocoded_pois
# to reject POIs whose coordinates fall outside the city's real bounding box.
_city_bbox_cache: dict[str, dict | None] = {}

# Google Maps `types` that indicate the geocoder returned a real, specific
# place rather than a city / region / generic area.  If a geocoded result
# has none of these types we know Google fell back to the city centre — the
# POI name was too generic (e.g. "kopitiam", "mamak stalls") or doesn't
# exist in the requested city, so we drop it.
_SPECIFIC_POI_TYPES = frozenset({
    "point_of_interest",
    "establishment",
    "tourist_attraction",
    "restaurant",
    "food",
    "park",
    "museum",
    "place_of_worship",
    "shopping_mall",
    "amusement_park",
    "aquarium",
    "art_gallery",
    "zoo",
    "natural_feature",
    "stadium",
    "premise",
    "store",
    "cafe",
    "bar",
    "lodging",
    "university",
    "library",
    "transit_station",
    "bus_station",
    "train_station",
    "subway_station",
    "airport",
    "night_club",
    # Extra types commonly returned by the Places API for Malaysian attractions
    # (e.g. Chew Jetty / Clan Jetties were being skipped by the Geocoding API
    # because it classified them as administrative_area_level_1).
    "neighborhood",
    "route",
    "jetty",
    "heritage_site",
})


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
        _city_bbox_cache[cache_key] = None
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

            # Extract the city's bounding box for coordinate-level validation.
            geometry = result.get("geometry", {})
            bounds = geometry.get("bounds") or geometry.get("viewport")
            if bounds:
                bbox = {
                    "north": bounds["northeast"]["lat"],
                    "south": bounds["southwest"]["lat"],
                    "east":  bounds["northeast"]["lng"],
                    "west":  bounds["southwest"]["lng"],
                }

                # Clamp oversized bboxes (e.g. Kuala Lumpur's Google bounds
                # can span an entire state) to 0.3° centred on the city point.
                max_span = 0.3
                lat_center = (bbox["north"] + bbox["south"]) / 2
                lng_center = (bbox["east"]  + bbox["west"])  / 2
                lat_span   =  bbox["north"] - bbox["south"]
                lng_span   =  bbox["east"]  - bbox["west"]

                if lat_span > max_span:
                    bbox["north"] = lat_center + max_span / 2
                    bbox["south"] = lat_center - max_span / 2

                if lng_span > max_span:
                    bbox["east"] = lng_center + max_span / 2
                    bbox["west"] = lng_center - max_span / 2

                _city_bbox_cache[cache_key] = bbox
            else:
                _city_bbox_cache[cache_key] = None

            print(f"[resolve_city_tokens] '{city}' → tokens={tokens}, bbox={_city_bbox_cache[cache_key]}")

        else:
            _city_bbox_cache[cache_key] = None

    except Exception as exc:
        print(f"[resolve_city_tokens] Warning for '{city}': {exc}")
        _city_bbox_cache[cache_key] = None

    _city_token_cache[cache_key] = tokens
    return tokens


def get_city_bbox(city: str, country: str) -> dict | None:
    """
    Return the cached bounding box for a city, or fetch it by triggering
    resolve_city_tokens (which populates _city_bbox_cache as a side-effect).
    Returns None when no bbox is available (API key missing, API error, etc.).
    """
    cache_key = f"{city.lower().strip()}|{country.lower().strip()}"
    if cache_key not in _city_bbox_cache:
        resolve_city_tokens(city, country)
    return _city_bbox_cache.get(cache_key)


def _within_bbox(lat: float, lng: float, bbox: dict) -> bool:
    """Return True if the coordinate falls inside the given bounding box."""
    return (
        bbox["south"] <= lat <= bbox["north"]
        and bbox["west"] <= lng <= bbox["east"]
    )


def geocode_pois(pois: list[str], city_hint: str = "") -> list[dict]:
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Missing GOOGLE_MAPS_API_KEY in .env")

    geocoded = []

    for poi in pois:
        query = f"{poi}, {city_hint}" if city_hint and city_hint.lower() not in poi.lower() else poi

        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
            params={
                "input": query,
                "inputtype": "textquery",
                "fields": "name,geometry,formatted_address,types,place_id",
                "key": GOOGLE_MAPS_API_KEY,
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK" or not data.get("candidates"):
            print(f"[geocode] Skipping '{poi}': {data.get('status')}")
            continue

        candidate = data["candidates"][0]
        location = candidate["geometry"]["location"]
        types = candidate.get("types", [])

        # Drop city-level fallbacks: if the Places API returned only a
        # locality / political / administrative result the POI name is too
        # generic or doesn't exist as a real place in the target city.
        if not _SPECIFIC_POI_TYPES.intersection(types):
            print(
                f"[geocode] Skipping '{poi}': result is a city/region, "
                f"not a specific place (types={types})"
            )
            continue

        geocoded.append({
            "name": poi,
            "formatted_address": candidate.get("formatted_address"),
            "lat": location["lat"],
            "lng": location["lng"],
            "types": types,
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

        if not matched_city:
            all_tokens = set().union(*city_tokens.values())
            print(
                f"[validate] Dropped '{poi['name']}' — "
                f"geocoded to '{poi.get('formatted_address')}' "
                f"(expected tokens: {all_tokens})"
            )
            continue

        # Second check: coordinates must fall within the city's bounding box.
        # This catches cases where the address string matched but the actual
        # lat/lng lands in a different city (e.g. a suburb that shares a name).
        bbox = get_city_bbox(matched_city, country)
        if bbox:
            lat, lng = poi.get("lat"), poi.get("lng")
            if lat is not None and lng is not None and not _within_bbox(lat, lng, bbox):
                print(
                    f"[validate] Dropped '{poi['name']}' — "
                    f"lat/lng ({lat}, {lng}) is outside {matched_city} bbox {bbox}"
                )
                continue

        valid.append({**poi, "city": matched_city})

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