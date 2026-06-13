import uuid
from sqlalchemy.orm import Session

from app.db.models import User, Trip, ChatMessage
from app.db.models import Trip, TripVersion


def create_message_id() -> str:
    return f"msg_{uuid.uuid4().hex[:12]}"


def get_or_create_user(
    db: Session,
    user_id: str = "local_user",
    email: str | None = None,
    name: str | None = None,
) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()

    if user:
        return user

    user = User(
        user_id=user_id,
        email=email,
        name=name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def save_trip(
    db: Session,
    user_id: str,
    trip: dict,
) -> Trip:
    existing = db.query(Trip).filter(
        Trip.trip_id == trip["trip_id"]
    ).first()

    if existing:
        new_version_number = existing.itinerary_version + 1

        history = TripVersion(
            trip_id=existing.trip_id,
            version_number=new_version_number,
            raw_itinerary=trip["raw_itinerary"],
            itinerary=trip["itinerary"],
            reason=trip.get("version_reason", "itinerary_updated"),
        )

        db.add(history)

        existing.title = trip["title"]
        existing.profile = trip["profile"]
        existing.raw_itinerary = trip["raw_itinerary"]
        existing.itinerary = trip["itinerary"]
        existing.geocoded = trip.get("geocoded", [])
        existing.enrichment_cache = trip.get("enrichment_cache", {})
        existing.clusters = trip.get("clusters", [])
        existing.itinerary_version = new_version_number

        db.commit()
        db.refresh(existing)
        return existing

    db_trip = Trip(
        trip_id=trip["trip_id"],
        user_id=user_id,
        title=trip["title"],
        profile=trip["profile"],
        raw_itinerary=trip["raw_itinerary"],
        itinerary=trip["itinerary"],
        geocoded=trip.get("geocoded", []),
        clusters=trip.get("clusters", []),
        enrichment_cache=trip.get("enrichment_cache", {}),
    )

    db.add(db_trip)
    db.flush()

    history = TripVersion(
        trip_id=db_trip.trip_id,
        version_number=1,
        raw_itinerary=db_trip.raw_itinerary,
        itinerary=db_trip.itinerary,
        reason="initial_generation",
    )

    db.add(history)
    db.commit()
    db.refresh(db_trip)

    return db_trip


def load_user_trips(
    db: Session,
    user_id: str,
) -> list[dict]:
    trips = db.query(Trip).filter(
        Trip.user_id == user_id
    ).order_by(
        Trip.created_at.desc()
    ).all()

    trip_dicts = []

    for trip in trips:
        item = trip_to_dict(trip)
        item["chat_history"] = load_chat_history(db, trip.trip_id)
        trip_dicts.append(item)

    return trip_dicts


def load_trip(
    db: Session,
    trip_id: str,
) -> dict | None:
    trip = db.query(Trip).filter(
        Trip.trip_id == trip_id
    ).first()

    if not trip:
        return None

    return trip_to_dict(trip)


def save_chat_message(
    db,
    trip_id: str,
    role: str,
    content,
):
    message = ChatMessage(
        trip_id=trip_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "message_id": message.message_id,
        "trip_id": message.trip_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def load_chat_history(
    db,
    trip_id: str,
):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.trip_id == trip_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "message_id": msg.message_id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


def trip_to_dict(trip: Trip) -> dict:
    return {
        "trip_id": trip.trip_id,
        "title": trip.title,
        "profile": trip.profile,
        "raw_itinerary": trip.raw_itinerary,
        "itinerary": trip.itinerary,
        "itinerary_version": trip.itinerary_version,
        "geocoded": trip.geocoded or [],
        "clusters": trip.clusters or [],
        "enrichment_cache": trip.enrichment_cache or {
            "restaurants": {},
            "travel_times": {},
        },
        "chat_history": [],
        "created_at": trip.created_at.isoformat() if trip.created_at else None,
        "updated_at": trip.updated_at.isoformat() if trip.updated_at else None,
    }


def load_chat_history_from_relationship_safe(trip: Trip) -> list:
    # Temporary: chat history is loaded separately through load_chat_history().
    # Keep this empty to avoid needing SQLAlchemy relationships right now.
    return []

def delete_trip(
    db: Session,
    user_id: str,
    trip_id: str,
) -> bool:
    trip = db.query(Trip).filter(
        Trip.trip_id == trip_id,
        Trip.user_id == user_id,
    ).first()

    if not trip:
        return False

    db.query(ChatMessage).filter(
        ChatMessage.trip_id == trip_id
    ).delete()

    db.delete(trip)
    db.commit()

    return True

def rename_trip(
    db: Session,
    user_id: str,
    trip_id: str,
    new_title: str,
) -> Trip | None:
    trip = db.query(Trip).filter(
        Trip.trip_id == trip_id,
        Trip.user_id == user_id,
    ).first()

    if not trip:
        return None

    trip.title = new_title

    db.commit()
    db.refresh(trip)

    return trip

def list_user_trip_summaries(
    db: Session,
    user_id: str,
) -> list[dict]:
    trips = db.query(Trip).filter(
        Trip.user_id == user_id
    ).order_by(
        Trip.updated_at.desc()
    ).all()

    return [
        {
            "trip_id": trip.trip_id,
            "title": trip.title,
            "country": trip.profile.get("country") if trip.profile else None,
            "cities": trip.profile.get("cities") if trip.profile else [],
            "created_at": trip.created_at.isoformat() if trip.created_at else None,
            "updated_at": trip.updated_at.isoformat() if trip.updated_at else None,
        }
        for trip in trips
    ]

def load_user_trip(
    db,
    user_id: str,
    trip_id: str,
):
    trip = (
        db.query(Trip)
        .filter(
            Trip.trip_id == trip_id,
            Trip.user_id == user_id,
        )
        .first()
    )

    if not trip:
        return None

    item = trip_to_dict(trip)
    item["chat_history"] = load_chat_history(db, trip_id)

    return item

def save_trip_version(
    db: Session,
    trip_id: str,
    version_number: int,
    raw_itinerary: dict | None,
    itinerary: dict,
    reason: str | None = None,
) -> TripVersion:
    version = TripVersion(
        trip_id=trip_id,
        version_number=version_number,
        raw_itinerary=raw_itinerary,
        itinerary=itinerary,
        reason=reason,
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return version

def restore_trip_version(
    db: Session,
    trip_id: str,
    version_number: int,
) -> Trip | None:

    trip = (
        db.query(Trip)
        .filter(Trip.trip_id == trip_id)
        .first()
    )

    if not trip:
        return None

    version = (
        db.query(TripVersion)
        .filter(
            TripVersion.trip_id == trip_id,
            TripVersion.version_number == version_number,
        )
        .first()
    )

    if not version:
        return None

    # Save current state as history first
    current_version = trip.itinerary_version + 1

    db.add(
        TripVersion(
            trip_id=trip.trip_id,
            version_number=current_version,
            raw_itinerary=trip.raw_itinerary,
            itinerary=trip.itinerary,
            reason=f"restore_backup_before_v{version_number}",
        )
    )

    # Restore selected version
    trip.raw_itinerary = version.raw_itinerary
    trip.itinerary = version.itinerary
    trip.itinerary_version = current_version

    db.commit()
    db.refresh(trip)

    return trip


def update_trip_weather_only(
    db: Session,
    trip_id: str,
    itinerary: dict,
) -> Trip | None:
    trip = db.query(Trip).filter(
        Trip.trip_id == trip_id
    ).first()

    if not trip:
        return None

    trip.itinerary = itinerary

    db.commit()
    db.refresh(trip)

    return trip