import json
from src.agent.state import AgentState
from src.query.rewriter import rewrite_and_extract
from src.query.hybrid_search import hybrid_search
from src.query.reranker import rerank
from src.query.cache import SemanticCache
from src.ingestion.embedder import Embedder
from src.storage.vector_store import VectorStore
from src.storage.document_store import DocumentStore
from src.storage.bm25_store import BM25Store
from src.agent.prompts import FASHION_MATCHER_PROMPT
from src.config import GROQ_API_KEY, GROQ_MODEL

from groq import Groq

_embedder: Embedder | None = None
_vector_store: VectorStore | None = None
_doc_store: DocumentStore | None = None
_bm25_store: BM25Store | None = None
_cache: SemanticCache | None = None


def init_stores(
    embedder: Embedder | None = None,
    vector_store: VectorStore | None = None,
    doc_store: DocumentStore | None = None,
    bm25_store: BM25Store | None = None,
    cache: SemanticCache | None = None,
):
    global _embedder, _vector_store, _doc_store, _bm25_store, _cache
    _embedder = embedder or Embedder()
    _vector_store = vector_store or VectorStore()
    _doc_store = doc_store or DocumentStore()
    _bm25_store = bm25_store or BM25Store()
    _cache = cache or SemanticCache()


def check_cache(state: AgentState) -> AgentState:
    cached = _cache.get(state["user_query"])
    reasoning = list(state.get("agent_reasoning", []))

    if cached:
        reasoning.append("Cache HIT - returning cached response")
        return {
            **state,
            "cache_hit": True,
            "cached_response": cached,
            "agent_reasoning": reasoning,
        }

    reasoning.append("Cache MISS - proceeding with full pipeline")
    return {
        **state,
        "cache_hit": False,
        "cached_response": None,
        "agent_reasoning": reasoning,
    }


def rewrite_query(state: AgentState) -> AgentState:
    query = state["user_query"]
    reasoning = list(state.get("agent_reasoning", []))

    rewritten, filters = rewrite_and_extract(query)
    reasoning.append(f"Rewrote query using HyDE: '{rewritten[:100]}...'")
    reasoning.append(f"Extracted filters: {filters}")

    return {
        **state,
        "rewritten_query": rewritten,
        "extracted_filters": filters,
        "agent_reasoning": reasoning,
    }


def embed_query(state: AgentState) -> AgentState:
    embedding = _embedder.embed_query(state["rewritten_query"])
    reasoning = list(state.get("agent_reasoning", []))
    reasoning.append(f"Embedded query into {len(embedding)}-dim vector")

    return {
        **state,
        "query_embedding": embedding,
        "agent_reasoning": reasoning,
    }


def search(state: AgentState) -> AgentState:
    reasoning = list(state.get("agent_reasoning", []))

    merged = hybrid_search(
        query_text=state["rewritten_query"],
        query_embedding=state["query_embedding"],
        vector_store=_vector_store,
        bm25_store=_bm25_store,
        filters=state.get("extracted_filters"),
    )

    reasoning.append(f"Hybrid search returned {len(merged)} candidates")

    return {
        **state,
        "merged_results": merged,
        "agent_reasoning": reasoning,
    }


def rerank_results(state: AgentState) -> AgentState:
    reasoning = list(state.get("agent_reasoning", []))

    enriched = []
    for r in state["merged_results"]:
        if not r.get("text") and r.get("metadata", {}).get("id"):
            product = _doc_store.get_product(r["metadata"]["id"])
            if product:
                r["text"] = f"{product['name']} {product['color']} {product['category']} {product['description']}"
        enriched.append(r)

    candidates_with_text = [r for r in enriched if r.get("text")]

    if not candidates_with_text:
        reasoning.append("No candidates with text to rerank")
        return {**state, "reranked_results": [], "agent_reasoning": reasoning}

    reranked = rerank(state["user_query"], candidates_with_text)
    reasoning.append(f"Reranked to top {len(reranked)} results")

    return {
        **state,
        "reranked_results": reranked,
        "agent_reasoning": reasoning,
    }


def assemble_context(state: AgentState) -> AgentState:
    reasoning = list(state.get("agent_reasoning", []))

    product_ids = []
    for r in state["reranked_results"]:
        pid = r.get("metadata", {}).get("id", "")
        if pid and pid not in product_ids:
            product_ids.append(pid)

    products = _doc_store.get_products_by_ids(product_ids)

    context_parts = []
    for p in products:
        context_parts.append(
            f"- {p['name']} | Category: {p['category']} | Color: {p['color']} | "
            f"Price: {p['price']} {p['currency']} | Source: {p['source']} | "
            f"Image: {p['image_url']} | ID: {p['id']}"
        )

    context_str = "\n".join(context_parts)
    reasoning.append(f"Assembled context from {len(products)} products")

    return {
        **state,
        "context_str": context_str,
        "agent_reasoning": reasoning,
    }


def generate_recommendation(state: AgentState) -> AgentState:
    reasoning = list(state.get("agent_reasoning", []))

    prompt = FASHION_MATCHER_PROMPT.format(
        query=state["user_query"],
        context=state["context_str"],
    )

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
    )

    raw_response = response.choices[0].message.content.strip()

    if "```" in raw_response:
        raw_response = raw_response.split("```")[1]
        if raw_response.startswith("json"):
            raw_response = raw_response[4:]
        raw_response = raw_response.strip()

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        result = {
            "recommended_items": [],
            "total_price": 0,
            "currency": "INR",
            "stylist_note": raw_response,
            "agent_reasoning": reasoning,
        }

    result["agent_reasoning"] = reasoning + [f"Generated recommendation with {GROQ_MODEL}"]

    _cache.set(state["user_query"], json.dumps(result))
    reasoning.append("Cached response for future queries")

    return {
        **state,
        "response": result,
        "agent_reasoning": result["agent_reasoning"],
    }
