from app.weather.triggers import (
    trigger_1a_itinerary_created,
    trigger_1b_place_updated,
    trigger_2_itinerary_opened
)
from app.weather.constraint import (
    run_constraint_validator,
    handle_user_weather_response
)


def run_weather_on_new_itinerary(itinerary: dict) -> dict:
    """Called by planning agent after itinerary is first built."""
    return trigger_1a_itinerary_created(itinerary)


def run_weather_on_place_update(itinerary: dict,
                                 day_num: int,
                                 old_location: str,
                                 new_location: str) -> dict:
    """Called after planning agent updates a place."""
    return trigger_1b_place_updated(
        itinerary, day_num, old_location, new_location
    )


def run_weather_on_open(itinerary: dict) -> dict:
    """Called every time user opens a saved itinerary."""
    return trigger_2_itinerary_opened(itinerary)


def run_weather_on_user_response(itinerary: dict,
                                  day_num: int,
                                  location: str,
                                  user_says: str,
                                  new_place: str = None) -> dict:
    """
    Called after user responds to weather notification.
    new_place comes from planning agent if user says yes.
    """
    return handle_user_weather_response(
        itinerary, day_num, location, user_says, new_place
    )