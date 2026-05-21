from src.ingestion.deduplicator import deduplicate_products
from src.scraper.models import Product


def _make_product(id: str, name: str, price: float, source: str) -> Product:
    return Product(id=id, name=name, price=price, category="tops", source=source)


def test_removes_exact_duplicates():
    products = [
        _make_product("a", "T-shirt", 799, "h&m"),
        _make_product("b", "T-shirt", 799, "h&m"),
    ]
    result = deduplicate_products(products)
    assert len(result) == 1


def test_keeps_different_products():
    products = [
        _make_product("a", "T-shirt", 799, "h&m"),
        _make_product("b", "Polo Shirt", 999, "h&m"),
    ]
    result = deduplicate_products(products)
    assert len(result) == 2


def test_same_name_different_source_kept():
    products = [
        _make_product("a", "T-shirt", 799, "h&m"),
        _make_product("b", "T-shirt", 799, "myntra"),
    ]
    result = deduplicate_products(products)
    assert len(result) == 2
