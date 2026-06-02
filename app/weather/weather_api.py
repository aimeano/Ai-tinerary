from datetime import datetime, timedelta
import requests


def get_historical_weather(lat: float, lon: float,
                            trip_date_str: str) -> dict:
    """
    Fetches weather data from the same date one year ago.
    Used as a reference when the trip is more than 16 days away.
    Free via Open-Meteo — no API key needed.
    """
    trip_date      = datetime.strptime(trip_date_str, "%Y-%m-%d")
    last_year_date = (trip_date - timedelta(days=365)).strftime("%Y-%m-%d")

    try:
        r = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude":   lat,
                "longitude":  lon,
                "start_date": last_year_date,
                "end_date":   last_year_date,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "windspeed_10m_max"
                ],
                "timezone": "auto"
            }
        )

        if r.status_code != 200 or not r.text.strip():
            print(f"    ❌ Open-Meteo historical error: {r.status_code}")
            return None

        d        = r.json()["daily"]
        rainfall = d["precipitation_sum"][0]
        temp_max = d["temperature_2m_max"][0]
        temp_min = d["temperature_2m_min"][0]
        wind     = d["windspeed_10m_max"][0]

        if rainfall > 10:
            suggestion = "Heavy rain last year — strongly recommend indoor alternatives"
        elif rainfall > 5:
            suggestion = "Light rain last year — consider bringing umbrella or backup plan"
        elif wind > 40:
            suggestion = "Windy conditions last year — check outdoor activity suitability"
        else:
            suggestion = "Good weather last year on this date — plan looks fine"

        return {
            "mode":           "historical",
            "reference_date": last_year_date,
            "temp_max":       temp_max,
            "temp_min":       temp_min,
            "rainfall_mm":    rainfall,
            "wind_kmh":       wind,
            "was_rainy":      rainfall > 5,
            "suggestion":     suggestion,
            "is_estimate":    True,
            "checked_at":     datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    except Exception as e:
        print(f"    ❌ Historical weather fetch failed: {e}")
        return None


def get_forecast_weather(lat: float, lon: float,
                          trip_date_str: str) -> dict:
    """
    Fetches forecast weather for a specific date.
    Works up to 16 days ahead.
    Free via Open-Meteo — no API key needed.
    Updates every hour.

    Args:
        lat:           latitude
        lon:           longitude
        trip_date_str: the trip date "YYYY-MM-DD"

    Returns:
        Weather dict marked as is_estimate = False
    """
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":   lat,
                "longitude":  lon,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "windspeed_10m_max",
                    "weathercode"
                ],
                "timezone":   "auto",
                "start_date": trip_date_str,
                "end_date":   trip_date_str
            }
        )

        if r.status_code != 200 or not r.text.strip():
            print(f"    ❌ Open-Meteo forecast error: {r.status_code}")
            return None

        d        = r.json()["daily"]
        rainfall = d["precipitation_sum"][0]
        temp_max = d["temperature_2m_max"][0]
        temp_min = d["temperature_2m_min"][0]
        wind     = d["windspeed_10m_max"][0]
        wcode    = d["weathercode"][0]

        # WMO weather codes
        # 0        = clear sky
        # 1,2,3    = partly cloudy
        # 45,48    = fog
        # 51-67    = drizzle/rain
        # 71-77    = snow
        # 80-82    = rain showers
        # 85,86    = snow showers
        # 95-99    = thunderstorm
        is_bad = wcode >= 51

        if wcode >= 95:
            severity    = "thunderstorm"
            description = "Thunderstorm expected"
        elif wcode >= 80:
            severity    = "rain showers"
            description = "Rain showers expected"
        elif wcode >= 51:
            severity    = "rain"
            description = "Rain expected"
        elif wcode >= 45:
            severity    = "fog"
            description = "Foggy conditions expected"
        else:
            severity    = "clear"
            description = "Clear or partly cloudy"

        if is_bad:
            suggestion = f"{description} — consider indoor alternatives"
        else:
            suggestion = "Weather looks good — plan looks fine"

        return {
            "mode":        "forecast",
            "temp_max":    temp_max,
            "temp_min":    temp_min,
            "rainfall_mm": rainfall,
            "wind_kmh":    wind,
            "weathercode": wcode,
            "severity":    severity,
            "description": description,
            "was_rainy":   rainfall > 5,
            "is_bad":      is_bad,
            "suggestion":  suggestion,
            "is_estimate": False,
            "checked_at":  datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    except Exception as e:
        print(f"    ❌ Forecast weather fetch failed: {e}")
        return None