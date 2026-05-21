from src.ingestion.chunker import chunk_product
from src.scraper.models import Product


def test_short_product_single_chunk():
    p = Product(
        id="test_001",
        name="Slim Fit Cotton T-shirt",
        price=799.0,
        category="tops",
        description="A nice t-shirt.",
        source="h&m",
    )
    chunks = chunk_product(p)
    assert len(chunks) == 1
    assert chunks[0]["product_id"] == "test_001"
    assert "Slim Fit Cotton T-shirt" in chunks[0]["text"]


def test_chunk_has_metadata():
    p = Product(
        id="test_001",
        name="Slim Fit Cotton T-shirt",
        price=799.0,
        category="tops",
        sub_category="t-shirt",
        color="navy",
        description="A nice t-shirt.",
        source="h&m",
    )
    chunks = chunk_product(p)
    meta = chunks[0]["metadata"]
    assert meta["category"] == "tops"
    assert meta["source"] == "h&m"
    assert meta["price"] == 799.0
