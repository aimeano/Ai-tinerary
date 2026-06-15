from difflib import SequenceMatcher


def validate_itinerary(
    itinerary: dict,
    max_driving_seconds: int = 2700,
    max_transit_seconds: int = 3600,
    max_walking_seconds: int = 2700,
) -> dict:
    issues = []
    warnings = []

    for day in itinerary.get("days", []):
        warnings.extend(validate_day_balance(day))
        day_num = day.get("day")
        seen_locations = set()

        for activity in day.get("activities", []):
            name = activity.get("location_name") or activity.get("title")

            if name in seen_locations:
                issues.append({
                    "type": "duplicate_poi",
                    "day": day_num,
                    "location": name,
                    "message": f"Duplicate POI on Day {day_num}: {name}",
                })

            seen_locations.add(name)

            travel = activity.get("travel_from_previous")

            if not travel:
                continue

            driving = travel.get("driving")
            transit = travel.get("transit")
            walking = travel.get("walking")

            driving_seconds = driving.get("duration_seconds", 0) if driving else None
            transit_seconds = transit.get("duration_seconds", 0) if transit else None
            walking_seconds = walking.get("duration_seconds", 0) if walking else None

            if driving_seconds is not None and driving_seconds > max_driving_seconds:
                issues.append({
                    "type": "long_driving_gap",
                    "day": day_num,
                    "to": name,
                    "duration_seconds": driving_seconds,
                    "duration": driving.get("duration"),
                    "distance": driving.get("distance"),
                    "message": f"Long driving gap before {name}: {driving.get('duration')}",
                })

            elif (
                transit_seconds is not None
                and transit_seconds > max_transit_seconds
                and driving_seconds is None
            ):
                issues.append({
                    "type": "long_transit_gap",
                    "day": day_num,
                    "to": name,
                    "duration_seconds": transit_seconds,
                    "duration": transit.get("duration"),
                    "distance": transit.get("distance"),
                    "message": f"Long transit gap before {name}: {transit.get('duration')}",
                })

            if walking_seconds is not None and walking_seconds > max_walking_seconds:
                warnings.append({
                    "type": "long_walking_gap",
                    "day": day_num,
                    "to": name,
                    "duration_seconds": walking_seconds,
                    "duration": walking.get("duration"),
                    "distance": walking.get("distance"),
                    "message": f"Too far to walk before {name}: {walking.get('duration')}",
                })

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
    }


def validate_day_balance(
    day: dict,
    max_same_category_ratio: float = 0.6,
) -> list[dict]:
    warnings = []

    activities = day.get("activities", [])

    if not activities:
        warnings.append({
            "type": "empty_day",
            "day": day.get("day"),
            "message": f"Day {day.get('day')} has no activities.",
        })
        return warnings

    category_counts = {}

    for activity in activities:
        category = (activity.get("category") or "other").lower()
        category_counts[category] = category_counts.get(category, 0) + 1

    total = len(activities)

    for category, count in category_counts.items():
        ratio = count / total

        if ratio >= max_same_category_ratio:
            warnings.append({
                "type": "category_dominance",
                "day": day.get("day"),
                "category": category,
                "count": count,
                "total": total,
                "message": f"Day {day.get('day')} is too {category}-heavy: {count}/{total} activities.",
            })

    if len(category_counts) == 1 and total >= 3:
        warnings.append({
            "type": "low_variety",
            "day": day.get("day"),
            "categories": list(category_counts.keys()),
            "message": f"Day {day.get('day')} has low activity variety.",
        })

    return warnings

def normalize_name(value: str) -> str:
    return (value or "").lower().strip()


def build_poi_lookup(geocoded_pois: list[dict]) -> dict:
    lookup = {}

    for poi in geocoded_pois:
        names = [
            poi.get("name"),
            poi.get("canonical_name"),
        ]

        for name in names:
            key = normalize_name(name)
            if key:
                lookup[key] = poi

    return lookup


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def find_best_poi_match(
    activity: dict,
    geocoded_pois: list[dict],
    min_score: float = 0.72,
) -> tuple[dict | None, float]:
    activity_names = [
        activity.get("title"),
        activity.get("location_name"),
    ]

    best_poi = None
    best_score = 0.0

    for poi in geocoded_pois:
        poi_names = [
            poi.get("name"),
            poi.get("canonical_name"),
        ]

        for activity_name in activity_names:
            for poi_name in poi_names:
                score = similarity(activity_name, poi_name)

                if score > best_score:
                    best_score = score
                    best_poi = poi

    if best_score >= min_score:
        return best_poi, best_score

    return None, best_score


def validate_and_fix_coordinates(
    raw_itinerary: dict,
    geocoded_pois: list[dict],
) -> tuple[dict, list[dict]]:
    issues = []
    lookup = build_poi_lookup(geocoded_pois)

    for day in raw_itinerary.get("days", []):
        for activity in day.get("activities", []):
            title_key = normalize_name(activity.get("title"))
            location_key = normalize_name(activity.get("location_name"))

            poi = lookup.get(title_key) or lookup.get(location_key)
            match_score = 1.0 if poi else 0.0

            if not poi:
                poi, match_score = find_best_poi_match(
                    activity=activity,
                    geocoded_pois=geocoded_pois,
                    min_score=0.72,
                )

            if not poi:
                activity["latitude"] = None
                activity["longitude"] = None
                activity["place_id"] = None
                activity["google_maps_url"] = None

                issues.append({
                    "type": "unsupported_poi",
                    "day": day.get("day"),
                    "title": activity.get("title"),
                    "location_name": activity.get("location_name"),
                    "best_match_score": match_score,
                    "message": "Activity does not match any verified POI.",
                })

                continue

            activity["title"] = poi.get("name") or activity.get("title")
            activity["location_name"] = poi.get("canonical_name") or poi.get("name")
            activity["latitude"] = poi.get("lat")
            activity["longitude"] = poi.get("lng")
            activity["category"] = poi.get("category", activity.get("category"))

            activity["place_id"] = poi.get("place_id")
            activity["google_maps_url"] = poi.get("google_maps_url")

    return raw_itinerary, issues


