import json
from app.retrieval.normalize_chunks import normalize_luxia_chunks
from app.retrieval.vectorstore import recreate_collection, upsert_chunks

with open("app/data/processed/malaysia_chunks.json", "r", encoding="utf-8") as f:
    chunk_result = json.load(f)

with open("app/data/processed/malaysia_vectors.json", "r", encoding="utf-8") as f:
    vectors = json.load(f)

chunks = normalize_luxia_chunks(
    result=chunk_result,
    source="malaysia-2.pdf",
    country="Malaysia"
)

print("Chunks:", len(chunks))
print("Vectors:", len(vectors))
print("Vector dim:", len(vectors[0]))

assert len(chunks) == len(vectors)

recreate_collection(vector_size=len(vectors[0]))
upsert_chunks(chunks, vectors)

print("Inserted into Qdrant.")