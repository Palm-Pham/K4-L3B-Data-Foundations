# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** PHAM DINH BAO KHOI
**Nhóm:** Linh Linh
**Ngày:** Sep 20, 2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có hướng gần nhau, nên hai đoạn văn thường có nội dung hoặc ý nghĩa liên quan. Giá trị càng gần 1 thì mức tương đồng ngữ nghĩa càng cao.

**Ví dụ có độ tương tự CAO:**

- Câu A: Tôi muốn đổi trả sản phẩm đã mua trên Shopee.
- Câu B: Chính sách hoàn tiền khi trả hàng trên Shopee là gì?
- Tại sao tương đồng: Cả hai đều đề cập đến quy trình trả hàng và hoàn tiền trên cùng nền tảng.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Tôi muốn đổi trả sản phẩm đã mua trên Shopee.
- Câu B: Hôm nay thời tiết ở Hà Nội như thế nào?
- Tại sao khác: Hai câu nói về hai chủ đề độc lập là thương mại điện tử và thời tiết, không có quan hệ ngữ nghĩa đáng kể.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity đo góc giữa các vector nên tập trung vào hướng ngữ nghĩa và ít bị ảnh hưởng bởi độ dài hoặc độ lớn vector. Khoảng cách Euclid nhạy với độ lớn vector hơn, nên có thể đánh giá sai các embedding cùng nghĩa nhưng có norm khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Bước dịch giữa hai chunk là 500 - 50 = 450 ký tự. Số chunk = ceil((10.000 - 500) / 450) + 1 = ceil(21,11) + 1 = 23.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap = 100, bước dịch còn 400 ký tự nên số chunk là ceil((10.000 - 500) / 400) + 1 = 25. Overlap lớn hơn giúp thông tin ở ranh giới không bị cắt mất ngữ cảnh, đổi lại tạo nhiều chunk hơn, tăng chi phí lưu trữ và embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Hàm dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách sau dấu chấm, chấm than hoặc chấm hỏi khi theo sau là khoảng trắng hoặc xuống dòng. Mỗi câu được `strip()` rồi gom tối đa `max_sentences_per_chunk` câu thành một chunk. Hàm trả về danh sách rỗng cho chuỗi rỗng/chỉ có khoảng trắng và ép số câu tối thiểu mỗi chunk là 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán ưu tiên tách theo các separator có ý nghĩa lớn đến nhỏ: đoạn trống, xuống dòng, kết thúc câu, khoảng trắng, rồi cuối cùng là ký tự. Các mảnh vừa kích thước được ghép lại; mảnh quá dài sẽ được đệ quy tách với separator kế tiếp. Base case là khi đoạn không vượt `chunk_size`; nếu không còn separator phù hợp thì cắt cứng theo từng đoạn dài `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` sao chép metadata, tạo ID riêng cho từng record, sinh embedding từ `content` và lưu vào ChromaDB nếu khả dụng, nếu không thì lưu trong danh sách bộ nhớ. Khi `search`, hệ thống sinh embedding cho query, tính cosine similarity với embedding của từng chunk, sắp xếp giảm dần theo score và trả về top-k. Với ChromaDB, distance được quy đổi thành score bằng `1.0 - distance`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc trước theo metadata rồi mới tính similarity trên tập record còn lại; điều này giảm nhiễu trước khi xếp hạng. `delete_document` xác định mọi chunk có `metadata.doc_id` bằng ID cần xóa và loại chúng khỏi in-memory store, hoặc lấy các ID tương ứng rồi xóa khỏi collection ChromaDB. Hàm trả về `True` khi thực sự có ít nhất một chunk bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm trước hết truy xuất `top_k` chunk liên quan từ vector store, sau đó nối nội dung các chunk bằng hai ký tự xuống dòng để tạo context. Prompt yêu cầu LLM chỉ dùng context để trả lời và nói không biết nếu context không chứa đáp án. Context được đặt trước câu hỏi, sau nhãn `Context:`, rồi kết thúc bằng `Answer:` để định hướng đầu ra.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

 Dán kết quả (output) của: pytest tests/ -v

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
| ------ | ----------- | ----------- | --------- | -------------- | ------- |
| 1 | Tôi muốn trả lại sản phẩm đã mua trên Shopee. | Làm thế nào để yêu cầu hoàn tiền cho đơn hàng Shopee? | cao | 0,870622 | Có |
| 2 | Người bán phải đóng gói hàng hóa đúng quy cách. | Nếu đóng gói sai khiến hàng hư hỏng thì ai chịu trách nhiệm? | cao | 0,832680 | Có |
| 3 | Shopee cấm đăng bán ma túy và vũ khí. | Hôm nay thời tiết ở Hà Nội như thế nào? | thấp | 0,441245 | Có |
| 4 | Chính sách bảo mật giải thích cách Shopee thu thập dữ liệu cá nhân. | Shopee sử dụng thông tin người dùng cho những mục đích nào? | cao | 0,840736 | Có |
| 5 | Đơn hàng của tôi đang được vận chuyển. | Tôi muốn thay đổi mật khẩu tài khoản Shopee. | thấp | 0,476297 | Có |

Ngưỡng phân loại thực nghiệm được sử dụng nhất quán là: điểm cosine từ `0,50` trở lên được xếp loại **cao**, dưới `0,50` được xếp loại **thấp**. Đây không phải là ngưỡng phổ quát cho mọi mô hình embedding hoặc mọi bộ dữ liệu. Các điểm trên được tính bằng Gemini `gemini-embedding-001`; `MockEmbedder` không được sử dụng.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 5 là kết quả bất ngờ nhất vì dù dự đoán đúng là thấp, điểm `0,476297` vẫn gần ngưỡng `0,50` nhất trong năm cặp. Hai câu cùng có thể xuất hiện trong ngữ cảnh hỗ trợ người dùng Shopee, nhưng thể hiện hai mục đích khác nhau là theo dõi vận chuyển và đổi mật khẩu. Kết quả này phù hợp với nhận định rằng embedding có thể phản ánh cả chủ đề chung lẫn mục đích của câu, nhưng một điểm cosine riêng lẻ không đủ để khẳng định nguyên nhân mô hình biểu diễn hai câu theo cách đó.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên corpus `data/ecommerce` bằng chiến lược cá nhân `HeadingStructureChunker`, embedding Gemini thật và `top_k=3`. Kết quả chính áp dụng đúng metadata filter được gợi ý trong báo cáo nhóm; các mâu thuẫn giữa báo cáo nhóm và corpus được giữ nguyên và nêu bên dưới.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| --- | ------- | -------------------------------- | ------- | ----------- | ------------------------ |
| 1 | Người bán cần làm gì để đăng bán đúng quy định trên Shopee? | Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM \| Shopee Trung tâm trợ giúp Xin chào, Shopee có thể giúp gì cho bạn? CHÍNH SÁCH CẤM… (`data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`, `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán`) | 0.813468 | Không | Các đoạn truy xuất không cung cấp đủ thông tin để nêu chi tiết những việc người bán cần làm để đăng bán đúng quy định. |
| 2 | Sản phẩm nào bị Shopee cấm hoặc hạn chế bán? | Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM \| Shopee Trung tâm trợ giúp Xin chào, Shopee có thể giúp gì cho bạn? CHÍNH SÁCH CẤM… (`data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`, `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán`) | 0.875936 | Không | Các đoạn truy xuất không nêu rõ cụ thể từng sản phẩm bị cấm hoặc hạn chế, mà chỉ đề cập đến mục "Chính sách cấm/hạn chế sản phẩm" và danh sách các mặt hàng bị cấm vận. Người bán cần tuân thủ luật pháp và các điều khoản, chính sách của Shopee. |
| 3 | Nếu hàng hóa dễ vỡ hoặc nguy hiểm, Shopee có quy định gì? | Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM \| Shopee Trung tâm trợ giúp Xin chào, Shopee có thể giúp gì cho bạn? CHÍNH SÁCH CẤM… (`data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`, `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán`) | 0.794000 | Không | Các đoạn truy xuất không cung cấp đủ thông tin. |
| 4 | Người mua có thể khiếu nại khi hàng vận chuyển bị hư hỏng không? | Chính sách bảo mật thông tin và dữ liệu cá nhân Shopee > 11. LOẠI TRỪ TRÁCH NHIỆM VỀ NGHĨA VỤ BẢO MẬT VÀ CÁC TRANG WEB BÊN THỨ BA > 14. THẮC MẮC, QUAN NGẠI HOẶC KHIẾU NẠI? LIÊN HỆ… (`data/ecommerce/shopee-chinh-sach-bao-mat.md`, `Chính sách bảo mật thông tin và dữ liệu cá nhân Shopee > 11. LOẠI TRỪ TRÁCH NHIỆM VỀ NGHĨA VỤ BẢO MẬT VÀ CÁC TRANG WEB BÊN THỨ BA > 14. THẮC MẮC, QUAN NGẠI HOẶC KHIẾU NẠI? LIÊN HỆ VỚI CHÚNG TÔI`) | 0.609904 | Không | Các đoạn truy xuất không cung cấp đủ thông tin. |
| 5 | Ai chịu trách nhiệm nếu hàng hóa đóng gói sai quy cách gây hư hỏng? | Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.3 13.3. Người Sử Dụng hiểu rằng Người Bán chịu toàn bộ rủi ro liên quan đến việc vận chuyển hàng hóa được… (`data/ecommerce/shopee-dieu-khoan-dich-vu.md`, `Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.3`) | 0.694197 | Có | Các đoạn truy xuất không cung cấp đủ thông tin. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng không có một chiến lược chunking tốt nhất cho mọi truy vấn: chunk theo câu mạnh với dữ kiện ngắn, còn chunk theo heading hoặc parent-child bảo toàn bối cảnh tốt hơn cho chính sách dài và nhiều điều kiện. Metadata filtering chỉ có ích khi metadata và tài liệu đích đúng với nội dung; filter sai có thể loại bỏ chính chunk chứa bằng chứng.

### Ghi chú đối chiếu Gold Answer với corpus

- Câu 1: Mâu thuẫn: bằng chứng đầy đủ nằm trong file `shopee-chinh-sach-bao-hanh-mall.md` có thân bài về đăng bán, không phải file/category được báo cáo nhóm chỉ ra; filter gợi ý loại mất bằng chứng này.
- Câu 2: Phù hợp: danh sách hàng giả, vũ khí, ma túy, thiết bị giám sát và hóa chất nguy hiểm có trong `shopee-quy-dinh-dang-ban-san-pham.md`.
- Câu 3: Gold Answer không được corpus hỗ trợ đầy đủ; chính sách trả hàng chỉ nêu các trường hợp bể vỡ, không nêu đủ đóng gói đặc biệt, cảnh báo và từ chối vận chuyển.
- Câu 4: Mâu thuẫn: tài liệu/filter `privacy-policy` không liên quan đến hư hỏng vận chuyển; corpus cũng thiếu đầy đủ bộ chứng cứ được nêu trong Gold Answer.
- Câu 5: Gold Answer không được corpus hỗ trợ đầy đủ; file được chỉ ra có thân bài về quy định đăng bán và không nêu Shopee từ chối bồi thường do đóng gói sai.
---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
| ---------- | ------------------- |
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
