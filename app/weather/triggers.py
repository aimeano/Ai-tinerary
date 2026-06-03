from datetime import datetime, timedelta
import requests
from app.weather.geocoding import geocode_place_smart
from app.weather.weather_api import get_historical_weather, get_forecast_weather
from app.weather.constraint import run_constraint_validator


# ============================================================
# TRIGGER 1A
# Fires once when itinerary is first created
# ============================================================

def trigger_1a_itinerary_created(itinerary: dict) -> dict:
    """
    Called ONCE when planning agent finishes building itinerary.
    Checks date first to decide historical or live weather.
    Never makes place decisions — only adds weather notes.
    """
    print("=" * 55)
    print("  TRIGGER 1A — Itinerary first created")
    print("=" * 55)

    if "trip_date" not in itinerary:
        itinerary["trip_date"] = itinerary["trip_start"]

    trip_date = itinerary["trip_date"]
    days_away = (datetime.strptime(trip_date, "%Y-%m-%d")
                 - datetime.now()).days

    print(f"\n  Trip date : {trip_date} ({days_away} days away)")
    print(f"  Places    : {len(itinerary['plan'])} total")

    api_calls = 0

    # ── Far away: use historical weather ───────────────────
    if days_away > 16:
        print(f"  Mode      : Historical weather (trip > 16 days away)\n")

        for place in itinerary["plan"]:
            print(f"  📍 Day {place['day']} — {place['location']}")

            if "lat" not in place or "lon" not in place:
                coords = geocode_place_smart(
                    place["location"], city=place["city"]
                )
                if coords:
                    place["lat"]  = coords["lat"]
                    place["lon"]  = coords["lon"]
                    place["city"] = coords["city"]
                else:
                    print(f"     ⚠️  Could not geocode — skipping")
                    continue
            else:
                print(f"     ✅ Coordinates already provided")

            if "user_modified" not in place:
                place["user_modified"] = False

            place_date = place.get("date") or trip_date
            weather = get_historical_weather(
                place["lat"], place["lon"], place_date
            )

            if weather:
                place["weather"]              = weather
                place["weather_last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                api_calls += 1

                # add note based on historical weather
                if weather["was_rainy"]:
                    place["weather_note"] = (
                        "Based on last year's weather, it may rain on this day. "
                        "Check back within 16 days for live weather updates."
                    )
                    print(f"     ⚠️  Historical rain detected — note added")
                else:
                    place["weather_note"] = (
                        "Weather looked fine last year on this date."
                    )
                    print(f"     ✅ Historical weather looks fine")

                print(f"     Temp     : {weather['temp_min']}°C – {weather['temp_max']}°C")
                print(f"     Rainfall : {weather['rainfall_mm']} mm")
                print(f"     Note     : {place['weather_note']}")

    # ── Within 16 days: use forecast weather ────────────────────
    else:
        print(f"  Mode      : Live weather (trip ≤ 16 days away)\n")

        bad_weather_places = []

        for place in itinerary["plan"]:
            print(f"  📍 Day {place['day']} — {place['location']}")

            if "lat" not in place or "lon" not in place:
                coords = geocode_place_smart(
                    place["location"], city=place["city"]
                )
                if coords:
                    place["lat"]  = coords["lat"]
                    place["lon"]  = coords["lon"]
                    place["city"] = coords["city"]
                else:
                    print(f"     ⚠️  Could not geocode — skipping")
                    continue
            else:
                print(f"     ✅ Coordinates already provided")

            if "user_modified" not in place:
                place["user_modified"] = False

            place_date = place.get("date") or trip_date
            weather = get_forecast_weather(place["lat"], place["lon"], place_date)

            if weather:
                place["weather"]              = weather
                place["weather_last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                api_calls += 1

                if weather["is_bad"]:
                    place["weather_note"] = (
                        f"Rain predicted on this day. "
                        f"Would you like to change this activity?"
                    )
                    place["needs_replan"] = True
                    bad_weather_places.append(place)
                    print(f"     ⚠️  Bad live weather — flagged for user")
                else:
                    place["weather_note"] = "Weather looks fine on this date."
                    place["needs_replan"] = False
                    print(f"     ✅ Live weather looks fine")

                print(f"     Temp     : {weather['temp_min']}°C – {weather['temp_max']}°C")
                print(f"     Note     : {place['weather_note']}")

        # fire constraint validator if bad weather found
        if bad_weather_places:
            print(f"\n  ⚠️  Bad weather found — firing constraint validator")
            itinerary = run_constraint_validator(itinerary)

    itinerary["weather_meta"] = {
        "trigger_1a_done":   True,
        "trigger_1a_ran_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "last_live_check":   None,
        "total_api_calls":   api_calls
    }

    print(f"\n  ✅ Done")
    print(f"  API calls : {api_calls}")
    print(f"  💾 Save itinerary to your database")

    return itinerary


# ============================================================
# TRIGGER 1B
# Fires when planning agent updates a place
# ============================================================

def trigger_1b_place_updated(itinerary: dict,
                              day_num: int,
                              old_location: str,
                              new_location: str) -> dict:
    """
    Called AFTER planning agent updates a place.
    Does NOT listen to user messages directly.
    Just fetches weather for the new place and updates itinerary.

    Args:
        itinerary:     current itinerary
        day_num:       which day the place is on
        old_location:  the place that was replaced
        new_location:  the new place from planning agent

    Returns:
        updated itinerary with weather for new place
    """
    print("=" * 55)
    print("  TRIGGER 1B — Planning agent updated a place")
    print("=" * 55)

    trip_date = itinerary.get("trip_date", "")
    days_away = (datetime.strptime(trip_date, "%Y-%m-%d")
                 - datetime.now()).days

    for place in itinerary["plan"]:
        if (place["day"] == day_num and
                place["location"].lower() == new_location.lower()):

            print(f"\n  📍 Day {day_num} — {new_location}")

            # geocode new place if needed
            if "lat" not in place or "lon" not in place:
                coords = geocode_place_smart(
                    place["location"], city=place["city"]
                )
                if coords:
                    place["lat"]  = coords["lat"]
                    place["lon"]  = coords["lon"]
                    place["city"] = coords["city"]
                else:
                    print(f"     ⚠️  Could not geocode — skipping")
                    return itinerary

            # fetch weather based on date
            place_date = place.get("date") or trip_date

            if days_away > 16:
                weather = get_historical_weather(
                    place["lat"], place["lon"], place_date
                )
                if weather:
                    if weather["was_rainy"]:
                        place["weather_note"] = (
                            "Based on last year's weather, it may rain on this day. "
                            "Check back within 16 days for live weather updates."
                        )
                    else:
                        place["weather_note"] = (
                            "Weather looked fine last year on this date."
                        )
            else:
                place_date = place.get("date") or trip_date
                weather = get_forecast_weather(place["lat"], place["lon"], place_date)
                if weather:
                    if weather["is_bad"]:
                        place["weather_note"] = (
                            "Rain predicted on this day. "
                            "Would you like to change this activity?"
                        )
                        place["needs_replan"] = True
                    else:
                        place["weather_note"] = "Weather looks fine on this date."
                        place["needs_replan"] = False

            if weather:
                place["weather"]              = weather
                place["weather_last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                print(f"     ✅ Weather updated for new place")
                print(f"     Note : {place['weather_note']}")

            # log the update
            if "edit_history" not in itinerary:
                itinerary["edit_history"] = []

            itinerary["edit_history"].append({
                "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M"),
                "day":         day_num,
                "old_place":   old_location,
                "new_place":   new_location,
                "trigger":     "1B"
            })

            break

    return itinerary


# ============================================================
# TRIGGER 2
# Fires when user opens a saved itinerary
# ============================================================

def trigger_2_itinerary_opened(itinerary: dict) -> dict:
    """
    Called every time user opens a saved itinerary.
    Checks date to decide what weather data to show.
    Notifies planning agent if bad weather found.
    """
    print("=" * 55)
    print("  TRIGGER 2 — User opened saved itinerary")
    print("=" * 55)

    trip_date = itinerary["trip_date"]
    days_away = (datetime.strptime(trip_date, "%Y-%m-%d")
                 - datetime.now()).days

    print(f"\n  Trip date : {trip_date} ({days_away} days away)")

    # ── Far away: show saved historical notes ──────────────
    if days_away > 16:
        print(f"  Mode      : Showing saved historical notes\n")

        for place in sorted(itinerary["plan"], key=lambda x: x["day"]):
            print(f"  📍 Day {place['day']} — {place['location']}")
            print(f"     Note : {place.get('weather_note', 'No note available')}")

        return itinerary

    # ── Within 16 days: forecast weather check ──────────────────
    elif days_away >= 0:
        print(f"  Mode      : Live weather check\n")

        # skip if checked within last 6 hours
        last_check = itinerary["weather_meta"].get("last_live_check")
        if last_check:
            last_dt     = datetime.strptime(last_check, "%Y-%m-%d %H:%M")
            hours_since = (datetime.now() - last_dt).total_seconds() / 3600

            if hours_since < 6:
                print(f"  ⏱️  Last checked {hours_since:.1f}hrs ago — showing cached\n")

                for place in sorted(itinerary["plan"], key=lambda x: x["day"]):
                    print(f"  📍 Day {place['day']} — {place['location']}")
                    print(f"     Note : {place.get('weather_note', 'No note')}")

                return itinerary

        # fresh live check
        print(f"  Running fresh live check...\n")

        city_cache   = {}
        needs_replan = False

        for place in itinerary["plan"]:
            city    = place["city"]
            day_num = place["day"]
            key     = f"{city}_{day_num}"

            if key not in city_cache:
                place_date = place.get("date") or trip_date
                live = get_forecast_weather(place["lat"], place["lon"], place_date)
                city_cache[key] = live
                print(f"  🌐 Fetched live: {city} Day {day_num}")
            else:
                live = city_cache[key]
                print(f"  📦 Reused cache: {city} Day {day_num}")

            if live:
                place["weather"]              = live
                place["weather_last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

                if live["is_bad"]:
                    place["weather_note"]  = (
                        "Rain predicted on this day. "
                        "Would you like to change this activity?"
                    )
                    place["needs_replan"]  = True
                    needs_replan           = True
                    print(f"     ⚠️  Bad weather — flagged for user")
                else:
                    place["weather_note"]  = "Weather looks fine on this date."
                    place["needs_replan"]  = False
                    print(f"     ✅ Weather fine")

                print(f"     Note : {place['weather_note']}")

        itinerary["weather_meta"]["last_live_check"] = \
            datetime.now().strftime("%Y-%m-%d %H:%M")

        # fire constraint validator if bad weather found
        if needs_replan:
            print(f"\n  ⚠️  Bad weather found — firing constraint validator")
            itinerary = run_constraint_validator(itinerary)
        else:
            print(f"\n  ✅ All clear — no changes needed")

        print(f"\n  API calls : {len(city_cache)}")
        print(f"  💾 Update itinerary in your database")

        return itinerary

    # ── Trip already passed ─────────────────────────────────
    else:
        print("  Trip has already passed — no weather check needed")
        return itinerary