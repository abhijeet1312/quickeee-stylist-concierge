from src.query.filter_builder import build_chroma_filter


def test_single_filter():
    filters = {"category": "tops"}
    result = build_chroma_filter(filters)
    assert result == {"category": "tops"}


def test_multiple_filters():
    filters = {"category": "tops", "color": "navy"}
    result = build_chroma_filter(filters)
    assert result == {"$and": [{"category": "tops"}, {"color": "navy"}]}


def test_price_filter():
    filters = {"max_price": 1000}
    result = build_chroma_filter(filters)
    assert result == {"price": {"$lte": 1000}}


def test_empty_filters():
    result = build_chroma_filter({})
    assert result is None
