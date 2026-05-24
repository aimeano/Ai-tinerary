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

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as e:
        print("\n===== INVALID JSON =====\n")
        print(json_text)

        raise e