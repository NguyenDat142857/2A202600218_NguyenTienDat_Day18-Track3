# Failure Analysis — Lab 18: Production RAG

**Nhóm:** RAG Masters  
**Thành viên:** 2A202600218-Nguyễn Tiến Đạt (M2) · [Tên 2 → M1] · [Tên 3 → M3] · [Tên 4 → M4]

---

## RAGAS Scores

| Metric | Naive Baseline | Production | Δ |
|--------|---------------|------------|---|
| Faithfulness | 0.4205 | 0.0943 | -0.3262 |
| Answer Relevancy | 0.0468 | 0.1982 | +0.1514 |
| Context Precision | 0.0348 | 0.0422 | +0.0074 |
| Context Recall | 0.0312 | 0.0421 | +0.0109 |

---

## 🔍 Tổng quan

Pipeline production **có cải thiện rõ về retrieval (precision/recall, relevancy)** nhưng **faithfulness giảm mạnh**.

👉 Điều này cho thấy:
- Hệ thống **tìm đúng context tốt hơn**
- Nhưng **trả lời sai hoặc hallucinate nhiều hơn**

➡️ Đây là lỗi classic trong RAG:
> Retrieval tốt nhưng Generation kém

---

## Bottom-5 Failures

---

### #1

- **Question:** Thuế GTGT phải nộp là bao nhiêu?  
- **Expected:** Giá trị cụ thể (số tiền)  
- **Got:** Một đoạn mô tả về thuế GTGT nhưng không có con số  
- **Worst metric:** Faithfulness  

#### 🔍 Error Tree:
- Output đúng? → ❌ Sai (không trả lời đúng số)
- Context đúng? → ✅ Có thông tin đúng trong context
- Query OK? → ✅ Không cần rewrite

#### 🎯 Root cause:
- LLM **không extract đúng thông tin số**
- Context có nhưng bị “nhiễu” (multiple numbers)

#### 💡 Suggested fix:
- Dùng **structured extraction prompt**
- Hoặc regex post-processing để lấy số

---

### #2

- **Question:** Nghị định 13 được ban hành vào ngày nào?  
- **Expected:** 17/04/2023  
- **Got:** Một đoạn mô tả về nghị định nhưng không có ngày  

#### Error Tree:
- Output đúng? → ❌  
- Context đúng? → ✅  
- Query OK? → ✅  

#### Root cause:
- LLM **trả lời chung chung thay vì extract fact**

#### Fix:
- Prompt dạng:
  > "Trả lời CHỈ bằng ngày tháng, không giải thích"

---

### #3

- **Question:** Embedding dùng để làm gì?  
- **Expected:** Biểu diễn text thành vector  
- **Got:** Câu trả lời chung chung về AI  

#### Error Tree:
- Output đúng? → ❌  
- Context đúng? → ⚠️ Có nhưng không top-1  
- Query OK? → ❌  

#### Root cause:
- Hybrid search chưa đủ mạnh
- Reranker chưa phân biệt tốt semantic intent

#### Fix:
- Increase `top_k` trước rerank
- Improve embedding model

---

### #4

- **Question:** Vector database dùng để làm gì?  
- **Expected:** Lưu trữ vector và tìm kiếm similarity  
- **Got:** Câu trả lời lan man  

#### Error Tree:
- Output đúng? → ❌  
- Context đúng? → ⚠️ Partial  
- Query OK? → ❌  

#### Root cause:
- Context retrieval bị noise
- Enrichment làm tăng nhiễu

#### Fix:
- Giảm aggressive enrichment
- Filter metadata

---

### #5

- **Question:** RAG giúp cải thiện điều gì?  
- **Expected:** Giảm hallucination, tăng accuracy  
- **Got:** Câu trả lời không liên quan  

#### Error Tree:
- Output đúng? → ❌  
- Context đúng? → ❌  
- Query OK? → ❌  

#### Root cause:
- Query không match document domain
- Retrieval fail hoàn toàn

#### Fix:
- Query expansion / rewrite
- Add fallback logic

---

## 🎯 Case Study (cho presentation)

### Question chọn phân tích:
**"Thuế GTGT phải nộp là bao nhiêu?"**

---

### 🔍 Error Tree walkthrough:

1. Output đúng? → ❌  
   → Không có số cụ thể  

2. Context đúng? → ✅  
   → Có thông tin đúng nhưng bị buried  

3. Query rewrite OK? → ✅  
   → Query rõ ràng  

4. Fix ở bước:
👉 **Answer generation**

---

### 💡 Insight quan trọng

> RAG không fail ở retrieval — mà fail ở extraction

---

## ⏱️ Nếu có thêm 1 giờ, sẽ optimize:

1. **Improve Prompt Engineering**
   - Structured answer format
   - Force extract answers

2. **Add Post-processing**
   - Regex extract numbers
   - Clean answer

3. **Better Reranker**
   - Increase top_k → rerank → top3

4. **Reduce Noise**
   - Limit enrichment methods

---

## 🧠 Key Lesson

> “RAG tốt không phải chỉ là tìm đúng — mà là trả lời đúng.”
