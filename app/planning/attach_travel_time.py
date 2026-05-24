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


def attach_travel_time(itinerary: dict):
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

            activity["travel_from_previous"] = get_travel_time(
                previous,
                activity
            )

    return itinerary