import hashlib
import sqlite3
import time
from pathlib import Path

from src.config import SQLITE_PATH, CACHE_TTL


class SemanticCache:
    def __init__(self, db_path: str | Path | None = None, ttl: int = CACHE_TTL):
        self.db_path = str(db_path or SQLITE_PATH)
        self.ttl = ttl
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                query_hash TEXT PRIMARY KEY,
                response TEXT,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def _hash_query(self, query: str) -> str:
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, query: str) -> str | None:
        query_hash = self._hash_query(query)
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT response, created_at FROM cache WHERE query_hash = ?",
            (query_hash,)
        ).fetchone()
        conn.close()

        if row is None:
            return None

        response, created_at = row
        if time.time() - created_at > self.ttl:
            self._delete(query_hash)
            return None

        print("[Cache] HIT - returning cached response")
        return response

    def set(self, query: str, response: str):
        query_hash = self._hash_query(query)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO cache (query_hash, response, created_at) VALUES (?, ?, ?)",
            (query_hash, response, time.time())
        )
        conn.commit()
        conn.close()

    def _delete(self, query_hash: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM cache WHERE query_hash = ?", (query_hash,))
        conn.commit()
        conn.close()
