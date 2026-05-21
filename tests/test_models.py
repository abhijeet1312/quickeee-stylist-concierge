from src.scraper.models import Product


def test_product_creation():
    p = Product(
        id="hm_tops_001",
        name="Slim Fit Cotton T-shirt",
        price=799.0,
        currency="INR",
        image_url="https://example.com/img.jpg",
        category="tops",
        sub_category="t-shirt",
        color="navy blue",
        description="Slim-fit T-shirt in soft cotton jersey with a round neckline.",
        source="h&m",
    )
    assert p.id == "hm_tops_001"
    assert p.category == "tops"
    assert p.price == 799.0


def test_product_to_text():
    p = Product(
        id="hm_tops_001",
        name="Slim Fit Cotton T-shirt",
        price=799.0,
        currency="INR",
        image_url="https://example.com/img.jpg",
        category="tops",
        sub_category="t-shirt",
        color="navy blue",
        description="Slim-fit T-shirt in soft cotton jersey.",
        source="h&m",
    )
    text = p.to_searchable_text()
    assert "Slim Fit Cotton T-shirt" in text
    assert "navy blue" in text
    assert "tops" in text


def test_product_to_metadata():
    p = Product(
        id="hm_tops_001",
        name="Slim Fit Cotton T-shirt",
        price=799.0,
        currency="INR",
        image_url="https://example.com/img.jpg",
        category="tops",
        sub_category="t-shirt",
        color="navy blue",
        description="Slim-fit T-shirt in soft cotton jersey.",
        source="h&m",
    )
    meta = p.to_metadata()
    assert meta["category"] == "tops"
    assert meta["source"] == "h&m"
    assert meta["price"] == 799.0
    assert meta["color"] == "navy blue"
