from datetime import datetime


# ============================================================
# CONSTRAINT VALIDATOR
# Fires when bad weather found
# Never decides replacement — notifies only
# ============================================================

def run_constraint_validator(itinerary: dict) -> dict:
    """
    Called when bad weather is detected for outdoor places.
    Never auto swaps anything.
    Only prepares notifications for the user.
    Actual place change decision goes back to planning agent.
    """
    print("\n  🔔 Constraint Validator — preparing notifications...\n")

    notifications = []

    for place in itinerary["plan"]:
        if place.get("needs_replan") == True:

            weather     = place.get("weather", {})
            description = weather.get("description", "bad weather")
            temp = f"{weather.get('temp_min', '?')}°C – {weather.get('temp_max', '?')}"

            notification = {
                "day":      place["day"],
                "location": place["location"],
                "type":     place["type"],
                "weather":  description,
                "temp":     temp,
                "message":  (
                    f"⚠️  Rain predicted for Day {place['day']} — "
                    f"{place['location']} ({description}, {temp}°C)\n"
                    f"Would you like to change this activity "
                    f"to other alternative? [yes/no]"
                ),
                "status":   "pending_user_response"
            }

            notifications.append(notification)
            place["needs_replan"]    = "pending"
            place["weather_warning"] = description

            print(f"  📱 Notification queued: Day {place['day']} — {place['location']}")
            print(f"     Weather  : {description}, {temp}°C")
            print(f"     Waiting  : user response before any changes")
            print(f"     Note     : planning agent will handle replacement if user says yes")

    itinerary["pending_notifications"] = notifications

    print(f"\n  Total notifications : {len(notifications)}")
    print(f"  No changes made — waiting for user and planning agent")

    return itinerary


def handle_user_weather_response(itinerary: dict,
                                  day_num: int,
                                  location: str,
                                  user_says: str,
                                  new_place: str = None) -> dict:
    """
    Called after user responds to weather notification.
    If user says yes, planning agent finds the replacement
    and passes it back here as new_place.
    If user says no, keep original with umbrella note.

    Args:
        itinerary:  current itinerary
        day_num:    which day the affected place is on
        location:   the place that was flagged
        user_says:  "yes" → change it / "no" → keep it
        new_place:  replacement from planning agent (only if yes)

    Returns:
        updated itinerary
    """
    print(f"\n  User response for '{location}' on Day {day_num}: '{user_says}'")

    for place in itinerary["plan"]:
        if place["day"] == day_num and place["location"] == location:

            if user_says.lower() == "yes":
                if new_place:
                    # planning agent already found the replacement
                    original          = place["location"]
                    place["location"] = new_place
                    place["needs_replan"] = False
                    place["replan_note"]  = (
                        f"Changed by user due to bad weather. "
                        f"Original: {original}. "
                        f"Replacement found by planning agent."
                    )
                    print(f"  ✅ Swapped: '{original}' → '{new_place}'")
                    print(f"     Planning agent provided the replacement")
                else:
                    # waiting for planning agent to find replacement
                    place["needs_replan"] = "waiting_for_planning_agent"
                    print(f"  ⏳ User said yes — waiting for planning agent")
                    print(f"     Planning agent needs to find otheralternative")

            elif user_says.lower() == "no":
                place["needs_replan"]    = False
                place["weather_warning"] = place.get("weather_warning", "")
                place["weather_note"]    = (
                    "Consider bringing an umbrella with you."
                )
                place["user_kept"]       = True
                print(f"  ✅ User kept original — '{location}' stays")
                print(f"     Note added: Consider bringing an umbrella")

            break

    return itinerary