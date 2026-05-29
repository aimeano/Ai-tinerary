"""
Post-generation coordinate guard.

After the LLM outputs an itinerary it may still:
  - Copy coordinates from a neighbouring POI instead of the correct one
    (e.g. Merdeka 118 accidentally gets Gurney Drive's lat/lng).
  - Use a place name that is not in the validated list at all.

This module fixes both problems:
  1. Exact name match  → snap lat/lng to the validated geocoded value.
  2. No match         → null out coordinates and log a warning so the
                        caller (travel_time, restaurants) skips gracefully.
"""


def _build_lookup(validated_pois: list[dict]) -> dict[str, dict]:
    """Case-insensitive name → POI dict."""
    return {p["name"].lower().strip(): p for p in validated_pois}


def fix_itinerary_coordinates(
    itinerary: dict,
    validated_pois: list[dict],
) -> dict:
    """
    Walk every activity in the itinerary and:

    - If location_name matches a validated POI (case-insensitive):
        overwrite latitude/longitude with the real geocoded coordinates.
    - If location_name does NOT match any validated POI:
        set latitude/longitude to None and add a _warning field so the
        issue is visible in the output without breaking downstream steps.

    Returns the (mutated) itinerary dict.
    """
    lookup = _build_lookup(validated_pois)

    for day in itinerary.get("days", []):
        day_num = day.get("day", "?")
        for activity in day.get("activities", []):
            raw_name = activity.get("location_name", "")
            key = raw_name.lower().strip()

            if key in lookup:
                poi = lookup[key]
                old_lat = activity.get("latitude")
                old_lng = activity.get("longitude")

                activity["latitude"] = poi["lat"]
                activity["longitude"] = poi["lng"]

                # Log coordinate corrections so they're easy to spot.
                if (old_lat, old_lng) != (poi["lat"], poi["lng"]):
                    print(
                        f"[coord_guard] Day {day_num} '{raw_name}': "
                        f"corrected ({old_lat}, {old_lng}) "
                        f"→ ({poi['lat']}, {poi['lng']})"
                    )

                # Remove any leftover warning from a previous run.
                activity.pop("_warning", None)

            else:
                print(
                    f"[coord_guard] Day {day_num} '{raw_name}': "
                    "NOT in validated places — nulling coordinates."
                )
                activity["latitude"] = None
                activity["longitude"] = None
                activity["_warning"] = (
                    f"'{raw_name}' was not found in the validated place list. "
                    "Coordinates have been removed."
                )

    return itinerary
