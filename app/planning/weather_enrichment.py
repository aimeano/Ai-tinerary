from datetime import datetime, timedelta
import requests


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"


BAD_WEATHER_CODES = {
    51, 53, 55,
    61, 63, 65,
    66, 67,
    71, 73, 75,
    80, 81, 82,
    95, 96, 99,
}


def get_weather_source(date_str: str) -> str:
    today = datetime.now().date()
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    days_away = (target_date - today).days

    if 0 <= days_away <= 16:
        return "forecast"

    return "historical"


def get_reference_date(date_str: str) -> str:
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.now().date()

    days_away = (target_date - today).days

    if 0 <= days_away <= 16:
        return date_str

    last_year = target_date.replace(year=today.year - 1)
    return last_year.strftime("%Y-%m-%d")


def fetch_forecast_weather(lat: float, lng: float, date_str: str):
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lng,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
            "start_date": date_str,
            "end_date": date_str,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    return parse_daily_weather(data, date_str, "forecast")


def fetch_historical_weather(lat: float, lng: float, date_str: str):
    reference_date = get_reference_date(date_str)

    response = requests.get(
        HISTORICAL_URL,
        params={
            "latitude": lat,
            "longitude": lng,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
            "start_date": reference_date,
            "end_date": reference_date,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    weather = parse_daily_weather(data, reference_date, "historical")
    weather["original_date"] = date_str
    weather["reference_date"] = reference_date

    return weather


def parse_daily_weather(data: dict, date_str: str, source: str):
    daily = data.get("daily", {})

    dates = daily.get("time", [])

    if date_str not in dates:
        return {
            "available": False,
            "source": source,
            "date": date_str,
            "is_bad_weather": False,
            "note": "Weather data unavailable.",
        }

    index = dates.index(date_str)

    weather_code = daily.get("weather_code", [None])[index]
    precipitation = daily.get("precipitation_sum", [None])[index]
    temp_max = daily.get("temperature_2m_max", [None])[index]
    temp_min = daily.get("temperature_2m_min", [None])[index]

    is_bad = is_bad_weather(
        weather_code=weather_code,
        precipitation=precipitation,
    )

    return {
        "available": True,
        "source": source,
        "date": date_str,
        "weather_code": weather_code,
        "temperature_max": temp_max,
        "temperature_min": temp_min,
        "precipitation_sum": precipitation,
        "is_bad_weather": is_bad,
        "suggestion": get_weather_suggestion(is_bad),
        "updated_at": datetime.now().isoformat(),
    }


def is_bad_weather(weather_code, precipitation) -> bool:
    if weather_code in BAD_WEATHER_CODES:
        return True

    if isinstance(precipitation, (int, float)) and precipitation >= 5:
        return True

    return False


def get_weather_suggestion(is_bad: bool) -> str:
    if is_bad:
        return "Weather may affect this outdoor activity. Consider changing it to an indoor activity."

    return "Weather looks acceptable for this activity."


def get_activity_weather(activity: dict, date_str: str):
    lat = activity.get("latitude")
    lng = activity.get("longitude")

    if lat is None or lng is None:
        return {
            "available": False,
            "is_bad_weather": False,
            "note": "Missing activity coordinates.",
        }

    source = get_weather_source(date_str)

    try:
        if source == "forecast":
            return fetch_forecast_weather(lat, lng, date_str)

        return fetch_historical_weather(lat, lng, date_str)

    except Exception as e:
        return {
            "available": False,
            "source": source,
            "is_bad_weather": False,
            "note": str(e),
        }

def is_activity_weather_safe(activity: dict, geocoded: list[dict]) -> bool:
    title = (activity.get("title") or "").lower()
    location = (activity.get("location_name") or "").lower()

    for poi in geocoded:
        names = [
            poi.get("name", ""),
            poi.get("canonical_name", ""),
        ]

        if any(n and n.lower() in {title, location} for n in names):
            return poi.get("weather_suitability") in {"indoor", "mixed"}

    return False

def attach_weather_to_itinerary(itinerary: dict,geocoded: list[dict]) -> dict:
    for day in itinerary.get("days", []):
        date_str = day.get("date")

        if not date_str:
            continue

        for activity in day.get("activities", []):
            weather = get_activity_weather(
                activity=activity,
                date_str=date_str,
            )

            activity["weather"] = weather
            safe_for_weather = is_activity_weather_safe(activity, geocoded)

            if safe_for_weather:
                activity["weather"]["is_bad_weather"] = False
                activity["weather"]["suggestion"] = "This activity is weather-safe."
                activity["weather_action_available"] = False
            else:
                activity["weather_action_available"] = activity["weather"].get("is_bad_weather", False)

    return itinerary

