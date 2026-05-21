import asyncio
import json

from src.config import SCRAPED_DIR
from src.scraper.hm_scraper import scrape_hm
from src.scraper.myntra_scraper import scrape_myntra


async def run_all():
    """Run all scrapers and merge results."""
    print("Starting scrapers...")

    hm_products = await scrape_hm()
    myntra_products = await scrape_myntra()

    all_products = hm_products + myntra_products

    output_path = SCRAPED_DIR / "all_products.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in all_products], f, indent=2, ensure_ascii=False)

    print(f"\nTotal scraped: {len(all_products)} products")
    print(f"  Flipkart: {len(hm_products)}")
    print(f"  Myntra: {len(myntra_products)}")
    print(f"Saved to: {output_path}")

    return all_products


if __name__ == "__main__":
    asyncio.run(run_all())
