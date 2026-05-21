VALID_FILTER_KEYS = {"category", "color", "source", "sub_category", "max_price"}


def build_chroma_filter(filters: dict) -> dict | None:
    """Convert extracted filters into ChromaDB where clause."""
    if not filters:
        return None

    # Only keep keys that correspond to actual metadata fields
    filters = {k: v for k, v in filters.items() if k in VALID_FILTER_KEYS and v}

    conditions = []

    if "category" in filters:
        conditions.append({"category": filters["category"]})
    if "color" in filters:
        # Use last word of color for matching (e.g., "dark navy" -> "navy")
        color = filters["color"].split()[-1].lower()
        conditions.append({"color": color})
    if "source" in filters:
        conditions.append({"source": filters["source"]})
    if "sub_category" in filters:
        conditions.append({"sub_category": filters["sub_category"]})
    if "max_price" in filters:
        conditions.append({"price": {"$lte": float(filters["max_price"])}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}
