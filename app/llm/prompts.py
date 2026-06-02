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
Budget: {profile["budget"]}
Must include: {", ".join(profile["must_include"])}

VALIDATED PLACES — the ONLY locations you may schedule activities at:
{place_menu}{few_places_note}

CONTEXT (use only for writing activity descriptions — do NOT derive new place names from this):
{context_block}

FLIGHT AND TRAVEL SCHEDULE — MUST BE FOLLOWED EXACTLY
{flight_context}

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
- FLIGHT RULES ARE MANDATORY AND OVERRIDE ALL OTHER SCHEDULING DECISIONS.
- If an arrival time is given, the first activity on that date must start at or after the arrival time. Never schedule sightseeing before the traveller has landed.
- If a departure time is given, calculate the airport cutoff as exactly 4 hours before departure. The last sightseeing activity must END before this cutoff. The final scheduled item must be "Depart to Airport".
- If an intercity travel event is given, treat that date as a transition day. Morning belongs to the departing city, afternoon to the arriving city (only if arrival is before 15:00, otherwise next day).
- Never schedule more than 2 activities on a travel/transition day.
- Never schedule an activity that would overlap with a flight or travel window.
- Always insert "Depart to Airport" as the last activity on a departure day, scheduled at exactly 4 hours before the flight time.
- For food/meal activities (breakfast, lunch, dinner, snack), do NOT invent a specific restaurant as the location_name. Instead, set the location_name to the nearest validated place where the meal would logically happen (e.g. the previous or next activity's location), and write the meal description in the description field. The nearby_restaurants field will automatically be populated with real restaurant options near that location. Example: Instead of location_name "Penang Restaurant", use location_name "Petronas Twin Towers" with description "Enjoy lunch at one of the many restaurants near the towers."

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