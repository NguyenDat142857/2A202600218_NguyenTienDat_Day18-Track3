import os, sys, time
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.m1_chunking import load_documents, chunk_hierarchical
from src.m2_search import HybridSearch
from src.m3_rerank import CrossEncoderReranker
from src.m4_eval import load_test_set, evaluate_ragas, failure_analysis, save_report
from src.m5_enrichment import enrich_chunks
from config import RERANK_TOP_K


# ================= ANSWER GENERATION =================

def extractive_answer(query: str, contexts: List[str]) -> str:
    """Fallback extractive QA (NO hallucination)."""

    if not contexts:
        return "Không tìm thấy thông tin."

    query_words = set(query.lower().split())

    best_sentence = ""
    best_score = 0

    for ctx in contexts:
        sentences = ctx.split(". ")
        for sent in sentences:
            sent_words = set(sent.lower().split())
            overlap = len(query_words & sent_words)

            if overlap > best_score:
                best_score = overlap
                best_sentence = sent

    if best_score == 0:
        return "Không tìm thấy thông tin trong tài liệu."

    return best_sentence.strip()


def llm_answer(query: str, contexts: List[str]) -> str:
    """LLM answer with strict grounding."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        context_str = "\n\n".join(contexts)

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là trợ lý QA. CHỈ trả lời dựa trên context.\n"
                        "- Không suy đoán\n"
                        "- Không thêm thông tin ngoài context\n"
                        "- Nếu không có → trả lời: 'Không tìm thấy thông tin.'"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context_str}\n\nCâu hỏi: {query}",
                },
            ],
        )

        return resp.choices[0].message.content.strip()

    except Exception:
        return extractive_answer(query, contexts)


# ================= BUILD PIPELINE =================

def build_pipeline():
    print("=" * 60)
    print("PRODUCTION RAG PIPELINE")
    print("=" * 60)

    # STEP 1: Chunking
    print("\n[1/4] Chunking documents...")
    docs = load_documents()

    all_chunks = []
    for doc in docs:
        _, children = chunk_hierarchical(doc["text"], metadata=doc["metadata"])

        for child in children:
            all_chunks.append({
                "text": child.text,
                "metadata": {**child.metadata, "parent_id": child.parent_id}
            })

    print(f"  {len(all_chunks)} chunks")

    if not all_chunks:
        print("❌ No chunks created")
        return None, None

    # STEP 2: Enrichment
    print("\n[2/4] Enriching chunks...")
    enriched = enrich_chunks(all_chunks, methods=["contextual", "hyqa", "metadata"])

    if enriched:
        all_chunks = [
            {
                # ✅ IMPORTANT: include HyQA
                "text": e.enriched_text + "\n" + " ".join(e.hypothesis_questions),
                "metadata": e.auto_metadata
            }
            for e in enriched
        ]
        print(f"  Enriched {len(all_chunks)} chunks")
    else:
        print("  ⚠️ fallback raw chunks")

    # STEP 3: Index
    print("\n[3/4] Indexing...")
    search = HybridSearch()
    search.index(all_chunks)

    # STEP 4: Reranker
    print("\n[4/4] Loading reranker...")
    reranker = CrossEncoderReranker()

    return search, reranker


# ================= QUERY =================

def run_query(query: str, search, reranker):
    results = search.search(query)

    docs = [
        {"text": r.text, "score": r.score, "metadata": r.metadata}
        for r in results
    ]

    reranked = reranker.rerank(query, docs, top_k=RERANK_TOP_K)

    contexts = (
        [r.text for r in reranked]
        if reranked else
        [r.text for r in results[:3]]
    )

    # ✅ MAIN FIX: LLM + fallback
    answer = llm_answer(query, contexts)

    return answer, contexts


# ================= EVALUATION =================

def evaluate_pipeline(search, reranker):

    print("\n[Eval] Running queries...")
    test_set = load_test_set()

    questions, answers, all_contexts, ground_truths = [], [], [], []

    for i, item in enumerate(test_set):
        answer, contexts = run_query(item["question"], search, reranker)

        questions.append(item["question"])
        answers.append(answer)
        all_contexts.append(contexts)
        ground_truths.append(item["ground_truth"])

        print(f"  [{i+1}/{len(test_set)}] {item['question'][:50]}...")

    print("\n[Eval] Running evaluation...")
    results = evaluate_ragas(questions, answers, all_contexts, ground_truths)

    print("\n" + "=" * 60)
    print("PRODUCTION RAG SCORES")
    print("=" * 60)

    for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        s = results.get(m, 0)
        print(f"  {'✓' if s >= 0.5 else '✗'} {m}: {s:.4f}")

    failures = failure_analysis(results.get("per_question", []))
    save_report(results, failures)

    return results


# ================= MAIN =================

if __name__ == "__main__":
    start = time.time()

    search, reranker = build_pipeline()

    if search is None:
        exit()

    evaluate_pipeline(search, reranker)

    print(f"\n⏱️ Total: {time.time() - start:.1f}s")