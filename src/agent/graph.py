from langgraph.graph import StateGraph, END

from src.agent.state import AgentState
from src.agent.nodes import (
    check_cache,
    rewrite_query,
    embed_query,
    search,
    rerank_results,
    assemble_context,
    generate_recommendation,
    init_stores,
)


def should_use_cache(state: AgentState) -> str:
    if state.get("cache_hit"):
        return "use_cache"
    return "continue"


def return_cached(state: AgentState) -> AgentState:
    import json
    response = json.loads(state["cached_response"])
    response["agent_reasoning"] = ["Cache HIT - returning cached response (0 LLM calls, 0 tokens used)"]
    return {
        **state,
        "response": response,
    }


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("check_cache", check_cache)
    graph.add_node("return_cached", return_cached)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("embed_query", embed_query)
    graph.add_node("search", search)
    graph.add_node("rerank", rerank_results)
    graph.add_node("assemble_context", assemble_context)
    graph.add_node("generate_recommendation", generate_recommendation)

    graph.set_entry_point("check_cache")

    graph.add_conditional_edges(
        "check_cache",
        should_use_cache,
        {
            "use_cache": "return_cached",
            "continue": "rewrite_query",
        },
    )

    graph.add_edge("return_cached", END)
    graph.add_edge("rewrite_query", "embed_query")
    graph.add_edge("embed_query", "search")
    graph.add_edge("search", "rerank")
    graph.add_edge("rerank", "assemble_context")
    graph.add_edge("assemble_context", "generate_recommendation")
    graph.add_edge("generate_recommendation", END)

    return graph.compile()


def create_agent(**kwargs):
    init_stores(**kwargs)
    return build_graph()
