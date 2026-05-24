import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

LUXIA_API_KEY = os.getenv("LUXIA_API_KEY")
EMBED_URL = "https://bridge.luxiacloud.com/luxia/v1/embedding"


def _embed_batch(texts: list[str], max_retries: int = 3) -> list[list[float]]:
    for attempt in range(max_retries):
        try:
            response = requests.post(
                EMBED_URL,
                headers={
                    "apikey": LUXIA_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"inputs": texts},
                timeout=(30, 300),
            )

            if response.status_code != 200:
                print("Status:", response.status_code)
                print("Response:", response.text[:500])

            response.raise_for_status()
            result = response.json()

            return [item["embedding"] for item in result["data"]]

        except requests.exceptions.RequestException as e:
            print(f"Embedding failed. Attempt {attempt + 1}/{max_retries}: {e}")
            time.sleep(2 * (attempt + 1))

    raise RuntimeError("Embedding batch failed after retries.")


def embed_texts(texts: list[str], batch_size: int = 8) -> list[list[float]]:
    if not LUXIA_API_KEY:
        raise ValueError("Missing LUXIA_API_KEY in .env")

    all_vectors = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        print(f"Embedding batch {start // batch_size + 1}: {start}–{start + len(batch) - 1}")

        vectors = _embed_batch(batch)
        all_vectors.extend(vectors)

        time.sleep(1)

    return all_vectors