from typing import TypedDict, Dict, Any, List

from langgraph.graph import StateGraph, END

from app.retrieval.hybrid_retrieve import hybrid_retrieve
from app.retrieval.rerank import rerank_hybrid_results
from app.llm.generate import generate_with_ollama
from app.llm.model_config import MODELS


class ChatState(TypedDict):
    profile: Dict[str, Any]
    itinerary: Any
    user_message: str
    intent: str
    query: str
    retrieved: List[dict]
    response: str


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


def build_query_for_country_info(state: ChatState) -> str:
    profile = state["profile"]
    country = profile["country"]
    cities = ", ".join(profile.get("cities", []))

    return f"""
{country} {cities} travel information.

Latest user question:
{state["user_message"]}

Retrieve only information relevant to the latest user question.
"""


def build_query_for_itinerary_edit(state: ChatState) -> str:
    profile = state["profile"]
    country = profile["country"]
    cities = ", ".join(profile.get("cities", []))

    return f"""
        {country} {cities} itinerary modification support.

        User requested change:
        {state["user_message"]}

        Retrieve information relevant to modifying the itinerary.
        Focus on places, activities, transport, food, shopping, cafes, nature, nightlife, nearby alternatives, and practical schedule changes.
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

    hybrid_results = hybrid_retrieve(
        query=state["query"],
        top_k=20,
        candidate_k=30,
        country=profile["country"],
        locations=profile["cities"],
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


def edit_itinerary_node(state: ChatState):
    prompt = f"""
You are an itinerary modification assistant.

User profile:
{state["profile"]}

Current itinerary:
{state["itinerary"]}

Retrieved travel context:
{state["retrieved"]}

User requested change:
{state["user_message"]}

Task:
- Modify the itinerary according to the user's request.
- Keep the same trip duration unless the user asks otherwise.
- Respect budget, cities, interests, dates, and must-include items.
- Use retrieved context when relevant.
- Preserve unchanged days where possible.
- Return the updated itinerary clearly.
"""

    updated_itinerary = generate_with_ollama(
                                prompt,
                                model=MODELS["edit_itinerary"]
                            )

    return {
        "itinerary": updated_itinerary,
        "response": updated_itinerary,
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
"""

    new_itinerary = generate_with_ollama(
                    prompt,
                    model=MODELS["generate_itinerary"]
                    )

    return {
        "itinerary": new_itinerary,
        "response": new_itinerary,
    }


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
        "itinerary": session["itinerary"],
        "user_message": user_message,
        "intent": "",
        "query": "",
        "retrieved": [],
        "response": "",
    }

    result = chat_app.invoke(state)

    if "itinerary" in result and result["itinerary"]:
        session["itinerary"] = result["itinerary"]

    return result["response"], session