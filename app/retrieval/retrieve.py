import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from typing import Optional, List
from app.services.luxia_embed import embed_texts

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "travel_docs")

client = QdrantClient(url=QDRANT_URL)


def normalize_title(value: str) -> str:
    return value.strip().title()


def build_qdrant_filter(
    country: Optional[str] = None,
    locations: Optional[List[str]] = None,
):
    must_conditions = []

    if country:
        must_conditions.append(
            FieldCondition(
                key="country",
                match=MatchValue(value=normalize_title(country))
            )
        )

    if locations:
        normalized_locations = [
            normalize_title(location)
            for location in locations
            if location and location.strip()
        ]

        if normalized_locations:
            must_conditions.append(
                FieldCondition(
                    key="location",
                    match=MatchAny(any=normalized_locations)
                )
            )

    if not must_conditions:
        return None

    return Filter(must=must_conditions)

def retrieve(
    query: str,
    top_k: int = 10,
    country: Optional[str] = None,
    locations: Optional[List[str]] = None,
):
    query_vector = embed_texts([query])[0]

    query_filter = build_qdrant_filter(
        country=country,
        locations=locations,
    )

    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
    )

    return [
        {
            "score": result.score,
            "payload": result.payload,
        }
        for result in response.points
    ]