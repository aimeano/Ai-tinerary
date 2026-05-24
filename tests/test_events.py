from app.planning.events import fetch_events_for_city
import json

events = fetch_events_for_city(
    city="Kuala Lumpur",
    country="Malaysia",
    start_date="2026-06-01",
    end_date="2026-06-07",
)

print(json.dumps(events, indent=2))