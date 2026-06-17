import os
import requests
from dotenv import load_dotenv

load_dotenv()

LUXIA_API_KEY = os.getenv("LUXIA_API_KEY")
CHUNK_URL = "https://bridge.luxiacloud.com/luxia/v1/document-chunk"


def chunk_text(text: str):
    response = requests.post(
        CHUNK_URL,
        headers={
            "apikey": LUXIA_API_KEY,
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "chunk_sizes": 700,
            "overlap": 100,
            "type": "length",
            "separator": r"##\s+",
            "enhanceChunkQuality": True,
        },
        timeout=(30, 300),
    )

    if response.status_code != 200:
        print("Status:", response.status_code)
        print("Response:", response.text[:1000])

    response.raise_for_status()
    result = response.json()

    print("Chunk response keys:", result.keys())
    return result