def collect_pois_from_metadata(results: list[dict]) -> list[str]:
    pois = set()

    for item in results:
        payload = item["payload"]

        for poi in payload.get("pois", []):
            if isinstance(poi, str) and poi.strip():
                pois.add(poi.strip())

    return sorted(pois)