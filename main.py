from app.orchestrator.langgraph_workflow import run_initial_itinerary
from app.orchestrator.chat_graph import run_chat_turn
from datetime import datetime
import json


def ask_form():
    print("\n===== AI ITINERARY PLANNER =====\n")

    country = input("Country: ").strip()
    cities = input("Cities, comma separated: ").strip().split(",")
    start_date = input("Start date (YYYY-MM-DD): ").strip()
    end_date = input("End date (YYYY-MM-DD): ").strip()
    print("\nTravel style options:")
    print("  1. relaxed")
    print("  2. adventurous")
    print("  3. honeymoon")
    print("  4. with friends")
    print("  5. family and kids")
    travel_style_input = input("Travel style (enter option number): ").strip()

    style_map = {
        "1": "relaxed",
        "2": "adventurous",
        "3": "honeymoon",
        "4": "with friends",
        "5": "family and kids",
    }
    travel_style = style_map.get(travel_style_input, travel_style_input)
    interests = input("Interests, comma separated: ").strip().split(",")
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
        "must_include": [m.strip() for m in must_include if m.strip()],
    }

    print("\nOptional: Enter flight numbers for automatic scheduling.")
    print("The system will look up departure and arrival times automatically.")
    print("Press Enter to skip any field.\n")

    flights = []
    cities_list = [c.strip().title() for c in cities if c.strip()]

    for i, city in enumerate(cities_list):
        if i == 0:
            fn = input(
                f"Inbound flight number arriving in {city} "
                f"on {start_date} (e.g. AK6153, or skip): "
            ).strip()
            if fn:
                flights.append({
                    "type": "arrival",
                    "city": city,
                    "date": start_date,
                    "flight_number": fn,
                })

        if i < len(cities_list) - 1:
            next_city = cities_list[i + 1]
            travel_date = input(
                f"Date of travel from {city} to {next_city} "
                f"(YYYY-MM-DD, or skip): "
            ).strip()
            fn = input(
                f"Flight number from {city} to {next_city} "
                f"(e.g. AK6154, or skip): "
            ).strip()
            if travel_date and fn:
                flights.append({
                    "type": "intercity",
                    "from_city": city,
                    "to_city": next_city,
                    "date": travel_date,
                    "flight_number": fn,
                })

        if i == len(cities_list) - 1:
            fn = input(
                f"Outbound flight number departing from {city} "
                f"on {end_date} (e.g. AK6155, or skip): "
            ).strip()
            if fn:
                flights.append({
                    "type": "departure",
                    "city": city,
                    "date": end_date,
                    "flight_number": fn,
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

    chat_loop(session)


if __name__ == "__main__":
    main()