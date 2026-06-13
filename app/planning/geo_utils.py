import re
from collections import Counter

KNOWN_CITIES = [
    "Kota Kinabalu", "Sandakan", "Tawau", "Lahad Datu",
    "Kuching", "Miri", "Sibu", "Bintulu",
    "George Town", "Butterworth",
    "Ipoh", "Taiping",
    "Johor Bahru", "Muar", "Batu Pahat",
    "Alor Setar", "Langkawi",
    "Kota Bharu", "Kuala Terengganu", "Kuantan",
    "Seremban", "Shah Alam", "Petaling Jaya", "Klang",
    "Kangar", "Melaka", "Kuala Lumpur", "Putrajaya",
    "Denpasar", "Ubud", "Seminyak", "Kuta", "Sanur",
    "Jakarta", "Bandung", "Surabaya", "Yogyakarta",
    "Medan", "Makassar", "Semarang", "Palembang",
    "Mataram", "Manado", "Ambon", "Jayapura",
    "Balikpapan", "Samarinda", "Pontianak",
]

def extract_city_from_chunks(retrieved_chunks, region_name):
    city_counts = Counter()
    for item in retrieved_chunks:
        payload = item.get("payload", {})
        location = payload.get("location", "")
        if location and location.lower() != region_name.lower():
            for city in KNOWN_CITIES:
                if city.lower() == location.lower():
                    city_counts[city] += 5
                    break
        text = payload.get("chunk_text", "") or ""
        text += " " + (payload.get("parent_chunk", "") or "")
        for city in KNOWN_CITIES:
            count = len(re.findall(
                rf"\b{re.escape(city)}\b",
                text, re.IGNORECASE
            ))
            if count > 0:
                city_counts[city] += count
    if not city_counts:
        print(f"[geo_utils] No specific city found in chunks for {region_name}")
        return region_name
    best_city = city_counts.most_common(1)[0][0]
    print(f"[geo_utils] Most mentioned city: {best_city}")
    return best_city

def resolve_profile_cities(profile):
    if profile.get("geocode_cities"):
        return profile
    cities = profile.get("cities", [])
    return {
        **profile,
        "geocode_cities": list(cities),
        "rag_locations": list(cities),
        "display_cities": list(cities),
    }
