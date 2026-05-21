import gc
import tempfile
import shutil
from src.storage.vector_store import VectorStore


def test_add_and_search():
    tmp_dir = tempfile.mkdtemp()
    store = None
    try:
        store = VectorStore(persist_dir=tmp_dir, collection_name="test")
        store.add_documents(
            ids=["p1_chunk_0", "p2_chunk_0"],
            texts=["navy blue cotton t-shirt casual summer", "black formal trousers slim fit"],
            metadatas=[
                {"id": "p1", "category": "tops", "price": 799.0, "color": "navy", "source": "h&m"},
                {"id": "p2", "category": "bottoms", "price": 1299.0, "color": "black", "source": "myntra"},
            ],
        )
        results = store.search("blue casual t-shirt", k=2)
        assert len(results) > 0
        assert results[0]["chunk_id"] == "p1_chunk_0"
    finally:
        if store is not None:
            store.reset()
        del store
        gc.collect()
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_search_with_filter():
    tmp_dir = tempfile.mkdtemp()
    store = None
    try:
        store = VectorStore(persist_dir=tmp_dir, collection_name="test")
        store.add_documents(
            ids=["p1_chunk_0", "p2_chunk_0"],
            texts=["navy blue cotton t-shirt", "navy blue formal trousers"],
            metadatas=[
                {"id": "p1", "category": "tops", "price": 799.0, "color": "navy", "source": "h&m"},
                {"id": "p2", "category": "bottoms", "price": 1299.0, "color": "navy", "source": "myntra"},
            ],
        )
        results = store.search("navy blue", k=2, where={"category": "tops"})
        assert len(results) == 1
        assert results[0]["metadata"]["category"] == "tops"
    finally:
        if store is not None:
            store.reset()
        del store
        gc.collect()
        shutil.rmtree(tmp_dir, ignore_errors=True)
