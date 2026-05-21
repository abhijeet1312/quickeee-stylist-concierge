from src.query.reranker import rerank


def test_rerank_orders_by_relevance():
    query = "blue casual t-shirt for summer"
    candidates = [
        {"chunk_id": "p1", "text": "black formal trousers", "metadata": {"id": "p1"}, "score": 0.5},
        {"chunk_id": "p2", "text": "blue cotton casual t-shirt summer wear", "metadata": {"id": "p2"}, "score": 0.4},
        {"chunk_id": "p3", "text": "red winter jacket heavy wool", "metadata": {"id": "p3"}, "score": 0.3},
    ]
    results = rerank(query, candidates, top_k=2)
    assert len(results) == 2
    assert results[0]["chunk_id"] == "p2"


def test_rerank_empty_candidates():
    results = rerank("anything", [], top_k=5)
    assert results == []
