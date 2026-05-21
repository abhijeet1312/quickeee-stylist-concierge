import json
from pathlib import Path

from src.config import SCRAPED_DIR
from src.scraper.models import Product
from src.ingestion.cleaner import clean_product
from src.ingestion.chunker import chunk_product
from src.ingestion.deduplicator import deduplicate_products
from src.ingestion.embedder import Embedder
from src.storage.vector_store import VectorStore
from src.storage.document_store import DocumentStore
from src.storage.bm25_store import BM25Store


def load_scraped_products(data_dir: Path | None = None) -> list[Product]:
    """Load all scraped JSON files."""
    data_dir = data_dir or SCRAPED_DIR
    products = []

    for json_file in data_dir.glob("*.json"):
        if json_file.name == "all_products.json":
            continue
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                products.append(Product(**item))

    print(f"[Pipeline] Loaded {len(products)} products from {data_dir}")
    return products


def run_ingestion(products: list[Product] | None = None) -> tuple[VectorStore, DocumentStore, BM25Store]:
    """Run the full ingestion pipeline."""
    if products is None:
        products = load_scraped_products()

    if not products:
        raise ValueError("No products to ingest. Run scrapers first.")

    print("[Pipeline] Cleaning products...")
    products = [clean_product(p) for p in products]

    print("[Pipeline] Deduplicating...")
    products = deduplicate_products(products)

    print("[Pipeline] Chunking...")
    all_chunks = []
    for product in products:
        chunks = chunk_product(product)
        all_chunks.extend(chunks)
    print(f"[Pipeline] Created {len(all_chunks)} chunks from {len(products)} products")

    print(f"[Pipeline] Embedding ({embedder.mode} mode)...")
    embedder = Embedder()
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = embedder.embed_texts(texts)

    print("[Pipeline] Storing in ChromaDB...")
    vector_store = VectorStore()
    vector_store.add_documents(
        ids=[chunk["chunk_id"] for chunk in all_chunks],
        texts=texts,
        metadatas=[chunk["metadata"] for chunk in all_chunks],
        embeddings=embeddings,
    )

    print("[Pipeline] Storing in SQLite...")
    doc_store = DocumentStore()
    doc_store.insert_products(products)

    print("[Pipeline] Building BM25 index...")
    bm25_store = BM25Store()
    bm25_store.add_documents(
        doc_ids=[chunk["chunk_id"] for chunk in all_chunks],
        texts=texts,
    )

    print(f"[Pipeline] Ingestion complete!")
    print(f"  ChromaDB: {vector_store.count()} vectors")
    print(f"  SQLite: {len(products)} products")
    print(f"  BM25: {len(all_chunks)} documents indexed")

    return vector_store, doc_store, bm25_store


if __name__ == "__main__":
    run_ingestion()
