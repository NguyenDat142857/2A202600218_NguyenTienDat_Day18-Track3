# RETRIEVAL-AUGMENTED GENERATION (RAG) TRONG AI

## Tổng quan

RAG (Retrieval-Augmented Generation) là phương pháp kết hợp:
- Truy xuất dữ liệu (retrieval)
- Sinh văn bản (generation)

---

## Tại sao cần RAG?

Các mô hình LLM có hạn chế:
- Không biết thông tin mới
- Dễ hallucination

RAG giúp:
- Tăng độ chính xác
- Giảm sai lệch thông tin

---

## Quy trình hoạt động

### Bước 1: Chunking
- Chia tài liệu thành các đoạn nhỏ

### Bước 2: Embedding
- Chuyển text thành vector

### Bước 3: Vector Search
- Tìm các đoạn liên quan

### Bước 4: Reranking
- Sắp xếp lại kết quả

### Bước 5: Generation
- LLM sinh câu trả lời

---

## Các thành phần chính

### Chunking
- Quyết định chất lượng retrieval

### Embedding
- Biểu diễn semantic của dữ liệu

### Vector Database
- Lưu trữ embedding

### Reranker
- Cải thiện độ chính xác

---

## Ưu điểm

- Truy xuất thông tin chính xác  
- Linh hoạt với dữ liệu mới  
- Dễ mở rộng  

---

## Nhược điểm

- Phụ thuộc vào chất lượng chunking  
- Cần tối ưu nhiều bước  

---

## Ứng dụng

- Chatbot  
- Hỏi đáp tài liệu  
- Trợ lý AI doanh nghiệp  

---

## Kết luận

RAG là một kiến trúc quan trọng trong AI hiện đại, giúp kết hợp:
👉 Tri thức bên ngoài  
👉 Khả năng sinh ngôn ngữ của LLM  

Từ đó tạo ra hệ thống thông minh và đáng tin cậy hơn.