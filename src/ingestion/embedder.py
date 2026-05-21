import math
import time
import requests as req_lib

from src.config import EMBEDDING_MODEL, EMBEDDING_DIM, HF_API_TOKEN, USE_HF_API, EMBEDDING_MODE

HF_API_URL = f"https://api-inference.huggingface.co/models/{EMBEDDING_MODEL}"


class Embedder:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self.mode = EMBEDDING_MODE

        if self.mode == "onnx":
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            self._onnx_ef = DefaultEmbeddingFunction()
            print(f"[Embedder] Using local ONNX (all-MiniLM-L6-v2, {EMBEDDING_DIM}d)")
        elif self.mode == "api":
            self._headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            self._session = req_lib.Session()
            print(f"[Embedder] Using HuggingFace Inference API for {model_name}")
        else:
            from sentence_transformers import SentenceTransformer
            print(f"[Embedder] Loading {model_name} locally...")
            self.model = SentenceTransformer(model_name)
            print(f"[Embedder] Model loaded. Dimension: {self.model.get_sentence_embedding_dimension()}")

    def _api_embed(self, texts: list[str]) -> list[list[float]]:
        """Call HuggingFace Inference API for embeddings."""
        resp = self._session.post(
            HF_API_URL,
            headers=self._headers,
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=120,
        )

        if resp.status_code == 503:
            wait_time = resp.json().get("estimated_time", 30)
            print(f"[Embedder] Model loading on HF, waiting {wait_time:.0f}s...")
            time.sleep(min(wait_time, 60))
            return self._api_embed(texts)

        resp.raise_for_status()
        return resp.json()

    def _normalize(self, vec: list) -> list[float]:
        norm = math.sqrt(sum(float(x) * float(x) for x in vec))
        if norm == 0:
            return [float(x) for x in vec]
        return [float(x) / norm for x in vec]

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if self.mode == "onnx":
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self._onnx_ef(batch)
                all_embeddings.extend([self._normalize(list(e)) for e in embeddings])
                if i + batch_size < len(texts):
                    print(f"[Embedder] Embedded {i + len(batch)}/{len(texts)}")
            return all_embeddings
        elif self.mode == "api":
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self._api_embed(batch)
                all_embeddings.extend([self._normalize(e) for e in embeddings])
                if i + batch_size < len(texts):
                    print(f"[Embedder] Embedded {i + len(batch)}/{len(texts)}")
            return all_embeddings
        else:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                normalize_embeddings=True,
            )
            return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        if self.mode == "onnx":
            result = self._onnx_ef([query])
            return self._normalize(list(result[0]))
        elif self.mode == "api":
            result = self._api_embed([query])
            return self._normalize(result[0])
        else:
            embedding = self.model.encode(query, normalize_embeddings=True)
            return embedding.tolist()
