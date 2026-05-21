import json
from groq import Groq

from src.config import GROQ_API_KEY, GROQ_MODEL
from src.agent.prompts import HYDE_PROMPT, FILTER_EXTRACTION_PROMPT


def _get_groq_client() -> Groq:
    return Groq(api_key=GROQ_API_KEY)


def rewrite_query_hyde(query: str) -> str:
    """Use HyDE to generate a hypothetical document for better retrieval."""
    client = _get_groq_client()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": HYDE_PROMPT.format(query=query)}],
        temperature=0.7,
        max_tokens=200,
    )

    hypothetical_doc = response.choices[0].message.content.strip()
    return f"{query} {hypothetical_doc}"


def extract_filters(query: str) -> dict:
    """Extract structured metadata filters from a natural language query."""
    client = _get_groq_client()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": FILTER_EXTRACTION_PROMPT.format(query=query)}],
        temperature=0.0,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()

    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        filters = json.loads(raw)
    except json.JSONDecodeError:
        filters = {}

    return {k: v for k, v in filters.items() if v is not None}
