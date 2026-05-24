def build_itinerary_prompt(profile: dict, retrieved_results: list[dict], clusters: list[dict]) -> str:
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

        for place in cluster["places"]:
            places.append(f"""
                - Name: {place.get("name")}
                Latitude: {place.get("lat")}
                Longitude: {place.get("lng")}
                Address: {place.get("formatted_address")}
                """)

            cluster_blocks.append(f"""
                [Cluster {cluster["cluster_id"]}]
                {''.join(places)}
                """)
            
    
            


    return f"""
You are an AI travel itinerary planner.

Create a realistic travel itinerary using ONLY the retrieved context and clustered places.

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

CLUSTERED PLACES WITH COORDINATES
{''.join(cluster_blocks)}


RULES
- Output ONLY valid JSON.
- Do not use markdown.
- Do not include explanations outside JSON.
- Every activity must have latitude and longitude.
- Use coordinates from CLUSTERED PLACES only.
- If coordinates are not available, set latitude and longitude to null.
- Respect the trip duration exactly.
- Group nearby places into the same day.
- Minimize unnecessary travel.
- Respect must-include places when possible.
- Do not invent unsupported places.
- Do not include places from unrelated countries or cities.
- Use realistic time blocks.
- Keep descriptions concise.

CRITICAL OUTPUT REQUIREMENTS
- Generate exactly {profile["days"]} day objects inside "days".
- Day numbers must be 1 to {profile["days"]}.
- Each day must contain 3 to 5 activities.
- Do not write "...".
- Do not summarize missing days.
- Do not include markdown fences.
- Do not write "Here is".
- Return raw JSON only.

JSON SCHEMA
{{
  "trip": {{
    "country": "",
    "cities": [],
    "duration_days": 0,
  }},
  "days": [
    {{
      "day": 1,
      "date" : "",
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