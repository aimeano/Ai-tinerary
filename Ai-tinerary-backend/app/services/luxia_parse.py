import os
import requests
from dotenv import load_dotenv

load_dotenv()

LUXIA_API_KEY = os.getenv("LUXIA_API_KEY")
PARSE_URL = "https://bridge.luxiacloud.com/luxia/v1/document-parse"


def extract_content(result: dict) -> str:
    print("Luxia response keys:", result.keys())

    if "content" in result:
        return result["content"]

    if "data" in result and isinstance(result["data"], dict):
        if "content" in result["data"]:
            return result["data"]["content"]
        if "html" in result["data"]:
            return result["data"]["html"]

    if "html" in result:
        return result["html"]

    raise KeyError(f"Could not find parsed content. Keys: {result.keys()}")


def parse_document(path_or_url: str, output_mode: str = "html", ocr: str = "auto") -> str:
    if not LUXIA_API_KEY:
        raise ValueError("Missing LUXIA_API_KEY in .env")

    headers = {
        "apikey": LUXIA_API_KEY
    }

    data = {
        "output_mode": output_mode,
        "ocr": ocr
    }

    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        data["url"] = path_or_url

        response = requests.post(
            PARSE_URL,
            headers=headers,
            data=data,
            timeout=(30, 600)
        )

    else:
        with open(path_or_url, "rb") as f:
            response = requests.post(
                PARSE_URL,
                headers=headers,
                files={"file": f},
                data=data,
                timeout=(30, 600)
            )

    if response.status_code != 200:
        print("Status:", response.status_code)
        print("Response:", response.text[:1000])

    response.raise_for_status()

    result = response.json()

    return extract_content(result)