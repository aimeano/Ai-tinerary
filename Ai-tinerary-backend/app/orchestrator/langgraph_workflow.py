from typing import TypedDict, Any
from copy import deepcopy

from langgraph.graph import StateGraph, END

from app.planning.preference_extractor import build_retrieval_query
from app.retrieval.hybrid_retrieve import retrieve_by_location_strategy, dedupe_results
from app.retrieval.rerank import rerank_hybrid_results
from app.planning.distance_planner import geocode_pois, cluster_pois, score_pois, score_clusters,select_clusters_for_llm
from app.llm.prompts import build_itinerary_prompt
from app.llm.generate import generate_with_ollama
from app.planning.poi_metadata import collect_pois_from_metadata
from app.llm.json_utils import extract_json_object
from app.planning.restaurant_suggestions import attach_restaurants_to_itinerary
from app.planning.attach_travel_time import attach_travel_time
from app.llm.model_config import MODELS
from app.planning.itinerary_validator import validate_and_fix_coordinates
from app.planning.weather_enrichment import attach_weather_to_itinerary



class TravelState(TypedDict):
    profile: dict
    query: str
    queries: list
    city_contexts: dict
    hybrid_results: list
    reranked_results: list
    llm_context: list
    poi_context: list
    pois: list
    geocoded: list
    scored_pois: list
    clusters: list
    raw_itinerary: Any
    itinerary: Any
    user_message: str
    response: Any
    enrichment_cache: dict

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
        print(f"Topic    : {payload.get('topic')}")


        text = payload.get("chunk_text", "")

        preview = text[:700].strip()

        print("\nTEXT:")
        print(preview)

        print("\n" + "=" * 80)

def build_query_node(state: TravelState):
    query_items = build_retrieval_query(state["profile"])

    rerank_query = (
        f"{' '.join(state['profile']['cities'])} "
        f"{' '.join(state['profile'].get('interests', []))} "
        f"{' '.join(state['profile'].get('must_include', []))}"
    )

    return {
        **state,
        "queries": query_items,
        "query": rerank_query,
    }

def get_retrieval_location_for_city(profile: dict, city: str, index: int) -> str:
    retrieval_locations = profile.get("retrieval_locations", profile["cities"])

    if index < len(retrieval_locations):
        return retrieval_locations[index]

    return city


def build_city_query(profile: dict, city: str) -> str:
    interests = " ".join(profile.get("interests", []))
    must_include = " ".join(profile.get("must_include", []))

    return f"{city} tourist attractions {interests} {must_include}".strip()


def retrieve_node(state: TravelState):
    profile = state["profile"]

    city_contexts = {}
    all_results = []

    print("\n===== CITY-WISE RETRIEVAL =====")

    for index, city in enumerate(profile["cities"]):
        retrieval_location = get_retrieval_location_for_city(
            profile,
            city,
            index,
        )

        query = build_city_query(
            profile,
            city,
        )

        print(f"\nCity: {city}")
        print(f"Retrieval location: {retrieval_location}")
        print(f"Query: {query}")

        city_results = retrieve_by_location_strategy(
            query=query,
            country=profile["country"],
            target_locations=[retrieval_location],
            intent="generate_itinerary",
            per_location_top_k=12,
            per_location_candidate_k=40,
        )

        print(f"Retrieved: {len(city_results)}")

        city_contexts[city] = {
            "query": query,
            "retrieval_location": retrieval_location,
            "hybrid_results": city_results,
            "reranked_results": [],
            "pois": [],
            "geocoded": [],
            "scored_pois": [],
            "clusters": [],
        }

        all_results.extend(city_results)

    return {
        **state,
        "city_contexts": city_contexts,
        "hybrid_results": dedupe_results(all_results),
    }


def rerank_node(state: TravelState):
    profile = state["profile"]
    city_contexts = state["city_contexts"]

    all_reranked = []

    print("\n===== CITY-WISE RERANK =====")

    for city, context in city_contexts.items():
        query = context["query"]
        hybrid_results = context["hybrid_results"]

        print(f"\nCity: {city}")
        print("Rerank query:", query)
        print("Hybrid count:", len(hybrid_results))

        reranked = rerank_hybrid_results(
            query=query,
            hybrid_results=hybrid_results,
            top_k=12,
        )

        print("Reranked count:", len(reranked))

        context["reranked_results"] = reranked
        context["llm_context"] = reranked[:6]
        context["poi_context"] = reranked[:8]

        all_reranked.extend(reranked)

    return {
        **state,
        "city_contexts": city_contexts,
        "reranked_results": all_reranked,
        "llm_context": all_reranked[:12],
        "poi_context": all_reranked[:16],
    }

def poi_node(state: TravelState):
    city_contexts = state["city_contexts"]

    all_pois = []

    print("\n===== CITY-WISE POI EXTRACTION =====")

    for city, context in city_contexts.items():
        poi_context = context.get("poi_context", [])

        pois = collect_pois_from_metadata(poi_context)

        print(f"\nCity: {city}")
        print("POI context:", len(poi_context))
        print("POIs:", len(pois))
        print(pois[:30])

        context["pois"] = pois
        all_pois.extend(pois)

    return {
        **state,
        "city_contexts": city_contexts,
        "pois": list(dict.fromkeys(all_pois)),
    }


def geocode_cluster_node(state: TravelState):
    profile = state["profile"]
    city_contexts = state["city_contexts"]

    all_geocoded = []
    all_scored_pois = []
    all_clusters = []

    print("\n===== CITY-WISE GEOCODE + CLUSTER =====")

    for city, context in city_contexts.items():
        pois = context.get("pois", [])

        print(f"\nCity: {city}")
        print("POIs before geocode:", len(pois))

        geocoded = geocode_pois(
            pois,
            cities=[city],
            country_hint=profile["country"],
            max_distance_from_city_km=80,
        )

        scored_pois = score_pois(
            geocoded,
            profile,
        )

        clusters = cluster_pois(
            scored_pois,
            radius_km=3,
            max_pois_per_cluster=8,
        )

        scored_clusters = score_clusters(
            clusters,
            profile,
        )

        print("Geocoded:", len(geocoded))
        print("Scored POIs:", len(scored_pois))
        print("Clusters:", len(scored_clusters))

        context["geocoded"] = geocoded
        context["scored_pois"] = scored_pois
        context["clusters"] = scored_clusters

        all_geocoded.extend(geocoded)
        all_scored_pois.extend(scored_pois)
        all_clusters.extend(scored_clusters)

    return {
        **state,
        "city_contexts": city_contexts,
        "geocoded": all_geocoded,
        "scored_pois": all_scored_pois,
        "clusters": all_clusters,
    }
  



def generate_itinerary_node(state: TravelState):
    clusters_for_llm = select_clusters_for_llm(
        state["city_contexts"],
        max_clusters_per_city=5,
        max_pois_per_cluster=10,
    )

    llm_context = state["llm_context"][:10]

    print("\n===== LLM CONTEXT =====")

    for i, item in enumerate(llm_context, start=1):
        payload = item["payload"]

        print(f"\n----- CHUNK {i} -----")
        print("Score    :", item["rerank_score"])
        print("Source   :", payload.get("source"))
        print("Location :", payload.get("location"))
        print("Section  :", payload.get("section"))

        text = (
            payload.get("parent_chunk")
            or payload.get("chunk_text")
            or ""
        )

        print(text[:500])
    
    print("\n===== ALL CLUSTERS =====")

    for cluster in state["clusters"]:
        print(
            f"\n{cluster['cluster_id']} "
            f"({cluster.get('assigned_city')})"
        )

        print(
            f"Score={cluster.get('cluster_score', 0):.4f} "
            f"Size={cluster.get('size', 0)}"
        )

        print([
            poi["name"]
            for poi in cluster.get("places", [])
        ])

    print("\n===== POIs PASSED TO LLM =====")

    for cluster in clusters_for_llm:
        print(
            f"{cluster['cluster_id']} "
            f"({cluster.get('assigned_city')})"
        )

        print([
            poi["name"]
            for poi in cluster.get("places", [])
        ])

    prompt = build_itinerary_prompt(
        profile=state["profile"],
        retrieved_results=llm_context,
        clusters=clusters_for_llm,
    )

    print("Prompt length:", len(prompt))

    raw = generate_with_ollama(
        prompt,
        model=MODELS["generate_itinerary"],
    )

    print("\n===== RAW MODEL OUTPUT =====\n")
    print(raw)

    raw_itinerary = extract_json_object(raw)

    raw_itinerary, coordinate_issues = validate_and_fix_coordinates(
        raw_itinerary,
        state["geocoded"],
    )

    if coordinate_issues:
        print("\n===== COORDINATE ISSUES =====")
        print(coordinate_issues)

    enriched_itinerary = deepcopy(raw_itinerary)

    restaurant_cache = {}
    travel_cache = {}

    enriched_itinerary, restaurant_cache = attach_restaurants_to_itinerary(
        enriched_itinerary,
        cache=restaurant_cache,
        limit_per_activity=3,
    )

    enriched_itinerary, travel_cache = attach_travel_time(
        enriched_itinerary,
        cache=travel_cache,
    )

    enriched_itinerary = attach_weather_to_itinerary(
        enriched_itinerary,
        geocoded=state["geocoded"],
    )

    return {
        "raw_itinerary": raw_itinerary,
        "itinerary": enriched_itinerary,
        "response": enriched_itinerary,
        "geocoded": state["geocoded"],
        "clusters": state["clusters"],
        "enrichment_cache": {
            "restaurants": restaurant_cache,
            "travel_times": travel_cache,
        },

    }



def resolve_flights_node(state: TravelState):
    from app.services.airlabs_service import get_flight_schedule
    print("\n===== RESOLVE FLIGHTS NODE RUNNING =====")
    print(state["profile"].get("flights"))

    profile = state["profile"]
    flights = profile.get("flights", [])

    if not flights:
        return state

    resolved = []

    for flight in flights:
        fn = flight.get("flight_number", "").strip()
        travel_date = flight.get("date", "").strip()

        if not fn or not travel_date:
            resolved.append(flight)
            continue

        try:
            schedule = get_flight_schedule(fn, travel_date)

            if "error" in schedule:
                print(f"[flights] Could not find schedule for {fn}: {schedule['error']}")
                resolved.append(flight)
                continue

            if not schedule.get("operates_on_date", True):
                print(
                    f"[flights] Warning: {fn} may not operate on {travel_date}. "
                    f"Operates on: {schedule.get('operates_days', [])}"
                )

            dep_time = schedule.get("dep_time")
            arr_time = schedule.get("arr_time")

            flight_type = flight.get("type")

            if flight_type == "arrival":
                resolved.append({
                    **flight,
                    "time": arr_time,
                    "resolved_from": fn,
                    "dep_iata": schedule.get("dep_iata"),
                    "arr_iata": schedule.get("arr_iata"),
                })

            elif flight_type == "departure":
                resolved.append({
                    **flight,
                    "time": dep_time,
                    "resolved_from": fn,
                    "dep_iata": schedule.get("dep_iata"),
                    "arr_iata": schedule.get("arr_iata"),
                })

            elif flight_type == "intercity":
                resolved.append({
                    **flight,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "resolved_from": fn,
                    "dep_iata": schedule.get("dep_iata"),
                    "arr_iata": schedule.get("arr_iata"),
                })

            else:
                resolved.append(flight)

        except Exception as e:
            print(f"[flights] Error resolving {fn}: {e}")
            resolved.append(flight)

    profile["flights"] = resolved

    return {
        **state,
        "profile": profile,
    }

def build_initial_itinerary_graph():
    graph = StateGraph(TravelState)

    graph.add_node("build_query", build_query_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("extract_pois", poi_node)
    graph.add_node("geocode_cluster", geocode_cluster_node)
    graph.add_node("resolve_flights", resolve_flights_node)
    graph.add_node("generate_itinerary", generate_itinerary_node)

    graph.set_entry_point("resolve_flights")

    graph.add_edge("resolve_flights", "build_query")
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
        "queries": [],
        "city_contexts": {},
        "hybrid_results": [],
        "reranked_results": [],
        "llm_context": [],
        "poi_context": [],
        "pois": [],
        "geocoded": [],
        "scored_pois": [],
        "clusters": [],
        "raw_itinerary": "",
        "itinerary": "",
        "user_message": "",
        "response": "",
        "enrichment_cache": {},
    }

    return initial_itinerary_app.invoke(initial_state)

