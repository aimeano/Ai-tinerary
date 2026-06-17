import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def get_travel_time(origin, destination):
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Missing GOOGLE_MAPS_API_KEY")

    modes = ["driving", "walking", "transit"]

    results = {}

    for mode in modes:
        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params={
                    "origins": f"{origin['latitude']},{origin['longitude']}",
                    "destinations": f"{destination['latitude']},{destination['longitude']}",
                    "mode": mode,
                    "key": GOOGLE_MAPS_API_KEY,
                },
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            element = data["rows"][0]["elements"][0]

            if element.get("status") != "OK":
                results[mode] = None
                continue

            results[mode] = {
                "distance": element["distance"]["text"],
                "duration": element["duration"]["text"],
                "duration_seconds": element["duration"]["value"],
            }

        except Exception as e:
            print(f"{mode} failed:", e)
            results[mode] = None

    return results


def attach_travel_time(
    itinerary: dict,
    cache: dict | None = None,
):
    cache = cache or {}

    for day in itinerary.get("days", []):

        activities = day.get("activities", [])

        for i, activity in enumerate(activities):

            if i == 0:
                activity["travel_from_previous"] = None
                continue

            previous = activities[i - 1]

            if not all([
                previous.get("latitude"),
                previous.get("longitude"),
                activity.get("latitude"),
                activity.get("longitude"),
            ]):
                activity["travel_from_previous"] = None
                continue

            key = make_travel_cache_key(
                previous,
                activity
            )

            if key in cache:
                activity["travel_from_previous"] = cache[key]
                continue

            travel_data = get_travel_time(
                previous,
                activity
            )

            cache[key] = travel_data

            activity["travel_from_previous"] = travel_data

            print("Travel cache size:", len(cache))

    return itinerary, cache

def make_travel_cache_key(origin, destination):
    return (
        f"{round(origin['latitude'],5)},"
        f"{round(origin['longitude'],5)}->"
        f"{round(destination['latitude'],5)},"
        f"{round(destination['longitude'],5)}"
    )