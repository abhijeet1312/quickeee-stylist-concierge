import json
import sqlite3
from pathlib import Path
from src.scraper.models import Product
from src.config import SQLITE_PATH


class DocumentStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = str(db_path or SQLITE_PATH)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL,
                currency TEXT DEFAULT 'INR',
                image_url TEXT DEFAULT '',
                category TEXT,
                sub_category TEXT DEFAULT '',
                color TEXT DEFAULT '',
                description TEXT DEFAULT '',
                source TEXT,
                scraped_at TEXT,
                raw_json TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                query_hash TEXT PRIMARY KEY,
                response TEXT,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def insert_products(self, products: list[Product]):
        conn = sqlite3.connect(self.db_path)
        for p in products:
            conn.execute("""
                INSERT OR REPLACE INTO products
                (id, name, price, currency, image_url, category, sub_category, color, description, source, scraped_at, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p.id, p.name, p.price, p.currency, p.image_url,
                p.category, p.sub_category, p.color, p.description,
                p.source, p.scraped_at, json.dumps(p.model_dump()),
            ))
        conn.commit()
        conn.close()
        print(f"[DocStore] Inserted {len(products)} products")

    def get_product(self, product_id: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        conn.close()
        if row is None:
            return None
        return dict(row)

    def get_products_by_ids(self, product_ids: list[str]) -> list[dict]:
        if not product_ids:
            return []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        placeholders = ",".join("?" for _ in product_ids)
        rows = conn.execute(
            f"SELECT * FROM products WHERE id IN ({placeholders})", product_ids
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def filter_products(self, category: str | None = None, source: str | None = None,
                        max_price: float | None = None, color: str | None = None) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM products WHERE 1=1"
        params: list = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if source:
            query += " AND source = ?"
            params.append(source)
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        if color:
            query += " AND color LIKE ?"
            params.append(f"%{color}%")

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_products(self) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM products").fetchall()
        conn.close()
        return [dict(r) for r in rows]
