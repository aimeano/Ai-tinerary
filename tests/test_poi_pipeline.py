from app.retrieval.hybrid_retrieve import hybrid_retrieve
from app.retrieval.rerank import rerank_hybrid_results
from app.planning.distance_planner import geocode_pois, build_local_distance_matrix, cluster_pois
from app.planning.poi_metadata import collect_pois_from_metadata
query = "shopping and food itinerary in Kuala Lumpur "

hybrid = hybrid_retrieve(query, top_k=20, candidate_k=30)
reranked = rerank_hybrid_results(query, hybrid, top_k=10)

retrieved = [
    r for r in reranked
    if r["rerank_score"] >= 0.2
]
for i, item in enumerate(retrieved, start=1):
    payload = item["payload"]

    print(f"\n===== CHUNK {i} =====")
    print(f"Score : {item['rerank_score']:.4f}")
    print(f"ID    : {payload['child_id']}")
    print(payload["chunk_text"][:500])
    print(payload["pois"])

pois = collect_pois_from_metadata(retrieved)
print("POIS:", pois)

geocoded = geocode_pois(pois, city_hint="Malaysia")


matrix = build_local_distance_matrix(geocoded)

clusters = cluster_pois(geocoded, radius_km=1)
print("\n===== CLUSTERS =====")

for cluster in clusters:
    print(f"\nCluster {cluster['cluster_id']}")

    for place in cluster["places"]:
        print(
            f"- {place['name']} "
            f"({place['lat']:.4f}, {place['lng']:.4f})"
        )