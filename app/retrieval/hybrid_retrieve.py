from pathlib import Path
import json
from typing import List, Optional
from app.retrieval.retrieve import retrieve
from app.retrieval.keyword_index import BM25Index
from app.retrieval.normalize_chunks import normalize_luxia_chunks


PROCESSED_DIR = Path("app/data/processed")

def infer_retrieval_profile(query: str) -> dict:
    q = query.lower()

    if any(k in q for k in [
        "visa",
        "passport",
        "immigration",
        "entry",
        "law",
        "rules",
    ]):
        return {
            "section_keywords": [
                "visa",
                "immigration",
                "entry",
                "law",
                "customs",
            ],
            "intent": "entry_rules"
        }

    if any(k in q for k in [
        "weather",
        "climate",
        "rain",
        "monsoon",
        "clothes",
        "pack",
    ]):
        return {
            "section_keywords": [
                "weather",
                "climate",
                "season",
                "temperature",
                "rain",
            ],
            "intent": "weather"
        }

    if any(k in q for k in [
        "food",
        "cafe",
        "restaurant",
        "eat",
        "dining",
    ]):
        return {
            "section_keywords": [
                "food",
                "eat",
                "dining",
                "restaurant",
                "cafe",
                "market",
            ],
            "intent": "food"
        }

    if any(k in q for k in [
        "shopping",
        "mall",
        "market",
        "buy",
    ]):
        return {
            "section_keywords": [
                "shopping",
                "market",
                "buy",
                "mall",
            ],
            "intent": "shopping"
        }

    if any(k in q for k in [
        "transport",
        "train",
        "bus",
        "airport",
        "taxi",
        "mrt",
        "lrt",
    ]):
        return {
            "section_keywords": [
                "transport",
                "getting around",
                "bus",
                "train",
                "airport",
                "taxi",
            ],
            "intent": "transport"
        }

    return {
        "section_keywords": [],
        "intent": "general"
    }

def load_chunks(
    country: Optional[str] = None,
    locations:  Optional[List[str]] = None
):
    all_chunks = []

    chunk_files = list(PROCESSED_DIR.glob("*_chunks.json"))

    for chunk_file in chunk_files:
        stem = chunk_file.name.replace("_chunks.json", "")
        source = f"{stem}.pdf"

        parts = stem.lower().split("-")

        file_country = parts[0].title()
        file_location = (
            " ".join(parts[1:-1]).title()
            if len(parts) > 2
            else "General"
        )
        file_source_type = (
            parts[-1].title()
            if len(parts) > 2
            else "Unknown"
        )

        if country and file_country.lower() != country.lower():
            continue

        with open(chunk_file, "r", encoding="utf-8") as f:
            result = json.load(f)

        if isinstance(result, list):
            chunks = result
        else:
            chunks = normalize_luxia_chunks(
                result=result,
                source=source,
                country=file_country,
                location=file_location,
                source_type=file_source_type
            )

        all_chunks.extend(chunks)

    return all_chunks


def make_doc_id(payload: dict):
    return (
        f'{payload["source"]}_'
        f'{payload.get("parent_id")}_'
        f'{payload.get("child_id")}'
    )


def rrf_fusion(vector_results, bm25_results, k: int = 60):
    scores = {}
    docs = {}

    for rank, item in enumerate(vector_results, start=1):
        payload = item["payload"]
        doc_id = make_doc_id(payload)

        scores[doc_id] = scores.get(doc_id, 0) + (1 / (k + rank))
        docs[doc_id] = payload

    for rank, item in enumerate(bm25_results, start=1):
        payload = item["payload"]
        doc_id = make_doc_id(payload)

        scores[doc_id] = scores.get(doc_id, 0) + (1 / (k + rank))
        docs[doc_id] = payload

    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [
        {
            "rrf_score": score,
            "payload": docs[doc_id]
        }
        for doc_id, score in fused
    ]

def apply_metadata_boosts(results, query, locations=None):
    q = query.lower()
    boosted = []

    for item in results:
        payload = item["payload"]
        score = item["rrf_score"]

        topic = payload.get("topic", "").lower()
        location = payload.get("location", "").lower()
        section = payload.get("section", "").lower()
        intents = [x.lower() for x in payload.get("travel_intents", [])]

        for loc in locations or []:
            if location == loc.lower():
                score += 0.35

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

        if topic in ALLOWED_TOPICS:
            if topic in q:
                score += 0.35

        if any(word in q for word in intents):
            score += 0.20

        boosted.append({**item, "rrf_score": score})

    return sorted(boosted, key=lambda x: x["rrf_score"], reverse=True)




def hybrid_retrieve(
    query: str,
    top_k: int = 5,
    candidate_k: int = 30,
    country:  Optional[str] = None,
    locations: Optional[List[str]] = None,
):
    chunks = load_chunks(
        country=country,
        locations=locations
    )

    bm25 = BM25Index(chunks)

    vector_results = retrieve(
        query=query,
        top_k=candidate_k,
        country=country
    )

    bm25_results = bm25.search(
        query=query,
        top_k=candidate_k
    )

    fused = rrf_fusion(vector_results, bm25_results)
    fused = apply_metadata_boosts(
    results=fused,
    query=query,
    locations=locations
)

    return fused[:top_k]