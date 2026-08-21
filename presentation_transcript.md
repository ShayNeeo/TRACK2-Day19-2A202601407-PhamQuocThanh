# Kịch Bản Thuyết Trình Bảo Vệ Lab 19 (Presentation Transcript)

**Học viên:** Pham Quoc Thanh (2A202601407)  
**Thời lượng dự kiến:** 10–12 phút  
**Slide tương ứng:** [`presentation.html`](presentation.html)  

---

### [00:00 – 02:00] Slide 1: Giới thiệu & Tổng quan Kiến trúc

> *"Kính chào Giảng viên và Hội đồng đánh giá. Em là Phạm Quốc Thanh, học viên Cohort A20-K1. Hôm nay em xin phép trình bày báo cáo kỹ thuật và bảo vệ kết quả thực nghiệm bài Lab 19: Kiến trúc Vector Store & Feature Store trong hệ thống AI thời gian thực.*
>
> *Trong bài lab này, mục tiêu của em là giải quyết 2 bài toán lớn trong sản xuất:*
> 1. *Truy xuất thông tin ngữ nghĩa lai (Hybrid Search) kết hợp giữa độ phủ rộng của Vector Store và độ chính xác của BM25.*
> 2. *Xây dựng Feature Store đạt tính đúng đắn Point-in-Time (PIT) để loại bỏ hoàn toàn hiện tượng rò rỉ dữ liệu trong huấn luyện và phục vụ mô hình.*
>
> *Hệ thống đã đạt điểm số tuyệt đối 170/170 điểm trên toàn bộ 8 Notebooks và hoàn thành trọn vẹn Bonus Challenge."*

---

### [02:00 – 05:00] Slide 2: Đột phá với Gemini Embedding 2 & Cơ chế RRF ($k=60$)

> *"Khi bắt đầu với mô hình mặc định `bge-small-en-v1.5`, em quan sát thấy một triệu chứng nghiêm trọng: Precision@10 trên các câu hỏi diễn đạt lại bằng tiếng Việt (`paraphrase`) chỉ đạt vỏn vẹn 33.3%. Nguyên nhân gốc rễ là do không gian vector của mô hình đơn ngữ tiếng Anh không thể ánh xạ được các cấu trúc ngữ nghĩa tiếng Việt phong phú.*
>
> *Em đã tích hợp mô hình **Google Gemini Embedding 2** với không gian vector 3072 chiều thông qua Google AI Studio API, kết hợp cơ chế xoay vòng Multi-API Keys và bộ nhớ đệm SQLite cục bộ. Kết quả là Precision@10 cho nhóm Paraphrase lập tức tăng vọt từ 33.3% lên **91.3%** (+58.0 pp).*
>
> *Đồng thời, em áp dụng thuật toán **Reciprocal Rank Fusion (RRF)** với hằng số $k=60$. Vì điểm BM25 và Cosine Similarity có thang đo hoàn toàn khác biệt, RRF chuyển đổi sang thứ hạng giúp triệt tiêu sự thiên vị và ưu tiên tối đa các tài liệu đạt được sự đồng thuận (consensus) từ cả hai kênh. Kết quả là Hybrid Search đạt 90.8% tổng thể và đánh bại BM25 tới +13.0 pp."*

---

### [05:00 – 07:30] Slide 3: FastAPI Serving & Feast Point-In-Time Correctness

> *"Chuyển sang khía cạnh phục vụ sản xuất (Production Serving):*
> 
> *Với REST API FastAPI, em đã áp dụng cơ chế Pre-warming trong `lifespan` handler và tối ưu hóa bộ nhớ đệm, giúp đạt độ trễ P99 cho chế độ Hybrid là **25.2 ms**, vượt xa yêu cầu SLA dưới 50 ms của đề bài.*
>
> *Về kho đặc trưng Feast Feature Store: Em xây dựng 3 Feature Views đại diện cho 3 chu kỳ biến thiên dữ liệu (30 ngày cho User Profile, 24 giờ cho Item Popularity, và 1 giờ cho Query Velocity). Độ trễ truy vấn Online Lookup chỉ đạt **0.92 ms** trên SQLite. Quan trọng nhất, phép As-Of Join lịch sử đảm bảo tính đúng đắn Point-in-Time, ngăn chặn 100% rủi ro Data Leakage trong quá trình huấn luyện mô hình."*

---

### [07:30 – 09:30] Slide 4: Phân tích Chuyên sâu NB5–NB8 (Recall Cliff & Caching Security)

> *"Tại các nhiệm vụ nâng cao:*
> * Ở bài toán **Filtered Vector Search (NB5)**: Em đã chứng minh bằng số liệu thực nghiệm rằng chiến lược Post-filter (lấy top-K ANN rồi lọc sau) gây ra hiện tượng **Recall Cliff** — khi bộ lọc chỉ chọn 5% tài liệu, Recall sập xuống 0.20. Giải pháp duy nhất là Filtered-ANN đẩy bitset filter trực tiếp vào đồ thị HNSW để bảo toàn Recall 1.00.
> * Ở bài toán **Semantic Cache (NB7)**: Em đã chứng minh rằng nếu bỏ qua bộ lọc Namespace, hệ thống sẽ gặp lỗ hổng rò rỉ dữ liệu chéo Tenant nghiêm trọng. Khi kích hoạt `namespaced=True`, hệ thống cô lập hoàn toàn không gian truy vấn của từng tổ chức.*"

---

### [09:30 – 11:30] Slide 5: Bonus Challenge — Hybrid Personal AI Memory System

> *"Cuối cùng, trong phần Bonus Challenge: Em đã xây dựng POC hoàn chỉnh `HybridMemoryAgent` tại thư mục `bonus/`:*
> * *Tài liệu `ARCHITECTURE.md` dài hơn 850 từ với sơ đồ Mermaid chi tiết, phân tích rõ ràng 3 đánh đổi kiến trúc (Semantic Sentence Chunking 250 từ, Tabular Feast Features, và Multi-tier Freshness).*
> * *Hệ thống xem xét sâu sắc bối cảnh người dùng Việt Nam (song ngữ kỹ thuật Code-Switching) và tuân thủ nghiêm ngặt **Nghị định 13/2023/NĐ-CP** về bảo vệ dữ liệu cá nhân.*
> * *Script `bonus/demo.py` thực thi thành công 5 kịch bản truy vấn mẫu, chứng minh tính khả thi thực tế của kiến trúc.*
>
> *Em xin chân thành cảm ơn Giảng viên đã lắng nghe và rất mong nhận được những nhận xét, phản biện từ Thầy/Cô."*
