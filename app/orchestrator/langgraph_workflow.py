from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END

from app.planning.preference_extractor import build_retrieval_query
from app.retrieval.hybrid_retrieve import hybrid_retrieve
from app.retrieval.rerank import rerank_hybrid_results
from app.planning.distance_planner import geocode_pois, cluster_pois
from app.llm.prompts import build_itinerary_prompt
from app.llm.generate import generate_with_ollama
from app.planning.poi_metadata import collect_pois_from_metadata
from app.llm.json_utils import extract_json_object
from app.planning.restaurant_suggestions import (
    attach_restaurants_to_itinerary
)
from app.planning.attach_travel_time import attach_travel_time



class TravelState(TypedDict):
    profile: Dict[str, Any]
    query: str
    hybrid_results: List[dict]
    reranked_results: List[dict]
    llm_context: List[dict]
    poi_context: List[dict]
    pois: List[str]
    geocoded: List[dict]
    clusters: List[dict]
    itinerary: str
    user_message: str
    response: str

def print_retrieved_chunks(results: list[dict]):
    print("\n===== RETRIEVED CHUNKS =====")

    for i, item in enumerate(results, start=1):
        payload = item["payload"]

        print(f"\n----- CHUNK {i} -----")

        if "rerank_score" in item:
            print(f"Rerank Score : {item['rerank_score']:.4f}")

        if "rrf_score" in item:
            print(f"RRF Score    : {item['rrf_score']:.4f}")

        print(f"Source       : {payload.get('source')}")
        print(f"Country      : {payload.get('country')}")
        print(f"Location     : {payload.get('location')}")
        print(f"Section      : {payload.get('section')}")
        print(f"Child ID     : {payload.get('child_id')}")

        text = payload.get("chunk_text", "")

        preview = text[:700].strip()

        print("\nTEXT:")
        print(preview)

        print("\n" + "=" * 80)

def build_query_node(state: TravelState):
    query = build_retrieval_query(state["profile"])
    return {**state, "query": query}


def retrieve_node(state: TravelState):
    profile = state["profile"]

    hybrid_results = hybrid_retrieve(
        query=state["query"],
        top_k=25,
        candidate_k=40,
        country=profile["country"],
        locations=profile["cities"],
    )

    return {**state, "hybrid_results": hybrid_results}


def rerank_node(state: TravelState):
    reranked = rerank_hybrid_results(
        query=state["query"],
        hybrid_results=state["hybrid_results"],
        top_k=5,
    )

    llm_context = [
        r for r in reranked
        if r["rerank_score"] >= 0.2
    ]

    print_retrieved_chunks(llm_context)

    poi_context = [
        r for r in reranked
        if r["rerank_score"] >= 0.5
    ]

    return {
        **state,
        "reranked_results": reranked,
        "llm_context": llm_context,
        "poi_context": poi_context,
    }

def poi_node(state: TravelState):
    poi_context = [
        r for r in state["reranked_results"]
        if r["rerank_score"] >= 0.5
    ]

    pois = collect_pois_from_metadata(poi_context)

    return {
        **state,
        "pois": pois
    }


def geocode_cluster_node(state: TravelState):
    profile = state["profile"]
    city_hint = f"{', '.join(profile['cities'])}, {profile['country']}"

    geocoded = geocode_pois(
        state["pois"],
        city_hint=city_hint,
    )

    clusters = cluster_pois(
        geocoded,
        radius_km=2.5,
    )

    return {
        **state,
        "geocoded": geocoded,
        "clusters": clusters,
    }


def generate_itinerary_node(state: TravelState):
    prompt = build_itinerary_prompt(
        profile=state["profile"],
        retrieved_results=state["reranked_results"],
        clusters=state["clusters"],
    )

    raw = generate_with_ollama(prompt)
    print("\n===== RAW MODEL OUTPUT =====\n")
    print(raw)

    itinerary_json = extract_json_object(raw)

    itinerary_json = attach_restaurants_to_itinerary(
        itinerary_json,
        limit_per_activity=3,
    )

    itinerary_json = attach_travel_time(itinerary_json)

    return {
        "itinerary": itinerary_json,
        "response": itinerary_json,
    }



def build_initial_itinerary_graph():
    graph = StateGraph(TravelState)

    graph.add_node("build_query", build_query_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("extract_pois", poi_node)
    graph.add_node("geocode_cluster", geocode_cluster_node)
    graph.add_node("generate_itinerary", generate_itinerary_node)

    graph.set_entry_point("build_query")

    graph.add_edge("build_query", "retrieve")
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "extract_pois")
    graph.add_edge("extract_pois", "geocode_cluster")
    graph.add_edge("geocode_cluster", "generate_itinerary")
    graph.add_edge("generate_itinerary", END)

    return graph.compile()


initial_itinerary_app = build_initial_itinerary_graph()


def run_initial_itinerary(profile: dict):
    initial_state: TravelState = {
        "profile": profile,
        "query": "",
        "hybrid_results": [],
        "reranked_results": [],
        "llm_context": [],
        "poi_context": [],
        "pois": [],
        "geocoded": [],
        "clusters": [],
        "itinerary": "",
        "user_message": "",
        "response": "",
    }

    return initial_itinerary_app.invoke(initial_state)