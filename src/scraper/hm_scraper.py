"""
Flipkart Fashion Scraper (replacing H&M which blocks automated access).
Scrapes men's tops and bottoms from Flipkart using Playwright + stealth.
"""
import asyncio
import json
import random
import re

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from src.config import SCRAPED_DIR
from src.scraper.models import Product


FLIPKART_SEARCH_URLS = {
    "tops": [
        "https://www.flipkart.com/search?q=men+t-shirts&otracker=search&marketplace=FLIPKART&page={}",
        "https://www.flipkart.com/search?q=men+casual+shirts&otracker=search&marketplace=FLIPKART&page={}",
    ],
    "bottoms": [
        "https://www.flipkart.com/search?q=men+trousers&otracker=search&marketplace=FLIPKART&page={}",
        "https://www.flipkart.com/search?q=men+shorts&otracker=search&marketplace=FLIPKART&page={}",
    ],
}

COMMON_COLORS = [
    "black", "white", "blue", "red", "green", "navy",
    "grey", "gray", "pink", "yellow", "beige", "brown",
    "olive", "maroon", "teal", "orange", "purple", "charcoal",
    "cream", "khaki", "lavender", "coral", "burgundy", "mustard",
    "wine", "peach", "rust", "mint", "ivory", "tan",
    "silver", "gold", "magenta", "turquoise", "indigo", "mauve",
    "aqua", "lilac", "plum", "copper", "taupe", "sand",
    "multicolor", "multicolour", "multi",
]


def extract_color(name: str, card_text: str = "") -> str:
    """Extract color from product name first, then fall back to full card text."""
    for source in [name, card_text]:
        source_lower = source.lower()
        for color in COMMON_COLORS:
            # Use word boundary check to avoid partial matches (e.g. "gold" in "marigold")
            if re.search(r'\b' + re.escape(color) + r'\b', source_lower):
                return color
    return ""


def parse_price(text: str) -> float:
    """Extract numeric price from text like '₹495₹1,99975% off'."""
    # Find the first price (current/discounted price)
    match = re.search(r'[\u20b9₹]?\s*([\d,]+)', text)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0


async def scrape_flipkart_category(page, category: str, url_templates: list[str], target_count: int = 50) -> list[Product]:
    """Scrape Flipkart product listings for a category."""
    products: list[Product] = []
    seen_names: set[str] = set()  # Track seen product names for deduplication
    product_idx = 0

    # Split target evenly across URL templates so each sub-category gets scraped
    per_template_target = target_count // len(url_templates)

    for template_idx, url_template in enumerate(url_templates):
        template_count = 0

        for page_num in range(1, 4):  # Up to 3 pages
            if template_count >= per_template_target:
                break

            url = url_template.format(page_num)
            print(f"[Flipkart] Scraping: {url}")

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                # Scroll to load lazy images
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)

                cards = await page.query_selector_all("div[data-id]")
                print(f"[Flipkart] Found {len(cards)} product cards on page {page_num}")

                for card in cards:
                    if template_count >= per_template_target:
                        break

                    try:
                        text = await card.inner_text()
                        lines = [l.strip() for l in text.split("\n") if l.strip()]

                        if len(lines) < 2:
                            continue

                        # Skip unavailable
                        if "Currently unavailable" in text:
                            continue

                        # First line is usually brand, second is product name
                        brand = lines[0]
                        name_line = lines[1] if len(lines) > 1 else ""

                        # Try to get the full (non-truncated) name from anchor title/aria-label
                        anchor = await card.query_selector("a[title]")
                        if anchor:
                            title_attr = await anchor.get_attribute("title") or ""
                            if title_attr and len(title_attr) > len(name_line):
                                name_line = title_attr
                        if not anchor or name_line.endswith("..."):
                            anchor_aria = await card.query_selector("a[aria-label]")
                            if anchor_aria:
                                aria_label = await anchor_aria.get_attribute("aria-label") or ""
                                if aria_label and len(aria_label) > len(name_line):
                                    name_line = aria_label

                        # Strip trailing "..." from truncated names
                        if name_line.endswith("..."):
                            name_line = name_line.rstrip(".")

                        full_name = f"{brand} {name_line}".strip()

                        # Strip trailing "..." from the combined name too
                        if full_name.endswith("..."):
                            full_name = full_name.rstrip(".")

                        # Deduplicate by normalized name
                        name_key = full_name.lower().strip()
                        if name_key in seen_names:
                            continue
                        seen_names.add(name_key)

                        # Find price line (contains ₹)
                        price = 0.0
                        for line in lines:
                            if "₹" in line or "\u20b9" in line:
                                price = parse_price(line)
                                if price > 0:
                                    break

                        # Image
                        img_el = await card.query_selector("img")
                        image_url = ""
                        if img_el:
                            image_url = await img_el.get_attribute("src") or ""

                        if not full_name or price == 0:
                            continue

                        # Determine sub_category from search query
                        sub_cat = ""
                        if "t-shirt" in url.lower():
                            sub_cat = "t-shirt"
                        elif "shirt" in url.lower():
                            sub_cat = "shirt"
                        elif "trouser" in url.lower() or "pant" in url.lower():
                            sub_cat = "pants"
                        elif "short" in url.lower():
                            sub_cat = "shorts"

                        # Extract color from name first, then full card text as fallback
                        color = extract_color(full_name, text)

                        product_idx += 1
                        template_count += 1
                        products.append(Product(
                            id=f"flipkart_{category}_{product_idx:03d}",
                            name=full_name,
                            price=price,
                            currency="INR",
                            image_url=image_url,
                            category=category,
                            sub_category=sub_cat,
                            color=color,
                            description=f"{full_name} - {sub_cat} from Flipkart",
                            source="flipkart",
                        ))

                    except Exception as e:
                        continue

            except Exception as e:
                print(f"[Flipkart] Error loading page: {e}")
                continue

            await asyncio.sleep(random.uniform(2, 4))

    return products


async def scrape_hm() -> list[Product]:
    """Scrape Flipkart for fashion products (replaces H&M which blocks scrapers)."""
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

        for category, url_templates in FLIPKART_SEARCH_URLS.items():
            products = await scrape_flipkart_category(page, category, url_templates, target_count=50)
            all_products.extend(products)
            print(f"[Flipkart] Scraped {len(products)} {category}")

        await browser.close()

    output_path = SCRAPED_DIR / "flipkart_products.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in all_products], f, indent=2, ensure_ascii=False)

    print(f"[Flipkart] Total: {len(all_products)} products saved to {output_path}")
    return all_products


if __name__ == "__main__":
    asyncio.run(scrape_hm())
