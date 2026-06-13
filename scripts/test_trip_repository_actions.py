from app.db.database import SessionLocal
from app.db.trip_repository import (
    save_trip,
    list_user_trip_summaries,
    rename_trip,
    delete_trip,
    load_user_trips,
)
from app.db.auth_repository import (
    signup_user,
    login_user,
)

db = SessionLocal()

try:
    # Create user if not exists, otherwise login
    try:
        user = signup_user(
            db,
            email="repo_test@example.com",
            password="Aiman123",
            name="Repo Test",
        )
        print("Created test user")
    except ValueError:
        user = login_user(
            db,
            email="repo_test@example.com",
            password="Aiman123",
        )
        print("Logged into existing test user")

    trip = {
        "trip_id": "trip_repo_test",
        "title": "Original Title",
        "profile": {
            "country": "Malaysia",
            "cities": ["Kuala Lumpur"],
        },
        "raw_itinerary": {
            "days": []
        },
        "itinerary": {
            "days": []
        },
        "geocoded": [],
        "enrichment_cache": {
            "restaurants": {},
            "travel_times": {},
        },
        "chat_history": [],
    }

    save_trip(
        db,
        user.user_id,
        trip,
    )

    print("\nAfter save:")
    print(
        list_user_trip_summaries(
            db,
            user.user_id,
        )
    )

    rename_trip(
        db,
        user.user_id,
        "trip_repo_test",
        "Renamed Trip",
    )

    print("\nAfter rename:")
    print(
        list_user_trip_summaries(
            db,
            user.user_id,
        )
    )

    loaded = load_user_trips(
        db,
        user.user_id,
    )

    print("\nLoaded trips:")
    print(loaded)

    deleted = delete_trip(
        db,
        user.user_id,
        "trip_repo_test",
    )

    print("\nDeleted:", deleted)

    print("\nAfter delete:")
    print(
        list_user_trip_summaries(
            db,
            user.user_id,
        )
    )

finally:
    db.close()