HYDE_PROMPT = """You are a fashion product search assistant. Given a user's styling query, generate a hypothetical product description that would be an ideal search result.

User query: {query}

Generate a short product description (2-3 sentences) that describes the ideal clothing item(s) the user is looking for. Focus on material, color, style, and occasion. Do not include prices.

Hypothetical product description:"""

FILTER_EXTRACTION_PROMPT = """Extract structured filters from this fashion query. Return ONLY valid JSON.

Query: {query}

Extract these fields if mentioned (use null if not mentioned):
- category: "tops" or "bottoms" or null
- color: the color mentioned or null
- max_price: number or null
- source: "h&m" or "myntra" or null
- occasion: the occasion/style mentioned or null

JSON:"""

COMBINED_REWRITE_PROMPT = """You are a fashion product search assistant. Do TWO things for this query:

Query: {query}

1. HYPOTHETICAL PRODUCT: Write a 2-sentence product description for the ideal item the user wants. Focus on material, color, style, occasion.

2. FILTERS: Extract structured filters as JSON with these fields (null if not mentioned):
- category: "tops" or "bottoms" or null
- color: the color or null
- max_price: number or null
- source: "h&m" or "myntra" or null
- occasion: the occasion or null
- gender: "men" or "women" or null (infer from context like "female", "girl", "him", "her", etc.)

Reply in EXACTLY this format (no extra text):
PRODUCT: <your hypothetical product description>
FILTERS: <json object>"""

FASHION_MATCHER_PROMPT = """You are a luxury fashion stylist for Quickeee. Given a user's request and a set of available clothing items, recommend the best outfit combination.

User request: {query}

Available items:
{context}

Rules:
1. Select items that work together as a cohesive outfit
2. Consider color coordination, style matching, and occasion appropriateness
3. Try to include both a top and a bottom if available
4. Explain WHY these pieces work together
5. GENDER MATCH: Pay attention to gendered terms in product names (e.g. "Men", "Women"). If the user asks for women's/female clothing and only men's items are available (or vice versa), acknowledge this in the stylist_note and recommend the closest match while noting the mismatch. Do NOT silently recommend the wrong gender.

Return your response as JSON with this exact format:
{{
    "recommended_items": [
        {{
            "id": "product_id",
            "name": "product name",
            "category": "tops/bottoms",
            "color": "color",
            "price": 0.0,
            "image_url": "url",
            "source": "source"
        }}
    ],
    "total_price": 0.0,
    "currency": "INR",
    "stylist_note": "A short, luxurious explanation of why these pieces work together (2-3 sentences).",
    "agent_reasoning": ["step 1", "step 2", "..."]
}}

JSON response:"""
