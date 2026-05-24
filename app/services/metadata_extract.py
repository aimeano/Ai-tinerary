import os
import json
import re
import requests

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LUXIA_API_KEY")

URL = "https://bridge.luxiacloud.com/luxia/v1/chat"

HEADERS = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}


ALLOWED_TOPICS = [
    "food",
    "shopping",
    "transport",
    "weather_climate",
    "visa_entry",
    "rules_laws",
    "safety",
    "culture_etiquette",
    "money_currency",
    "sim_internet",
    "electricity",
    "accommodation",
    "attractions",
    "nature",
    "nightlife",
    "general_overview",
]


def parse_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)

    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def normalize_pois(raw_pois) -> list[str]:
    normalized = []

    if not isinstance(raw_pois, list):
        return []

    for poi in raw_pois:
        if isinstance(poi, str):
            name = poi.strip()

        elif isinstance(poi, dict):
            name = str(poi.get("name", "")).strip()

        else:
            continue

        if not name:
            continue

        normalized.append(name)

    return list(dict.fromkeys(normalized))


def extract_chunk_metadata(
    chunk_text: str,
    country: str,
    location: str,
):
    prompt = f"""
    Extract travel metadata from this chunk.

    Country:
    {country}

    Location:
    {location}

    Chunk:
    {chunk_text}

    Return ONLY valid JSON.

    Schema:
    {{
    "topic": "",
    "content_type": "",
    "travel_intents": [],
    "pois": [],
    "is_itinerary_content": true,
    "is_practical_info": false
    }}

    Allowed topic values:
    {ALLOWED_TOPICS}

    Rules:
    - topic must be one allowed value.
    - pois must always be an array of strings.
    - Extract only real named places.
    - Do not include generic words.
    - travel_intents should be short keywords.
    """

    response = requests.post(
        URL,
        headers=HEADERS,
        json={
            "model": "luxia3-llm-8b-0731",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0
        }
    )

    response.raise_for_status()

    data = response.json()

    raw = data["choices"][0]["message"]["content"].strip()

    parsed = parse_json(raw)

    topic = parsed.get("topic", "general_overview")

    if topic not in ALLOWED_TOPICS:
        topic = "general_overview"

    return {
        "topic": topic,
        "content_type": parsed.get("content_type", ""),
        "travel_intents": parsed.get("travel_intents", []),
        "pois": normalize_pois(parsed.get("pois", [])),
        "is_itinerary_content": bool(
            parsed.get("is_itinerary_content", False)
        ),
        "is_practical_info": bool(
            parsed.get("is_practical_info", False)
        ),
    }