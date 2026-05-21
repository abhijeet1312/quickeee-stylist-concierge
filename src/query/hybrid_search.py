from src.storage.vector_store import VectorStore
from src.storage.bm25_store import BM25Store
from src.query.filter_builder import build_chroma_filter
from src.config import VECTOR_SEARCH_K, BM25_SEARCH_K


def hybrid_search(
    query_text: str,
    query_embedding: list[float],
    vector_store: VectorStore,
    bm25_store: BM25Store,
    filters: dict | None = None,
    vector_k: int = VECTOR_SEARCH_K,
    bm25_k: int = BM25_SEARCH_K,
) -> list[dict]:
    """Combine vector search + BM25 keyword search results."""

    chroma_filter = build_chroma_filter(filters) if filters else None
    vector_results = vector_store.search(
        query_embedding=query_embedding,
        k=vector_k,
        where=chroma_filter,
    )

    # Fall back to unfiltered search if filters returned nothing
    if not vector_results and chroma_filter:
        vector_results = vector_store.search(
            query_embedding=query_embedding,
            k=vector_k,
        )

    bm25_results = bm25_store.search(query_text, k=bm25_k)

    seen_ids: set[str] = set()
    merged: list[dict] = []

    for r in vector_results:
        if r["chunk_id"] not in seen_ids:
            seen_ids.add(r["chunk_id"])
            r["search_source"] = "vector"
            merged.append(r)

    for r in bm25_results:
        if r["doc_id"] not in seen_ids:
            seen_ids.add(r["doc_id"])
            # Extract product ID from chunk_id (e.g., "flipkart_tops_001_chunk_0" -> "flipkart_tops_001")
            chunk_id = r["doc_id"]
            product_id = chunk_id.rsplit("_chunk_", 1)[0] if "_chunk_" in chunk_id else chunk_id
            merged.append({
                "chunk_id": chunk_id,
                "text": r.get("text", ""),
                "metadata": {"id": product_id},
                "score": r["score"],
                "search_source": "bm25",
            })

    print(f"[HybridSearch] Vector: {len(vector_results)}, BM25: {len(bm25_results)}, Merged: {len(merged)}")
    return merged
