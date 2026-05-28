def build_itinerary_prompt(profile, retrieved_results, clusters):
    context_blocks = []

    for i, item in enumerate(retrieved_results, start=1):
        payload = item["payload"]

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

    cluster_blocks = []

    for cluster in clusters:
        places = []

        for place in cluster.get("places", []):
            places.append(f"""
- Name: {place.get("name")}
  Canonical name: {place.get("canonical_name")}
  Category: {place.get("category")}
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

    return f"""
You are an AI travel itinerary planner.

Generate a realistic, geographically sensible, and well-balanced itinerary using ONLY the clustered places provided.

USER PROFILE
Country: {profile["country"]}
Cities: {", ".join(profile["cities"])}
Trip dates: {profile["start_date"]} to {profile["end_date"]}
Duration: {profile["days"]} days
Travel style: {profile["travel_style"]}
Interests: {", ".join(profile["interests"])}
Budget: {profile["budget"]}
Must include: {", ".join(profile["must_include"])}

RETRIEVED CONTEXT
{''.join(context_blocks)}

CLUSTERED VERIFIED PLACES
{''.join(cluster_blocks)}

PLANNING RULES
- Use ONLY places listed under CLUSTERED VERIFIED PLACES.
- Do not invent new places.
- Do not use places that are not listed in the clusters.
- Prefer higher-scoring clusters and higher-scoring POIs.
- Group places from the same cluster into the same day when possible.
- Do not mix far-apart clusters in the same day unless necessary.
- Avoid repeating the same POI across multiple days.
- Respect must-include places when they appear in the clusters.
- Prioritize the user's interests and travel style.
- Each day should feel varied, not dominated by only one category.
- Avoid too many museums, galleries, malls, cafes, or landmarks in one day unless the user clearly asked for that.
- Prefer a natural mix of experiences such as sightseeing, food, shopping, culture, nature, local exploration, and rest.
- Use realistic pacing and time order.

COORDINATE RULES
- Each activity's latitude and longitude MUST be copied from its own listed clustered place.
- Do not reuse coordinates from another activity.
- Do not guess coordinates.
- Do not change coordinate values.
- If a clustered place has lat/lng, use those exact numbers.

ENRICHMENT RULES
- Do not generate nearby_restaurants.
- Do not generate travel_from_previous.
- Backend will attach restaurants and travel time later.

OUTPUT RULES
- Output ONLY valid JSON.
- Do not use markdown.
- Do not include explanations outside JSON.
- Do not write "Here is".
- Do not include markdown fences.
- Return raw JSON only.

CRITICAL OUTPUT REQUIREMENTS
- Generate exactly {profile["days"]} day objects inside "days".
- Day numbers must be 1 to {profile["days"]}.
- Dates must start from {profile["start_date"]} and end at {profile["end_date"]}.
- Each day must contain 3 to 5 activities if enough clustered places are available.
- If there are not enough places, use fewer activities but do not invent new places.
- Every activity must include:
  - time
  - title
  - location_name
  - latitude
  - longitude
  - category
  - description

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