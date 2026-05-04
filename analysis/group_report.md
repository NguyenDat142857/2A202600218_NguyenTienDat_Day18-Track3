# Group Report — Lab 18: Production RAG

**Nhóm:** C401  
**Ngày:** [04/05/2025]

---

## Thành viên & Phân công

| Tên | Module | Hoàn thành | Tests pass |
|-----|--------|-----------|-----------|
| Nguyễn Tiến Đạt | M2: Hybrid Search | ✅ | 5/5 |
| [Tên 2] | M1: Chunking | ✅ | 8/8 |
| [Tên 3] | M3: Reranking | ✅ | 5/5 |
| [Tên 4] | M4: Evaluation | ✅ | 4/4 |

---

## Kết quả RAGAS

| Metric | Naive | Production | Δ |
|--------|-------|-----------|---|
| Faithfulness | 0.4205 | 0.0943 | -0.3262 |
| Answer Relevancy | 0.0468 | 0.1982 | +0.1514 |
| Context Precision | 0.0348 | 0.0422 | +0.0074 |
| Context Recall | 0.0312 | 0.0421 | +0.0109 |

---

## 🔍 Phân tích tổng thể

Pipeline production đã:

✅ Cải thiện:
- Retrieval quality (precision, recall)
- Answer relevancy (↑ mạnh)

❌ Nhưng:
- Faithfulness giảm mạnh (~ -0.33)

👉 Đây là trade-off phổ biến:
> “Better retrieval does NOT guarantee better answers”

---

## 🚀 Key Findings

### 1. Biggest improvement

👉 **Answer Relevancy (+0.15)**

- Nhờ:
  - Hybrid Search (BM25 + Dense)
  - RRF fusion
- System hiểu query tốt hơn

---

### 2. Biggest challenge

👉 **Faithfulness giảm mạnh**

Nguyên nhân:
- LLM không extract đúng
- Context noise từ enrichment
- Prompt chưa đủ constraint

---

### 3. Surprise finding

👉 **Enrichment không luôn tốt**

- Tăng recall
- Nhưng giảm precision + faithfulness

➡️ “More data ≠ better data”

---

## 🎤 Presentation Notes (5 phút)

---

### 1. RAGAS scores

- Baseline: stable nhưng yếu
- Production:
  - Retrieval ↑
  - Generation ↓

👉 Highlight trade-off

---

### 2. Biggest win

👉 Hybrid Search (M2)

- BM25 + Dense → capture lexical + semantic
- RRF → combine effectively

---

### 3. Case study

**Question:** Thuế GTGT phải nộp là bao nhiêu?

- Retrieval: ✅ đúng
- Output: ❌ sai

👉 Issue = Answer generation

---

### 4. Next optimization

Nếu có thêm 1 giờ:

1. Prompt engineering
2. Answer extraction logic
3. Reduce noise (enrichment)
4. Improve reranking

---

## 🧠 Final Conclusion

> Production RAG không chỉ là “tìm đúng”  
> mà cần “trả lời đúng và chính xác”.
