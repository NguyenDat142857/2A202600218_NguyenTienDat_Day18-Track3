"""
Module 5: Enrichment Pipeline (No-API version)
=============================================
Lightweight enrichment: summary + HyQA + contextual + metadata
"""

import os, sys, re
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ================= DATA CLASS =================

@dataclass
class EnrichedChunk:
    original_text: str
    enriched_text: str
    summary: str
    hypothesis_questions: list[str]
    auto_metadata: dict
    method: str


# ================= UTILS =================

def split_sentences(text: str):
    return [s.strip() for s in re.split(r'[.!?]\s+', text) if s.strip()]


# ================= 1. SUMMARY =================

def summarize_chunk(text: str) -> str:
    sentences = split_sentences(text)

    if not sentences:
        return ""

    # lấy 2 câu đầu
    summary = ". ".join(sentences[:2])
    return summary.strip() + "."


# ================= 2. HYQA =================

def generate_hypothesis_questions(text: str, n_questions: int = 3) -> list[str]:

    sentences = split_sentences(text)

    questions = []

    for s in sentences[:n_questions]:
        if "bao nhiêu" not in s.lower():
            questions.append(f"{s}?")

    # fallback nếu không có câu
    if not questions:
        questions = [
            "Nội dung đoạn văn này là gì?",
            "Thông tin chính trong đoạn là gì?",
            "Đoạn văn đề cập đến vấn đề gì?"
        ]

    return questions[:n_questions]


# ================= 3. CONTEXTUAL =================

def contextual_prepend(text: str, document_title: str = "") -> str:

    context = f"Trích từ tài liệu '{document_title}'. Nội dung liên quan đến: {text[:80]}..."

    return f"{context}\n\n{text}"


# ================= 4. METADATA =================

def extract_metadata(text: str) -> dict:

    text_lower = text.lower()

    # simple rules
    if "thuế" in text_lower:
        category = "finance"
    elif "nghỉ phép" in text_lower or "nhân viên" in text_lower:
        category = "hr"
    elif "dữ liệu" in text_lower:
        category = "it"
    else:
        category = "general"

    # entities (very simple)
    entities = re.findall(r'\b[A-Z][A-Z\s]+\b', text)

    return {
        "category": category,
        "entities": entities[:5],
        "language": "vi"
    }


# ================= PIPELINE =================

def enrich_chunks(
    chunks: list[dict],
    methods: list[str] | None = None,
) -> list[EnrichedChunk]:

    if methods is None:
        methods = ["contextual", "hyqa", "metadata"]

    enriched = []

    for chunk in chunks:

        text = chunk["text"]
        meta = chunk.get("metadata", {})

        summary = ""
        questions = []
        enriched_text = text
        auto_meta = {}

        # summary
        if "summary" in methods or "full" in methods:
            summary = summarize_chunk(text)

        # hyqa
        if "hyqa" in methods or "full" in methods:
            questions = generate_hypothesis_questions(text)

        # contextual
        if "contextual" in methods or "full" in methods:
            enriched_text = contextual_prepend(text, meta.get("source", ""))

        # metadata
        if "metadata" in methods or "full" in methods:
            auto_meta = extract_metadata(text)

        enriched.append(EnrichedChunk(
            original_text=text,
            enriched_text=enriched_text,
            summary=summary,
            hypothesis_questions=questions,
            auto_metadata={**meta, **auto_meta},
            method="+".join(methods)
        ))

    return enriched


# ================= TEST =================

if __name__ == "__main__":
    sample = "Nhân viên chính thức được nghỉ phép năm 12 ngày làm việc mỗi năm. Số ngày nghỉ phép tăng thêm theo thâm niên."

    print("=== Enrichment Demo ===\n")

    print("Original:")
    print(sample)

    print("\nSummary:")
    print(summarize_chunk(sample))

    print("\nQuestions:")
    print(generate_hypothesis_questions(sample))

    print("\nContextual:")
    print(contextual_prepend(sample, "Sổ tay nhân viên"))

    print("\nMetadata:")
    print(extract_metadata(sample))