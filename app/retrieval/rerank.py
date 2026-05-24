from app.services.luxia_rerank import rerank_texts


def rerank_hybrid_results(query: str, hybrid_results: list[dict], top_k: int = 5):
    documents = [
        item["payload"]["chunk_text"]
        for item in hybrid_results
    ]

    rerank_result = rerank_texts(
        query=query,
        documents=documents,
        top_k=top_k
    )

    final_results = []

    for item in rerank_result["results"]:
        idx = item["index"]
        score = item["score"]

        original = hybrid_results[idx]

        final_results.append({
            "rerank_score": score,
            "rrf_score": original.get("rrf_score"),
            "payload": original["payload"]
        })

    return final_results