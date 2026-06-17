import ollama
import os
import requests

from dotenv import load_dotenv

load_dotenv()

LUXIA_API_KEY = os.getenv("LUXIA_API_KEY")

URL = "https://bridge.luxiacloud.com/luxia/v1/chat"

HEADERS = {
    "apikey": LUXIA_API_KEY,
    "Content-Type": "application/json"
}



def generate_with_ollama(
    prompt: str,
    model: str
) -> str:
    response = requests.post(
        URL,
        headers=HEADERS,
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 12000,
        },
        timeout=(30, 600),
    )

    if response.status_code != 200:
        print("Luxia status:", response.status_code)
        print("Luxia response:", response.text[:2000])
        print("Prompt length:", len(prompt))

    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]

"""
def generate_with_ollama(prompt: str, model: str = "qwen2.5:14b") -> str:
    response = ollama.chat(
        model=model,
        options={
            "temperature": 0.1,
            "num_ctx": 12000,
            "num_predict": 12000,
        },
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response["message"]["content"]
    """