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