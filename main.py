from app.orchestrator.langgraph_workflow import run_initial_itinerary
from app.orchestrator.chat_graph import run_chat_turn
from datetime import datetime
import json
from app.memory.trip_state import (
    create_user_session,
    create_trip_from_generation,
    add_trip,
    get_active_trip,
    update_active_trip,
    set_active_trip,
)
from app.db.database import SessionLocal
from app.db.trip_repository import (
    get_or_create_user,
    save_trip,
    load_user_trips,
    save_chat_message,
)
from app.db.auth_repository import signup_user, login_user







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


def chat_loop(user_session: dict):
    print("\n===== CHAT MODE =====")
    print("Ask travel questions or request changes. Type 'exit' to stop.\n")

    while True:
        message = input("You: ").strip()

        if message.lower() in ["exit", "quit"]:
            break


        if message.lower() == "/trips":
            print("\n===== YOUR TRIPS =====")
            for trip_id, trip in user_session["trips"].items():
                active_marker = " (active)" if trip_id == user_session["active_trip_id"] else ""
                print(f"- {trip_id}: {trip['title']}{active_marker}")
                print(f"  Chat messages: {len(trip.get('chat_history', []))}")
            continue

        if message.lower().startswith("/switch "):
            trip_id = message.split(" ", 1)[1].strip()

            try:
                user_session = set_active_trip(user_session, trip_id)
                print(f"Switched to {trip_id}")
            except ValueError as e:
                print(e)

            continue

        if message.lower() == "/new":
            profile = ask_form()

            print("\nGenerating new itinerary...\n")

            generated = run_initial_itinerary(profile)
            trip = create_trip_from_generation(generated)
            user_session = add_trip(user_session, trip)
            db = SessionLocal()
            try:
                save_trip(db, user_session["user_id"], trip)
            finally:
                db.close()

            print(f"Created new trip: {trip['title']} ({trip['trip_id']})")
            print(json.dumps(trip["itinerary"], indent=2, ensure_ascii=False))

            continue

        active_trip = get_active_trip(user_session)

        answer, updated_trip = run_chat_turn(
            active_trip,
            message
        )
        updated_trip.setdefault("chat_history", [])

        updated_trip["chat_history"].append({
            "role": "user",
            "content": message,
        })

        updated_trip["chat_history"].append({
            "role": "assistant",
            "content": answer,
        })

        db = SessionLocal()
        try:
            save_trip(db, user_session["user_id"], updated_trip)
            save_chat_message(db, updated_trip["trip_id"], "user", message)
            save_chat_message(db, updated_trip["trip_id"], "assistant", answer)
        finally:
            db.close()

        user_session = update_active_trip(
            user_session,
            updated_trip
        )

        active_trip = get_active_trip(user_session)

        print("Restaurant cache:", len(active_trip["enrichment_cache"]["restaurants"]))

        print("Travel cache:", len(active_trip["enrichment_cache"]["travel_times"]))

        print("\nAssistant:")

        if isinstance(answer, (dict, list)):

            print(json.dumps(answer, indent=2, ensure_ascii=False))

        else:

            print(answer)

def load_user_session_from_db(user_id: str = "local_user") -> dict:
    db = SessionLocal()

    try:
        user = get_or_create_user(db, user_id=user_id)

        trips = load_user_trips(db, user.user_id)

        user_session = create_user_session(user_id=user.user_id)

        for trip in trips:
            user_session["trips"][trip["trip_id"]] = trip

        if trips:
            user_session["active_trip_id"] = trips[0]["trip_id"]

        return user_session

    finally:
        db.close()

def auth_menu():
    while True:
        print("\n===== AUTH =====")
        print("1. Login")
        print("2. Signup")
        print("3. Exit")

        choice = input("Choose: ").strip()

        if choice == "3":
            return None

        email = input("Email: ").strip().lower()
        password = input("Password: ").strip()

        db = SessionLocal()

        try:
            if choice == "1":
                user = login_user(db, email, password)
                print(f"Logged in as {user.email}")
                return user

            if choice == "2":
                name = input("Name: ").strip()
                user = signup_user(db, email, password, name)
                print(f"Signed up as {user.email}")
                return user

        except ValueError as e:
            print(e)

        finally:
            db.close()


def main():

    user = auth_menu()
    if not user:
        return
    user_session = load_user_session_from_db(user.user_id)

    if not user_session["trips"]:
        profile = ask_form()
        print("\nGenerating itinerary with LangGraph...\n")
        generated = run_initial_itinerary(profile)
        trip = create_trip_from_generation(generated)
        user_session = add_trip(
            user_session,
            trip
        )
        db = SessionLocal()
        try:
            save_trip(
                db,
                user_session["user_id"],
                trip
)
        finally:
            db.close()

    session = get_active_trip(user_session)

    print("\n===== USER SESSION =====")
    print("Active trip:", user_session["active_trip_id"])
    print("Trips:", list(user_session["trips"].keys()))
    """
    print("\n===== SESSION KEYS =====")
    print(session.keys())

    print("\n===== HAS RAW ITINERARY =====")
    print("raw_itinerary" in session)

    print("\n===== RAW ITINERARY SAMPLE =====")
    print(json.dumps(session["raw_itinerary"], indent=2, ensure_ascii=False)[:1000])

    print("\n===== ENRICHED ITINERARY SAMPLE =====")
    print(json.dumps(session["itinerary"], indent=2, ensure_ascii=False)[:1000])
    """


    print("\n===== GENERATED ITINERARY =====\n")
    print(
        json.dumps(
            session["itinerary"],
            indent=2,
            ensure_ascii=False
        )
    )

    #print(len(session["enrichment_cache"]["restaurants"]))
    #print(len(session["enrichment_cache"]["travel_times"]))

    chat_loop(user_session)


if __name__ == "__main__":
    main()