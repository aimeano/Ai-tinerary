from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END

from app.planning.preference_extractor import build_retrieval_query
from app.retrieval.hybrid_retrieve import hybrid_retrieve
from app.retrieval.rerank import rerank_hybrid_results
from app.planning.distance_planner import geocode_pois, cluster_pois, validate_geocoded_pois
from app.llm.prompts import build_itinerary_prompt
from app.llm.generate import generate_with_ollama
from app.planning.poi_metadata import collect_pois_from_metadata
from app.llm.json_utils import extract_json_object
from app.planning.restaurant_suggestions import (
    attach_restaurants_to_itinerary
)
from app.planning.attach_travel_time import attach_travel_time
from app.planning.coordinate_guard import fix_itinerary_coordinates
from app.llm.model_config import MODELS



class TravelState(TypedDict):
    profile: Dict[str, Any]
    queries: List[str]   # one focused query per intent (landmarks / interests / must-include)
    query: str           # joined string used by the reranker (needs a single str)
    hybrid_results: List[dict]
    reranked_results: List[dict]
    llm_context: List[dict]
    poi_context: List[dict]
    pois: List[str]
    geocoded: List[dict]
    validated_pois: List[dict]
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
    result = build_retrieval_query(state["profile"])

    # build_retrieval_query returns a list of focused query strings.
    # Keep the list for multi-pass retrieval and also store a joined string
    # for the reranker which expects a single query.
    if isinstance(result, list):
        queries = [q for q in result if q.strip()]
        query = " ".join(queries)
    else:
        queries = [result]
        query = result

    return {**state, "queries": queries, "query": query}


def retrieve_node(state: TravelState):
    profile = state["profile"]
    cities = profile["cities"]
    query = state["query"]  # pre-joined string set by build_query_node

    seen: set[str] = set()
    all_results: list[dict] = []

    for city in cities:
        city_query = f"{city} {profile['country']} tourist attractions landmarks {' '.join(profile['interests'])}"
        results = hybrid_retrieve(
            query=city_query,
            top_k=15,
            candidate_k=30,
            country=profile["country"],
            locations=[city],
        )
        for r in results:
            payload = r["payload"]
            doc_id = f"{payload.get('source')}_{payload.get('child_id')}"
            if doc_id not in seen:
                seen.add(doc_id)
                # Tag the result with its source city so downstream nodes
                # can filter strictly by city without cross-contamination.
                all_results.append({**r, "city": city})

    print(f"\n[retrieve] {len(cities)} city pass(es) → {len(all_results)} unique chunks")
    return {**state, "hybrid_results": all_results}


def rerank_node(state: TravelState):
    profile = state["profile"]

    # Build a lookup before reranking so the city tag can be re-attached
    # afterwards. The reranker only copies rerank_score, rrf_score, and
    # payload — the city field is stripped from the result dicts.
    city_lookup: dict[str, str] = {
        f"{r['payload'].get('source')}_{r['payload'].get('child_id')}": r.get("city", "")
        for r in state["hybrid_results"]
    }

    reranked = rerank_hybrid_results(
        query=f"{' '.join(profile['cities'])} {profile['country']} {' '.join(profile['interests'])}",
        hybrid_results=state["hybrid_results"],
        top_k=12,
    )

    for r in reranked:
        doc_id = f"{r['payload'].get('source')}_{r['payload'].get('child_id')}"
        r["city"] = city_lookup.get(doc_id, "")

    llm_context = [r for r in reranked if r["rerank_score"] >= 0.15]
    print_retrieved_chunks(llm_context)
    poi_context = [r for r in reranked if r["rerank_score"] >= 0.4]

    return {
        **state,
        "reranked_results": reranked,
        "llm_context": llm_context,
        "poi_context": poi_context,
    }

def poi_node(state: TravelState):
    profile = state["profile"]
    all_validated: list[dict] = []

    for city in profile["cities"]:
        # Only use chunks that were retrieved for this specific city.
        city_results = [
            r for r in state["reranked_results"]
            if r.get("city") == city
        ]

        pois = collect_pois_from_metadata(city_results)

        geocoded = geocode_pois(
            pois,
            city_hint=f"{city}, {profile['country']}",
        )

        # Validate strictly against this city only — no cross-city leakage.
        validated = validate_geocoded_pois(
            geocoded,
            cities=[city],
            country=profile["country"],
        )

        all_validated.extend(validated)

    print(
        f"\n[poi] {len(profile['cities'])} cities "
        f"→ {len(all_validated)} total validated POIs"
    )
    return {**state, "validated_pois": all_validated}


def geocode_cluster_node(state: TravelState):
    # Geocoding and per-city validation now happen in poi_node.
    # This node only clusters the already-validated POIs.
    clusters = cluster_pois(
        state["validated_pois"],
        radius_km=2.5,
    )

    return {
        **state,
        "clusters": clusters,
    }


def validate_itinerary_against_clusters(
    itinerary: dict,
    validated_pois: list[dict],
) -> dict:
    """
    Post-generation hallucination check.

    Walk every activity and verify its location_name appears (or is a
    substring of) a validated POI name.  Activities that cannot be matched
    have their coordinates nulled so that attach_restaurants and
    attach_travel_time skip them gracefully.
    """
    valid_names = {p["name"].lower().strip() for p in validated_pois}

    for day in itinerary.get("days", []):
        for activity in day.get("activities", []):
            name = activity.get("location_name", "").lower().strip()
            matched = (
                name in valid_names
                or any(name in v or v in name for v in valid_names)
            )
            if not matched:
                print(
                    f"[hallucination_check] Day {day.get('day')} "
                    f"'{activity.get('location_name')}' not in validated places — nulling."
                )
                activity["latitude"] = None
                activity["longitude"] = None
                activity["_warning"] = (
                    f"'{activity['location_name']}' was not found "
                    f"in the validated place list. "
                    f"Coordinates have been removed."
                )

    return itinerary


def generate_itinerary_node(state: TravelState):
    prompt = build_itinerary_prompt(
        profile=state["profile"],
        retrieved_results=state["reranked_results"],
        clusters=state["clusters"],
        validated_pois=state["validated_pois"],
    )

    raw = generate_with_ollama(
        prompt,
        model=MODELS["generate_itinerary"]
        )
    print("\n===== RAW MODEL OUTPUT =====\n")
    print(raw)

    itinerary_json = extract_json_object(raw)

    # ── Hallucination check ───────────────────────────────────────────────────
    # Null coordinates for any activity whose location_name cannot be matched
    # against the validated POI list.  Runs before the coordinate guard so
    # the guard only needs to snap coordinates for known-good places.
    itinerary_json = validate_itinerary_against_clusters(
        itinerary_json,
        state["validated_pois"],
    )

    # ── Coordinate guard ──────────────────────────────────────────────────────
    # Snap lat/lng to validated values and null out any hallucinated places
    # before restaurants and travel time are computed from those coordinates.
    itinerary_json = fix_itinerary_coordinates(
        itinerary_json,
        validated_pois=state["validated_pois"],
    )

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
        "queries": [],
        "query": "",
        "hybrid_results": [],
        "reranked_results": [],
        "llm_context": [],
        "poi_context": [],
        "pois": [],
        "geocoded": [],
        "validated_pois": [],
        "clusters": [],
        "itinerary": "",
        "user_message": "",
        "response": "",
    }

    return initial_itinerary_app.invoke(initial_state)