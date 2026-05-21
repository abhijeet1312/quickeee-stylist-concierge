from rank_bm25 import BM25Plus


class BM25Store:
    def __init__(self):
        self.doc_ids: list[str] = []
        self.corpus: list[list[str]] = []
        self.bm25: BM25Plus | None = None

    def add_documents(self, doc_ids: list[str], texts: list[str]):
        self.doc_ids = doc_ids
        self.corpus = [text.lower().split() for text in texts]
        self.bm25 = BM25Plus(self.corpus)
        print(f"[BM25] Indexed {len(doc_ids)} documents")

    def search(self, query: str, k: int = 20) -> list[dict]:
        if self.bm25 is None or len(self.doc_ids) == 0:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        scored_indices = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:k]

        results = []
        for idx, score in scored_indices:
            if score > 0:
                results.append({
                    "doc_id": self.doc_ids[idx],
                    "score": float(score),
                    "text": " ".join(self.corpus[idx]),
                })

        return results
