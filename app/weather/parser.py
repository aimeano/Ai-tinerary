import re
from datetime import datetime

def parse_user_edit_message(message: str) -> dict:
    """
    Parses the user's raw chatbot message to extract:
        - day number
        - old place name (to be replaced)
        - new place name (what user wants instead)

    Handles natural language variations:
        "Change Namsan Tower to Lotte World Tower on Day 2"
        "Replace Gyeongbokgung with Bukchon Hanok on day 1"
        "Swap Gwangjang Market for COEX Mall on Day 3"
        "I want to change Namsan Tower to Lotte World on day 2"

    Args:
        message: raw text from chatbot input

    Returns:
        dict with day_num, old_place, new_place
        OR None if message could not be understood
    """
    msg = message.lower().strip()

    # ── Extract day number ──────────────────────────────────
    day_match = re.search(r'day\s*(\d+)', msg)
    if not day_match:
        print("  ⚠️  Could not find day number in message")
        print("       Include 'Day X' e.g. 'Change X to Y on Day 2'")
        return None

    day_num = int(day_match.group(1))

    # ── Extract old and new place names ────────────────────
    # Matches: change/replace/swap [old] to/with/for [new]
    pattern = re.search(
        r'(?:change|replace|swap|want to change)\s+(.+?)'
        r'\s+(?:to|with|for)\s+(.+?)'
        r'(?:\s+on\s+day|\s+day\s*\d|$)',
        msg
    )

    if not pattern:
        print("  ⚠️  Could not understand the place change")
        print("       Try: 'Change [old place] to [new place] on Day X'")
        return None

    # Capitalize properly
    old_place = pattern.group(1).strip().title()
    new_place = pattern.group(2).strip().title()

    return {
        "day_num":          day_num,
        "old_place":        old_place,
        "new_place":        new_place,
        "original_message": message
    }
