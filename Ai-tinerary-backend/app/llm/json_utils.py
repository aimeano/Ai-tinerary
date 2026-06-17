import json
import re


def extract_json_object(raw: str) -> dict:
    raw = raw.strip()

    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")

    match = re.search(r"\{.*\}", raw, re.DOTALL)

    if not match:
        raise ValueError("No JSON found.")

    json_text = match.group(0)

    if "..." in json_text:
        raise ValueError("Truncated JSON detected.")

    # Python-style values → JSON values
    json_text = re.sub(r":\s*None\b", ": null", json_text)
    json_text = re.sub(r":\s*True\b", ": true", json_text)
    json_text = re.sub(r":\s*False\b", ": false", json_text)

    # Fix accidental non-numeric characters before latitude/longitude numbers
    json_text = re.sub(
        r'("latitude"\s*:\s*)[^\d\-\.\n]+(-?\d+(?:\.\d+)?)',
        r'\1\2',
        json_text,
    )
    json_text = re.sub(
        r'("longitude"\s*:\s*)[^\d\-\.\n]+(-?\d+(?:\.\d+)?)',
        r'\1\2',
        json_text,
    )

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as e:
        print("\n===== INVALID JSON =====\n")
        print(json_text)
        raise e