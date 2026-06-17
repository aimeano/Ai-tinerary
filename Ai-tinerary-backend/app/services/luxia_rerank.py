import os
import requests
from dotenv import load_dotenv

load_dotenv()

LUXIA_API_KEY = os.getenv("LUXIA_API_KEY")
RERANK_URL = "https://bridge.luxiacloud.com/luxia/v1/rerank"


def rerank_texts(
    query: str,
    documents: list[str],
    top_k: int = 5,
    lang: str = "en"
):
    response = requests.post(
        RERANK_URL,
        headers={
            "Content-Type": "application/json",
            "apikey": LUXIA_API_KEY
        },
        json={
            "model": "luxia-rerank-v0.9",
            "query": query,
            "documents": documents,
            "top_k": top_k,
            "lang": lang
        },
        timeout=(30, 300)
    )

    if response.status_code != 200:
        print("Status:", response.status_code)
        print("Response:", response.text[:1000])

    response.raise_for_status()

    result = response.json()

    print("Rerank response keys:", result.keys())

    return result