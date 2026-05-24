from app.retrieval.retrieve import retrieve

query = "best food places in Kuala Lumpur"

results = retrieve(query, top_k=5)

for i, item in enumerate(results, start=1):
    payload = item["payload"]

    print(f"\n===== RESULT {i} =====")
    print("Score:", item["score"])
    print("Source:", payload["source"])
    print("Country:", payload["country"])
    print("Child ID:", payload["child_id"])
    print("\nTEXT:")
    print(payload["chunk_text"][:1000])



    """
            "address": item.get("vicinity"),
            "rating": item.get("rating"),
            "user_ratings_total": item.get("user_ratings_total"),
            "latitude": loc.get("lat"),
            "longitude": loc.get("lng"),
            "place_id": item.get("place_id"), */
            """