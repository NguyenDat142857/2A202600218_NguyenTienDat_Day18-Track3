"""Module 2: Hybrid Search — BM25 + Dense + RRF."""

import os, sys
from dataclasses import dataclass
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME,
    EMBEDDING_MODEL, EMBEDDING_DIM,
    BM25_TOP_K, DENSE_TOP_K, HYBRID_TOP_K
)


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict
    method: str


# ========================
# Vietnamese tokenizer
# ========================
def segment_vietnamese(text: str) -> str:
    try:
        from underthesea import word_tokenize
        return word_tokenize(text, format="text")
    except:
        return text


# ========================
# BM25
# ========================
class BM25Search:
    def __init__(self):
        self.documents = []
        self.corpus_tokens = []
        self.bm25 = None

    def index(self, chunks):
        from rank_bm25 import BM25Okapi

        self.documents = chunks
        self.corpus_tokens = [
            segment_vietnamese(c["text"]).split()
            for c in chunks
        ]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def search(self, query, top_k=BM25_TOP_K):
        tokenized_query = segment_vietnamese(query).split()
        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for i in ranked:
            doc = self.documents[i]
            results.append(SearchResult(
                text=doc["text"],
                score=float(scores[i]),
                metadata=doc["metadata"],
                method="bm25"
            ))
        return results


# ========================
# Dense Search (Qdrant FIXED)
# ========================
class DenseSearch:
    def __init__(self):
        from qdrant_client import QdrantClient
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self._encoder = None

    def _get_encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer(EMBEDDING_MODEL)
        return self._encoder

    def index(self, chunks, collection=COLLECTION_NAME):
        from qdrant_client.models import VectorParams, Distance, PointStruct

        self.client.recreate_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )

        texts = [c["text"] for c in chunks]
        vectors = self._get_encoder().encode(texts)

        points = []
        for i, (vec, c) in enumerate(zip(vectors, chunks)):
            points.append(PointStruct(
                id=i,
                vector=vec.tolist(),
                payload={**c["metadata"], "text": c["text"]}
            ))

        self.client.upsert(collection_name=collection, points=points)

    def search(self, query, top_k=DENSE_TOP_K, collection=COLLECTION_NAME):
        query_vector = self._get_encoder().encode(query).tolist()

        # ✅ FIX CHUẨN API MỚI
        hits = self.client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k
        ).points

        results = []
        for hit in hits:
            results.append(SearchResult(
                text=hit.payload["text"],
                score=float(hit.score),
                metadata=hit.payload,
                method="dense"
            ))
        return results


# ========================
# RRF
# ========================
def reciprocal_rank_fusion(results_list, k=60, top_k=HYBRID_TOP_K):
    scores = defaultdict(lambda: {"score": 0, "doc": None})

    for results in results_list:
        for rank, r in enumerate(results):
            scores[r.text]["score"] += 1 / (k + rank + 1)
            scores[r.text]["doc"] = r

    ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

    final = []
    for i, (text, data) in enumerate(ranked[:top_k]):
        doc = data["doc"]
        final.append(SearchResult(
            text=text,
            score=data["score"],
            metadata=doc.metadata,
            method="hybrid"
        ))
    return final


# ========================
# Hybrid
# ========================
class HybridSearch:
    def __init__(self):
        self.bm25 = BM25Search()
        self.dense = DenseSearch()

    def index(self, chunks):
        self.bm25.index(chunks)
        self.dense.index(chunks)

    def search(self, query, top_k=HYBRID_TOP_K):
        bm25_res = self.bm25.search(query)
        dense_res = self.dense.search(query)
        return reciprocal_rank_fusion([bm25_res, dense_res], top_k=top_k)