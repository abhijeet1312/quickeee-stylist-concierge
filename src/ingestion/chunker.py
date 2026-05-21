from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.scraper.models import Product


splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
)


def chunk_product(product: Product) -> list[dict]:
    """Split a product's searchable text into chunks with metadata."""
    text = product.to_searchable_text()
    metadata = product.to_metadata()

    text_chunks = splitter.split_text(text)

    chunks = []
    for i, chunk_text in enumerate(text_chunks):
        chunks.append({
            "product_id": product.id,
            "chunk_id": f"{product.id}_chunk_{i}",
            "text": chunk_text,
            "metadata": metadata,
        })

    return chunks
