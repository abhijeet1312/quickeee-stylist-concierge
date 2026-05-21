import hashlib
from src.scraper.models import Product


def _product_hash(product: Product) -> str:
    """Hash on name + source + price for dedup."""
    key = f"{product.name.lower().strip()}|{product.source.lower()}|{product.price}"
    return hashlib.sha256(key.encode()).hexdigest()


def deduplicate_products(products: list[Product]) -> list[Product]:
    """Remove duplicate products based on name + source + price hash."""
    seen: set[str] = set()
    unique: list[Product] = []

    for product in products:
        h = _product_hash(product)
        if h not in seen:
            seen.add(h)
            unique.append(product)

    removed = len(products) - len(unique)
    if removed > 0:
        print(f"[Dedup] Removed {removed} duplicates, {len(unique)} unique products remain")

    return unique
