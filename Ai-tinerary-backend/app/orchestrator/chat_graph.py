from typing import TypedDict, Dict, Any, List
import json
from langgraph.graph import StateGraph, END

from app.retrieval.hybrid_retrieve import retrieve_by_location_strategy
from app.retrieval.rerank import rerank_hybrid_results
from app.llm.generate import generate_with_ollama
from app.llm.model_config import MODELS
from app.llm.json_utils import extract_json_object
from copy import deepcopy
from app.planning.restaurant_suggestions import attach_restaurants_to_itinerary
from app.planning.attach_travel_time import attach_travel_time
from app.planning.itinerary_validator import validate_itinerary,validate_and_fix_coordinates,normalize_name
from app.planning.weather_enrichment import attach_weather_to_itinerary
from app.planning.distance_planner import get_weather_safe_clusters,geocode_pois,score_pois
from app.planning.poi_metadata import collect_pois_from_metadata


class ChatState(TypedDict):
    profile: Dict[str, Any]
    raw_itinerary: Any
    itinerary: Any
    user_message: str
    intent: str
    query: str
    retrieved: List[dict]
    response: Any
    enrichment_cache: dict
    geocoded: list
    clusters: list
    weather_safe_clusters: list


def print_retrieved_chunks(results: List[dict]):
    print("\n===== RETRIEVED CHUNKS =====")

    if not results:
        print("No retrieved chunks passed the rerank threshold.")
        return

    for i, item in enumerate(results, start=1):
        payload = item["payload"]

        print(f"\n----- CHUNK {i} -----")
        print(f"Rerank Score : {item.get('rerank_score', 0):.4f}")
        print(f"RRF Score    : {item.get('rrf_score', 0):.4f}")
        print(f"Source       : {payload.get('source')}")
        print(f"Country      : {payload.get('country')}")
        print(f"Location     : {payload.get('location')}")
        print(f"Topic        : {payload.get('topic')}")
        print(f"Section      : {payload.get('section')}")
        print(f"POIs         : {payload.get('pois')}")

        print("\nTEXT:")
        print(payload.get("chunk_text", "")[:700].strip())
        print("\n" + "=" * 80)


def classify_intent_node(state: ChatState):
    prompt = f"""
You are a routing classifier for a travel itinerary chatbot.

Classify the user's message into EXACTLY ONE route.

Routes:
1. ask_country_info
Use for destination facts: visa, laws, weather, climate, transport, safety, currency, culture, food, places, public transport, SIM card, packing, rules, etiquette.

2. ask_itinerary_details
Use when the user asks about the current itinerary: why a place was chosen, distance, timing, cost, whether a day is too packed, or details about listed activities.

3. edit_itinerary
Use when the user wants to modify the itinerary: change, replace, remove, add, reorder, make cheaper, make more adventurous, swap days.

4. regenerate_itinerary
Use when the user wants a full new itinerary: regenerate, remake, start over, another itinerary.

5. casual_chat
Use only for greetings, thanks, confirmations, or casual conversation.

Examples:
"what is the visa rule in malaysia?" -> ask_country_info
"is there public transport in KL?" -> ask_country_info
"why did you put bangsar on day 2?" -> ask_itinerary_details
"change day 3 to shopping" -> edit_itinerary
"regenerate the itinerary" -> regenerate_itinerary
"thanks" -> casual_chat

User message:
{state["user_message"]}

Return ONLY the route name.
"""

    raw = generate_with_ollama(
        prompt,
        model=MODELS["router"]
    ).strip().lower()

    allowed = [
        "ask_country_info",
        "ask_itinerary_details",
        "edit_itinerary",
        "regenerate_itinerary",
        "casual_chat",
    ]

    intent = raw if raw in allowed else "casual_chat"

    print("\n===== ROUTER =====")
    print("Message:", state["user_message"])
    print("Intent :", intent)

    return {"intent": intent}


def get_target_locations_from_message(
        message: str,
        profile: dict,
    ) -> list[str] | None:
    message_lower = message.lower()

    matched = [
        city for city in profile.get("cities", [])
        if city.lower() in message_lower
    ]

    return matched or None

def build_query_for_country_info(state: ChatState) -> str:
    profile = state["profile"]
    country = profile["country"]

    return f"""
    {country} travel information.

    User question:
    {state["user_message"]}
    """


def build_query_for_itinerary_edit(state: ChatState) -> str:
    profile = state["profile"]

    prompt = f"""
        You are a retrieval query rewriting assistant.

        Rewrite the user's itinerary edit request into a better search query for travel document retrieval.

        Rules:
        - Do not modify the itinerary.
        - Do not answer the user.
        - Extract only useful travel search terms.
        - Add relevant country and city names.
        - If the user mentions a day, infer the city from the itinerary.
        - Do not invent specific POIs.
        - Keep it short.
        - Return plain text only.

        Important:
        - Only add indoor/weather-safe terms if the user explicitly mentions rain, storm, bad weather, heat, or weather.
        - If the user asks for nature, use: parks, gardens, lakes, viewpoints, botanical gardens, forest parks, outdoor nature attractions.
        - If the user asks for shopping, use: malls, markets, shopping streets, outlets.
        - If the user asks for food, use: local food, street food, restaurants, cafes, dining areas.
        - If the user asks for culture or arts, use: museums, galleries, heritage sites, cultural attractions.

        Country: {profile.get("country")}
        Cities: {", ".join(profile.get("cities", []))}
        Interests: {", ".join(profile.get("interests", []))}

        Current raw itinerary:
        {state["raw_itinerary"]}

        User requested change:
        {state["user_message"]}

        Better retrieval query:
        """

    try:
        rewritten_query = generate_with_ollama(
            prompt,
            model=MODELS.get("rewrite_query", MODELS["edit_itinerary"]),
        )

        rewritten_query = rewritten_query.strip()

        if rewritten_query:
            print(rewritten_query)
            return rewritten_query
        


    except Exception as e:
        print("Edit retrieval query rewrite failed:", e)

    return f"""
    {profile.get("country")} {", ".join(profile.get("cities", []))}
    {state["user_message"]}
    """

def build_chat_query_node(state: ChatState):
    intent = state["intent"]

    if intent == "ask_country_info":
        query = build_query_for_country_info(state)
    elif intent in ["edit_itinerary", "regenerate_itinerary"]:
        query = build_query_for_itinerary_edit(state)
    else:
        query = ""

    return {"query": query}


def should_retrieve(intent: str) -> bool:
    return intent in [
        "ask_country_info",
        "edit_itinerary",
        "regenerate_itinerary",
    ]


def retrieve_chat_context_node(state: ChatState):
    if not should_retrieve(state["intent"]):
        print("\n===== RETRIEVAL SKIPPED =====")
        print(f"Intent: {state['intent']}")
        return {"retrieved": []}

    profile = state["profile"]

    if state["intent"] == "ask_country_info":
        target_locations = get_target_locations_from_message(
            state["user_message"],
            profile,
        )
    else:
        target_locations = profile["cities"]

    print("\n===== CHAT RETRIEVAL TARGET LOCATIONS =====")
    print(target_locations)

    hybrid_results = retrieve_by_location_strategy(
        query=state["query"],
        country=profile["country"],
        target_locations=target_locations,
        intent=state["intent"],
    )

    reranked = rerank_hybrid_results(
        query=state["query"],
        hybrid_results=hybrid_results,
        top_k=8,
    )

    threshold = 0.1 if state["intent"] == "ask_country_info" else 0.2

    retrieved = [
        r for r in reranked
        if r["rerank_score"] >= threshold
    ]

    print_retrieved_chunks(retrieved)

    return {"retrieved": retrieved}


def answer_country_info_node(state: ChatState):
    prompt = f"""
        You are a helpful travel assistant.

        User profile:
        {state["profile"]}

        Retrieved travel context:
        {state["retrieved"]}

        User question:
        {state["user_message"]}

        Instructions:
        - Answer the latest question directly.
        - Use retrieved context when relevant.
        - If retrieved context is empty or unrelated, say the uploaded travel documents do not contain enough information.
        - For live weather, current prices, opening hours, or current visa rules, say live verification/API is needed.
        - Do not pretend unsupported facts came from retrieved context.
        - Be practical and concise.
        """

    answer = generate_with_ollama(
            prompt,
            model=MODELS["simple_qa"]
        )


    return {"response": answer}


def answer_itinerary_details_node(state: ChatState):
    prompt = f"""
You are answering a question about the current itinerary.

User profile:
{state["profile"]}

Current itinerary:
{state["itinerary"]}

User question:
{state["user_message"]}

Instructions:
- Use the current itinerary as the main source.
- Do not create a new itinerary.
- Do not invent new destination facts.
- Keep the answer short and useful.
"""

    answer = generate_with_ollama(
        prompt,
        model=MODELS["simple_qa"]
    )


    return {"response": answer}

def build_weather_safe_cluster_context(clusters: list[dict]) -> str:
    if not clusters:
        return "No weather-safe clusters available."

    blocks = []

    for cluster in clusters:
        places = []

        for poi in cluster.get("places", []):
            places.append(f"""
- Name: {poi.get("name")}
  Canonical name: {poi.get("canonical_name")}
  Category: {poi.get("category")}
  Weather suitability: {poi.get("weather_suitability")}
  Latitude: {poi.get("lat")}
  Longitude: {poi.get("lng")}
  Address: {poi.get("formatted_address")}
""")

        blocks.append(f"""
[Cluster {cluster.get("cluster_id")}]
City: {cluster.get("assigned_city")}
Cluster score: {cluster.get("cluster_score")}
Places:
{''.join(places)}
""")

    return "\n".join(blocks)


def edit_itinerary_node(state: ChatState):
    user_message_lower = state["user_message"].lower()

    is_weather_replacement = (
        "weather is bad" in user_message_lower
        or "bad weather" in user_message_lower
        or "rain" in user_message_lower
        or "storm" in user_message_lower
    )

    weather_rules = ""

    if is_weather_replacement:
        safe_clusters = state.get("weather_safe_clusters", [])

        weather_safe_cluster_context = build_weather_safe_cluster_context(
            safe_clusters
        )

        print("\n===== WEATHER SAFE CLUSTERS PASSED TO EDIT LLM =====")
        print(weather_safe_cluster_context[:5000])

        weather_rules = f"""
            WEATHER REPLACEMENT RULES:
            - Regenerate the entire requested day, not only one activity.
            - Keep all other days exactly the same.
            - Use ONLY places listed under WEATHER SAFE CLUSTERS.
            - Do not invent new locations.
            - Do not use outdoor activities.
            - Do not use beaches, parks, gardens, islands, waterfalls, hiking areas, viewpoints, outdoor monuments, outdoor markets, marinas, waterfront walks, or open-air attractions.
            - Prefer places from the same cluster so the day remains geographically sensible.
            - Keep the same date and same city for the requested day.
            - Use exact latitude and longitude from WEATHER SAFE CLUSTERS.
            - Do not reuse coordinates from another place.

            WEATHER SAFE CLUSTERS:
            {weather_safe_cluster_context}
            """

        # =========================
    # Geocode POIs from newly retrieved chat chunks
    # =========================

    existing_geocoded = state.get("geocoded", [])

    retrieved_pois = collect_pois_from_metadata(
        state.get("retrieved", [])
    )

    existing_names = {
        normalize_name(poi.get("name"))
        for poi in existing_geocoded
    } | {
        normalize_name(poi.get("canonical_name"))
        for poi in existing_geocoded
    }

    new_pois = [
        poi for poi in retrieved_pois
        if normalize_name(poi) not in existing_names
    ]

    new_pois = list(dict.fromkeys(new_pois))

    if new_pois:
        print("\n===== CHAT EDIT NEW POIs FROM RETRIEVAL =====")
        print(new_pois[:50])

        new_geocoded = geocode_pois(
            new_pois,
            cities=state["profile"]["cities"],
            country_hint=state["profile"]["country"],
            max_distance_from_city_km=80,
        )

        new_geocoded = score_pois(
            new_geocoded,
            state["profile"],
        )

        existing_place_ids = {
            poi.get("place_id")
            for poi in existing_geocoded
            if poi.get("place_id")
        }

        updated_geocoded = list(existing_geocoded)

        for poi in new_geocoded:
            place_id = poi.get("place_id")

            if place_id and place_id not in existing_place_ids:
                updated_geocoded.append(poi)
                existing_place_ids.add(place_id)
    else:
        updated_geocoded = existing_geocoded

    verified_pois_for_prompt = json.dumps(
    [
        {
            "name": poi.get("canonical_name") or poi.get("name"),
            "latitude": poi.get("lat"),
            "longitude": poi.get("lng"),
            "category": poi.get("category"),
            "place_id": poi.get("place_id"),
            "google_maps_url": poi.get("google_maps_url"),
        }
        for poi in updated_geocoded
    ],
    ensure_ascii=False,
    indent=2,
    )
    
    prompt = f"""
You are an itinerary modification assistant.

{weather_rules}

User profile:
{state["profile"]}

Current raw itinerary:
{state["raw_itinerary"]}

Retrieved travel context:
{state["retrieved"]}

User requested change:
{state["user_message"]}

Verified POIs:
{verified_pois_for_prompt}

Task:
- Modify the raw itinerary according to the user's request.
- Keep the same trip duration unless the user asks otherwise.
- Preserve unchanged days where possible.
- Do not include nearby_restaurants.
- Do not include travel_from_previous.
- Return ONLY valid JSON.
- JSON null values must be written as null, never None.
- Boolean values must be true/false, never True/False.
- Do not use markdown.
- Do not wrap in ```json.
- Do not write explanation.
- Use double quotes only.
- If the user mentions a specific day, modify that day only.
- Keep all other days exactly the same.
- Do not move activities between days unless the user asks.
- Do not duplicate any location already used elsewhere in the itinerary.
- Before adding a location, check that it does not already appear in another day.
- When adding or replacing activities, use ONLY places from Verified POIs.
- Copy latitude, longitude, place_id, and google_maps_url exactly from Verified POIs.
- If the requested place is not in Verified POIs, use the closest relevant verified POI instead.
- Never invent coordinates, place_id, or google_maps_url.
"""
    
    

    updated_raw_itinerary = generate_with_ollama(
        prompt,
        model=MODELS["edit_itinerary"]
    )


    updated_raw_itinerary = extract_json_object(updated_raw_itinerary)

    updated_raw_itinerary, coordinate_issues = validate_and_fix_coordinates(
        updated_raw_itinerary,
        updated_geocoded,
    )

    if coordinate_issues:
        print("\n===== COORDINATE ISSUES =====")
        print(coordinate_issues)

    cache = state["enrichment_cache"]

    restaurant_cache = cache.get("restaurants", {})
    travel_cache = cache.get("travel_times", {})

    enriched_itinerary = deepcopy(updated_raw_itinerary)

    enriched_itinerary, restaurant_cache = attach_restaurants_to_itinerary(
        enriched_itinerary,
        cache=restaurant_cache,
    )

    enriched_itinerary, travel_cache = attach_travel_time(
        enriched_itinerary,
        cache=travel_cache,
    )

    enriched_itinerary = attach_weather_to_itinerary(
        enriched_itinerary,
        geocoded=updated_geocoded,
    )

    validation = validate_itinerary(enriched_itinerary)

    repaired_raw_itinerary = repair_itinerary_if_needed(
        raw_itinerary=updated_raw_itinerary,
        enriched_itinerary=enriched_itinerary,
        validation=validation,
        state={
            **state,
            "geocoded": updated_geocoded,
        },
    )

    if repaired_raw_itinerary != updated_raw_itinerary:
        updated_raw_itinerary = repaired_raw_itinerary
        enriched_itinerary = deepcopy(updated_raw_itinerary)

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
            geocoded=updated_geocoded,
        )

        validation = validate_itinerary(enriched_itinerary)

    return {
        "raw_itinerary": updated_raw_itinerary,
        "itinerary": enriched_itinerary,
        "response": {
            "itinerary": enriched_itinerary,
            "validation": validation,
        },
        "enrichment_cache": {
            "restaurants": restaurant_cache,
            "travel_times": travel_cache,
        },
        "geocoded": updated_geocoded,
    }



def regenerate_itinerary_node(state: ChatState):
    prompt = f"""
        You are an itinerary regeneration assistant.

        User profile:
        {state["profile"]}

        Previous itinerary:
        {state["itinerary"]}

        Retrieved travel context:
        {state["retrieved"]}

        User request:
        {state["user_message"]}

        Generate a new improved itinerary.
        Respect the original profile unless the user explicitly changed something.
        Use retrieved context when relevant.
        Do not invent unsupported travel facts.
        - Return ONLY valid JSON.
        - Do not use markdown.
        - Do not wrap in ```json.
        - Do not write explanation.
        - Do not use single quotes.
        - Use double quotes only.
        - The output must be directly parseable by json.loads().
        """

    new_itinerary = generate_with_ollama(
                    prompt,
                    model=MODELS["generate_itinerary"]
                    )
    
    new_itinerary = extract_json_object(new_itinerary)




    return {
        "itinerary": new_itinerary,
        "response": new_itinerary,
    }

def repair_itinerary_if_needed(
    raw_itinerary: dict,
    enriched_itinerary: dict,
    validation: dict,
    state: ChatState,
):
    if validation.get("valid") and not validation.get("warnings"):
        return raw_itinerary

    prompt = f"""
        You are an itinerary repair assistant.

        User profile:
        {state["profile"]}

        User requested change:
        {state["user_message"]}

        Current raw itinerary:
        {raw_itinerary}

        Validation result:
        {validation}

        Task:
        - Repair ONLY the affected day(s).
        - Keep unaffected days exactly the same.
        - Fix travel flow, category imbalance, repeated places, or unrealistic pacing.
        - Do not add nearby_restaurants.
        - Do not add travel_from_previous.
        - Use only places already in the itinerary or retrieved context.
        - Return ONLY valid JSON.
        - Do not use markdown.
        - Use double quotes only.
        """

    repaired = generate_with_ollama(
        prompt,
        model=MODELS["edit_itinerary"]
    )

    return extract_json_object(repaired)


def casual_chat_node(state: ChatState):
    prompt = f"""
            You are a travel chatbot continuing a conversation about the user's itinerary.

            User profile:
            {state["profile"]}

            Current itinerary:
            {state["itinerary"]}

            User message:
            {state["user_message"]}

            Instructions:
            - Respond naturally.
            - Do not create a new itinerary.
            - Do not switch countries or cities.
            """

    answer = generate_with_ollama(
            prompt,
            model=MODELS["simple_qa"]
        )

    return {"response": answer}


def route_after_retrieval(state: ChatState):
    intent = state["intent"]

    if intent == "ask_country_info":
        return "answer_country_info"

    if intent == "ask_itinerary_details":
        return "answer_itinerary_details"

    if intent == "edit_itinerary":
        return "edit_itinerary"

    if intent == "regenerate_itinerary":
        return "regenerate_itinerary"

    return "casual_chat"


def build_chat_graph():
    graph = StateGraph(ChatState)

    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("build_query", build_chat_query_node)
    graph.add_node("retrieve_context", retrieve_chat_context_node)

    graph.add_node("answer_country_info", answer_country_info_node)
    graph.add_node("answer_itinerary_details", answer_itinerary_details_node)
    graph.add_node("edit_itinerary", edit_itinerary_node)
    graph.add_node("regenerate_itinerary", regenerate_itinerary_node)
    graph.add_node("casual_chat", casual_chat_node)

    graph.set_entry_point("classify_intent")

    graph.add_edge("classify_intent", "build_query")
    graph.add_edge("build_query", "retrieve_context")

    graph.add_conditional_edges(
        "retrieve_context",
        route_after_retrieval,
        {
            "answer_country_info": "answer_country_info",
            "answer_itinerary_details": "answer_itinerary_details",
            "edit_itinerary": "edit_itinerary",
            "regenerate_itinerary": "regenerate_itinerary",
            "casual_chat": "casual_chat",
        },
    )

    graph.add_edge("answer_country_info", END)
    graph.add_edge("answer_itinerary_details", END)
    graph.add_edge("edit_itinerary", END)
    graph.add_edge("regenerate_itinerary", END)
    graph.add_edge("casual_chat", END)

    return graph.compile()


chat_app = build_chat_graph()


def run_chat_turn(session: dict, user_message: str):
    state: ChatState = {

        "profile": session["profile"],
        "raw_itinerary": session["raw_itinerary"],
        "itinerary": session["itinerary"],
        "enrichment_cache": session.get("enrichment_cache", {
            "restaurants": {},
            "travel_times": {},
        }),
        "user_message": user_message,
        "intent": "",
        "query": "",
        "retrieved": [],
        "response": "",
        "geocoded": session.get("geocoded", []),
        "clusters": session.get("clusters", []),
        "weather_safe_clusters": session.get("weather_safe_clusters", []),
    }

    result = chat_app.invoke(state)

    if "raw_itinerary" in result and result["raw_itinerary"]:
        session["raw_itinerary"] = result["raw_itinerary"]

    if "itinerary" in result and result["itinerary"]:
        session["itinerary"] = result["itinerary"]
    
    if "enrichment_cache" in result and result["enrichment_cache"]:
        session["enrichment_cache"] = result["enrichment_cache"]

    return result["response"], session