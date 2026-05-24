import json
from app.services.luxia_chunk import chunk_text

with open("app/data/clean/malaysia_clean.md", "r", encoding="utf-8") as f:
    text = f.read()

result = chunk_text(text)

with open("app/data/processed/malaysia_chunks.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Saved chunks.")