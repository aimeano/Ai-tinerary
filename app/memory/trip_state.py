import uuid


def create_trip_id() -> str:
    return f"trip_{uuid.uuid4().hex[:8]}"


def create_user_session(user_id: str = "local_user") -> dict:
    return {
        "user_id": user_id,
        "active_trip_id": None,
        "trips": {},
    }


def build_trip_title(profile: dict) -> str:
    cities = profile.get("cities", [])
    country = profile.get("country", "Trip")

    if cities:
        return f"{', '.join(cities)} Trip"

    return f"{country} Trip"


def create_trip_from_generation(generated: dict) -> dict:
    profile = generated["profile"]

    trip_id = create_trip_id()

    return {
        "trip_id": trip_id,
        "title": build_trip_title(profile),
        "profile": profile,
        "raw_itinerary": generated["raw_itinerary"],
        "itinerary": generated["itinerary"],
        "geocoded": generated.get("geocoded", []),
        "clusters": generated.get("clusters", []),
        "enrichment_cache": generated.get("enrichment_cache", {
            "restaurants": {},
            "travel_times": {},
        }),
        "chat_history": [],
    }


def add_trip(session: dict, trip: dict) -> dict:
    trip_id = trip["trip_id"]

    session["trips"][trip_id] = trip
    session["active_trip_id"] = trip_id

    return session


def get_active_trip(session: dict) -> dict:
    trip_id = session.get("active_trip_id")

    if not trip_id:
        raise ValueError("No active trip selected.")

    return session["trips"][trip_id]


def update_active_trip(session: dict, trip: dict) -> dict:
    trip_id = trip["trip_id"]

    session["trips"][trip_id] = trip
    session["active_trip_id"] = trip_id

    return session

def set_active_trip(session: dict, trip_id: str) -> dict:
    if trip_id not in session["trips"]:
        raise ValueError(f"Trip not found: {trip_id}")

    session["active_trip_id"] = trip_id
    return session