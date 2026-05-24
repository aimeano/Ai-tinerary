import json
from app.retrieval.normalize_chunks import normalize_luxia_chunks
from app.services.luxia_embed import embed_texts

with open("app/data/processed/malaysia_chunks.json", "r", encoding="utf-8") as f:
    result = json.load(f)

chunks = normalize_luxia_chunks(
    result=result,
    source="malaysia-2.pdf",
    country="Malaysia"
)

texts = [chunk["chunk_text"] for chunk in chunks[:3]]

vectors = embed_texts(texts)

print("Number of vectors:", len(vectors))
print("Vector dimension:", len(vectors[0]))
print("First 5 values:", vectors[0][:5])