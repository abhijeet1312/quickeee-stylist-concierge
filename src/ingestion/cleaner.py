import re
from src.scraper.models import Product


def clean_text(text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_product(product: Product) -> Product:
    """Clean all text fields of a product."""
    return product.model_copy(update={
        "name": clean_text(product.name),
        "description": clean_text(product.description),
        "color": clean_text(product.color).lower(),
        "sub_category": clean_text(product.sub_category).lower(),
    })
