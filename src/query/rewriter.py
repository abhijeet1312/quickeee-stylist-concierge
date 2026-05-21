import json
from groq import Groq

from src.config import GROQ_API_KEY, GROQ_FAST_MODEL
from src.agent.prompts import COMBINED_REWRITE_PROMPT


def _get_groq_client() -> Groq:
    return Groq(api_key=GROQ_API_KEY)


def rewrite_and_extract(query: str) -> tuple[str, dict]:
    """Combined HyDE rewrite + filter extraction in a single LLM call."""
    client = _get_groq_client()

    response = client.chat.completions.create(
        model=GROQ_FAST_MODEL,
        messages=[{"role": "user", "content": COMBINED_REWRITE_PROMPT.format(query=query)}],
        temperature=0.3,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()

    # Parse the combined response
    rewritten = query
    filters = {}

    if "PRODUCT:" in raw and "FILTERS:" in raw:
        parts = raw.split("FILTERS:")
        product_part = parts[0].replace("PRODUCT:", "").strip()
        filters_part = parts[1].strip()

        rewritten = f"{query} {product_part}"

        # Parse filters JSON
        if "```" in filters_part:
            filters_part = filters_part.split("```")[1]
            if filters_part.startswith("json"):
                filters_part = filters_part[4:]
            filters_part = filters_part.strip()

        try:
            filters = json.loads(filters_part)
            filters = {k: v for k, v in filters.items() if v is not None}
        except json.JSONDecodeError:
            filters = {}
    else:
        # Fallback: treat entire response as hypothetical doc
        rewritten = f"{query} {raw}"

    return rewritten, filters
