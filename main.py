from app.orchestrator.langgraph_workflow import run_initial_itinerary
from app.orchestrator.chat_graph import run_chat_turn
from app.planning.events import fetch_events_for_profile
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

    profile = {
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

    print("\nOptional: Enter flight/travel details for accurate scheduling.")
    print("Press Enter to skip any field.\n")

    flights = []
    cities_list = [c.strip().title() for c in cities if c.strip()]

    for i, city in enumerate(cities_list):
        if i == 0:
            arr = input(f"Arrival time in {city} on {start_date} (HH:MM, e.g. 14:30): ").strip()
            if arr:
                flights.append({
                    "type": "arrival",
                    "city": city,
                    "date": start_date,
                    "time": arr
                })

        if i < len(cities_list) - 1:
            next_city = cities_list[i + 1]
            travel_date = input(f"Date of travel from {city} to {next_city} (YYYY-MM-DD): ").strip()
            depart_time = input(f"Departure time from {city} to {next_city} (HH:MM): ").strip()
            if travel_date and depart_time:
                flights.append({
                    "type": "intercity",
                    "from_city": city,
                    "to_city": next_city,
                    "date": travel_date,
                    "departure_time": depart_time
                })

        if i == len(cities_list) - 1:
            dep = input(f"Departure time FROM {city} on {end_date} (HH:MM, e.g. 18:00): ").strip()
            if dep:
                flights.append({
                    "type": "departure",
                    "city": city,
                    "date": end_date,
                    "time": dep
                })

    profile["flights"] = flights

    return profile


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

    print("\n===== GENERATED ITINERARY =====\n")
    print(
        json.dumps(
            session["response"],
            indent=2,
            ensure_ascii=False
        )
    )

    print("\n===== EVENTS HAPPENING DURING YOUR TRIP =====\n")
    print(
        json.dumps(
            events_by_city,
            indent=2
        )
    )

    chat_loop(session)


if __name__ == "__main__":
    main()