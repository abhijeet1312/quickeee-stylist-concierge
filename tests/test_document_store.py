import os
import tempfile
from src.storage.document_store import DocumentStore
from src.scraper.models import Product


def _make_product(id: str = "test_001") -> Product:
    return Product(
        id=id,
        name="Slim Fit Cotton T-shirt",
        price=799.0,
        currency="INR",
        image_url="https://example.com/img.jpg",
        category="tops",
        sub_category="t-shirt",
        color="navy blue",
        description="A nice t-shirt.",
        source="h&m",
    )


def test_insert_and_get():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = DocumentStore(db_path)
        store.insert_products([_make_product("p1"), _make_product("p2")])
        result = store.get_product("p1")
        assert result is not None
        assert result["name"] == "Slim Fit Cotton T-shirt"
    finally:
        os.unlink(db_path)


def test_get_products_by_ids():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = DocumentStore(db_path)
        store.insert_products([_make_product("p1"), _make_product("p2"), _make_product("p3")])
        results = store.get_products_by_ids(["p1", "p3"])
        assert len(results) == 2
        ids = {r["id"] for r in results}
        assert ids == {"p1", "p3"}
    finally:
        os.unlink(db_path)


def test_get_nonexistent_returns_none():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = DocumentStore(db_path)
        assert store.get_product("nonexistent") is None
    finally:
        os.unlink(db_path)


def test_filter_by_category():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = DocumentStore(db_path)
        p1 = _make_product("p1")
        p2 = Product(id="p2", name="Chinos", price=1299, category="bottoms", source="h&m")
        store.insert_products([p1, p2])
        results = store.filter_products(category="tops")
        assert len(results) == 1
        assert results[0]["category"] == "tops"
    finally:
        os.unlink(db_path)
