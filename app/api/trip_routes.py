from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user_id
from app.db.database import SessionLocal
from app.db.trip_repository import (
    list_user_trip_summaries,
    load_user_trip,
    save_trip,
    delete_trip,
    save_chat_message
)
from datetime import datetime

from app.api.schemas import CreateTripRequest,ChatRequest
from app.orchestrator.langgraph_workflow import run_initial_itinerary
from app.orchestrator.chat_graph import run_chat_turn
from app.memory.trip_state import create_trip_from_generation
from app.api.schemas import CreateTripRequest, ChatRequest, WeatherReplaceRequest
from app.planning.distance_planner import get_parent_retrieval_locations, get_weather_safe_clusters,find_city_for_activity

router = APIRouter(
    prefix="/trips",
    tags=["trips"],
)


@router.get("")
def get_trips(
    user_id: str = Depends(get_current_user_id),
):
    db = SessionLocal()

    try:
        trips = list_user_trip_summaries(
            db,
            user_id,
        )

        return {
            "user_id": user_id,
            "trips": trips,
        }

    finally:
        db.close()


@router.get("/{trip_id}")
def get_trip(
    trip_id: str,
    user_id: str = Depends(get_current_user_id),
):
    db = SessionLocal()

    try:
        trip = load_user_trip(
            db,
            user_id,
            trip_id,
        )

        if not trip:
            raise HTTPException(
                status_code=404,
                detail="Trip not found",
            )

        clean_chat_history = []

        for msg in trip.get("chat_history", []):
            content = msg.get("content")

            if isinstance(content, dict):
                content = content.get(
                    "message",
                    "I've updated your itinerary."
                )

            clean_chat_history.append({
                "role": msg.get("role"),
                "content": content,
                "created_at": msg.get("created_at"),
            })

        return {
            "trip_id": trip["trip_id"],
            "title": trip["title"],
            "profile": trip["profile"],
            "itinerary": trip["itinerary"],
            "itinerary_version": trip.get("itinerary_version", 1),
            "chat_history": clean_chat_history,
            "created_at": trip["created_at"],
            "updated_at": trip["updated_at"],
        }

    finally:
        db.close()

@router.delete("/{trip_id}")
def delete_trip_route(
    trip_id: str,
    user_id: str = Depends(get_current_user_id),
):
    db = SessionLocal()

    try:
        deleted = delete_trip(
            db,
            user_id,
            trip_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Trip not found",
            )

        return {
            "deleted": True,
            "trip_id": trip_id,
        }

    finally:
        db.close()

@router.post("")
def create_trip(
    payload: CreateTripRequest,
    user_id: str = Depends(get_current_user_id),
):
    start_dt = datetime.strptime(payload.start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(payload.end_date, "%Y-%m-%d")

    days = (end_dt - start_dt).days + 1

    cities = [
        city.strip().title()
        for city in payload.cities
        if city.strip()
    ]

    flights = []

    if payload.arrival_flight_number:
        flights.append({
            "type": "arrival",
            "city": cities[0],
            "date": payload.start_date,
            "flight_number": payload.arrival_flight_number.strip(),
        })

    if payload.departure_flight_number:
        flights.append({
            "type": "departure",
            "city": cities[-1],
            "date": payload.end_date,
            "flight_number": payload.departure_flight_number.strip(),
        })

    print("\n===== CREATE TRIP FLIGHT INPUT =====")
    print("arrival:", payload.arrival_flight_number)
    print("departure:", payload.departure_flight_number)

    profile = {
        "country": payload.country.title(),
        "cities": cities,
        "retrieval_locations": get_parent_retrieval_locations(
            cities,
            payload.country.title(),
        ),
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "days": days,
        "travel_style": payload.travel_style,
        "interests": payload.interests,
        "budget": payload.budget,
        "must_include": payload.must_include,
        "flights": flights,
    }

    print("\n===== PROFILE FLIGHTS BEFORE GRAPH =====")
    print(profile.get("flights"))

    generated = run_initial_itinerary(profile)
    trip = create_trip_from_generation(generated)

    db = SessionLocal()


    try:
        save_trip(db, user_id, trip)

        return {
            "trip_id": trip["trip_id"],
            "title": trip["title"],
            "profile": trip["profile"],
            "itinerary": trip["itinerary"],
            "created": True,
        }

    finally:
        db.close()



@router.post("/{trip_id}/chat")
def chat_trip(
    trip_id: str,
    payload: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    db = SessionLocal()

    try:
        trip = load_user_trip(
            db,
            user_id,
            trip_id,
        )

        if not trip:
            raise HTTPException(
                status_code=404,
                detail="Trip not found",
            )

        answer, updated_trip = run_chat_turn(
            trip,
            payload.message,
        )

        if isinstance(answer, dict):
            itinerary_updated = "itinerary" in answer

            message = answer.get(
                "message",
                "I've updated your itinerary."
                if itinerary_updated
                else "Done."
            )

            response = {
                "trip_id": updated_trip["trip_id"],
                "message": message,
                "itinerary_updated": itinerary_updated,
            }

            if itinerary_updated:
                response["itinerary"] = answer.get("itinerary")
                response["validation"] = answer.get("validation")
                response["itinerary_version"] = updated_trip.get("itinerary_version", 1)

        else:
            message = answer

            response = {
                "trip_id": updated_trip["trip_id"],
                "message": message,
                "itinerary_updated": False,
            }

        if response["itinerary_updated"]:
            save_trip(
                db,
                user_id,
                updated_trip,
            )



        save_chat_message(
            db,
            updated_trip["trip_id"],
            "user",
            payload.message,
        )

        save_chat_message(
            db,
            updated_trip["trip_id"],
            "assistant",
            message,
        )

        return response

    finally:
        db.close()

@router.post("/{trip_id}/weather-replace")
def replace_bad_weather_activity(
    trip_id: str,
    payload: WeatherReplaceRequest,
    user_id: str = Depends(get_current_user_id),
):
    db = SessionLocal()

    try:
        trip = load_user_trip(db, user_id, trip_id)

        if not trip:
            raise HTTPException(
                status_code=404,
                detail="Trip not found",
            )

        day_index = payload.day - 1
        activity_index = payload.activity_index

        try:
            day = trip["itinerary"]["days"][day_index]
            activity = day["activities"][activity_index]
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid day or activity_index",
            )
        
        city = find_city_for_activity(
            activity,
            trip.get("clusters", []),
        )

        if not city:
            city = trip["profile"]["cities"][0]

        print("\n===== WEATHER DAY CITY =====")
        print(city)

        print("\n===== WEATHER DAY CITY =====")
        print(city)

        safe_clusters = get_weather_safe_clusters(
            trip.get("clusters", []),
            city,
        )



        print("\n===== WEATHER SAFE CLUSTERS =====")

        for cluster in safe_clusters:
            print(
                cluster["cluster_id"],
                cluster["assigned_city"],
                len(cluster["places"]),
            )

        weather = activity.get("weather", {})

        if not weather.get("is_bad_weather"):
            raise HTTPException(
                status_code=400,
                detail="This activity is not marked as bad weather.",
            )

        message = (
            f"Edit itinerary only. Weather is bad on day {payload.day}. "
            f"Replace the entire day {payload.day} with indoor weather-safe activities only. "
            f"Use only the provided WEATHER SAFE CLUSTERS. "
            f"Keep the same city and same date. "
            f"Keep all other days exactly the same."
        )

        trip["weather_safe_clusters"] = safe_clusters

        answer, updated_trip = run_chat_turn(
            trip,
            message,
        )

        if isinstance(answer, dict):
            itinerary_updated = "itinerary" in answer
            assistant_message = answer.get(
                "message",
                "I've replaced the bad-weather activity with an indoor option."
            )
        else:
            itinerary_updated = False
            assistant_message = answer

        save_trip(db, user_id, updated_trip)

        return {
            "trip_id": trip_id,
            "message": assistant_message,
            "itinerary_updated": itinerary_updated,
            "itinerary": updated_trip["itinerary"],
        }

    finally:
        db.close()