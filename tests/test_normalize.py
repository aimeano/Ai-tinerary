import json
from app.retrieval.normalize_chunks import normalize_luxia_chunks

with open("app/data/processed/malaysia_chunks.json", "r", encoding="utf-8") as f:
    result = json.load(f)

chunks = normalize_luxia_chunks(
    result=result,
    source="malaysia-2.pdf",
    country="Malaysia"
)

print("Normalized chunks:", len(chunks))
print(chunks[0])