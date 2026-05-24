from app.retrieval.hybrid_retrieve import hybrid_retrieve
from app.retrieval.rerank import rerank_hybrid_results

from app.llm.prompts import build_itinerary_prompt
from app.llm.generate import generate_with_ollama

def build_retrieval_query(profile: dict) -> str:
    return f"""
    Country: {profile["country"]}
    Cities: {", ".join(profile["cities"])}
    Travel style: {profile["travel_style"]}
    Budget: {profile["budget"]}
    Interests: {", ".join(profile["interests"])}
    Must include: {", ".join(profile["must_include"])}
    """
profile = {
    "country": "Malaysia",
    "cities": ["Kuala Lumpur"],
    "travel_style": "food-focused, casual, local experience",
    "budget": "mid-range",
    "interests": ["street food", "local food", "night markets"],
    "must_include": ["Jalan Alor"]
}

query = build_retrieval_query(profile)

hybrid_results = hybrid_retrieve(query, top_k=20, candidate_k=30)

reranked = rerank_hybrid_results(query, hybrid_results, top_k=5)

# Step 3: filter weak results
retrieved = [
    r for r in reranked
    if r["rerank_score"] >= 0.2
]

# Step 4: build prompt
prompt = build_itinerary_prompt(query, retrieved)

# Step 5: generate
answer = generate_with_ollama(prompt)

print(answer)