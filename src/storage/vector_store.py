from pathlib import Path

import chromadb
from chromadb.config import Settings

from src.config import CHROMA_DIR, EMBEDDING_MODEL


class VectorStore:
    def __init__(self, persist_dir: str | Path | None = None, collection_name: str = "products"):
        persist_dir = str(persist_dir or CHROMA_DIR)
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, ids: list[str], texts: list[str], metadatas: list[dict],
                      embeddings: list[list[float]] | None = None):
        kwargs = {
            "ids": ids,
            "documents": texts,
            "metadatas": metadatas,
        }
        if embeddings:
            kwargs["embeddings"] = embeddings

        self.collection.upsert(**kwargs)
        print(f"[VectorStore] Upserted {len(ids)} documents")

    def search(self, query_text: str | None = None, query_embedding: list[float] | None = None,
               k: int = 20, where: dict | None = None) -> list[dict]:
        kwargs = {"n_results": k}

        if where:
            kwargs["where"] = where
        if query_embedding:
            kwargs["query_embeddings"] = [query_embedding]
        elif query_text:
            kwargs["query_texts"] = [query_text]
        else:
            raise ValueError("Must provide either query_text or query_embedding")

        results = self.collection.query(**kwargs)

        documents = []
        for i in range(len(results["ids"][0])):
            documents.append({
                "chunk_id": results["ids"][0][i],
                "text": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })

        return documents

    def count(self) -> int:
        return self.collection.count()

    def reset(self):
        """Release file handles held by the underlying ChromaDB client."""
        try:
            self.client._server.close()
        except Exception:
            pass
        try:
            del self.client
        except Exception:
            pass
