import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from math import radians, sin, cos, sqrt, atan2

import numpy as np
from sklearn.cluster import DBSCAN


load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
CACHE_PATH = Path("app/data/cache/geocode_cache.json")
_city_token_cache = {}
_city_bbox_cache = {}


# =========================
# Cache
# =========================

def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def make_cache_key(name: str, cities: list[str], country_hint: str):
    city_part = "|".join(sorted([c.lower().strip() for c in cities]))
    return f"{name.lower().strip()}|{city_part}|{country_hint.lower().strip()}"


# =========================
# Distance
# =========================

def haversine_km(lat1, lng1, lat2, lng2):
    radius_km = 6371

    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlng / 2) ** 2
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
                destination["lng"],
            )

            matrix.append({
                "from": origin["name"],
                "to": destination["name"],
                "distance_km": round(distance_km, 2),
            })

    return matrix


# =========================
# Google API
# =========================

def geocode_one(query: str):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "address": query,
            "key": GOOGLE_MAPS_API_KEY,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if data.get("status") != "OK" or not data.get("results"):
        return None

    return data["results"][0]


def search_place_one(query: str):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        params={
            "query": query,
            "key": GOOGLE_MAPS_API_KEY,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if data.get("status") not in ["OK", "ZERO_RESULTS"]:
        print("GOOGLE STATUS:", data.get("status"))
        print(data)

    if data.get("status") != "OK":
        return None

    results = data.get("results", [])
    if not results:
        return None

    return results[0]


# =========================
# City helpers
# =========================

def resolve_city_tokens(city: str, country: str) -> set[str]:
    cache_key = f"{city.lower().strip()}|{country.lower().strip()}"

    if cache_key in _city_token_cache:
        return _city_token_cache[cache_key]

    tokens = {city.lower().strip()}

    if not GOOGLE_MAPS_API_KEY:
        _city_token_cache[cache_key] = tokens
        _city_bbox_cache[cache_key] = None
        return tokens

    try:
        result = geocode_one(f"{city}, {country}")

        if not result:
            _city_bbox_cache[cache_key] = None
            _city_token_cache[cache_key] = tokens
            return tokens

        for component in result.get("address_components", []):
            component_types = component.get("types", [])

            if any(t in component_types for t in (
                "locality",
                "administrative_area_level_1",
                "administrative_area_level_2",
                "sublocality",
                "sublocality_level_1",
            )):
                tokens.add(component.get("long_name", "").lower().strip())
                tokens.add(component.get("short_name", "").lower().strip())

        tokens.discard("")

        geometry = result.get("geometry", {})
        bounds = geometry.get("bounds") or geometry.get("viewport")

        if bounds:
            bbox = {
                "north": bounds["northeast"]["lat"],
                "south": bounds["southwest"]["lat"],
                "east": bounds["northeast"]["lng"],
                "west": bounds["southwest"]["lng"],
            }


            _city_bbox_cache[cache_key] = bbox
        else:
            _city_bbox_cache[cache_key] = None

    except Exception as exc:
        print(f"[resolve_city_tokens] Warning for {city}: {exc}")
        _city_bbox_cache[cache_key] = None

    _city_token_cache[cache_key] = tokens
    return tokens

def get_parent_retrieval_locations(
    cities: list[str],
    country: str,
) -> list[str]:
    locations = []

    for city in cities:
        tokens = resolve_city_tokens(city, country)
        city_norm = city.lower().strip()

        parent_tokens = [
            token for token in tokens
            if token != city_norm
        ]
        if parent_tokens:
            location = parent_tokens[0].title()
        else:
            location = city.title()
        locations.append(location)
    return locations  


def get_city_center(city: str, country_hint: str = ""):
    query = f"{city}, {country_hint}" if country_hint else city
    result = geocode_one(query)

    if not result:
        print(f"Could not geocode city center: {query}")
        return None

    location = result["geometry"]["location"]

    resolve_city_tokens(city, country_hint)

    return {
        "name": city,
        "lat": location["lat"],
        "lng": location["lng"],
        "tokens": resolve_city_tokens(city, country_hint),
        "bbox": _city_bbox_cache.get(
            f"{city.lower().strip()}|{country_hint.lower().strip()}"
        ),
    }


def get_city_centers(cities: list[str], country_hint: str = ""):
    centers = []

    for city in cities:
        center = get_city_center(city, country_hint)

        if center:
            centers.append(center)

    return centers


def point_inside_bbox(lat: float, lng: float, bbox: dict | None) -> bool:
    if not bbox:
        return False

    return (
        bbox["south"] <= lat <= bbox["north"]
        and bbox["west"] <= lng <= bbox["east"]
    )

def estimate_city_radius_km(
    center: dict,
    fallback_km: float = 35.0,
    min_km: float = 50.0,
    max_km: float = 80.0,
) -> float:
    bbox = center.get("bbox")

    if not bbox:
        return fallback_km

    mid_lat = (bbox["north"] + bbox["south"]) / 2
    mid_lng = (bbox["east"] + bbox["west"]) / 2

    corners = [
        (bbox["north"], bbox["east"]),
        (bbox["north"], bbox["west"]),
        (bbox["south"], bbox["east"]),
        (bbox["south"], bbox["west"]),
    ]

    bbox_radius = max(
        haversine_km(mid_lat, mid_lng, lat, lng)
        for lat, lng in corners
    )

    dynamic_radius = bbox_radius * 1.8

    return min(
        max(dynamic_radius, min_km),
        max_km,
    )


def find_nearest_city(lat: float, lng: float, city_centers: list[dict]):
    nearest_city = None
    nearest_distance = float("inf")

    for center in city_centers:
        bbox = center.get("bbox")

        if point_inside_bbox(lat, lng, bbox):
            return center["name"], 0.0

        distance = haversine_km(
            lat,
            lng,
            center["lat"],
            center["lng"],
        )

        if distance < nearest_distance:
            nearest_city = center["name"]
            nearest_distance = distance

    return nearest_city, nearest_distance

# =========================
# Google result validation
# =========================
def is_bad_activity_result(result: dict) -> bool:
    types = set(result.get("types", []))

    bad_types = {
        # Accommodation
        "lodging",

        # Government
        "local_government_office",

        # Health
        "hospital",
        "doctor",
        "health",

        # Emergency
        "police",
        "fire_station",

        # Admin / business
        "embassy",
        "courthouse",
        "accounting",
        "insurance_agency",

        # Transport
        "bus_station",
        "transit_station",

        # Finance
        "atm",
        "bank",

        # Utilities
        "parking",
        "gas_station",

        # Education
        "school",
        "secondary_school",
        "primary_school",

        # Residential
        "real_estate_agency",
        "apartment",
    }

    return bool(types & bad_types)

def is_admin_or_region_result(result: dict) -> bool:
    types = set(result.get("types", []))

    poi_types = {
        "tourist_attraction",
        "point_of_interest",
        "establishment",
        "park",
        "museum",
        "shopping_mall",
        "restaurant",
        "cafe",
        "place_of_worship",
        "amusement_park",
        "zoo",
        "library",
        "university",
        "stadium",
        "aquarium",
        "art_gallery",
        "natural_feature",
        "store",
        "food",
    }

    admin_types = {
        "country",
        "administrative_area_level_1",
        "administrative_area_level_2",
        "administrative_area_level_3",
        "locality",
    }

    if types & poi_types:
        return False

    return bool(types & admin_types)

def is_bad_name(name: str) -> bool:
    name = name.lower()

    BAD_NAME_KEYWORDS = {
    "hotel",
    "hostel",
    "residence",
    "residences",
    "suite",
    "suites",
    "condominium",
    "condominuim",

    "wisma",
    "jabatan",
    "ministry",
    "department",
    "embassy",

    "hospital",
    "clinic",
    "medical",

    "police",
    "balai polis",

    "terminal",
    "bus terminal",

    "university",
    "college",
    "school",

    "library",

    "court",
    "courthouse",

    "office",
}

    return any(
        keyword in name
        for keyword in BAD_NAME_KEYWORDS
    )

def infer_category(place: dict) -> str:
    types = set(place.get("types", []))

    if "museum" in types or "art_gallery" in types:
        return "culture"

    if "park" in types or "natural_feature" in types:
        return "nature"

    if "shopping_mall" in types or "store" in types:
        return "shopping"

    if "restaurant" in types or "cafe" in types or "food" in types:
        return "food"

    if "place_of_worship" in types:
        return "religious"

    if "aquarium" in types or "zoo" in types or "amusement_park" in types:
        return "entertainment"

    if "tourist_attraction" in types:
        return "attraction"

    return "other"

def infer_weather_suitability(place: dict) -> str:
    types = set(place.get("types", []))
    name = normalize_text(place.get("name", ""))

    outdoor_types = {
        "park",
        "camping_cabin",
        "campground",
        "rv_park",
        "hiking_area",
        "beach",
        "marina",
        "farmstay",
        "cemetery",
        "golf_course",
        "playground",
        "amusement_park",
        "zoo",
        "botanical_garden",
        "historical_landmark",
        "natural_feature",
    }

    indoor_types = {
        "shopping_mall",
        "department_store",
        "supermarket",
        "grocery_store",
        "museum",
        "art_gallery",
        "movie_theater",
        "bowling_alley",
        "casino",
        "aquarium",
        "gym",
        "arena",
        "planetarium",
        "library",
        "convention_center",
        "airport",
        "subway_station",
    }

    outdoor_keywords = {
        "beach",
        "island",
        "park",
        "garden",
        "waterfall",
        "hill",
        "mount",
        "mountain",
        "trail",
        "wetland",
        "forest",
        "lake",
        "river",
        "marina",
        "jetty",
        "esplanade",
        "waterfront",
        "golf",
        "farm",
    }

    indoor_keywords = {
        "museum",
        "gallery",
        "mall",
        "aquarium",
        "planetarium",
        "theatre",
        "theater",
        "cinema",
        "library",
        "convention",
        "indoor",
        "complex",
        "centre",
        "center",
    }

    if types & indoor_types:
        return "indoor"

    if types & outdoor_types:
        return "outdoor"

    if any(word in name for word in indoor_keywords):
        return "indoor"

    if any(word in name for word in outdoor_keywords):
        return "outdoor"

    return "mixed"

def normalize_place_name(value: str) -> str:
    return (value or "").lower().strip()


def find_city_for_activity(
    activity: dict,
    clusters: list[dict],
) -> str | None:
    activity_lat = activity.get("latitude")
    activity_lng = activity.get("longitude")

    activity_names = {
        normalize_place_name(activity.get("title")),
        normalize_place_name(activity.get("location_name")),
    }

    # 1. Coordinate match with tolerance
    if activity_lat is not None and activity_lng is not None:
        for cluster in clusters:
            for poi in cluster.get("places", []):
                poi_lat = poi.get("lat")
                poi_lng = poi.get("lng")

                if poi_lat is None or poi_lng is None:
                    continue

                if (
                    abs(float(activity_lat) - float(poi_lat)) < 0.0002
                    and abs(float(activity_lng) - float(poi_lng)) < 0.0002
                ):
                    return cluster.get("assigned_city")

    # 2. Name fallback
    for cluster in clusters:
        for poi in cluster.get("places", []):
            poi_names = {
                normalize_place_name(poi.get("name")),
                normalize_place_name(poi.get("canonical_name")),
            }

            if activity_names & poi_names:
                return cluster.get("assigned_city")

    return None

def get_weather_safe_clusters(
    clusters: list[dict],
    city: str,
) -> list[dict]:

    filtered_clusters = []

    allowed_weather = {
        "indoor",
        "mixed",
        "hybrid",
    }
    print("\n===== INSIDE get_weather_safe_clusters =====")
    print("city:", city)
    print("clusters:", len(clusters))

    for cluster in clusters:
        print(
            cluster.get("cluster_id"),
            cluster.get("assigned_city"),
            [
                poi.get("weather_suitability")
                for poi in cluster.get("places", [])
            ],
        )

    for cluster in clusters:

        if cluster.get("assigned_city") != city:
            continue

        safe_places = [
            poi
            for poi in cluster.get("places", [])
            if poi.get("weather_suitability") in allowed_weather
        ]

        if not safe_places:
            continue

        filtered_clusters.append({
            **cluster,
            "places": safe_places,
            "size": len(safe_places),
        })

    return filtered_clusters

def filter_indoor_clusters(clusters):
    indoor_clusters = []

    for cluster in clusters:
        indoor_places = [
            p
            for p in cluster["places"]
            if p.get("weather_suitability") == "indoor"
        ]

        if not indoor_places:
            continue

        indoor_clusters.append({
            **cluster,
            "places": indoor_places,
            "size": len(indoor_places),
        })

    return indoor_clusters


def validate_google_result(
    poi_name: str,
    result: dict,
    city_centers: list[dict],
    max_distance_from_city_km: float,
):
    if not result:
        return None, "No Google result"

    location = result.get("geometry", {}).get("location")

    if not location:
        return None, "No valid coordinates"

    place_id = result.get("place_id")

    if not place_id:
        return None, "No place_id"

    if is_admin_or_region_result(result):
        return None, "Administrative/region result"
    
    if is_bad_activity_result(result):
        return None, f"Bad activity type: {result.get('types')}"
    
    if is_bad_name(result.get("name", "")):
        return None, "Blacklisted place name"

    lat = location["lat"]
    lng = location["lng"]

    assigned_city = None
    distance_from_city = None
    allowed_radius_km = None

    if city_centers:
        assigned_city, distance_from_city = find_nearest_city(
            lat,
            lng,
            city_centers,
        )

        inside_any_bbox = any(
            point_inside_bbox(lat, lng, center.get("bbox"))
            for center in city_centers
        )

        nearest_center = next(
            (
                center for center in city_centers
                if center["name"] == assigned_city
            ),
            None,
        )

        dynamic_radius_km = (
            estimate_city_radius_km(
                nearest_center,
                max_km=max_distance_from_city_km,
            )
            if nearest_center
            else max_distance_from_city_km
        )

        allowed_radius_km = max(
            dynamic_radius_km,
            max_distance_from_city_km,
        )

        if not inside_any_bbox and distance_from_city > allowed_radius_km:
            return None, (
                f"Too far from {assigned_city}: "
                f"{distance_from_city:.1f} km > allowed {allowed_radius_km:.1f} km"
            )

    google_maps_url = (
        f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        if place_id
        else f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    )
    canonical = {
        "name": poi_name,
        "canonical_name": result.get("name") or poi_name,
        "formatted_address": result.get("formatted_address"),
        "place_id": place_id,
        "google_maps_url": google_maps_url,
        "lat": lat,
        "lng": lng,
        "types": result.get("types", []),
        "category": infer_category(result),
        "assigned_city": assigned_city,
        "weather_suitability": infer_weather_suitability(result),
        "distance_from_city_km": round(distance_from_city, 2)
        if distance_from_city is not None
        else None,
        "allowed_radius_km": round(allowed_radius_km, 2)
        if city_centers
        else None,
        "verified": True,
    }

    return canonical, None


def geocode_pois(
    pois: list[str],
    cities: list[str],
    country_hint: str = "",
    max_distance_from_city_km: float = 80.0,
) -> list[dict]:
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Missing GOOGLE_MAPS_API_KEY in .env")

    cache = load_cache()
    geocoded = []
    seen_place_ids = set()

    print("\n===== GEOCODE SETTINGS =====")
    print("cities:", cities)
    print("country_hint:", country_hint)
    print("max_distance_from_city_km:", max_distance_from_city_km)

    city_centers = get_city_centers(cities, country_hint)

    for poi in pois:
        cache_key = make_cache_key(poi, cities, country_hint)

        if cache_key in cache:
            cached = cache[cache_key]

            if cached.get("accepted"):
                item = cached["data"]

                if item["place_id"] not in seen_place_ids:
                    item["category"] = item.get("category") or infer_category(item)
                    geocoded.append(item)
                    seen_place_ids.add(item["place_id"])
            else:
                print(f"Skipping cached rejected POI: {poi} -> {cached.get('reason')}")

            continue

        query_parts = [poi]

        if cities:
            query_parts.append(" or ".join(cities))

        if country_hint:
            query_parts.append(country_hint)

        query = ", ".join(query_parts)

        result = search_place_one(query)

        canonical, reason = validate_google_result(
            poi_name=poi,
            result=result,
            city_centers=city_centers,
            max_distance_from_city_km=max_distance_from_city_km,
        )

        if reason:
            print(
                f"Rejected POI: {poi} -> {reason} | "
                f"types={result.get('types') if result else None}"
            )

            cache[cache_key] = {
                "accepted": False,
                "reason": reason,
            }
            continue

        if canonical["place_id"] in seen_place_ids:
            continue

        cache[cache_key] = {
            "accepted": True,
            "data": canonical,
        }

        geocoded.append(canonical)
        seen_place_ids.add(canonical["place_id"])

    save_cache(cache)
    return geocoded


# =========================
# POI scoring
# =========================

def normalize_text(value: str) -> str:
    return value.lower().strip() if isinstance(value, str) else ""


def score_poi(poi: dict, profile: dict) -> float:
    score = 0.0

    poi_name = normalize_text(poi.get("name", ""))
    category = normalize_text(poi.get("category", ""))
    types = [normalize_text(t) for t in poi.get("types", [])]

    interests = [
        normalize_text(i)
        for i in profile.get("interests", [])
    ]

    must_include = [
        normalize_text(m)
        for m in profile.get("must_include", [])
    ]

    # =====================
    # Must include boost
    # =====================

    for item in must_include:
        if item and item in poi_name:
            score += 0.50

    # =====================
    # Interest matching
    # =====================

    for interest in interests:
        if interest and interest in category:
            score += 0.30

        if interest and interest in poi_name:
            score += 0.25

        if interest and interest in types:
            score += 0.20

    # =====================
    # Attraction boost
    # =====================

    attraction_types = {
        "tourist_attraction",
        "museum",
        "park",
        "aquarium",
        "zoo",
        "art_gallery",
        "natural_feature",
        "amusement_park",
        "place_of_worship",
    }

    if any(t in attraction_types for t in types):
        score += 0.30

    # =====================
    # Verified Google place
    # =====================

    if poi.get("verified"):
        score += 0.15

    if poi.get("place_id"):
        score += 0.10

    # =====================
    # Distance bonus
    # =====================

    distance = poi.get("distance_from_city_km")

    if isinstance(distance, (int, float)):
        if distance <= 5:
            score += 0.10
        elif distance <= 15:
            score += 0.05

    # =====================
    # Mention frequency bonus
    # =====================

    mention_count = poi.get("mention_count", 1)

    score += min(
        mention_count * 0.05,
        0.30,
    )

    # =====================
    # Penalize generic places
    # =====================

    generic_types = {
        "establishment",
        "premise",
        "subpremise",
    }

    if set(types).issubset(generic_types):
        score -= 0.30

    # =====================
    # Bad keywords
    # =====================

    bad_keywords = {
        "wisma",
        "jabatan",
        "department",
        "ministry",
        "office",
        "condominium",
        "residence",
        "suite",
        "hotel",
        "hospital",
        "clinic",
        "terminal",
        "bus station",
        "police",
        "fire station",
        "government",
        "embassy",
        "court",
    }

    if any(word in poi_name for word in bad_keywords):
        score -= 0.40

    return round(score, 4)


def score_pois(
    pois: list[dict],
    profile: dict,
) -> list[dict]:

    scored = []

    for poi in pois:
        poi = {
            **poi,
            "category": poi.get("category")
            or infer_category(poi),
        }

        scored_poi = {
            **poi,
            "poi_score": score_poi(
                poi,
                profile,
            ),
        }

        scored.append(scored_poi)

    scored.sort(
        key=lambda x: x["poi_score"],
        reverse=True,
    )

    # Remove weak POIs
    scored = [
        poi
        for poi in scored
        if poi["poi_score"] >= 0.35
    ]

    return scored

# =========================
# Clustering
# =========================

def cluster_single_city_pois(
    geocoded_pois: list[dict],
    radius_km: float = 1.0,
    max_pois_per_cluster: int = 8,
) -> list[dict]:
    if not geocoded_pois:
        return []

    # Start with strongest POIs first
    remaining = sorted(
        geocoded_pois,
        key=lambda p: p.get("poi_score", 0),
        reverse=True,
    )

    clusters = []
    cluster_id = 0

    while remaining:
        seed = remaining.pop(0)
        cluster_places = [seed]

        # Keep adding nearest POIs to this cluster
        while len(cluster_places) < max_pois_per_cluster:
            best_index = None
            best_distance = float("inf")

            for i, candidate in enumerate(remaining):
                # candidate can join if near ANY current POI in cluster
                nearest_distance = min(
                    haversine_km(
                        candidate["lat"],
                        candidate["lng"],
                        existing["lat"],
                        existing["lng"],
                    )
                    for existing in cluster_places
                )

                if nearest_distance <= radius_km and nearest_distance < best_distance:
                    best_index = i
                    best_distance = nearest_distance

            if best_index is None:
                break

            cluster_places.append(
                remaining.pop(best_index)
            )

        center_lat = sum(p["lat"] for p in cluster_places) / len(cluster_places)
        center_lng = sum(p["lng"] for p in cluster_places) / len(cluster_places)

        clusters.append({
            "cluster_id": cluster_id,
            "assigned_city": cluster_places[0].get("assigned_city"),
            "center": {
                "lat": center_lat,
                "lng": center_lng,
            },
            "places": cluster_places,
            "size": len(cluster_places),
        })

        cluster_id += 1

    return clusters


def cluster_pois(
    geocoded_pois: list[dict],
    radius_km: float = 1.0,
    max_pois_per_cluster: int = 8,
) -> list[dict]:
    if not geocoded_pois:
        return []

    by_city = {}

    for poi in geocoded_pois:
        city = poi.get("assigned_city") or "Unknown"
        by_city.setdefault(city, []).append(poi)

    all_clusters = []

    for city, city_pois in by_city.items():
        city_clusters = cluster_single_city_pois(
            city_pois,
            radius_km=radius_km,
            max_pois_per_cluster=max_pois_per_cluster,
        )

        for cluster in city_clusters:
            cluster["cluster_id"] = f"{city}_{cluster['cluster_id']}"

        all_clusters.extend(city_clusters)

    return all_clusters

def select_clusters_for_llm(
    city_contexts: dict,
    max_clusters_per_city: int = 5,
    max_pois_per_cluster: int = 6,
) -> list[dict]:
    selected = []

    for city, context in city_contexts.items():
        clusters = context.get("clusters", [])

        clusters = sorted(
            clusters,
            key=lambda x: x.get("cluster_score", 0),
            reverse=True,
        )

        for cluster in clusters[:max_clusters_per_city]:
            selected.append({
                **cluster,
                "places": cluster.get("places", [])[:max_pois_per_cluster],
                "size": min(cluster.get("size", 0), max_pois_per_cluster),
            })

    return selected


# =========================
# Cluster scoring
# =========================

def average_pairwise_distance_km(places: list[dict]) -> float:
    if len(places) < 2:
        return 0.0

    distances = []

    for i in range(len(places)):
        for j in range(i + 1, len(places)):
            d = haversine_km(
                places[i]["lat"],
                places[i]["lng"],
                places[j]["lat"],
                places[j]["lng"],
            )
            distances.append(d)

    return sum(distances) / len(distances)


def score_cluster(cluster: dict, profile: dict) -> float:
    places = cluster.get("places", [])

    if not places:
        return 0.0

    poi_scores = [place.get("poi_score", 0) for place in places]
    avg_poi_score = sum(poi_scores) / len(poi_scores)

    categories = set(
        normalize_text(place.get("category", "other"))
        for place in places
    )

    diversity_score = min(len(categories) / 4, 1.0) * 0.30
    size_score = min(len(places) / 5, 1.0) * 0.20

    avg_distance = average_pairwise_distance_km(places)

    if len(places) == 1:
        compactness_score = -0.10
    elif avg_distance <= 1:
        compactness_score = 0.25
    elif avg_distance <= 2:
        compactness_score = 0.20
    elif avg_distance <= 5:
        compactness_score = 0.10
    else:
        compactness_score = 0.0

    must_include_score = 0.0
    must_include = [
        normalize_text(m)
        for m in profile.get("must_include", [])
    ]

    for place in places:
        name = normalize_text(place.get("name", ""))

        for item in must_include:
            if item and item in name:
                must_include_score += 0.35

    # Penalize boring mall-heavy clusters
    mall_count = sum(
        1
        for place in places
        if place.get("category") == "shopping"
    )

    mall_ratio = mall_count / len(places)

    mall_penalty = 0.25 if mall_ratio >= 0.60 else 0.0

    attraction_count = sum(
        1
        for p in places
        if p.get("category") in {
            "attraction",
            "nature",
            "culture",
            "entertainment",
            "religious",
        }
    )

    cluster_quality = attraction_count / len(places)

    quality_bonus = cluster_quality * 0.40

    final_score = (
        avg_poi_score
        + diversity_score
        + size_score
        + compactness_score
        + must_include_score
        + quality_bonus
        - mall_penalty
    )

    return round(final_score, 4)


def score_clusters(clusters: list[dict], profile: dict) -> list[dict]:
    scored = []

    for cluster in clusters:
        scored.append({
            **cluster,
            "cluster_score": score_cluster(cluster, profile),
        })

    return sorted(
        scored,
        key=lambda x: x["cluster_score"],
        reverse=True,
    )




