from pathlib import Path

from app.retrieval.ingest import (
    infer_metadata_from_filename,
    build_chunks_from_markdown,
    enrich_chunks_with_metadata,
)
from app.preprocessing.clean_html import clean_luxia_html


def main():
    source = "Malaysia-general-wikivoyage.pdf"
    stem = Path(source).stem

    metadata = infer_metadata_from_filename(source)

    html_path = Path(f"app/data/clean/{stem}_raw.html")
    clean_path = Path(f"app/data/clean/{stem}_clean.md")

    if clean_path.exists():
        cleaned = clean_path.read_text(encoding="utf-8")
    else:
        html = html_path.read_text(encoding="utf-8")
        cleaned = clean_luxia_html(html)
        clean_path.write_text(cleaned, encoding="utf-8")

    chunks = build_chunks_from_markdown(
        cleaned=cleaned,
        source=source,
        country=metadata["country"],
        location=metadata["location"],
        source_type=metadata["source_type"],
    )

    print("Chunks:", len(chunks))

    sample_chunks = chunks[:5]

    enriched = enrich_chunks_with_metadata(
        chunks=sample_chunks,
        country=metadata["country"],
        location=metadata["location"],
    )

    for i, chunk in enumerate(enriched, start=1):
        print("\n" + "=" * 80)
        print("CHUNK", i)
        print("Section:", chunk.get("section"))
        print("Topic:", chunk.get("topic"))
        print("Content type:", chunk.get("content_type"))
        print("Travel intents:", chunk.get("travel_intents"))
        print("POIs:", chunk.get("pois"))
        print("Practical:", chunk.get("is_practical_info"))
        print("Itinerary:", chunk.get("is_itinerary_content"))
        print("\nText preview:")
        print(chunk.get("chunk_text", "")[:500])


if __name__ == "__main__":
    main()