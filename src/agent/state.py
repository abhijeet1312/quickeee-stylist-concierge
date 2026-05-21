from typing import Any
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Input
    user_query: str

    # Query processing
    rewritten_query: str
    query_embedding: list[float]
    extracted_filters: dict

    # Search results
    vector_results: list[dict]
    bm25_results: list[dict]
    merged_results: list[dict]
    reranked_results: list[dict]

    # Context for LLM
    context_str: str

    # Output
    response: dict
    agent_reasoning: list[str]

    # Cache
    cache_hit: bool
    cached_response: str | None
