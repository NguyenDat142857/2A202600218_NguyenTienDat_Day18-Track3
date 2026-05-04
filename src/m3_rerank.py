"""
Module 3: Reranking — Cross-encoder
====================================
Top-K reranking to improve precision.
"""

import os, sys, time
from dataclasses import dataclass
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RERANK_TOP_K


@dataclass
class RerankResult:
    text: str
    original_score: float
    rerank_score: float
    metadata: dict
    rank: int


# ================= CROSS ENCODER =================

class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:

        if not documents:
            return []

        model = self._load_model()

        pairs = [(query, doc["text"]) for doc in documents]

        scores = model.predict(pairs)

        combined = []
        for score, doc in zip(scores, documents):
            combined.append({
                "score": float(score),
                "doc": doc
            })

        # sort by rerank score
        combined.sort(key=lambda x: x["score"], reverse=True)

        results = []
        for i, item in enumerate(combined[:top_k]):
            doc = item["doc"]

            results.append(RerankResult(
                text=doc["text"],
                original_score=doc.get("score", 0.0),
                rerank_score=item["score"],
                metadata=doc.get("metadata", {}),
                rank=i + 1
            ))

        return results


# ================= LIGHTWEIGHT (FALLBACK) =================

class FlashrankReranker:
    """
    Fallback lightweight reranker (no extra libs).
    Uses simple keyword overlap scoring.
    """

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:

        q_words = set(query.lower().split())

        scored = []
        for doc in documents:
            d_words = set(doc["text"].lower().split())

            overlap = len(q_words & d_words)
            score = overlap / (len(q_words) + 1e-6)

            scored.append({
                "score": score,
                "doc": doc
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        results = []
        for i, item in enumerate(scored[:top_k]):
            doc = item["doc"]

            results.append(RerankResult(
                text=doc["text"],
                original_score=doc.get("score", 0.0),
                rerank_score=item["score"],
                metadata=doc.get("metadata", {}),
                rank=i + 1
            ))

        return results


# ================= BENCHMARK =================

def benchmark_reranker(reranker, query: str, documents: list[dict], n_runs: int = 5) -> dict:

    times = []

    for _ in range(n_runs):
        start = time.perf_counter()

        reranker.rerank(query, documents)

        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    return {
        "avg_ms": round(mean(times), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2)
    }


# ================= TEST =================

if __name__ == "__main__":
    query = "Nhân viên được nghỉ phép bao nhiêu ngày?"

    docs = [
        {"text": "Nhân viên được nghỉ 12 ngày mỗi năm.", "score": 0.8, "metadata": {}},
        {"text": "Mật khẩu thay đổi mỗi 90 ngày.", "score": 0.7, "metadata": {}},
        {"text": "Thử việc kéo dài 60 ngày.", "score": 0.75, "metadata": {}},
    ]

    print("=== CrossEncoder ===")
    reranker = CrossEncoderReranker()

    results = reranker.rerank(query, docs)
    for r in results:
        print(f"[{r.rank}] {r.rerank_score:.4f} | {r.text}")

    print("\n=== Benchmark ===")
    print(benchmark_reranker(reranker, query, docs))