from src.storage.bm25_store import BM25Store


def test_add_and_search():
    store = BM25Store()
    store.add_documents(
        doc_ids=["p1", "p2", "p3"],
        texts=[
            "navy blue cotton t-shirt casual summer wear",
            "black formal trousers slim fit office wear",
            "red polo shirt cotton casual friday",
        ],
    )
    results = store.search("blue cotton t-shirt", k=2)
    assert len(results) == 2
    assert results[0]["doc_id"] == "p1"


def test_search_returns_scores():
    store = BM25Store()
    store.add_documents(
        doc_ids=["p1"],
        texts=["navy blue cotton t-shirt"],
    )
    results = store.search("navy", k=1)
    assert results[0]["score"] > 0


def test_empty_store():
    store = BM25Store()
    results = store.search("anything", k=5)
    assert results == []
