import os
import tempfile
from src.query.cache import SemanticCache


def test_cache_miss():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        cache = SemanticCache(db_path)
        result = cache.get("what shirt for party?")
        assert result is None
    finally:
        os.unlink(db_path)


def test_cache_hit():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        cache = SemanticCache(db_path)
        cache.set("what shirt for party?", '{"items": []}')
        result = cache.get("what shirt for party?")
        assert result == '{"items": []}'
    finally:
        os.unlink(db_path)


def test_different_query_no_hit():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        cache = SemanticCache(db_path)
        cache.set("what shirt for party?", '{"items": []}')
        result = cache.get("best pants for office?")
        assert result is None
    finally:
        os.unlink(db_path)
