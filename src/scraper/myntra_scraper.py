"""
Myntra Fashion Scraper.
Extracts product data from window.__myx.searchData (Myntra's client-side state).
"""
import asyncio
import json
import random

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from src.config import SCRAPED_DIR
from src.scraper.models import Product


MYNTRA_URLS = {
    "tops": [
        "https://www.myntra.com/men-tshirts?p={}",
        "https://www.myntra.com/men-casual-shirts?p={}",
    ],
    "bottoms": [
        "https://www.myntra.com/men-trousers?p={}",
        "https://www.myntra.com/men-shorts?p={}",
    ],
}


async def extract_myntra_products(page) -> list[dict]:
    """Extract product data from Myntra's window.__myx.searchData."""
    try:
        data = await page.evaluate("() => JSON.stringify(window.__myx && window.__myx.searchData)")
        if not data or data == "null":
            return []
        parsed = json.loads(data)
        results = parsed.get("results", {})
        products = results.get("products", [])
        return products
    except Exception as e:
        print(f"[Myntra] Error extracting __myx data: {e}")
        return []


async def scrape_myntra_category(page, category: str, url_templates: list[str], target_count: int = 50) -> list[Product]:
    """Scrape Myntra product listings for a category."""
    products: list[Product] = []
    seen: set[str] = set()  # Dedup by (name, price) composite key
    product_idx = 0
    per_template_target = target_count // len(url_templates)
    template_count = 0  # Products scraped for current URL template

    for url_template in url_templates:
        template_count = 0
        if len(products) >= target_count:
            break

        for page_num in range(1, 6):  # Up to 5 pages to compensate for dedup
            if template_count >= per_template_target or len(products) >= target_count:
                break

            url = url_template.format(page_num)
            print(f"[Myntra] Scraping: {url}")

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000)

                raw_products = await extract_myntra_products(page)
                print(f"[Myntra] Found {len(raw_products)} products on page {page_num}")

                for item in raw_products:
                    if template_count >= per_template_target or len(products) >= target_count:
                        break

                    try:
                        brand = item.get("brand", "")
                        name = item.get("product", item.get("productName", ""))
                        # Avoid duplicating brand in product name
                        if brand and name.startswith(brand):
                            full_name = name
                        else:
                            full_name = f"{brand} {name}".strip()

                        price = float(item.get("price", item.get("mrp", 0)))
                        image_url = item.get("searchImage", "")
                        color = item.get("primaryColour", "").lower()

                        # Determine sub_category
                        raw_article = item.get("articleType", "")
                        if isinstance(raw_article, dict):
                            article_type = raw_article.get("typeName", "").lower()
                        else:
                            article_type = str(raw_article).lower()
                        sub_cat = ""
                        if "tshirt" in url or "t-shirt" in article_type or "tshirt" in article_type:
                            sub_cat = "t-shirt"
                        elif "shirt" in url or "shirt" in article_type:
                            sub_cat = "shirt"
                        elif "trouser" in url or "trouser" in article_type or "pant" in article_type:
                            sub_cat = "pants"
                        elif "short" in url or "short" in article_type:
                            sub_cat = "shorts"

                        if not full_name or price == 0:
                            continue

                        # Deduplicate by composite key of name + price
                        dedup_key = f"{full_name.lower()}|{price}"
                        if dedup_key in seen:
                            continue
                        seen.add(dedup_key)

                        product_idx += 1
                        template_count += 1
                        products.append(Product(
                            id=f"myntra_{category}_{product_idx:03d}",
                            name=full_name,
                            price=price,
                            currency="INR",
                            image_url=image_url,
                            category=category,
                            sub_category=sub_cat,
                            color=color,
                            description=f"{full_name} - {sub_cat} from Myntra. Color: {color}",
                            source="myntra",
                        ))

                    except Exception as e:
                        continue

            except Exception as e:
                print(f"[Myntra] Error loading {url}: {e}")
                continue

            await asyncio.sleep(random.uniform(2, 5))

    return products


async def scrape_myntra() -> list[Product]:
    """Scrape all Myntra products."""
    all_products: list[Product] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-IN",
        )
        page = await context.new_page()
        await stealth_async(page)

        for category, url_templates in MYNTRA_URLS.items():
            products = await scrape_myntra_category(page, category, url_templates, target_count=50)
            all_products.extend(products)
            print(f"[Myntra] Scraped {len(products)} {category}")

        await browser.close()

    output_path = SCRAPED_DIR / "myntra_products.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in all_products], f, indent=2, ensure_ascii=False)

    print(f"[Myntra] Total: {len(all_products)} products saved to {output_path}")
    return all_products


if __name__ == "__main__":
    asyncio.run(scrape_myntra())
