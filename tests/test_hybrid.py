from app.retrieval.hybrid_retrieve import hybrid_retrieve

query = "Jalan Alor food in Kuala Lumpur"

results = hybrid_retrieve(query, top_k=5, candidate_k=30)

for i, item in enumerate(results, start=1):
    payload = item["payload"]

    print(f"\n===== RESULT {i} =====")
    print("RRF Score:", item["rrf_score"])
    print("Source:", payload["source"])
    print("Child ID:", payload["child_id"])
    print("\nTEXT:")
    print(payload["chunk_text"][:1000])