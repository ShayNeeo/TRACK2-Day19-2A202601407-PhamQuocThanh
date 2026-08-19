# Reflection — Lab 19

**Tên:** Pham Quoc Thanh
**Cohort:** A20-K1
**Path đã chạy:** lite (Google AI Studio Gemini Embedding 2 3072d)

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

- **Exact (15 queries)**: BM25 (96.7%) và Vector (100.0%) đều tốt; BM25 tối ưu chi phí khi query chứa chính xác từ khoá kỹ thuật.
- **Paraphrase (15 queries)**: Semantic Vector (Gemini Embedding 2) thắng áp đảo (**91.3%** vs 33.3% BM25) nhờ hiểu ngữ nghĩa tiếng Việt đa dạng mà từ khoá không khớp.
- **Mixed (20 queries)**: Hybrid RRF (**99.5%**) cân bằng hoàn hảo giữa neo từ khoá và mở rộng ngữ cảnh.
- **Khi nào KHÔNG dùng hybrid**: 
  1. *Pure BM25*: Khi tìm kiếm mã lỗi cụ thể (e.g. `ERR_403_FORBIDDEN`), mã SKU, tên hàm/API chính xác cần độ trễ < 2ms và zero chi phí embedding.
  2. *Pure Vector*: Khi hệ thống truy vấn đa ngôn ngữ hoàn toàn trừu tượng, tìm kiếm bằng hình ảnh/ý niệm không có từ khoá cố định.

---

## Điều ngạc nhiên nhất khi làm lab này

Hiện tượng **recall cliff** khi dùng post-filter: chỉ cần filter chọn lọc 5% tài liệu, recall của vector search lập tức sập từ 1.0 xuống 0.20 trừ khi over-fetch tới 50% corpus; và rủi ro rò rỉ dữ liệu chéo tenant (cross-tenant leak) nếu semantic cache quên namespace filter.

---

## Bonus challenge

- [x] Đã làm bonus (xem `bonus/`)
- [ ] Pair work với: _Pham Quoc Thanh_

