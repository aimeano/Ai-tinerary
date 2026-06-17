import json
from datetime import datetime, timedelta


def build_context_block(retrieved_results: list[dict]) -> str:
    context_blocks = []

    for i, item in enumerate(retrieved_results, start=1):
        payload = item.get("payload", {})

        context_blocks.append(f"""
[Context {i}]
Source: {payload.get("source")}
Section: {payload.get("section")}
Topic: {payload.get("topic")}
Travel intents: {payload.get("travel_intents")}
POIs: {payload.get("pois")}

Text:
{payload.get("parent_chunk") or payload.get("chunk_text")}
""")

    return "\n".join(context_blocks) if context_blocks else "No context available."


def build_place_menu(validated_pois: list[dict] | None) -> str:
    if not validated_pois:
        return "[]"

    places = []

    for p in validated_pois:
        places.append({
            "name": p.get("name"),
            "canonical_name": p.get("canonical_name"),
            "latitude": p.get("lat"),
            "longitude": p.get("lng"),
            "category": p.get("category"),
            "city": p.get("assigned_city"),
            "address": p.get("formatted_address", ""),
            "types": p.get("types", []),
        })

    return json.dumps(places, indent=2, ensure_ascii=False)


def build_cluster_block(clusters: list[dict]) -> str:
    cluster_blocks = []

    for cluster in clusters:
        places = []

        for place in cluster.get("places", []):
            places.append(f"""
- Name: {place.get("name")}
  Canonical name: {place.get("canonical_name")}
  Category: {place.get("category")}
  Weather suitability: {place.get("weather_suitability")}
  Latitude: {place.get("lat")}
  Longitude: {place.get("lng")}
  Address: {place.get("formatted_address")}
  City: {place.get("assigned_city")}
  POI score: {place.get("poi_score")}
""")

        cluster_blocks.append(f"""
[Cluster {cluster.get("cluster_id")}]
Assigned city: {cluster.get("assigned_city")}
Cluster score: {cluster.get("cluster_score")}
Cluster size: {cluster.get("size")}

Places:
{''.join(places)}
""")

    return "\n".join(cluster_blocks) if cluster_blocks else "No clusters available."


def build_travel_style_rules(travel_style: str) -> str:
    style = (travel_style or "").lower().strip()

    rules = {
        "relaxed": """
Travel style is RELAXED.

Rules:
- Maximum 3 activities per day
- Include rest time between activities
- Avoid long travel distances between activities (prefer under 5km)
- No physically demanding activities
- Prefer parks, cafes, scenic walks, museums, shopping
""",

        "adventurous": """
Travel style is ADVENTUROUS.

Rules:
- Up to 5 activities per day
- Prioritize outdoor activities: hiking, water sports, wildlife, nature parks, extreme sports
- Include physically challenging activities where available
- Day trips to nature reserves or remote areas are encouraged
""",

        "honeymoon": """
Travel style is HONEYMOON.

Rules:
- Maximum 3 activities per day
- Prioritize romantic settings: sunset spots, scenic viewpoints, fine dining areas, beach resorts, gardens
- Avoid crowded tourist markets or family activity centers
- Activities should feel intimate and special
- Suggest evening activities like waterfront walks or hilltop views
""",

        "with friends": """
Travel style is WITH FRIENDS.

Rules:
- Up to 5 activities per day
- Mix of shopping, street food areas, nightlife districts, social activities, and popular tourist spots
- Include vibrant areas with lots of options
- Night markets, entertainment districts, and group activities preferred
""",

        "family and kids": """
Travel style is FAMILY AND KIDS.

Rules:
- Maximum 4 activities per day
- ONLY include family-friendly and child-appropriate activities
- Prioritize: zoos, aquariums, theme parks, beaches, interactive museums, nature parks with easy trails
- NEVER include: bars, nightlife, adult-only venues, strenuous hikes
- Include rest breaks between activities
- Prefer locations with facilities.
""",
    }

    return rules.get(style, f"""
Travel style is {travel_style}.

Rules:
- Plan according to this travel style.
- Keep pacing realistic.
- Avoid extreme or unsuitable activities unless clearly requested.
""")


def build_flight_context(profile: dict, flights: list[dict] | None = None) -> tuple[str, str]:
    if not flights:
        flights = profile.get("flights", [])

    if not flights:
        return "No flight or travel details provided.", ""

    flight_lines = []

    for f in flights:
        flight_type = f.get("type")

        if flight_type == "arrival":
          flight_lines.append(
              f"- ARRIVAL FLIGHT: Traveller arrives in {f.get('city')} at "
              f"{f.get('time')} on {f.get('date')}. "
              f"Treat the first 2 hours after arrival as airport transfer, baggage collection, "
              f"immigration, hotel check-in, and settling time. "
              f"Do NOT schedule any activity before 2 hours after the arrival time. "
              f"The first activity on this date must start at least 2 hours after arrival."
          )

        elif flight_type == "departure":
            try:
                dep_dt = datetime.strptime(f.get("time"), "%H:%M")
                cutoff_dt = dep_dt - timedelta(hours=4)
                cutoff_str = cutoff_dt.strftime("%H:%M")
            except Exception:
                cutoff_str = "at least 4 hours before departure"

            flight_lines.append(
                f"- DEPARTURE: Traveller departs from {f.get('city')} at {f.get('time')} "
                f"on {f.get('date')}. Last normal activity must end by {cutoff_str}. "
                f"Add final activity titled 'Depart to Airport' at {cutoff_str}."
            )

        elif flight_type == "intercity":
            try:
                dep_dt = datetime.strptime(f.get("departure_time"), "%H:%M")
                ready_dt = dep_dt - timedelta(hours=1)
                ready_str = ready_dt.strftime("%H:%M")
            except Exception:
                ready_str = "1 hour before departure"

            flight_lines.append(
                f"- INTERCITY TRAVEL: On {f.get('date')}, traveller travels from "
                f"{f.get('from_city')} to {f.get('to_city')}, departing at "
                f"{f.get('departure_time')}. Last activity in {f.get('from_city')} "
                f"must end by {ready_str}. Add mandatory activity titled "
                f"'Travel to {f.get('to_city')}'."
            )

    flight_context = "\n".join(flight_lines)

    flight_rules = """
- Flight rules are mandatory.
- Arrival day activities must start after arrival time.
- Departure day activities must finish 4 hours before departure.
- Insert "Depart to Airport" only if departure flight exists.
- Intercity travel days are transition days.
- Never schedule more than 2 attractions on transition days.
"""

    return flight_context, flight_rules


def build_itinerary_prompt(
    profile: dict,
    retrieved_results: list[dict],
    clusters: list[dict],
    validated_pois: list[dict] | None = None,
    flights: list[dict] | None = None,
) -> str:
    context_block = build_context_block(retrieved_results)
    place_menu = build_place_menu(validated_pois)
    cluster_block = build_cluster_block(clusters)
    travel_style_rules = build_travel_style_rules(profile.get("travel_style", ""))
    flight_context, flight_rules = build_flight_context(profile, flights)

    return f"""
You are an AI travel itinerary planner.

Generate a realistic, geographically sensible, enjoyable itinerary using ONLY the validated places provided.

Never invent locations.
Never invent coordinates.
Never use places outside VALIDATED PLACES.

USER PROFILE

Country: {profile["country"]}
Cities: {", ".join(profile["cities"])}
Trip dates: {profile["start_date"]} to {profile["end_date"]}
Duration: {profile["days"]} days
Travel style: {profile["travel_style"]}
Interests: {", ".join(profile.get("interests", []))}
Budget: {profile.get("budget", "not specified")}
Must include: {", ".join(profile.get("must_include", []))}

VALIDATED PLACES

These are the ONLY places that may appear in the itinerary.

{place_menu}

CLUSTERED VERIFIED PLACES

Use this to group nearby places into sensible days.

{cluster_block}

RETRIEVED CONTEXT

Use this only to improve descriptions.
Do NOT derive new place names from this context.

{context_block}

TRAVEL STYLE RULES

{travel_style_rules}

FLIGHT AND TRAVEL SCHEDULE

{flight_context}

{flight_rules}

CITY ALLOCATION RULES

Before generating:
- Determine how many usable validated places exist per city.
- Allocate days based on attraction availability.
- Do not automatically favor the first city.
- Every city should contribute meaningfully if it has enough validated places.
- Never mix cities within one day unless it is an explicit travel day.

CLUSTER PLANNING RULES

- Prefer higher-scoring clusters.
- Prefer higher-scoring POIs.
- Build each day around one main cluster when possible.
- Keep activities geographically close.
- Avoid unnecessary travel between distant clusters.
- Avoid repeating the same POI across multiple days.

ATTRACTION PRIORITY

Prefer:
- landmarks
- museums
- cultural attractions
- heritage districts
- nature attractions
- parks
- beaches
- viewpoints
- shopping districts
- local experiences


DAY DESIGN RULES

- Each day must have a clear theme or geographic focus.
- Mix culture, sightseeing, nature, shopping, and local exploration where possible.
- Do not create museum-only days unless strongly supported by available POIs.
- Do not create shopping-only days unless strongly supported by available POIs.
- Day title must reflect actual activities.
- Generate the day title after selecting the activities.

TIME RULES

Morning, 08:00–11:00:
- landmarks
- museums
- parks
- cultural attractions

Afternoon, 11:00–17:00:
- city exploration
- shopping
- beaches
- attractions
- local experiences

Evening, 18:00 onwards:
- night markets
- food streets
- waterfronts
- sunset viewpoints
- nightlife areas

Never schedule a night market before 18:00.

STRICT LOCATION RULES

Every activity must satisfy all rules:

- activity.location_name MUST exactly match a "name" from VALIDATED PLACES.
- activity.latitude MUST exactly match that validated place latitude.
- activity.longitude MUST exactly match that validated place longitude.
- activity.category should match the validated place category.
- Do not use canonical_name as location_name unless it is also listed as a validated place name.
- Do not invent coordinates.
- Do not modify coordinates.
- Do not create generic locations.

Forbidden generic location names:
- Food Court
- Local Restaurant
- Beach
- Park
- Cafe
- Shopping Area
- Island
- Street Food Area
- Viewpoint

MEAL RULES

Do NOT create standalone meal activities.

Nearby restaurants are added later by the backend.

MUST INCLUDE & INTEREST RULES

- Treat must_include and interests as guidance, not strict requirements.
- Use them to influence attraction selection and itinerary design.
- Do NOT assume they are exact place names.
- Do NOT invent locations to satisfy them.
- If they match validated places, prioritize those places when appropriate.
- If they do not match validated places, choose validated attractions that provide a similar experience or theme.
- Focus on creating the best overall itinerary from the available validated POIs.

OUTPUT RULES

- Output ONLY valid JSON.
- No markdown.
- No explanations.
- No comments.
- No code fences.
- Return raw JSON only.

CRITICAL OUTPUT REQUIREMENTS

- Generate exactly {profile["days"]} day objects.
- Day numbers must be sequential from 1 to {profile["days"]}.
- Dates must match the trip dates.
- Each day should contain 3–5 activities when enough POIs exist.
- If insufficient POIs exist, use fewer activities rather than inventing attractions.
- Every activity must include time, title, location_name, latitude, longitude, category, description.

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