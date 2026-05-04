"""
Module 4: Evaluation — lightweight RAGAS-like metrics + failure analysis
"""

import os, sys, json
from dataclasses import dataclass
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


# ================= LOAD =================

def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ================= UTILS =================

def normalize(text: str) -> set:
    return set(text.lower().split())


def overlap_score(a: str, b: str) -> float:
    a_set, b_set = normalize(a), normalize(b)
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / len(a_set | b_set)


# ================= METRICS =================

def compute_metrics(question, answer, contexts, ground_truth):

    # faithfulness: answer có nằm trong context không
    context_text = " ".join(contexts)
    faithfulness = overlap_score(answer, context_text)

    # answer relevancy: answer vs ground truth
    answer_relevancy = overlap_score(answer, ground_truth)

    # context precision: context có liên quan câu hỏi không
    context_precision = overlap_score(context_text, question)

    # context recall: context có chứa ground truth không
    context_recall = overlap_score(context_text, ground_truth)

    return faithfulness, answer_relevancy, context_precision, context_recall


# ================= MAIN EVAL =================

def evaluate_ragas(questions, answers, contexts, ground_truths):

    results = []

    for q, a, c, gt in zip(questions, answers, contexts, ground_truths):

        f, ar, cp, cr = compute_metrics(q, a, c, gt)

        results.append(EvalResult(
            question=q,
            answer=a,
            contexts=c,
            ground_truth=gt,
            faithfulness=f,
            answer_relevancy=ar,
            context_precision=cp,
            context_recall=cr
        ))

    # aggregate
    agg = {
        "faithfulness": round(mean([r.faithfulness for r in results]), 4),
        "answer_relevancy": round(mean([r.answer_relevancy for r in results]), 4),
        "context_precision": round(mean([r.context_precision for r in results]), 4),
        "context_recall": round(mean([r.context_recall for r in results]), 4),
        "per_question": results
    }

    return agg


# ================= FAILURE ANALYSIS =================

def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10):

    scored = []

    for r in eval_results:
        avg_score = mean([
            r.faithfulness,
            r.answer_relevancy,
            r.context_precision,
            r.context_recall
        ])
        scored.append((avg_score, r))

    scored.sort(key=lambda x: x[0])  # thấp nhất trước

    failures = []

    for _, r in scored[:bottom_n]:

        metrics = {
            "faithfulness": r.faithfulness,
            "answer_relevancy": r.answer_relevancy,
            "context_precision": r.context_precision,
            "context_recall": r.context_recall
        }

        worst_metric = min(metrics, key=metrics.get)
        score = metrics[worst_metric]

        # diagnosis rules
        if worst_metric == "faithfulness":
            diagnosis = "LLM hallucinating"
            fix = "Improve prompt or reduce temperature"

        elif worst_metric == "context_recall":
            diagnosis = "Missing relevant chunks"
            fix = "Improve chunking or retrieval"

        elif worst_metric == "context_precision":
            diagnosis = "Too many irrelevant chunks"
            fix = "Use reranking or filtering"

        else:
            diagnosis = "Answer not aligned with question"
            fix = "Improve prompt template"

        failures.append({
            "question": r.question,
            "worst_metric": worst_metric,
            "score": round(score, 4),
            "diagnosis": diagnosis,
            "suggested_fix": fix
        })

    return failures


# ================= SAVE =================

def save_report(results, failures, path="ragas_report.json"):

    report = {
        "aggregate": {
            k: v for k, v in results.items() if k != "per_question"
        },
        "num_questions": len(results.get("per_question", [])),
        "failures": failures
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Report saved to {path}")


# ================= TEST =================

if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} questions")