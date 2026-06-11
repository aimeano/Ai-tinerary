import json
from datetime import datetime, timedelta


def build_itinerary_prompt(
    profile: dict,
    retrieved_results: list[dict],
    clusters: list[dict],
    validated_pois: list[dict] | None = None,
    flights: list[dict] | None = None,
) -> str:

    # ── Validated place menu ──────────────────────────────────────────────────
    # This is the single source of truth for what locations the LLM may use.
    # Every activity must reference a place from this list.
    if validated_pois:
        place_menu = json.dumps(
            [
                {
                    "name": p["name"],
                    "latitude": p["lat"],
                    "longitude": p["lng"],
                    "address": p.get("formatted_address", ""),
                    "types": p.get("types", []),
                }
                for p in validated_pois
            ],
            indent=2,
            ensure_ascii=False,
        )
        few_places_note = (
            "\nNOTE: There are fewer validated places than days. "
            "Reuse locations with different activity types "
            "(e.g., same beach for morning swim and sunset walk)."
            if len(validated_pois) < profile.get("days", 3)
            else ""
        )
    else:
        place_menu = "[]"
        few_places_note = (
            "\nNOTE: No validated places were found for this city. "
            "Generate activities with latitude and longitude set to null. "
            "Do not invent coordinates. "
            "The post-processing pipeline will handle coordinate lookup."
        )

    # ── Context snippets (descriptions only, no new place names) ─────────────
    context_snippets = []

    for i, item in enumerate(retrieved_results, start=1):
        payload = item["payload"]

    context_block = "\n\n".join(context_snippets) if context_snippets else "No context available."

    # ── Flight / travel schedule context ─────────────────────────────────────
    if not flights:
        flights = profile.get("flights", [])

    flight_lines = []
    for f in flights:
        if f["type"] == "arrival":
            flight_lines.append(
                f"- ARRIVAL: Traveller arrives in {f['city']} at {f['time']} "
                f"on {f['date']}. Do NOT schedule any activity before {f['time']} "
                f"on this date. First activity must start at {f['time']} or later."
            )
        elif f["type"] == "departure":
            try:
                dep_dt = datetime.strptime(f["time"], "%H:%M")
                cutoff_dt = dep_dt - timedelta(hours=4)
                cutoff_str = cutoff_dt.strftime("%H:%M")
            except Exception:
                cutoff_str = "at least 4 hours before departure"
            flight_lines.append(
                f"- DEPARTURE: Traveller departs FROM {f['city']} at {f['time']} "
                f"on {f['date']}. The LAST activity on {f['date']} MUST end by "
                f"{cutoff_str} at the latest. After the last activity, add a "
                f"mandatory final activity titled 'Depart to Airport' with "
                f"location_name set to the main airport serving {f['city']}, "
                f"scheduled at {cutoff_str}. No activities after this."
            )
        elif f["type"] == "intercity":
            try:
                dep_dt = datetime.strptime(f["departure_time"], "%H:%M")
                ready_dt = dep_dt - timedelta(hours=1)
                ready_str = ready_dt.strftime("%H:%M")
            except Exception:
                ready_str = "1 hour before departure"
            flight_lines.append(
                f"- INTERCITY TRAVEL: On {f['date']}, traveller travels from "
                f"{f['from_city']} to {f['to_city']}, departing at "
                f"{f['departure_time']}. Schedule this as a half travel day. "
                f"Last activity in {f['from_city']} must end by {ready_str}. "
                f"After that, add a mandatory activity titled "
                f"'Travel to {f['to_city']}' with no specific location coordinates "
                f"(set latitude and longitude to null). "
                f"Remaining activities that day should be in {f['to_city']} "
                f"if arrival time permits, otherwise start {f['to_city']} "
                f"activities the next day."
            )

    flight_context = "\n".join(flight_lines) if flight_lines else "No flight or travel details provided."

    if flights:
        flight_section = f"""FLIGHT AND TRAVEL SCHEDULE — MUST BE FOLLOWED EXACTLY
{flight_context}
"""
        flight_rules = """\
- FLIGHT RULES ARE MANDATORY AND OVERRIDE ALL OTHER SCHEDULING.
- If an arrival time is given, first activity must start at or after arrival time.
- If a departure time is given, last activity must end 4 hours before departure. Insert "Depart to Airport" as final activity.
- If intercity travel is given, treat that date as a transition day.
- Never schedule more than 2 activities on a travel/transition day.
- Never insert "Depart to Airport" unless a departure flight time was explicitly provided by the user."""
    else:
        flight_section = ""
        flight_rules = ""

    return f"""
You are an AI travel itinerary planner.

Your task is to create a day-by-day itinerary using ONLY the validated places listed below.
Do NOT invent, guess, or use any place not in the VALIDATED PLACES list.

USER PROFILE
Country: {profile["country"]}
Cities: {", ".join(profile["cities"])}
Trip dates: {profile["start_date"]} to {profile["end_date"]}
Duration: {profile["days"]} days
Travel style: {profile["travel_style"]}
Interests: {", ".join(profile["interests"])}
Must include: {", ".join(profile["must_include"])}

TRAVEL STYLE: {profile["travel_style"]}

Apply these style-specific rules strictly:

If travel_style is "relaxed":
- Maximum 3 activities per day
- Include rest time between activities
- Avoid long travel distances between activities (prefer under 5km)
- No physically demanding activities
- Prefer parks, cafes, scenic walks, museums, shopping

If travel_style is "adventurous":
- Up to 5 activities per day
- Prioritize outdoor activities: hiking, water sports, wildlife, nature parks, extreme sports
- Include physically challenging activities where available
- Day trips to nature reserves or remote areas are encouraged

If travel_style is "honeymoon":
- Maximum 3 activities per day
- Prioritize romantic settings: sunset spots, scenic viewpoints, fine dining areas, beach resorts, gardens
- Avoid crowded tourist markets or family activity centers
- Activities should feel intimate and special
- Suggest evening activities like waterfront walks or hilltop views

If travel_style is "with friends":
- Up to 5 activities per day
- Mix of shopping, street food areas, nightlife districts, social activities, and popular tourist spots
- Include vibrant areas with lots of options
- Night markets, entertainment districts, and group activities preferred

If travel_style is "family and kids":
- Maximum 4 activities per day
- ONLY include family-friendly and child-appropriate activities
- Prioritize: zoos, aquariums, theme parks, beaches, interactive museums, nature parks with easy trails
- NEVER include: bars, nightlife, adult-only venues, strenuous hikes
- Include rest breaks between activities
- Prefer locations with facilities (toilets, parking, food nearby)

VALIDATED PLACES — the ONLY locations you may schedule activities at:
{place_menu}{few_places_note}

CONTEXT (use only for writing activity descriptions — do NOT derive new place names from this):
{context_block}

{flight_section}
RULES
- Every activity.location_name MUST exactly match a "name" from VALIDATED PLACES.
- Every activity.latitude and activity.longitude MUST be copied exactly from VALIDATED PLACES.
- Do NOT use any place that is not in VALIDATED PLACES above.
- location_name must be a specific proper-noun place name (e.g. "Petronas Twin Towers"). NEVER use generic category words like "kopitiam", "food_court", "mamak_stalls", "nasi_kandar", "beach", "park", or any underscore-separated placeholder.
- ALL activities on a given day must belong to the SAME city — never mix cities within one day.
- When a day is in City A, only use places listed under City A's section.
- Group geographically close places on the same day.
- Respect must-include items when possible.
- Use realistic time blocks.
- Keep descriptions concise (1–2 sentences).
- Output ONLY valid JSON, no markdown fences, no explanations outside JSON.
- ONLY use location names that appear exactly in the VALIDATED PLACES list. Never invent or guess place names.
- For island hopping activities, only use island names from VALIDATED PLACES. Never invent island names.
- If a must-include activity has no matching place in VALIDATED PLACES, describe it as an activity type rather than a specific named location. For example use "Island Hopping Tour" as the title with location_name set to the nearest ferry terminal or departure point that IS in VALIDATED PLACES.
{flight_rules}
- Do NOT create standalone food or meal activities such as "Lunch at X", "Breakfast at X", "Dinner at X", or any activity whose sole purpose is eating a meal. Every activity must be a real attraction, landmark, experience, or place to explore. The nearby_restaurants field already provides food suggestions near each activity. Schedule natural time gaps between activities for meals without creating explicit meal activity slots.
- The day title MUST accurately reflect the actual activities planned for that day. Never write a title like "Explore Bukit Bintang" if the activities are all in Bangsar.
- Generate the day title AFTER deciding the activities, not before.
- The title must be derived from the location_name values of the activities in that day — use the most prominent or repeated area.
- If activities span multiple neighborhoods, use the most visited area or a general descriptor like "Kuala Lumpur City Highlights".

CRITICAL OUTPUT REQUIREMENTS
- Generate exactly {profile["days"]} day objects inside "days".
- Day numbers must be 1 to {profile["days"]}.
- Each day must contain 3 to 5 activities.
- Do not write "..." or summarize missing days.
- Return raw JSON only.

JSON SCHEMA
{{
  "trip": {{
    "country": "",
    "cities": [],
    "duration_days": 0
  }},
  "days": [
    {{
      "day": 1,
      "date": "",
      "title": "",
      "summary": "",
      "activities": [
        {{
          "time": "09:00",
          "title": "",
          "location_name": "",
          "latitude": null,
          "longitude": null,
          "category": "",
          "description": ""
        }}
      ]
    }}
  ]
}}
"""