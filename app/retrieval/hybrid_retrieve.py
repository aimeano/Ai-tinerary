from pathlib import Path
import json
from typing import List, Optional

from app.retrieval.retrieve import retrieve
from app.retrieval.keyword_index import BM25Index
from app.retrieval.normalize_chunks import normalize_luxia_chunks


PROCESSED_DIR = Path("app/data/processed")


def normalize_text(value: str) -> str:
    return (value or "").lower().strip()


def is_general_location(location: str, country: Optional[str] = None) -> bool:
    loc = normalize_text(location)
    country_norm = normalize_text(country)

    if loc in {"", "general", "overview", "country"}:
        return True

    if country_norm and loc == country_norm:
        return True

    return False


def location_matches(chunk_location: str, locations: Optional[List[str]]) -> bool:
    if not locations:
        return True

    chunk_loc = normalize_text(chunk_location)

    for loc in locations:
        loc_norm = normalize_text(loc)

        if not loc_norm:
            continue

        if chunk_loc == loc_norm:
            return True

        if loc_norm in chunk_loc:
            return True

        if chunk_loc in loc_norm:
            return True

    return False


def infer_file_metadata(chunk_file: Path) -> dict:
    stem = chunk_file.name.replace("_chunks.json", "")
    source = f"{stem}.pdf"

    parts = stem.lower().split("-")

    country = parts[0].title() if len(parts) > 0 else "Unknown"

    location = (
        " ".join(parts[1:-1]).replace("_", " ").title()
        if len(parts) > 2
        else "General"
    )

    source_type = (
        parts[-1].replace("_", " ").title()
        if len(parts) > 2
        else "Unknown"
    )

    return {
        "source": source,
        "country": country,
        "location": location,
        "source_type": source_type,
    }


def make_doc_id(payload: dict) -> str:
    source = payload.get("source", "unknown_source")
    section = payload.get("section", "unknown_section")
    parent_id = payload.get("parent_id", "unknown_parent")
    child_id = payload.get("child_id", "unknown_child")

    return f"{source}|{section}|{parent_id}|{child_id}"


def dedupe_payloads(chunks: list[dict]) -> list[dict]:
    seen = set()
    deduped = []

    for chunk in chunks:
        key = make_doc_id(chunk)

        if key in seen:
            continue

        seen.add(key)
        deduped.append(chunk)

    return deduped


def dedupe_results(results):
    seen = set()
    deduped = []

    for item in results:

        payload = item.get("payload", item)

        key = make_doc_id(payload)

        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    return deduped


def load_chunks(
    country: Optional[str] = None,
    locations: Optional[List[str]] = None,
):
    all_chunks = []

    chunk_files = list(PROCESSED_DIR.glob("*_chunks.json"))

    for chunk_file in chunk_files:
        meta = infer_file_metadata(chunk_file)

        file_country = meta["country"]
        file_location = meta["location"]

        if country and normalize_text(file_country) != normalize_text(country):
            continue

        if locations:
            allow_general = is_general_location(file_location, country)

            if not allow_general and not location_matches(file_location, locations):
                continue

        with open(chunk_file, "r", encoding="utf-8") as f:
            result = json.load(f)

        if isinstance(result, list):
            chunks = result
        else:
            chunks = normalize_luxia_chunks(
                result=result,
                source=meta["source"],
                country=meta["country"],
                location=meta["location"],
                source_type=meta["source_type"],
            )

        for chunk in chunks:
            chunk.setdefault("source", meta["source"])
            chunk.setdefault("country", meta["country"])
            chunk.setdefault("location", meta["location"])
            chunk.setdefault("source_type", meta["source_type"])

        all_chunks.extend(chunks)

    return dedupe_payloads(all_chunks)


def rrf_fusion(vector_results, bm25_results, k: int = 60):
    scores = {}
    docs = {}

    vector_results = dedupe_results(vector_results)
    bm25_results = dedupe_results(bm25_results)

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
            "payload": docs[doc_id],
        }
        for doc_id, score in fused
    ]


def apply_metadata_boosts(
    results,
    query,
    locations=None,
    country=None,
    intent="general",
):
    q = query.lower()
    boosted = []
    itinerary_good_topics = {
        "food",
        "shopping",
        "attractions",
        "nature",
        "culture_etiquette",
        "nightlife",
        "accommodation",
    }

    itinerary_weak_topics = {
        "visa_entry",
        "rules_laws",
        "money_currency",
        "sim_internet",
        "electricity",
        "weather_climate",
        "transport",
        "safety",
        "hotel",
    }

    allowed_topics = {
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
    }

    country_info_topics = {
        "visa_entry",
        "rules_laws",
        "weather_climate",
        "safety",
        "culture_etiquette",
        "money_currency",
        "sim_internet",
        "electricity",
        "transport",
    }

    country_norm = normalize_text(country)

    for item in results:
        payload = item["payload"]
        score = item["rrf_score"]

        topic = normalize_text(payload.get("topic"))
        location = normalize_text(payload.get("location"))
        section = normalize_text(payload.get("section"))

        intents = [
            normalize_text(x)
            for x in payload.get("travel_intents", [])
            if x
        ]

        if intent == "ask_country_info":
            if topic in country_info_topics:
                score += 0.35

            if any(x in country_info_topics for x in intents):
                score += 0.25

            if is_general_location(location, country_norm):
                score += 0.25

            # weak city boost only
            for loc in locations or []:
                loc_norm = normalize_text(loc)

                if location == loc_norm:
                    score += 0.20
                elif loc_norm and loc_norm in location:
                    score += 0.20

        else:
            for loc in locations or []:
                loc_norm = normalize_text(loc)

                if intent == "generate_itinerary":
                    if location in loc_norm:
                        score += 0.40
            

            if intent == "generate_itinerary":
                if topic in itinerary_good_topics:
                    score += 0.25

                if topic in itinerary_weak_topics:
                    score -= 0.20

                if payload.get("is_itinerary_content") is True:
                    score += 0.25

                if payload.get("is_practical_info") is True:
                    score -= 0.20

            if topic in allowed_topics and topic in q:
                score += 0.35

            if any(intent_word in q for intent_word in intents):
                score += 0.20

            if is_general_location(location, country_norm):
                score += 0.03

        boosted.append({
            **item,
            "rrf_score": score,
        })

    boosted = sorted(boosted, key=lambda x: x["rrf_score"], reverse=True)

    return dedupe_results(boosted)


def hybrid_retrieve(
    query: str,
    top_k: int = 5,
    candidate_k: int = 30,
    country: Optional[str] = None,
    locations: Optional[List[str]] = None,
    intent: str = "general",
):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("hybrid_retrieve received an empty or invalid query.")

    query = query.strip()

    chunks = load_chunks(
        country=country,
        locations=locations,
    )

    if not chunks:
        return []

    bm25 = BM25Index(chunks)

    vector_results = retrieve(
        query=query,
        top_k=candidate_k,
        country=country,
        locations=locations,
    )

    bm25_results = bm25.search(
        query=query,
        top_k=candidate_k,
    )

    fused = rrf_fusion(
        vector_results=vector_results,
        bm25_results=bm25_results,
    )

    boosted = apply_metadata_boosts(
        results=fused,
        query=query,
        locations=locations,
        country=country,
        intent=intent,
    )

    return boosted[:top_k]


def retrieve_by_location_strategy(
    query: str,
    country: str,
    target_locations: Optional[List[str]] = None,
    intent: str = "general",
    per_location_top_k: int = 15,
    per_location_candidate_k: int = 35,
):
    all_results = []

    # Initial itinerary: city docs + general country docs
    if intent == "generate_itinerary":
        if target_locations:
            for location in target_locations:
                all_results.extend(
                    hybrid_retrieve(
                        query=query,
                        top_k=per_location_top_k,
                        candidate_k=per_location_candidate_k,
                        country=country,
                        locations=[location],
                        intent=intent,
                    )
                )

        all_results.extend(
            hybrid_retrieve(
                query=query,
                top_k=max(4, per_location_top_k // 2),
                candidate_k=per_location_candidate_k,
                country=country,
                locations=["General"],
                intent=intent,
            )
        )

        return dedupe_results(all_results)

    # Country info with city mentioned: retrieve city + general
    if intent == "ask_country_info" and target_locations:
        for location in target_locations:
            all_results.extend(
                hybrid_retrieve(
                    query=query,
                    top_k=per_location_top_k,
                    candidate_k=per_location_candidate_k,
                    country=country,
                    locations=[location],
                    intent=intent,
                )
            )

        all_results.extend(
            hybrid_retrieve(
                query=query,
                top_k=max(4, per_location_top_k // 2),
                candidate_k=per_location_candidate_k,
                country=country,
                locations=["General"],
                intent=intent,
            )
        )

        return dedupe_results(all_results)

    # Pure country info: broad retrieval
    if intent == "ask_country_info":
        results = hybrid_retrieve(
            query=query,
            top_k=per_location_top_k * 3,
            candidate_k=per_location_candidate_k * 2,
            country=country,
            locations=None,
            intent=intent,
        )
        return dedupe_results(results)

    # Normal city-focused retrieval
    if target_locations:
        for location in target_locations:
            all_results.extend(
                hybrid_retrieve(
                    query=query,
                    top_k=per_location_top_k,
                    candidate_k=per_location_candidate_k,
                    country=country,
                    locations=[location],
                    intent=intent,
                )
            )
    else:
        all_results.extend(
            hybrid_retrieve(
                query=query,
                top_k=per_location_top_k * 3,
                candidate_k=per_location_candidate_k * 2,
                country=country,
                locations=None,
                intent=intent,
            )
        )

    return dedupe_results(all_results)