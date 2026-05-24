from app.retrieval.hybrid_retrieve import hybrid_retrieve
from app.retrieval.rerank import rerank_hybrid_results

query = "Jalan Alor food in Kuala Lumpur"

hybrid_results = hybrid_retrieve(query, top_k=20, candidate_k=30)
final_results = rerank_hybrid_results(query, hybrid_results, top_k=5)

for i, item in enumerate(final_results, start=1):
    payload = item["payload"]

    print(f"\n===== FINAL RESULT {i} =====")
    print("Rerank Score:", item["rerank_score"])
    print("RRF Score:", item["rrf_score"])
    print("Source:", payload["source"])
    print("Child ID:", payload["child_id"])

    print("\nCHILD:")
    print(payload["chunk_text"][:700])

    print("\nPARENT CONTEXT:")
    print(payload.get("parent_chunk", "")[:1200])