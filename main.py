from app.orchestrator.langgraph_workflow import run_initial_itinerary
from app.orchestrator.chat_graph import run_chat_turn
from app.planning.events import fetch_events_for_profile
from app.weather.main import run_weather_on_new_itinerary
from datetime import datetime
import json


def ask_form():
    print("\n===== AI ITINERARY PLANNER =====\n")
    country = input("Country: ").strip()
    cities = input("Cities, comma separated: ").strip().split(",")
    start_date = input("Start date (YYYY-MM-DD): ").strip()
    end_date = input("End date (YYYY-MM-DD): ").strip()
    travel_style = input("Travel style: ").strip()
    interests = input("Interests, comma separated: ").strip().split(",")
    budget = input("Budget: ").strip()
    must_include = input("Must include places/activities, comma separated: ").strip().split(",")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end_dt - start_dt).days + 1

    return {
        "country": country.title(),
        "cities": [c.strip().title() for c in cities if c.strip()],
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "travel_style": travel_style,
        "interests": [i.strip() for i in interests if i.strip()],
        "budget": budget,
        "must_include": [m.strip() for m in must_include if m.strip()],
    }


def adapt_planning_output(itinerary_json: dict) -> dict:
    plan = []

    for day in itinerary_json.get("days", []):
        for order, activity in enumerate(day.get("activities", []), start=1):

            plan.append({
                "day":           day["day"],
                "order":         order,
                "date":          day.get("date"),
                "location":      activity["location_name"],
                "city":          itinerary_json.get("destination") or itinerary_json.get("city") or "",
                "lat":           activity["latitude"],
                "lon":           activity["longitude"],
                "user_modified": False
            })

    raw_date = itinerary_json["days"][0]["date"]
    trip_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    return {
        "destination":  itinerary_json.get("destination") or itinerary_json.get("city") or "",
        "trip_date":    trip_date,
        "weather_meta": {},
        "edit_history": [],
        "plan":         plan
    }


def inject_weather_into_itinerary(itinerary_json: dict, weather_result: dict) -> dict:
    """
    Merges weather data into each activity in the original itinerary.
    """
    weather_lookup = {}
    for place in weather_result.get("plan", []):
        key = place["location"].lower()
        weather_lookup[key] = {
            "weather":      place.get("weather"),
            "weather_note": place.get("weather_note")
        }

    for day in itinerary_json.get("days", []):
        for activity in day.get("activities", []):
            location_key = activity["location_name"].lower()
            if location_key in weather_lookup:
                activity["weather"]      = weather_lookup[location_key]["weather"]
                activity["weather_note"] = weather_lookup[location_key]["weather_note"]

    return itinerary_json


def chat_loop(session: dict):
    print("\n===== CHAT MODE =====")
    print("Ask travel questions or request changes. Type 'exit' to stop.\n")

    while True:
        message = input("You: ").strip()

        if message.lower() in ["exit", "quit"]:
            break

        answer, session = run_chat_turn(session, message)

        print("\nAssistant:")
        print(answer)


def main():
    profile = ask_form()
    events_by_city = fetch_events_for_profile(profile)

    print("\nGenerating itinerary with LangGraph...\n")

    session = run_initial_itinerary(profile)

    # run weather after planning agent finishes
    print("\nRunning weather check...\n")
    weather_input  = adapt_planning_output(session["response"])
    weather_result = run_weather_on_new_itinerary(weather_input)

    # merge weather into itinerary
    session["response"] = inject_weather_into_itinerary(
        session["response"], weather_result
    )
    session["weather"] = weather_result

    print("\n===== GENERATED ITINERARY WITH WEATHER =====\n")
    print(json.dumps(session["response"], indent=2, ensure_ascii=False))

    print("\n===== EVENTS HAPPENING DURING YOUR TRIP =====\n")
    print(json.dumps(events_by_city, indent=2))

    chat_loop(session)


if __name__ == "__main__":
    main()