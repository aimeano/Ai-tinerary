import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import Optional, List
from app.services.luxia_embed import embed_texts

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "travel_docs")

client = QdrantClient(url=QDRANT_URL)


def build_qdrant_filter(country: Optional[str] = None):
    must_conditions = []

    if country:
        must_conditions.append(
            FieldCondition(
                key="country",
                match=MatchValue(value=country.title())
            )
        )

    if not must_conditions:
        return None

    return Filter(must=must_conditions)


def retrieve(
    query: str,
    top_k: int = 10,
    country: Optional[str] = None,
):
    query_vector = embed_texts([query])[0]

    query_filter = build_qdrant_filter(country=country)

    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
    )

    results = response.points

    return [
        {
            "score": result.score,
            "payload": result.payload,
        }
        for result in results
    ]