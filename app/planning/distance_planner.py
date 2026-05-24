import os
import requests
from dotenv import load_dotenv
from math import radians, sin, cos, sqrt, atan2

import numpy as np
from sklearn.cluster import DBSCAN

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def geocode_pois(pois: list[str], city_hint: str = "") -> list[dict]:
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Missing GOOGLE_MAPS_API_KEY in .env")

    geocoded = []

    for poi in pois:
        query = f"{poi}, {city_hint}" if city_hint and city_hint.lower() not in poi.lower() else poi

        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": query,
                "key": GOOGLE_MAPS_API_KEY
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            print(f"Skipping {poi}: {data.get('status')}")
            continue

        result = data["results"][0]
        location = result["geometry"]["location"]

        geocoded.append({
            "name": poi,
            "formatted_address": result.get("formatted_address"),
            "lat": location["lat"],
            "lng": location["lng"],
            "types": result.get("types", [])
        })

    return geocoded


def haversine_km(lat1, lng1, lat2, lng2):
    radius_km = 6371

    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return radius_km * c


def build_local_distance_matrix(geocoded_pois: list[dict]) -> list[dict]:
    matrix = []

    for i, origin in enumerate(geocoded_pois):
        for j, destination in enumerate(geocoded_pois):
            if i == j:
                continue

            distance_km = haversine_km(
                origin["lat"],
                origin["lng"],
                destination["lat"],
                destination["lng"]
            )

            matrix.append({
                "from": origin["name"],
                "to": destination["name"],
                "distance_km": round(distance_km, 2)
            })

    return matrix


def cluster_pois(geocoded_pois: list[dict], radius_km: float = 2.5) -> list[dict]:
    if not geocoded_pois:
        return []

    coords = np.array([
        [poi["lat"], poi["lng"]]
        for poi in geocoded_pois
    ])

    coords_rad = np.radians(coords)

    earth_radius_km = 6371
    epsilon = radius_km / earth_radius_km

    clustering = DBSCAN(
        eps=epsilon,
        min_samples=1,
        metric="haversine"
    ).fit(coords_rad)

    clusters = {}

    for poi, label in zip(geocoded_pois, clustering.labels_):
        label = int(label)
        clusters.setdefault(label, []).append(poi)

    return [
        {
            "cluster_id": label,
            "places": places
        }
        for label, places in clusters.items()
    ]