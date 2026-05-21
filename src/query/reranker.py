import time
import requests as req_lib

from src.config import RERANKER_MODEL, RERANK_TOP_K, HF_API_TOKEN, USE_HF_API

HF_RERANKER_URL = f"https://api-inference.huggingface.co/models/{RERANKER_MODEL}"

_reranker = None
_hf_session: req_lib.Session | None = None


def _get_reranker():
    global _reranker
    if USE_HF_API:
        return None
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        print(f"[Reranker] Loading {RERANKER_MODEL} locally...")
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker


def _get_hf_session() -> req_lib.Session:
    global _hf_session
    if _hf_session is None:
        _hf_session = req_lib.Session()
    return _hf_session


def _api_rerank(query: str, texts: list[str]) -> list[float]:
    """Call HuggingFace Inference API for reranking."""
    session = _get_hf_session()
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

    payload = {
        "inputs": {"query": query, "texts": texts},
        "options": {"wait_for_model": True},
    }

    resp = session.post(HF_RERANKER_URL, headers=headers, json=payload, timeout=120)

    if resp.status_code == 503:
        wait_time = resp.json().get("estimated_time", 30)
        print(f"[Reranker] Model loading on HF, waiting {wait_time:.0f}s...")
        time.sleep(min(wait_time, 60))
        return _api_rerank(query, texts)

    resp.raise_for_status()
    result = resp.json()

    # Response format: [{"index": 0, "score": 0.95}, ...]
    if isinstance(result, list) and result and isinstance(result[0], dict) and "score" in result[0]:
        # Sort by original index to match input order
        sorted_by_idx = sorted(result, key=lambda x: x["index"])
        return [r["score"] for r in sorted_by_idx]

    # Fallback: flat list of scores
    if isinstance(result, list) and result and isinstance(result[0], (int, float)):
        return result

    # If unexpected format, return equal scores
    return [0.0] * len(texts)


def rerank(query: str, candidates: list[dict], top_k: int = RERANK_TOP_K) -> list[dict]:
    """Rerank candidates using BGE cross-encoder."""
    if not candidates:
        return []

    texts = [c["text"] for c in candidates]

    if USE_HF_API:
        try:
            scores = _api_rerank(query, texts)
        except Exception as e:
            print(f"[Reranker] API failed ({type(e).__name__}), skipping rerank")
            return candidates[:top_k]
    else:
        reranker = _get_reranker()
        pairs = [(query, t) for t in texts]
        scores = reranker.predict(pairs)
        if not hasattr(scores, '__len__'):
            scores = [scores]

    for i, candidate in enumerate(candidates):
        candidate["rerank_score"] = float(scores[i])

    ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

    return ranked[:top_k]
