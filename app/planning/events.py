import os
import requests
from dotenv import load_dotenv

load_dotenv()

PREDICTHQ_API_KEY = os.getenv("PREDICTHQ_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

EVENT_CATEGORIES = (
    "concerts,festivals,performing-arts,sports,"
    "community,conferences,expos"
)


def geocode_city(city: str, country: str):
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Missing GOOGLE_MAPS_API_KEY")

    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "address": f"{city}, {country}",
            "key": GOOGLE_MAPS_API_KEY,
        },
    )

    response.raise_for_status()
    data = response.json()

    if not data.get("results"):
        raise ValueError(f"Could not geocode city: {city}, {country}")

    location = data["results"][0]["geometry"]["location"]

    return location["lat"], location["lng"]


def normalize_event(event: dict):
    location = event.get("location") or []

    return {
        "title": event.get("title"),
        "description": event.get("description"),
        "start": event.get("start"),
        "end": event.get("end"),
        "latitude": location[1] if len(location) == 2 else None,
        "longitude": location[0] if len(location) == 2 else None,
    }


def fetch_events_for_city(
    city: str,
    country: str,
    start_date: str,
    end_date: str,
    limit: int = 10,
    radius_km: int = 25,
):
    if not PREDICTHQ_API_KEY:
        raise ValueError("Missing PREDICTHQ_API_KEY")

    lat, lng = geocode_city(city, country)

    response = requests.get(
        "https://api.predicthq.com/v1/events/",
        headers={
            "Authorization": f"Bearer {PREDICTHQ_API_KEY}",
            "Accept": "application/json",
        },
        params={
            "within": f"{radius_km}km@{lat},{lng}",
            "start.gte": start_date,
            "start.lte": end_date,
            "category": EVENT_CATEGORIES,
            "rank_level": "3,4,5",
            "limit": limit,
            "sort": "start",
        },
    )

    response.raise_for_status()
    data = response.json()

    return [normalize_event(e) for e in data.get("results", [])]


def fetch_events_for_profile(profile: dict):
    country = profile["country"]
    start_date = profile["start_date"]
    end_date = profile["end_date"]

    events_by_city = {}

    for city in profile["cities"]:
        try:
            events_by_city[city] = fetch_events_for_city(
                city=city,
                country=country,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            print(f"Event fetch failed for {city}: {e}")
            events_by_city[city] = []

    return events_by_city