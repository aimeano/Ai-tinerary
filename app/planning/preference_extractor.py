"""def build_retrieval_query(profile: dict) -> str:
    country = profile.get("country", "").strip()
    cities = [c.strip() for c in profile.get("cities", []) if c.strip()]
    days = profile.get("days", 0)
    travel_style = profile.get("travel_style", "").strip()
    interests = [i.strip() for i in profile.get("interests", []) if i.strip()]
    budget = profile.get("budget", "").strip()
    must_include = [m.strip() for m in profile.get("must_include", []) if m.strip()]

    locations = ", ".join(cities)
    interests_text = ", ".join(interests)
    must_include_text = ", ".join(must_include)

    return f
Travel itinerary planning request.

Primary destination:
- Country: {country}
- Target cities/locations: {locations}
- Trip duration: {days} days

User preferences:
- Travel style: {travel_style}
- Interests: {interests_text}
- Budget: {budget}
- Must include places or activities: {must_include_text}

Retrieval focus:
Find detailed travel information specifically about {locations}, {country}.
Prioritize chunks that mention these target locations: {locations}.
Prioritize content related to: {interests_text}.
Prioritize must-include items: {must_include_text}.

Useful information to retrieve:
- attractions and landmarks in {locations}
- food areas, cafes, restaurants, markets, and local specialties
- shopping districts and malls
- beaches, nature areas, hiking spots, parks, or outdoor activities if relevant
- nightlife areas if relevant
- transportation and getting around
- nearby areas only if they are practical for a {days}-day itinerary

Avoid:
- unrelated countries
- unrelated regions outside {locations}
- generic country overview unless it directly supports the trip
- table of contents, cover pages, contact pages, or noisy OCR text
"""

#test
def build_retrieval_query(profile: dict) -> list[str]:
    country = profile["country"]
    cities = ", ".join(profile["cities"])
    interests = " ".join(profile["interests"])
    must_include = " ".join(profile["must_include"])

    queries = []

    base = f"{cities} {country}"

    queries.append(
        f"{base} tourist attractions landmarks"
    )

    if interests:
        queries.append(
            f"{base} {interests}"
        )

    if must_include:
        queries.append(
            f"{base} {must_include}"
        )

    return queries