import requests

geocode_cache = {}


def geocode_place_smart(place_name: str, city: str = "") -> dict:
    """
    Converts a place name to lat/lon coordinates.
    Checks memory cache before making an external API call.

    Args:
        place_name: e.g. "Lotte World Tower"
        city:       destination city as a search hint e.g. "Seoul"

    Returns:
        dict with lat, lon, city, display_name
        OR None if place not found
    """
    cache_key = place_name.strip().lower()

    # ── Level 1: Check memory cache ────────────────────────
    if cache_key in geocode_cache:
        print(f"    ⚡ Cache hit: '{place_name}'")
        return geocode_cache[cache_key]

    # ── Level 2: Call Nominatim API ─────────────────────────
    # For AWS deployment: swap Nominatim for Google Maps
    # Geocoding API ($0.005 per call)
    print(f"    🌐 Geocoding: '{place_name}'...")
    coords = _call_nominatim(place_name, city)

    if coords:
        # Save to cache so we never call this again
        geocode_cache[cache_key] = coords
        # On AWS: also save to DynamoDB / RDS here

    return coords


def _call_nominatim(place_name: str, city: str = "") -> dict:
    """
    Internal function — calls OpenStreetMap Nominatim.
    Tries multiple search variations before giving up.
    """
    headers = {"User-Agent": "ItineraryPlannerApp/1.0 (student_project)"}

    # Attempt 1 — with city hint
    query = f"{place_name}, {city}" if city and city.lower() \
            not in place_name.lower() else place_name

    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json",
                "limit": 1, "addressdetails": 1},
        headers=headers
    )
    results = r.json()

    # Attempt 2 — without city hint
    if not results and city:
        r2 = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place_name, "format": "json",
                    "limit": 1, "addressdetails": 1},
            headers=headers
        )
        results = r2.json()

    # Attempt 3 — first 3 words only (shorter query)
    if not results:
        short = " ".join(place_name.split()[:3])
        if short != place_name:
            r3 = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": short, "format": "json",
                        "limit": 1, "addressdetails": 1},
                headers=headers
            )
            results = r3.json()

    if not results:
        print(f"    ❌ Could not find: '{place_name}'")
        print(f"       Try: '{place_name}, {city}' or be more specific")
        return None

    top     = results[0]
    address = top.get("address", {})
    city_found = (
        address.get("city") or
        address.get("town") or
        address.get("village") or
        city or
        place_name
    )

    return {
        "lat":          float(top["lat"]),
        "lon":          float(top["lon"]),
        "city":         city_found,
        "display_name": top["display_name"]
    }

