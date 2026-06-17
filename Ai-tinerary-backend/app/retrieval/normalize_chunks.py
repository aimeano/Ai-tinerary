import re

def normalize_luxia_chunks(
    result: dict,
    source: str,
    country: str,
    location: str,
    source_type: str,
    section: str = ""
):
    raw_chunks = (
        result.get("chunks")
        or result.get("data")
        or result.get("result")
        or []
    )
    normalized = []

    if not isinstance(raw_chunks, list):
        raise ValueError("normalize_luxia_chunks expected list of chunks")

    for item in raw_chunks:
        # Luxia chunk format
        child_text = item.get("child_chunk")
        parent_text = item.get("parent_chunk")

        # Manual section chunk format
        if not child_text:
            child_text = item.get("chunk_text")

        if not parent_text:
            parent_text = child_text

        text = child_text or parent_text
        

        if not text:
            continue

        quality = chunk_quality_score(text)

        if quality < 0.45:
            continue

        section_value = item.get("section") or section

        normalized.append({
            "source": source,
            "country": country,
            "location": location,
            "source_type": source_type,

            "topic": item.get("topic", "general_overview"),
            "content_type": item.get("content_type", ""),
            "travel_intents": item.get("travel_intents", []),
            "pois": item.get("pois", []),
            "is_itinerary_content": item.get("is_itinerary_content", False),
            "is_practical_info": item.get("is_practical_info", False),

            "section": section_value,
            "parent_id": item.get("parent_id"),
            "child_id": item.get("child_id"),
            "length": item.get("length"),
            "chunk_text": child_text,
            "parent_chunk": parent_text,
        })

    return normalized

def chunk_quality_score(text: str) -> float:
    score = 1.0

    lines = text.splitlines()

    # too many short lines → TOC/navigation
    short_lines = sum(1 for l in lines if len(l.strip()) < 25)

    if len(lines) > 0:
        short_ratio = short_lines / len(lines)

        if short_ratio > 0.6:
            score -= 0.4

    # too many standalone numbers
    standalone_numbers = len(
        re.findall(r"\b\d+\b", text)
    )

    if standalone_numbers > 15:
        score -= 0.3

    # low sentence count
    sentences = re.split(r"[.!?]", text)

    real_sentences = [
        s for s in sentences
        if len(s.strip().split()) > 5
    ]

    if len(real_sentences) < 3:
        score -= 0.3

    # excessive formatting markers
    formatting = text.count("##") + text.count("|")

    if formatting > 15:
        score -= 0.2

    return max(score, 0.0)