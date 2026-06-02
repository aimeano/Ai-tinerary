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
        activities = day.get("activities", [])

        for i, activity in enumerate(activities):
            lat = activity.get("latitude")
            lng = activity.get("longitude")

            if lat is None or lng is None:
                activity["nearby_restaurants"] = []
                continue

            # Food activities that share coordinates with the previous activity
            # are anchored to a nearby landmark rather than their own venue.
            # Widen the search radius so the restaurant options are actually
            # walkable from that shared location.
            is_food = activity.get("category", "").lower() == "food"
            shares_coords = (
                i > 0
                and activities[i - 1].get("latitude") == lat
                and activities[i - 1].get("longitude") == lng
            )
            radius = 800 if (is_food and shares_coords) else 300

            activity["nearby_restaurants"] = find_restaurants_near_point(
                latitude=lat,
                longitude=lng,
                limit=limit_per_activity,
                radius=radius,
            )

    return itinerary