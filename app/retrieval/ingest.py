import json
import hashlib
from pathlib import Path

from app.services.luxia_parse import parse_document
from app.preprocessing.clean_html import clean_luxia_html
from app.services.luxia_chunk import chunk_text
from app.services.luxia_embed import embed_texts
from app.services.metadata_extract import extract_chunk_metadata
from app.preprocessing.section_splitter import split_markdown_by_h2
from app.retrieval.normalize_chunks import normalize_luxia_chunks
from app.retrieval.vectorstore import recreate_collection, upsert_chunks


RAW_DIR = Path("app/data/raw")
CLEAN_DIR = Path("app/data/clean")
PROCESSED_DIR = Path("app/data/processed")
MANIFEST_PATH = PROCESSED_DIR / "ingest_manifest.json"


def infer_metadata_from_filename(filename: str) -> dict:
    stem = filename.replace(".pdf", "").lower()
    parts = stem.split("-")

    country = parts[0].title() if len(parts) > 0 else "Unknown"
    location = parts[1].replace("_", " ").title() if len(parts) > 1 else "General"
    source_type = "-".join(parts[2:]).replace("_", " ").title() if len(parts) > 2 else "Unknown"

    return {
        "country": country,
        "location": location,
        "source_type": source_type,
        "source": filename,
    }


def file_hash(path: Path) -> str:
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict):
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def make_manual_chunk(
    text: str,
    section: str,
    source: str,
    country: str,
    location: str,
    source_type: str,
    parent_id: int,
    child_id: int,
) -> dict:
    text = text.strip()

    return {
        "source": source,
        "country": country,
        "location": location,
        "source_type": source_type,
        "topic": "general_overview",
        "content_type": "",
        "travel_intents": [],
        "pois": [],
        "is_itinerary_content": False,
        "is_practical_info": False,
        "section": section,
        "parent_id": parent_id,
        "child_id": child_id,
        "length": len(text),
        "chunk_text": text,
        "parent_chunk": text,
    }


def build_chunks_from_markdown(
    cleaned: str,
    source: str,
    country: str,
    location: str,
    source_type: str,
) -> list[dict]:
    sections = split_markdown_by_h2(cleaned)

    chunks = []
    child_id = 0

    for parent_id, section in enumerate(sections):
        title = section["section_title"]
        content = section["content"].strip()

        if not content:
            continue

        word_count = len(content.split())

        if word_count < 40:
            continue

        if word_count <= 900:
            chunk = make_manual_chunk(
                text=content,
                section=title,
                source=source,
                country=country,
                location=location,
                source_type=source_type,
                parent_id=parent_id,
                child_id=child_id,
            )

            chunks.append(chunk)
            child_id += 1

        else:
            luxia_result = chunk_text(content)

            normalized = normalize_luxia_chunks(
                result=luxia_result,
                source=source,
                country=country,
                location=location,
                source_type=source_type,
                section=title,
            )

            for chunk in normalized:
                chunk["child_id"] = child_id
                chunks.append(chunk)
                child_id += 1

    return chunks


def enrich_chunks_with_metadata(
    chunks: list[dict],
    country: str,
    location: str,
) -> list[dict]:
    enriched = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"Extracting metadata {i}/{len(chunks)}")

        text = chunk.get("chunk_text", "")

        metadata = extract_chunk_metadata(
            chunk_text=text,
            country=country,
            location=location,
        )

        enriched.append({
            **chunk,
            **metadata,
        })

    return enriched


def clean_valid_chunks(chunks: list[dict]) -> list[dict]:
    valid_chunks = []

    for chunk in chunks:
        text = chunk.get("chunk_text")

        if not isinstance(text, str):
            continue

        text = text.strip()

        if not text:
            continue

        if len(text) > 6000:
            text = text[:6000]

        chunk["chunk_text"] = text

        if not chunk.get("parent_chunk"):
            chunk["parent_chunk"] = text

        valid_chunks.append(chunk)

    return valid_chunks


def ingest_pdf(pdf_path: Path):
    source = pdf_path.name
    stem = pdf_path.stem

    file_metadata = infer_metadata_from_filename(source)

    country = file_metadata["country"]
    location = file_metadata["location"]
    source_type = file_metadata["source_type"]

    html_path = CLEAN_DIR / f"{stem}_raw.html"
    clean_path = CLEAN_DIR / f"{stem}_clean.md"
    chunks_path = PROCESSED_DIR / f"{stem}_chunks.json"
    enriched_chunks_path = PROCESSED_DIR / f"{stem}_enriched_chunks.json"
    vectors_path = PROCESSED_DIR / f"{stem}_vectors.json"

    manifest = load_manifest()
    current_hash = file_hash(pdf_path)

    print(f"\nProcessing: {source}")
    print(f"Inferred country: {country}")
    print(f"Inferred location: {location}")
    print(f"Inferred source type: {source_type}")

    if (
        source in manifest
        and manifest[source]["hash"] == current_hash
        and enriched_chunks_path.exists()
        and vectors_path.exists()
    ):
        print("Already ingested. Loading cached enriched chunks and vectors.")

        chunks = load_json(enriched_chunks_path)
        vectors = load_json(vectors_path)

        return chunks, vectors

    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
        print("Loaded cached parsed HTML.")
    else:
        html = parse_document(str(pdf_path))
        html_path.write_text(html, encoding="utf-8")
        print("Parsed PDF with Luxia and saved HTML.")

    if clean_path.exists():
        cleaned = clean_path.read_text(encoding="utf-8")
        print("Loaded cached cleaned Markdown.")
    else:
        cleaned = clean_luxia_html(html)
        clean_path.write_text(cleaned, encoding="utf-8")
        print("Cleaned HTML and saved Markdown.")

    if chunks_path.exists():
        chunks = load_json(chunks_path)
        print("Loaded cached chunks.")
    else:
        chunks = build_chunks_from_markdown(
            cleaned=cleaned,
            source=source,
            country=country,
            location=location,
            source_type=source_type,
        )

        chunks = clean_valid_chunks(chunks)

        save_json(chunks_path, chunks)
        print("Header-aware chunks saved.")

    print("Chunks:", len(chunks))

    if enriched_chunks_path.exists():
        chunks = load_json(enriched_chunks_path)
        print("Loaded cached enriched metadata chunks.")
    else:
        chunks = enrich_chunks_with_metadata(
            chunks=chunks,
            country=country,
            location=location,
        )

        chunks = clean_valid_chunks(chunks)

        save_json(enriched_chunks_path, chunks)
        print("Saved enriched metadata chunks.")

    if vectors_path.exists():
        vectors = load_json(vectors_path)
        print("Loaded cached vectors.")
    else:
        chunks = clean_valid_chunks(chunks)

        texts = [chunk["chunk_text"] for chunk in chunks]

        print("Embedding texts:", len(texts))

        if not texts:
            raise ValueError(f"No valid chunk_text found for embedding: {source}")

        print("First text preview:", texts[0][:200])

        vectors = embed_texts(texts, batch_size=4)

        save_json(vectors_path, vectors)
        print("Embedded chunks and saved vectors.")

    if len(chunks) != len(vectors):
        raise ValueError(
            f"Chunk/vector mismatch for {source}: "
            f"{len(chunks)} chunks vs {len(vectors)} vectors"
        )

    manifest[source] = {
        "hash": current_hash,
        "country": country,
        "location": location,
        "source_type": source_type,
        "chunks_path": str(chunks_path),
        "enriched_chunks_path": str(enriched_chunks_path),
        "vectors_path": str(vectors_path),
        "html_path": str(html_path),
        "clean_path": str(clean_path),
    }

    save_manifest(manifest)

    return chunks, vectors


def ingest_all():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(RAW_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError("No PDF files found in app/data/raw")

    all_chunks = []
    all_vectors = []

    for pdf_path in pdf_files:
        chunks, vectors = ingest_pdf(pdf_path)

        all_chunks.extend(chunks)
        all_vectors.extend(vectors)

    print("\nTotal chunks:", len(all_chunks))
    print("Total vectors:", len(all_vectors))

    if not all_chunks or not all_vectors:
        raise ValueError("No chunks or vectors generated.")

    if len(all_chunks) != len(all_vectors):
        raise ValueError("Total chunks and vectors do not match.")

    recreate_collection(vector_size=len(all_vectors[0]))
    upsert_chunks(all_chunks, all_vectors)

    print("Finished ingesting all documents into Qdrant.")


if __name__ == "__main__":
    ingest_all()