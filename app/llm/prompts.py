import json


def build_itinerary_prompt(
    profile: dict,
    retrieved_results: list[dict],
    clusters: list[dict],
    validated_pois: list[dict] | None = None,
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
            "\nNOTE: No validated places were found. "
            "Use well-known, real landmarks in "
            f"{', '.join(profile.get('cities', []))} only."
        )

    # ── Context snippets (descriptions only, no new place names) ─────────────
    context_snippets = []

    for i, item in enumerate(retrieved_results, start=1):
        payload = item["payload"]

    context_block = "\n\n".join(context_snippets) if context_snippets else "No context available."

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

RULES
- Every activity.location_name MUST exactly match a "name" from VALIDATED PLACES.
- Every activity.latitude and activity.longitude MUST come from VALIDATED PLACES.
- Do NOT use any place that is not in VALIDATED PLACES above.
- ALL activities on a given day must belong to the SAME city — never mix cities within one day.
- When a day is in City A, only use places listed under City A's section.
- Group geographically close places on the same day.
- Respect must-include items when possible.
- Use realistic time blocks.
- Keep descriptions concise (1–2 sentences).
- Output ONLY valid JSON, no markdown fences, no explanations outside JSON.
- If the trip covers multiple cities, dedicate full days to one city at a time.
- Do not mix cities within a single day's activities.

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