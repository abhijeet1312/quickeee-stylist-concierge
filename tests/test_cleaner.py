from src.ingestion.cleaner import clean_text, clean_product
from src.scraper.models import Product


def test_clean_text_strips_html():
    assert clean_text("<p>Hello <b>World</b></p>") == "Hello World"


def test_clean_text_normalizes_whitespace():
    assert clean_text("hello   world\n\tfoo") == "hello world foo"


def test_clean_text_empty():
    assert clean_text("") == ""


def test_clean_product():
    p = Product(
        id="test_001",
        name="  Slim Fit   T-shirt  ",
        price=799.0,
        currency="INR",
        image_url="https://example.com/img.jpg",
        category="tops",
        sub_category="t-shirt",
        color="navy",
        description="<p>A  great  t-shirt</p>",
        source="h&m",
    )
    cleaned = clean_product(p)
    assert cleaned.name == "Slim Fit T-shirt"
    assert cleaned.description == "A great t-shirt"
