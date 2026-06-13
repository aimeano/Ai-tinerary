from app.db.database import SessionLocal
from app.db.trip_repository import (
    get_or_create_user,
    save_trip,
    load_user_trips,
)

db = SessionLocal()

try:
    user = get_or_create_user(
        db,
        user_id="local_user",
        email="local@example.com",
        name="Local User",
    )

    trip = {
        "trip_id": "trip_test",
        "title": "Test Trip",
        "profile": {"country": "Malaysia"},
        "raw_itinerary": {"days": []},
        "itinerary": {"days": []},
        "geocoded": [],
        "enrichment_cache": {
            "restaurants": {},
            "travel_times": {},
        },
    }

    save_trip(db, user.user_id, trip)

    trips = load_user_trips(db, user.user_id)

    print(trips)

finally:
    db.close()