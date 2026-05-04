# Individual Reflection — Lab 18

**Tên:** 2A202600218-Nguyễn Tiến Đạt  
**Module phụ trách:** M2 — Hybrid Search

---

## 1. Đóng góp kỹ thuật

### Module đã implement:
- Hybrid Search (BM25 + Dense)
- Reciprocal Rank Fusion (RRF)

### Các thành phần chính:
- `BM25Search`
- `DenseSearch` (Qdrant)
- `HybridSearch`
- `reciprocal_rank_fusion()`

### Số tests pass:
- 5/5 (M2)

---

## 2. Kiến thức học được

### Khái niệm mới nhất:

- Hybrid Retrieval
- RRF (Reciprocal Rank Fusion)
- Trade-off giữa precision vs recall

---

### Điều bất ngờ nhất:

> Dense search KHÔNG luôn tốt hơn BM25

- BM25 tốt với keyword
- Dense tốt với semantic
→ Kết hợp mới mạnh

---

### Kết nối với bài giảng:

- Slide về:
  - Retrieval pipeline
  - Hybrid search
  - RAG architecture

---

## 3. Khó khăn & Cách giải quyết

### Khó khăn lớn nhất:

- Qdrant API lỗi (`client.search`)
- Version mismatch

---

### Cách giải quyết:

- Debug docs Qdrant
- Sửa lại API call
- Test từng bước

---

### Thời gian debug:

~3–4 giờ

---

## 4. Nếu làm lại

### Sẽ làm khác:

- Test từng module sớm hơn
- Không để lỗi dồn cuối

---

### Module muốn thử thêm:

- Query rewriting
- Better reranking
- Prompt engineering

---

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|--------------|
| Hiểu bài giảng | 4 |
| Code quality | 4 |
| Teamwork | 4 |
| Problem solving | 5 |

---

## 🎯 Reflection cuối

Lab này giúp mình hiểu rõ:

> RAG không chỉ là kỹ thuật — mà là hệ thống nhiều bước

Sai ở 1 bước → fail toàn bộ

---

## 💡 Insight quan trọng nhất

> “Garbage in → garbage out”  
> Retrieval sai → LLM không cứu được

Nhưng:

> Retrieval đúng → LLM vẫn có thể làm sai

➡️ Vì vậy cần:
- Retrieval tốt
- Rerank tốt
- Prompt tốt
