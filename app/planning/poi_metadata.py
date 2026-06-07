# Exact supermarket / hypermarket brand names that should never appear as
# itinerary POIs.
_BLOCKED_POI_NAMES = frozenset({
    "MYDIN", "Giant", "Tesco", "AEON", "Econsave", "Lotus", "Lotus's",
    "Pasaraya", "Jaya Grocer", "Village Grocer", "Ben's Independent Grocer",
    "Cold Storage", "Mercato", "NSK", "Hero", "Billion", "Pacific",
    "Servay", "Milimewa", "Servay Hypermarket", "KK Super Mart", "KK Mart",
    "99 Speedmart", "myNEWS", "CU", "Family Mart", "FamilyMart",
})

# Substring keywords (case-insensitive) that mark a POI as a retail/
# convenience store rather than a tourist attraction.
_BLOCKED_POI_KEYWORDS = frozenset({
    "Hypermarket", "Supermarket", "Hyperstore", "Wholesale",
    "Convenience Store", "Minimart", "Mini Mart",
})


def _is_blocked(name: str) -> bool:
    if name in _BLOCKED_POI_NAMES:
        return True
    name_lower = name.lower()
    return any(kw.lower() in name_lower for kw in _BLOCKED_POI_KEYWORDS)


def collect_pois_from_metadata(results: list[dict]) -> list[str]:
    pois = set()

    for item in results:
        payload = item["payload"]

        for poi in payload.get("pois", []):
            if isinstance(poi, str) and poi.strip():
                pois.add(poi.strip())

    return sorted(p for p in pois if not _is_blocked(p))
