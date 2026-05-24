import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def find_restaurants_near_point(
    latitude: float,
    longitude: float,
    limit: int = 3,
    radius: int = 300,
):
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Missing GOOGLE_MAPS_API_KEY")

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    params = {
        "location": f"{latitude},{longitude}",
        "radius": radius,
        "type": "restaurant",
        "keyword": "local food restaurant",
        "key": GOOGLE_MAPS_API_KEY,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    restaurants = []

    for item in data.get("results", [])[:limit]:
        loc = item.get("geometry", {}).get("location", {})

        restaurants.append({
            "name": item.get("name"),
            "link": f"https://www.google.com/maps/place/?q=place_id:{item.get('place_id')}"
        })

        
    return restaurants


def attach_restaurants_to_itinerary(
    itinerary: dict,
    limit_per_activity: int = 3,
):
    for day in itinerary.get("days", []):
        for activity in day.get("activities", []):
            lat = activity.get("latitude")
            lng = activity.get("longitude")

            if lat is None or lng is None:
                activity["nearby_restaurants"] = []
                continue

            activity["nearby_restaurants"] = find_restaurants_near_point(
                latitude=lat,
                longitude=lng,
                limit=limit_per_activity,
            )

    return itinerary