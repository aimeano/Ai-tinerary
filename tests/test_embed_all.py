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

texts = [chunk["chunk_text"] for chunk in chunks]

vectors = embed_texts(texts, batch_size=8)

with open("app/data/processed/malaysia_vectors.json", "w", encoding="utf-8") as f:
    json.dump(vectors, f)

print("Saved vectors:", len(vectors))
print("Dimension:", len(vectors[0]))