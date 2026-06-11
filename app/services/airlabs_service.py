import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRLABS_API_KEY = os.getenv("AIRLABS_API_KEY")

DAYS_MAP = {
    "mon": 0, "tue": 1, "wed": 2,
    "thu": 3, "fri": 4, "sat": 5, "sun": 6
}

def get_flight_schedule(flight_iata: str, travel_date: str) -> dict:
    """
    Look up scheduled departure and arrival times for a flight number
    using AirLabs Routes DB.

    Args:
        flight_iata: Flight number e.g. "AK6153"
        travel_date: Date string "YYYY-MM-DD"

    Returns dict with:
        dep_iata, dep_time, arr_iata, arr_time, duration, operates_on_date
    """
    if not AIRLABS_API_KEY:
        raise ValueError("Missing AIRLABS_API_KEY in .env")

    response = requests.get(
        "https://airlabs.co/api/v9/routes",
        params={
            "flight_iata": flight_iata.upper().strip(),
            "api_key": AIRLABS_API_KEY,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    routes = data.get("response", [])
    if not routes:
        return {"error": f"No route found for flight {flight_iata}"}

    route = routes[0]

    # Check if flight operates on the given travel date
    from datetime import datetime
    travel_dt = datetime.strptime(travel_date, "%Y-%m-%d")
    day_name = travel_dt.strftime("%a").lower()  # e.g. "mon"
    flight_days = [d.lower() for d in route.get("days", [])]
    operates = day_name in flight_days if flight_days else True

    return {
        "flight_iata": flight_iata.upper(),
        "dep_iata": route.get("dep_iata", ""),
        "dep_time": route.get("dep_time", ""),
        "arr_iata": route.get("arr_iata", ""),
        "arr_time": route.get("arr_time", ""),
        "duration_mins": route.get("duration", 0),
        "operates_on_date": operates,
        "operates_days": flight_days,
    }
