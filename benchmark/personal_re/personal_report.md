# Gemini Similarity Predictions — Individual Experiment

## Objective

Evaluate the five supplied high/low predictions using actual Gemini sentence embeddings and a consistent cosine threshold. Sentence wording and predictions are unchanged; the Vietnamese example sentences in the reference report are not substituted.

## Sources reviewed and domain alignment

- `src/embeddings.py`
- `src/chunking.py`
- `report/REPORT_CANHAN.md`
- `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`
- `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`
- `data/ecommerce/shopee-chinh-sach-bao-mat.md`
- `data/ecommerce/shopee-dieu-khoan-dich-vu.md`

The ecommerce file inventory was reviewed. Return/refund clauses 1.1–1.2 align with pair 1; the product-listing rules discuss packaging and prohibited weapons/drugs (sections 4.5–4.6 and food-packaging requirements), aligning with pairs 2–3; the privacy policy covers collection and use of personal information (sections 4 and 6), aligning with pair 4; terms sections 5 and 13 cover account security and transport, aligning with pair 5. These are domain-aligned experimental sentences, not claimed verbatim quotations or independently verified policy advice. The weather sentence is an intentional unrelated control.

## Configuration and method

`load_dotenv(ROOT / ".env", override=False)` loads repository configuration while respecting existing environment values. `GeminiEmbedder` accepts `GEMINI_API_KEY` or `GOOGLE_API_KEY`; credentials are never serialized. The model is explicitly taken from `src.embeddings.GEMINI_EMBEDDING_MODEL`: **`gemini-embedding-001`**.

Observed vector dimensions: **[3072]**. Task type and output dimensionality use the existing wrapper/API defaults; no explicit task type is sent. **MockEmbedder was not used.** There were 10 API calls and 0 cached sentence reuses in this run; successful vectors are cached per exact sentence and model/configuration. No chunking or retrieval is involved.

`src.chunking.compute_similarity` computes cosine as dot(A, B) / (sqrt(dot(A, A)) × sqrt(dot(B, B))). Vectors must have equal dimensions, finite values and nonzero norms before use. Classification uses the full-precision score: **high ≥ 0.50; low < 0.50**; displayed scores use six decimals. This threshold is an empirical convention for these five pairs, not a universal embedding threshold.

## Results

Correct predictions: **5/5**.

| Pair | Sentence A | Sentence B | Prediction | Actual Score | Actual Classification | Correct? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | I want to return a product bought on Shopee. | How can I request a refund for a Shopee order? | high | 0.870622 | high | Yes |
| 2 | The seller must properly package the goods. | If improper packaging causes damage to the goods, who is responsible? | high | 0.832680 | high | Yes |
| 3 | Shopee prohibits the listing and sale of drugs and weapons. | What is the weather like in Hanoi today? | low | 0.441245 | low | Yes |
| 4 | The privacy policy explains how Shopee collects personal data. | What purposes does Shopee use user information for? | high | 0.840736 | high | Yes |
| 5 | My order is currently being shipped. | I want to change my Shopee account password. | low | 0.476297 | low | Yes |

## Per-pair interpretation

**Pair 1:** Both sentences concern Shopee post-purchase remedies: returning goods and requesting a refund. Their intents are related, though a return and a refund are not identical actions. The measured cosine 0.870622 is at or above 0.50, so it is classified as high; the initial prediction is correct.

**Pair 2:** Both sentences concern packaging goods; the second asks about responsibility when packaging is improper. This connects a general duty with a possible consequence, rather than expressing the same proposition. The measured cosine 0.832680 is at or above 0.50, so it is classified as high; the initial prediction is correct.

**Pair 3:** The first sentence concerns prohibited e-commerce listings, while the second asks about weather. They differ in both subject matter and communicative purpose. The measured cosine 0.441245 is below 0.50, so it is classified as low; the initial prediction is correct.

**Pair 4:** Both sentences concern Shopee personal-information practices. Data collection and the purposes of using data are related aspects of privacy, but are distinct questions. The measured cosine 0.840736 is at or above 0.50, so it is classified as high; the initial prediction is correct.

**Pair 5:** Both could occur in an e-commerce support conversation, but shipment status and changing an account password are different user intents. The measured cosine 0.476297 is below 0.50, so it is classified as low; the initial prediction is correct.

## Most unexpected result

All five predictions were correct; pair 5 was the most unexpected because its score of 0.476297 was closest to the 0.50 threshold (distance 0.023703). Shipment status and password changes share a possible support setting but express different user goals. This observation is consistent with embeddings reflecting overlapping topics and intents, but one cosine score does not establish why the model represented the sentences that way.

## Copyable section 4

```markdown
## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Model: `gemini-embedding-001`; dimensions: [3072]; Gemini API, no MockEmbedder. Cosine = dot(A, B) / (norm(A) × norm(B)); high if cosine ≥ 0.50, otherwise low. This empirical threshold depends on the model and dataset. The supplied English sentences were embedded unchanged.

| Pair | Sentence A | Sentence B | Prediction | Actual Score | Actual Classification | Correct? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | I want to return a product bought on Shopee. | How can I request a refund for a Shopee order? | high | 0.870622 | high | Yes |
| 2 | The seller must properly package the goods. | If improper packaging causes damage to the goods, who is responsible? | high | 0.832680 | high | Yes |
| 3 | Shopee prohibits the listing and sale of drugs and weapons. | What is the weather like in Hanoi today? | low | 0.441245 | low | Yes |
| 4 | The privacy policy explains how Shopee collects personal data. | What purposes does Shopee use user information for? | high | 0.840736 | high | Yes |
| 5 | My order is currently being shipped. | I want to change my Shopee account password. | low | 0.476297 | low | Yes |

Correct predictions: **5/5**.

**Pair 1:** Both sentences concern Shopee post-purchase remedies: returning goods and requesting a refund. Their intents are related, though a return and a refund are not identical actions. The measured cosine 0.870622 is at or above 0.50, so it is classified as high; the initial prediction is correct.

**Pair 2:** Both sentences concern packaging goods; the second asks about responsibility when packaging is improper. This connects a general duty with a possible consequence, rather than expressing the same proposition. The measured cosine 0.832680 is at or above 0.50, so it is classified as high; the initial prediction is correct.

**Pair 3:** The first sentence concerns prohibited e-commerce listings, while the second asks about weather. They differ in both subject matter and communicative purpose. The measured cosine 0.441245 is below 0.50, so it is classified as low; the initial prediction is correct.

**Pair 4:** Both sentences concern Shopee personal-information practices. Data collection and the purposes of using data are related aspects of privacy, but are distinct questions. The measured cosine 0.840736 is at or above 0.50, so it is classified as high; the initial prediction is correct.

**Pair 5:** Both could occur in an e-commerce support conversation, but shipment status and changing an account password are different user intents. The measured cosine 0.476297 is below 0.50, so it is classified as low; the initial prediction is correct.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

All five predictions were correct; pair 5 was the most unexpected because its score of 0.476297 was closest to the 0.50 threshold (distance 0.023703). Shipment status and password changes share a possible support setting but express different user goals. This observation is consistent with embeddings reflecting overlapping topics and intents, but one cosine score does not establish why the model represented the sentences that way.
```

## Files created

- `benchmark/personal_re/run_similarity.py`
- `benchmark/personal_re/embeddings_cache.json`
- `benchmark/personal_re/similarity_results.json`
- `benchmark/personal_re/verification.json`
- `benchmark/personal_re/personal_report.md`

## Steps and verification

1. Read the existing embedder, cosine function, report template and relevant corpus excerpts.
2. Load configuration without exposing credentials; initialize the declared Gemini model.
3. Embed ten unique sentences, saving successful responses to avoid duplicate requests.
4. Validate vectors, compute cosine scores and evaluate predictions with the fixed threshold.
5. Select the most unexpected pair (incorrect predictions first; otherwise nearest threshold), and write the report and copyable snippet.
6. Check protected file hashes, output locations and sensitive values.

- all_5_pairs_have_valid_embeddings: `True`
- all_10_sentence_embeddings_present: `True`
- same_dimensionality: `True`
- all_5_cosines_finite_and_in_range: `True`
- exactly_5_result_rows: `True`
- unexpected_analysis_sentence_count: `3`
- protected_files_unchanged: `True`
- all_created_files_within_benchmark_personal_re: `True`
- sensitive_value_scan_passed: `True`
- method_checks: `{'identical_vectors': True, 'orthogonal_vectors': True, 'opposite_vectors': True}`

## Limitations

Only five hand-selected English pairs are evaluated, so this is not a representative accuracy estimate for Vietnamese policy retrieval. The threshold depends on model, dataset, language and embedding configuration; scores are neither probabilities nor proof of equivalence, contradiction or policy correctness. Related sentences can have different intents, and shared platform vocabulary can influence similarity without making requests equivalent. API model behavior may change; the timestamp and saved vectors preserve this run. Per-pair explanations are semantic interpretations of the observations, not causal explanations of model internals.

Reproduce without unnecessary requests: `python -B benchmark/personal_re/run_similarity.py` (valid cached vectors are reused). Source files, corpus files and `REPORT_CANHAN.md` were not edited.
<!-- COMPETITION_RESULTS_START -->
# Competition Results — Phạm Đình Bảo Khôi

## Phương pháp và cấu hình

- Chiến lược cá nhân lấy từ `REPORT_NHOM.md`: `HeadingStructureChunker`; giới hạn 1000 ký tự, giữ heading path và tách cấu trúc trước khi fallback theo đoạn/câu.
- Corpus: 6 file Markdown trong `data/ecommerce`, tổng 345 chunk trong một index.
- Embedding: Gemini `gemini-embedding-001`, chiều vector 3072; không dùng `MockEmbedder`.
- Xếp hạng: cosine similarity từ `src.chunking.compute_similarity`, `top_k=3`; score hiển thị 6 chữ số thập phân.
- Agent: Gemini `gemini-flash-lite-latest`, nhiệt độ 0, chỉ được trả lời từ top-3.
- Cấu hình được nạp bằng `load_dotenv(ROOT / '.env', override=False)` và chấp nhận `GEMINI_API_KEY` hoặc `GOOGLE_API_KEY`; key không được ghi ra output.
- Kết quả chính dùng đúng filter gợi ý của báo cáo nhóm. `competition_results.json` còn lưu top-3 không lọc để chẩn đoán tác động của filter.

## Mục 5 hoàn chỉnh

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

## Chi tiết top-3

### Câu 1. Người bán cần làm gì để đăng bán đúng quy định trên Shopee?

- Gold Answer: Người bán phải đảm bảo tên sản phẩm, hình ảnh, mô tả, danh mục ngành hàng, nguồn gốc và bảo hành phù hợp; không được sử dụng hình ảnh sai, mô tả sai hoặc vi phạm pháp luật.
- Vị trí được báo cáo nhóm chỉ ra: shopee-quy-dinh-dang-ban-san-pham.md — Mục Quy định chung / Tiêu chuẩn đăng bán
- Filter dùng cho kết quả chính: `{"audience": "seller", "category": "seller-rules"}`
- Top-3 có chunk liên quan: **Không**. Top-3 thiếu bằng chứng cho: tên sản phẩm, hình ảnh sản phẩm, mô tả sản phẩm, danh mục ngành hàng, nguồn gốc, bảo hành.
- Agent: Các đoạn truy xuất không cung cấp đủ thông tin để nêu chi tiết những việc người bán cần làm để đăng bán đúng quy định.

**Hạng 1 — cosine 0.813468; không liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán`; chunk: `shopee-quy-dinh-dang-ban-san-pham:c5a3f994f9eb2634c1d60911`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán
> 
> CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM | Shopee Trung tâm trợ giúp
> Xin chào, Shopee có thể giúp gì cho bạn?
> CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 2 — cosine 0.812795; không liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 1. ĐỐI TƯỢNG ÁP DỤNG`; chunk: `shopee-quy-dinh-dang-ban-san-pham:fa1186c741f7f1ffd5d1b658`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 1. ĐỐI TƯỢNG ÁP DỤNG
> 
> Chính sách này áp dụng đối với tất cả Người Bán trên Sàn TMĐT Shopee (“Sàn Shopee”).

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 3 — cosine 0.807262; không liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 2. PHẠM VI ÁP DỤNG`; chunk: `shopee-quy-dinh-dang-ban-san-pham:0e0352f07a94b897a70a153f`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 2. PHẠM VI ÁP DỤNG
> 
> Chính sách này áp dụng đối với việc đăng bán sản phẩm, hàng hóa, dịch vụ trên Sàn Shopee. Mỗi khi đăng bán sản phẩm, Người Bán có trách nhiệm đảm bảo hàng hóa của mình tuân thủ Luật pháp hiện hành đồng thời không vi phạm các Điều Khoản Sử Dụng và Chính Sách Shopee. Vui lòng đọc kỹ các hướng dẫn dưới đây về Chính Sách Cấm/Hạn Chế Sản Phẩm mua bán trên Shopee.
> Danh sách có thể sẽ thay đổi dựa theo tình hình thực tế, vui lòng cập nhật thường xuyên để đảm bảo hàng hóa của bạn không vi phạm Chính Sách Shopee.

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

### Câu 2. Sản phẩm nào bị Shopee cấm hoặc hạn chế bán?

- Gold Answer: Các nhóm hàng như vũ khí, chất nguy hiểm, ma túy, thiết bị giám sát, nội dung nhạy cảm, hàng giả và các mặt hàng vi phạm pháp luật hoặc quyền sở hữu trí tuệ.
- Vị trí được báo cáo nhóm chỉ ra: shopee-quy-dinh-dang-ban-san-pham.md — Danh mục hàng hóa cấm kinh doanh
- Filter dùng cho kết quả chính: `{"audience": "seller", "category": "seller-rules"}`
- Top-3 có chunk liên quan: **Có**. Top-3 thiếu bằng chứng cho: vũ khí, ma túy, thiết bị giám sát, hàng giả.
- Agent: Các đoạn truy xuất không nêu rõ cụ thể từng sản phẩm bị cấm hoặc hạn chế, mà chỉ đề cập đến mục "Chính sách cấm/hạn chế sản phẩm" và danh sách các mặt hàng bị cấm vận. Người bán cần tuân thủ luật pháp và các điều khoản, chính sách của Shopee.

**Hạng 1 — cosine 0.875936; không liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán`; chunk: `shopee-quy-dinh-dang-ban-san-pham:c5a3f994f9eb2634c1d60911`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán
> 
> CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM | Shopee Trung tâm trợ giúp
> Xin chào, Shopee có thể giúp gì cho bạn?
> CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 2 — cosine 0.832525; không liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 2. PHẠM VI ÁP DỤNG`; chunk: `shopee-quy-dinh-dang-ban-san-pham:0e0352f07a94b897a70a153f`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 2. PHẠM VI ÁP DỤNG
> 
> Chính sách này áp dụng đối với việc đăng bán sản phẩm, hàng hóa, dịch vụ trên Sàn Shopee. Mỗi khi đăng bán sản phẩm, Người Bán có trách nhiệm đảm bảo hàng hóa của mình tuân thủ Luật pháp hiện hành đồng thời không vi phạm các Điều Khoản Sử Dụng và Chính Sách Shopee. Vui lòng đọc kỹ các hướng dẫn dưới đây về Chính Sách Cấm/Hạn Chế Sản Phẩm mua bán trên Shopee.
> Danh sách có thể sẽ thay đổi dựa theo tình hình thực tế, vui lòng cập nhật thường xuyên để đảm bảo hàng hóa của bạn không vi phạm Chính Sách Shopee.

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 3 — cosine 0.819915; liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 3. HÀNH VI VI PHẠM VÀ BIỆN PHÁP XỬ LÝ > 4. DANH SÁCH SẢN PHẨM BỊ CẤM/HẠN CHẾ MUA BÁN TRÊN SHOPEE > 4.20`; chunk: `shopee-quy-dinh-dang-ban-san-pham:ba6bc579fec53dc0e2ad5163`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 3. HÀNH VI VI PHẠM VÀ BIỆN PHÁP XỬ LÝ > 4. DANH SÁCH SẢN PHẨM BỊ CẤM/HẠN CHẾ MUA BÁN TRÊN SHOPEE > 4.20
> 
> 4.20. Các mặt hàng bị cấm vận

Đánh giá: Nội dung hỗ trợ mệnh đề Gold Answer: mặt hàng bị cấm vận.

### Câu 3. Nếu hàng hóa dễ vỡ hoặc nguy hiểm, Shopee có quy định gì?

- Gold Answer: Hàng dễ vỡ, hàng hóa nguy hiểm hoặc có rủi ro vận chuyển cao cần đóng gói đặc biệt, có cảnh báo rõ ràng và có thể bị từ chối vận chuyển nếu không đủ điều kiện.
- Vị trí được báo cáo nhóm chỉ ra: shopee-chinh-sach-doi-tra-hoan-tien.md — Điều kiện & Thời hạn trả hàng
- Filter dùng cho kết quả chính: `null`
- Top-3 có chunk liên quan: **Không**. Top-3 thiếu bằng chứng cho: đóng gói đặc biệt, cảnh báo rõ ràng, từ chối vận chuyển.
- Agent: Các đoạn truy xuất không cung cấp đủ thông tin.

**Hạng 1 — cosine 0.794000; không liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán`; chunk: `shopee-quy-dinh-dang-ban-san-pham:c5a3f994f9eb2634c1d60911`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán
> 
> CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM | Shopee Trung tâm trợ giúp
> Xin chào, Shopee có thể giúp gì cho bạn?
> CHÍNH SÁCH CẤM/HẠN CHẾ SẢN PHẨM

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 2 — cosine 0.778283; không liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 3. HÀNH VI VI PHẠM VÀ BIỆN PHÁP XỬ LÝ > 4. DANH SÁCH SẢN PHẨM BỊ CẤM/HẠN CHẾ MUA BÁN TRÊN SHOPEE > 4.10`; chunk: `shopee-quy-dinh-dang-ban-san-pham:57e9d01d3ecea7074fc36306`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 3. HÀNH VI VI PHẠM VÀ BIỆN PHÁP XỬ LÝ > 4. DANH SÁCH SẢN PHẨM BỊ CẤM/HẠN CHẾ MUA BÁN TRÊN SHOPEE > 4.10
> 
> 4.10. Các loại hóa chất nguy hiểm và dễ gây cháy, nổ
> a. Các loại pháo: Pháo nổ, pháo hoa, pháo đập, giàn phun viên, pháo khói, đạn đập làm bằng thuốc pháo hoặc bằng các loại vật liệu khác có thể gây cháy, bỏng…
> b. Các hóa chất liên quan đến chế tạo chất nổ sẽ cấm bán: Natri Clora, Kali Clorat, Kali Perclorat, NH4NO3, NaNO3, CH3NO2, KNO3, NaClO3, KClO3, KClO4, Hexogen, Trinitrotoluen, Octogen, Pentrit…
> c. Xăng, dầu, gas
> d. Bật lửa
> e. Thuốc trừ sâu

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 3 — cosine 0.764190; không liên quan**

Nguồn: `data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md`; heading: `Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 2. PHẠM VI ÁP DỤNG`; chunk: `shopee-quy-dinh-dang-ban-san-pham:0e0352f07a94b897a70a153f`.

> Quy định về đăng bán sản phẩm và tiêu chuẩn dành cho Người bán > 2. PHẠM VI ÁP DỤNG
> 
> Chính sách này áp dụng đối với việc đăng bán sản phẩm, hàng hóa, dịch vụ trên Sàn Shopee. Mỗi khi đăng bán sản phẩm, Người Bán có trách nhiệm đảm bảo hàng hóa của mình tuân thủ Luật pháp hiện hành đồng thời không vi phạm các Điều Khoản Sử Dụng và Chính Sách Shopee. Vui lòng đọc kỹ các hướng dẫn dưới đây về Chính Sách Cấm/Hạn Chế Sản Phẩm mua bán trên Shopee.
> Danh sách có thể sẽ thay đổi dựa theo tình hình thực tế, vui lòng cập nhật thường xuyên để đảm bảo hàng hóa của bạn không vi phạm Chính Sách Shopee.

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

### Câu 4. Người mua có thể khiếu nại khi hàng vận chuyển bị hư hỏng không?

- Gold Answer: Có, người mua hoặc người bán có thể gửi khiếu nại trong thời hạn quy định và cần cung cấp hình ảnh/video, biên bản đồng kiểm, hóa đơn và bằng chứng liên quan.
- Vị trí được báo cáo nhóm chỉ ra: shopee-chinh-sach-bao-mat.md — Thu thập, sử dụng và chia sẻ thông tin
- Filter dùng cho kết quả chính: `{"category": "privacy-policy"}`
- Top-3 có chunk liên quan: **Không**. Top-3 thiếu bằng chứng cho: hư hỏng, hình ảnh, video, biên bản đồng kiểm, hóa đơn.
- Agent: Các đoạn truy xuất không cung cấp đủ thông tin.

**Hạng 1 — cosine 0.609904; không liên quan**

Nguồn: `data/ecommerce/shopee-chinh-sach-bao-mat.md`; heading: `Chính sách bảo mật thông tin và dữ liệu cá nhân Shopee > 11. LOẠI TRỪ TRÁCH NHIỆM VỀ NGHĨA VỤ BẢO MẬT VÀ CÁC TRANG WEB BÊN THỨ BA > 14. THẮC MẮC, QUAN NGẠI HOẶC KHIẾU NẠI? LIÊN HỆ VỚI CHÚNG TÔI`; chunk: `shopee-chinh-sach-bao-mat:c28647b27ad9e56c98f1eff5`.

> Chính sách bảo mật thông tin và dữ liệu cá nhân Shopee > 11. LOẠI TRỪ TRÁCH NHIỆM VỀ NGHĨA VỤ BẢO MẬT VÀ CÁC TRANG WEB BÊN THỨ BA > 14. THẮC MẮC, QUAN NGẠI HOẶC KHIẾU NẠI? LIÊN HỆ VỚI CHÚNG TÔI
> 
> Nếu bạn có bất kỳ thắc mắc, yêu cầu bảo vệ hoặc khiếu nại nào về các phương pháp bảo vệ quyền riêng tư của chúng tôi vui lòng liên hệ với chúng tôi theo thông tin sau:
> CÔNG TY TNHH SHOPEE
> Địa chỉ: Tầng 4-5-6, Tòa nhà Capital Place, số 29 đường Liễu Giai, Phường Ngọc Hà, Thành phố Hà Nội, Việt Nam
> Email: dpo.vn@shopee.com hoặc tại ĐÂY.
> Chính sách này được cập nhật vào ngày 04/6/2026 và có hiệu lực sau 07 (bảy) ngày kể từ ngày đăng tải. Để tham khảo phiên bản trước của Chính sách Bảo mật, vui lòng bấm vào ĐÂY.
> Bạn có hài lòng với bài viết này?
> Hài lòng
> Không hài lòng

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 2 — cosine 0.605861; không liên quan**

Nguồn: `data/ecommerce/shopee-chinh-sach-bao-mat.md`; heading: `Chính sách bảo mật thông tin và dữ liệu cá nhân Shopee > 5. COOKIES > 6. CHÚNG TÔI SỬ DỤNG THÔNG TIN BẠN CUNG CẤP CHO CHÚNG TÔI NHƯ THẾ NÀO? > 6.2`; chunk: `shopee-chinh-sach-bao-mat:46e46deaebe5d5655b6b6d2f`.

> Chính sách bảo mật thông tin và dữ liệu cá nhân Shopee > 5. COOKIES > 6. CHÚNG TÔI SỬ DỤNG THÔNG TIN BẠN CUNG CẤP CHO CHÚNG TÔI NHƯ THẾ NÀO? > 6.2
> 
> (d) phản hồi bất kỳ khiếu nại nào du cho là nguy cơ hoặc đang xảy ra trên thực tế để chống lại Shopee hoặc các chi nhánh có liên quan hoặc khiếu nại khác rằng bất kỳ Nội dung nào vi phạm quyền của bên thứ ba; (e) đáp ứng các yêu cầu của bạn về dịch vụ khách hàng; hoặc (f) bảo vệ quyền, tài sản hoặc sự an toàn cá nhân của Shopee hoặc các chi nhánh có liên quan, người dùng và / hoặc công chúng.

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 3 — cosine 0.585625; không liên quan**

Nguồn: `data/ecommerce/shopee-chinh-sach-bao-mat.md`; heading: `Chính sách bảo mật thông tin và dữ liệu cá nhân Shopee > 11. LOẠI TRỪ TRÁCH NHIỆM VỀ NGHĨA VỤ BẢO MẬT VÀ CÁC TRANG WEB BÊN THỨ BA > 11.3`; chunk: `shopee-chinh-sach-bao-mat:965ea9e362f52a52005c0823`.

> Chính sách bảo mật thông tin và dữ liệu cá nhân Shopee > 11. LOẠI TRỪ TRÁCH NHIỆM VỀ NGHĨA VỤ BẢO MẬT VÀ CÁC TRANG WEB BÊN THỨ BA > 11.3
> 
> 11.3. Do đó chúng tôi không chịu trách nhiệm hay trách nhiệm pháp lý đối với nội dung, các biện pháp bảo mật (hoặc sự thiếu biện pháp bảo mật) và các hoạt động của các trang web/ứng dụng/dịch vụ được liên kết này. Những trang web/ứng dụng/dịch vụ được liên kết này chỉ vì sự thuận tiện cho bạn và do đó bạn tự chịu trách nhiệm khi truy cập chúng. Tuy nhiên, chúng tôi tìm cách bảo vệ tính toàn vẹn của Nền tảng của chúng tôi và các liên kết được đặt trên từng trang web đó và do đó chúng tôi hoan nghênh ý kiến phản hồi về các trang web được liên kết này (bao gồm nếu một trang web cụ thể không hoạt động).

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

### Câu 5. Ai chịu trách nhiệm nếu hàng hóa đóng gói sai quy cách gây hư hỏng?

- Gold Answer: Người bán chịu trách nhiệm về đóng gói sai quy cách; Shopee có thể từ chối bồi thường nếu nguyên nhân do lỗi đóng gói của người bán.
- Vị trí được báo cáo nhóm chỉ ra: shopee-chinh-sach-bao-hanh-mall.md — Quy trình & Điều kiện tiếp nhận bảo hành Shopee Mall
- Filter dùng cho kết quả chính: `null`
- Top-3 có chunk liên quan: **Có**. Top-3 thiếu bằng chứng cho: đóng gói sai, từ chối bồi thường.
- Agent: Các đoạn truy xuất không cung cấp đủ thông tin.

**Hạng 1 — cosine 0.694197; liên quan**

Nguồn: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; heading: `Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.3`; chunk: `shopee-dieu-khoan-dich-vu:a131b7dc41ebbdf40035fa5c`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.3
> 
> 13.3. Người Sử Dụng hiểu rằng Người Bán chịu toàn bộ rủi ro liên quan đến việc vận chuyển hàng hóa được mua và bảo đảm rằng Người Bán đã hoặc sẽ mua bảo hiểm hàng hóa, bao gồm cả việc vận chuyển. Trong trường hợp hàng hóa được mua bị hư hỏng, thất lạc hoặc không chuyển phát được trong quá trình vận chuyển, Người Sử Dụng thừa nhận và đồng ý rằng Shopee sẽ không chịu trách nhiệm đối với bất kỳ tổn thất, chi phí, phí tổn hoặc bất kỳ khoản phí nào phát sinh từ sự cố đó.

Đánh giá: Nội dung hỗ trợ mệnh đề Gold Answer: Người Bán chịu rủi ro vận chuyển và Shopee không chịu trách nhiệm khi hàng hư hỏng.

**Hạng 2 — cosine 0.675304; không liên quan**

Nguồn: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; heading: `Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.3. Lý do Trả hàng/Hoàn tiền`; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:61f618999cceabd24e81561a`.

> Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.3. Lý do Trả hàng/Hoàn tiền
> 
> | Hàng bể vỡ – rò rỉ chất lỏng | Sản phẩm có chứa chất lỏng và đã bị rò rỉ do bể vỡ bao bì sản phẩm trong quá trình vận chuyển. | Tất cả sản phẩm. |
> | Hàng bể vỡ – thùng hàng không nguyên vẹn | Bao bì của nhà sản xuất bị hư hại, ảnh hưởng đến chất lượng/giá trị sản phẩm. | Tất cả sản phẩm. |
> | Hàng bể vỡ – khác | Các loại bể vỡ khác với bốn loại bể vỡ đã liệt kê bên trên (bạn có thể chú thích cụ thể thêm khi yêu cầu trả hàng). | Tất cả sản phẩm. |
> | Hàng lỗi, không hoạt động | Sản phẩm không thực hiện được chức năng như mô tả của Người bán. | Tất cả sản phẩm. |
> | Khác với mô tả | Sản phẩm có sự khác biệt rõ ràng về chất liệu, màu sắc, thông số, kiểu dáng so với mô tả của Người bán. | Tất cả sản phẩm. |

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

**Hạng 3 — cosine 0.668998; không liên quan**

Nguồn: `data/ecommerce/shopee-chinh-sach-bao-hanh-mall.md`; heading: `Chính sách bảo hành sản phẩm chính hãng Shopee Mall > C. HƯỚNG DẪN ĐĂNG BÁN SẢN PHẨM TRÊN SHOPEE > 7. Phí vận chuyển`; chunk: `shopee-chinh-sach-bao-hanh-mall:58964d44507a6ab0f40478e7`.

> Chính sách bảo hành sản phẩm chính hãng Shopee Mall > C. HƯỚNG DẪN ĐĂNG BÁN SẢN PHẨM TRÊN SHOPEE > 7. Phí vận chuyển
> 
> a. Người Bán phải xác định chính xác khối lượng sản phẩm cần vận chuyển để ước lượng chi phí vận chuyển.
> b. Khối lượng sản phẩm đăng ký phải là khối lượng sau khi đóng gói của hàng hóa để chuyển đi. Người Bán chịu trách nhiệm về tính chính xác đối với khối lượng sản phẩm đăng ký này.
> c. Với các sản phẩm cồng kềnh, Người Bán nên tham khảo thêm Chính sách vận chuyển để biết chi tiết cách thức xác định khối lượng sản phẩm.
> Tham khảo Cách tính phí vận chuyển Shopee cho Người bán tại đây.

Đánh giá: Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file.

## Mâu thuẫn giữa báo cáo nhóm và corpus

1. Câu 1 chỉ tới `shopee-quy-dinh-dang-ban-san-pham.md`, nhưng các quy định đầy đủ về tên, hình ảnh, mô tả, danh mục, nguồn gốc và bảo hành nằm trong file mang tên `shopee-chinh-sach-bao-hanh-mall.md`. Front matter của file này ghi category `warranty`, audience `buyer`, trong khi thân bài lại là “QUY ĐỊNH VỀ ĐĂNG BÁN SẢN PHẨM”; vì vậy filter `seller-rules` loại mất bằng chứng chính.
2. Câu 3 chỉ tới chính sách trả hàng/hoàn tiền. Corpus có lý do trả hàng khi hàng bể vỡ và có quy định đóng gói hợp lý cho thực phẩm dễ hỏng, nhưng không có đủ bộ mệnh đề “đóng gói đặc biệt, cảnh báo rõ ràng, có thể bị từ chối vận chuyển”.
3. Câu 4 chỉ tới chính sách bảo mật và đề xuất filter `privacy-policy`; đây không phải nội dung khiếu nại hư hỏng vận chuyển. Chính sách trả hàng có hỗ trợ từ chối nhận/gửi yêu cầu khi hàng hư hỏng, nhưng corpus không chứa đầy đủ danh sách hình ảnh/video, biên bản đồng kiểm, hóa đơn như Gold Answer.
4. Câu 5 chỉ tới file bảo hành Mall, nhưng thân file là quy định đăng bán. Corpus có nghĩa vụ đóng gói hợp lý cho một số thực phẩm và điều khoản rủi ro vận chuyển, nhưng không có đủ mệnh đề Shopee từ chối bồi thường vì lỗi đóng gói của Người Bán.

## Hạn chế

Relevance được chấm theo việc chunk chứa mệnh đề hỗ trợ Gold Answer, không theo tên file hay chỉ trùng từ khóa. Tuy nhiên đây vẫn là đánh giá quy tắc trên năm câu hỏi; corpus bị thiếu/đặt sai nội dung nên điểm thấp không thể quy hoàn toàn cho chunking hoặc embedding. Gemini API và model có thể thay đổi theo thời gian; cache lưu vector và câu trả lời của lần chạy này để tái kiểm tra mà không gọi API lặp lại. Câu trả lời agent chỉ phản ánh top-3 chính, không phải tư vấn chính sách đầy đủ.

## Việc đã làm và xác minh

- Trích đúng năm câu hỏi, Gold Answer và vị trí đáp án từ mục 3 báo cáo nhóm.
- Xác định đúng chiến lược HeadingStructureChunker của Phạm Đình Bảo Khôi.
- Index toàn bộ corpus Markdown với metadata front matter và heading path.
- Dùng Gemini embedding thật; lưu top-3 chính và top-3 không lọc cho cả năm query.
- Tạo câu trả lời có căn cứ từ top-3; lỗi API được ghi rõ thay vì bịa nội dung.
- Kiểm tra vector, cosine, đúng năm dòng bảng, key bí mật, hash file bảo vệ và phạm vi file output.

<!-- COMPETITION_RESULTS_END -->
