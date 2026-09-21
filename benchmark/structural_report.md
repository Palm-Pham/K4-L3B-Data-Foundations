# Two-document structural chunking benchmark

## Configuration

- Backend: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; vector dimension 384; token limit 128 (including special tokens).
- Store: Chroma; ranking score: 1 - squared L2 distance (Chroma default, normalized vectors; equivalent ranking to cosine). One collection per strategy contains both documents; top_k=3; no retrieval filters.
- Sources: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`, `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`
- Corpus SHA-256: {"data/ecommerce/shopee-dieu-khoan-dich-vu.md": "24f42b2ea538a8b74ad0722fba9398dc57e59317c857f6c7c4a73090867739c5", "data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md": "235af95619ed964d36b95bf8e7e3b5b5352c7da53b3e00a4ef7cf68836b0f269"}
- Character cap: 1000; overlap: 0. Exact tokenizer checks apply to all embedded chunks and queries; no truncation or mock fallback.
- Front matter and heading-only lines are removed from baseline text. All strategies run independently within each major section; fixed-size and recursive use the existing repository classes. Header chunks additionally retain clause boundaries and prefix the heading path.
- Zero overlap is intentional: it avoids consuming the limited token budget with duplicate text. Single sentences too large for the model are explicitly split at whitespace, then characters only as a last resort.
- Gold answers and verbatim answer propositions are in `structural_questions.json`. Source hashes, all chunks, and raw top-3 results are in `structural_results.json`.

## Relevance and rubric

Relevance requires a complete, manually source-verified answer proposition or an explicitly annotated partial-support statement, not keyword overlap or merely the correct clause label. Full support requires all gold propositions across the top 3. Hit@1/Hit@3 and MRR include useful partial support; full-support rate is reported separately. The scorer conservatively matches complete evidence spans with whitespace normalized. All 45 retrieved results were also inspected for alternative support and split/incomplete facts. The reminder that requests remain possible within the 15-day period after acknowledging receipt is partial evidence for Q5, even though it omits the deadline start and exceptions. Manual rationales are recorded in structural_review.json.

Rubric resolves the overlapping instructions as: 2 = first supporting result at rank 1 and all answer facts supported by top 3; 1 = partial support or first relevant rank 2/3; 0 = no supporting proposition in top 3. This is a retrieval/support evaluation, not an LLM answer-generation test.

## Comparison

| Strategy | Hit@1 | Hit@3 | MRR | Full support | Rubric /10 |
|---|---:|---:|---:|---:|---:|
| fixed_size | 0.80 | 0.80 | 0.800 | 0.60 | 7 |
| recursive | 0.60 | 0.80 | 0.700 | 0.60 | 7 |
| header | 0.60 | 0.80 | 0.700 | 0.40 | 6 |

## Chunk statistics

Lengths are characters including heading prefixes. Fallback counts count output chunks belonging to an oversized input unit.

| Strategy | Document | Count | Min | Average | Median | Max | Max tokens | Fallback chunks | Major crossings |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed_size | data/ecommerce/shopee-dieu-khoan-dich-vu.md | 288 | 4 | 284.07 | 292.0 | 521 | 128 | 271 | 0 |
| fixed_size | data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md | 24 | 73 | 255.38 | 266.0 | 439 | 125 | 23 | 0 |
| recursive | data/ecommerce/shopee-dieu-khoan-dich-vu.md | 282 | 4 | 289.87 | 291.5 | 534 | 128 | 248 | 0 |
| recursive | data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md | 21 | 104 | 291.9 | 316 | 480 | 128 | 20 | 0 |
| header | data/ecommerce/shopee-dieu-khoan-dich-vu.md | 358 | 82 | 317.3 | 327.0 | 524 | 128 | 308 | 0 |
| header | data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md | 35 | 133 | 317.89 | 342 | 471 | 127 | 34 | 0 |

## Questions and top-3 evidence

### Q1. Nếu hàng hóa bị hư hỏng, thất lạc hoặc không giao được trong quá trình vận chuyển thì ai chịu rủi ro?

Gold: Người Bán chịu toàn bộ rủi ro vận chuyển; Shopee không chịu trách nhiệm về tổn thất, chi phí phát sinh từ sự cố.

Expected: `shopee-dieu-khoan-dich-vu`, clause `13.3`.

#### fixed_size

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=True; rubric=2/2.

Failure: None.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.385472; full support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.3; clause: `13.3`; chunk: `shopee-dieu-khoan-dich-vu:0419a97e9cdada6587619136`.

> 13.3. Người Sử Dụng hiểu rằng Người Bán chịu toàn bộ rủi ro liên quan đến việc vận chuyển hàng hóa được mua và bảo đảm rằng Người Bán đã hoặc sẽ mua bảo hiểm hàng hóa, bao gồm cả việc vận chuyển. Trong trường hợp hàng hóa được mua bị hư hỏng, thất lạc hoặc không chuyển phát được trong quá trình vận chuyển, Người Sử Dụng thừa nhận và đồng ý rằng Shopee sẽ không chịu trách nhiệm đối với bất kỳ tổn thất, chi phí, phí tổn hoặc bất kỳ khoản phí nào phát sinh từ sự cố đó.

**Rank 2 — score 0.096410; none support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.3. Lý do Trả hàng/Hoàn tiền; clause: `1.3`; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:72e02beb627f4f68bf86992e`.

> hoặc phụ kiện, thiếu quà tặng kèm. | Tất cả sản phẩm. |
> | Người bán gửi sai hàng | Sản phẩm nhận được không phải sản phẩm đã đặt. | Tất cả sản phẩm. |
> | Hàng bể vỡ – bể/vỡ vụn | Sản phẩm bị bể vỡ nặng, không còn giá trị sử dụng. | Tất cả sản phẩm. |

**Rank 3 — score 0.050995; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 7. VI PHẠM ĐIỀU KHOẢN DỊCH VỤ > 7.1; clause: `7.1`; chunk: `shopee-dieu-khoan-dich-vu:1002c89b4f06597ef7a34e2b`.

> 7.1. Việc vi phạm Điều Khoản Dịch Vụ này có thể dẫn tới một số hành động, bao gồm bất kỳ hoặc tất cả các hành động sau:
> (a) Xóa danh mục sản phẩm;
> (b) Giới hạn quyền sử dụng Tài Khoản;
> (c) Đình chỉ và chấm dứt Tài Khoản;
> (d) Thu hồi tiền/tài sản có được do hành vi gian lận, và các chi phí có liên quan như chi phí vận chuyển của đơn hàng, phí Xử Lý Giao Dịch…;
> (e) Cáo buộc hình sự;

</details>

#### recursive

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=True; rubric=2/2.

Failure: None.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.385472; full support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.3; clause: `13.3`; chunk: `shopee-dieu-khoan-dich-vu:f29461d3270e87e99dcb7c0d`.

> 13.3. Người Sử Dụng hiểu rằng Người Bán chịu toàn bộ rủi ro liên quan đến việc vận chuyển hàng hóa được mua và bảo đảm rằng Người Bán đã hoặc sẽ mua bảo hiểm hàng hóa, bao gồm cả việc vận chuyển. Trong trường hợp hàng hóa được mua bị hư hỏng, thất lạc hoặc không chuyển phát được trong quá trình vận chuyển, Người Sử Dụng thừa nhận và đồng ý rằng Shopee sẽ không chịu trách nhiệm đối với bất kỳ tổn thất, chi phí, phí tổn hoặc bất kỳ khoản phí nào phát sinh từ sự cố đó.

**Rank 2 — score 0.100000; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.4; clause: `13.4`; chunk: `shopee-dieu-khoan-dich-vu:05305fcc8638d1e8e7761391`.

> Người Sử Dụng hiểu rằng, khi một đăng bán có mô tả rằng sản phẩm được đăng bán sẽ được gửi từ nước ngoài ("Sản Phẩm Ở Nước Ngoài"), sản phẩm đó được bán bởi Người Bán ngoài Việt Nam, và việc xuất/nhập khẩu sản phẩm đó chịu sự điều chỉnh của pháp luật. Người Sử Dụng cần hiểu rõ các hạn chế về xuất/nhập khẩu hàng hóa của quốc gia nhập khẩu.

**Rank 3 — score 0.050995; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 7. VI PHẠM ĐIỀU KHOẢN DỊCH VỤ > 7.1; clause: `7.1`; chunk: `shopee-dieu-khoan-dich-vu:e1a598859c95394e005003ee`.

> 7.1. Việc vi phạm Điều Khoản Dịch Vụ này có thể dẫn tới một số hành động, bao gồm bất kỳ hoặc tất cả các hành động sau:
> (a) Xóa danh mục sản phẩm;
> (b) Giới hạn quyền sử dụng Tài Khoản;
> (c) Đình chỉ và chấm dứt Tài Khoản;
> (d) Thu hồi tiền/tài sản có được do hành vi gian lận, và các chi phí có liên quan như chi phí vận chuyển của đơn hàng, phí Xử Lý Giao Dịch…;
> (e) Cáo buộc hình sự;

</details>

#### header

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=False; rubric=1/2.

Failure: Answer evidence is incomplete across top 3.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.245461; partial support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.3; clause: `13.3`; chunk: `shopee-dieu-khoan-dich-vu:8d56027e1897e7a5d337242b`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.3
> 
> 13.3. Người Sử Dụng hiểu rằng Người Bán chịu toàn bộ rủi ro liên quan đến việc vận chuyển hàng hóa được mua và bảo đảm rằng Người Bán đã hoặc sẽ mua bảo hiểm hàng hóa, bao gồm cả việc vận chuyển.

**Rank 2 — score 0.075287; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 7. VI PHẠM ĐIỀU KHOẢN DỊCH VỤ > 7.1; clause: `7.1`; chunk: `shopee-dieu-khoan-dich-vu:782d157c7f32460903648dd0`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 7. VI PHẠM ĐIỀU KHOẢN DỊCH VỤ > 7.1
> 
> (d) Thu hồi tiền/tài sản có được do hành vi gian lận, và các chi phí có liên quan như chi phí vận chuyển của đơn hàng, phí Xử Lý Giao Dịch…;
> (e) Cáo buộc hình sự;
> (f) Áp dụng biện pháp dân sự, bao gồm khiếu nại bồi thường thiệt hại và/hoặc áp dụng biện pháp khẩn cấp tạm thời;

**Rank 3 — score 0.045115; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.4; clause: `13.4`; chunk: `shopee-dieu-khoan-dich-vu:a43247292d9b2565b2eb4214`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.4
> 
> Người Sử Dụng hiểu rằng, khi một đăng bán có mô tả rằng sản phẩm được đăng bán sẽ được gửi từ nước ngoài ("Sản Phẩm Ở Nước Ngoài"), sản phẩm đó được bán bởi Người Bán ngoài Việt Nam, và việc xuất/nhập khẩu sản phẩm đó chịu sự điều chỉnh của pháp luật. Người Sử Dụng cần hiểu rõ các hạn chế về xuất/nhập khẩu hàng hóa của quốc gia nhập khẩu.

</details>

### Q2. Khi xảy ra tranh chấp giao dịch, Người Mua và Người Bán cần làm gì trước tiên?

Gold: Hai bên trước tiên đối thoại, thảo luận với nhau để cố gắng giải quyết tranh chấp.

Expected: `shopee-dieu-khoan-dich-vu`, clause `17.1`.

#### fixed_size

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=True; rubric=2/2.

Failure: None.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.520633; full support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 17. TRANH CHẤP > 17.1; clause: `17.1`; chunk: `shopee-dieu-khoan-dich-vu:bdc895b8dfd1acebba967247`.

> 17.1. Trường hợp phát sinh vấn đề liên quan đến giao dịch, Người Bán và Người Mua đồng ý đầu tiên sẽ đối thoại với nhau để cố gắng giải quyết tranh chấp đó bằng thảo luận hai bên, và Shopee sẽ cố gắng một cách hợp lý để thu xếp. Nếu vấn đề không được giải quyết bằng thảo luận hai bên, Người Sử Dụng có thể khiếu nại lên cơ quan có thẩm quyền của địa phương để giải quyết tranh chấp phát sinh đối với giao dịch.

**Rank 2 — score 0.213288; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 1. GIỚI THIỆU > 1.2; clause: `1.2`; chunk: `shopee-dieu-khoan-dich-vu:34fabbba30e3282cd9bd32e9`.

> Dung hoặc thông tin nào trên Trang Shopee theo Điều 6.4 bên dưới. Shopee không bảo đảm cho việc các Người Sử Dụng sẽ thực tế hoàn thành giao dịch. Lưu ý, Shopee sẽ là bên trung gian quản lý tình trạng hàng hóa và mua bán giữa Người Mua và Người Bán và quản lý vấn đề vận chuyển, trừ khi Người Mua và Người Bán thể hiện mong muốn tự giao dịch với nhau một cách rõ ràng.

**Rank 3 — score 0.166225; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 13. VẬN CHUYỂN > 13.2; clause: `13.2`; chunk: `shopee-dieu-khoan-dich-vu:885a8cb26f910e3aeeda68e0`.

> 13.2. Người Bán phải luôn nỗ lực để đảm bảo Người Mua sẽ nhận được hàng đúng hẹn trong Thời Gian Shopee Đảm Bảo.
> Đối với việc vận chuyển sản phẩm bởi Người Bán đến cho Người Mua trong lãnh thổ Việt Nam, Shopee đóng vai trò như một bên trung gian nhằm kết nối Người Bán và Người Mua với các đơn vị cung cấp dịch vụ vận chuyển (“Đơn Vị Cung Cấp Dịch Vụ Vận Chuyển”).

</details>

#### recursive

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=True; rubric=2/2.

Failure: None.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.520633; full support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 17. TRANH CHẤP > 17.1; clause: `17.1`; chunk: `shopee-dieu-khoan-dich-vu:6b3a99e2fe29fa202b057ac1`.

> 17.1. Trường hợp phát sinh vấn đề liên quan đến giao dịch, Người Bán và Người Mua đồng ý đầu tiên sẽ đối thoại với nhau để cố gắng giải quyết tranh chấp đó bằng thảo luận hai bên, và Shopee sẽ cố gắng một cách hợp lý để thu xếp. Nếu vấn đề không được giải quyết bằng thảo luận hai bên, Người Sử Dụng có thể khiếu nại lên cơ quan có thẩm quyền của địa phương để giải quyết tranh chấp phát sinh đối với giao dịch.

**Rank 2 — score 0.278640; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 1. GIỚI THIỆU > 1.2; clause: `1.2`; chunk: `shopee-dieu-khoan-dich-vu:7bd3eaa8962951c1f40e0707`.

> Lưu ý, Shopee sẽ là bên trung gian quản lý tình trạng hàng hóa và mua bán giữa Người Mua và Người Bán và quản lý vấn đề vận chuyển, trừ khi Người Mua và Người Bán thể hiện mong muốn tự giao dịch với nhau một cách rõ ràng.

**Rank 3 — score 0.222687; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 10. SỐ DƯ TÀI KHOẢN SHOPEE > 10.6; clause: `10.6`; chunk: `shopee-dieu-khoan-dich-vu:d3b6ba861e6a949855dccb9d`.

> (ix) liên quan đến bất kỳ việc thay đổi thỏa thuận đã cam kết giữa Người Mua và Người Bán.

</details>

#### header

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=True; rubric=2/2.

Failure: None.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.457327; full support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 17. TRANH CHẤP > 17.1; clause: `17.1`; chunk: `shopee-dieu-khoan-dich-vu:c677e86f3bc75affc96fcc8a`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 17. TRANH CHẤP > 17.1
> 
> 17.1. Trường hợp phát sinh vấn đề liên quan đến giao dịch, Người Bán và Người Mua đồng ý đầu tiên sẽ đối thoại với nhau để cố gắng giải quyết tranh chấp đó bằng thảo luận hai bên, và Shopee sẽ cố gắng một cách hợp lý để thu xếp. Nếu vấn đề không được giải quyết bằng thảo luận hai bên, Người Sử Dụng có thể khiếu nại lên cơ quan có thẩm quyền của địa phương để giải quyết tranh chấp phát sinh đối với giao dịch.

**Rank 2 — score 0.148224; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 1. GIỚI THIỆU > 1.2; clause: `1.2`; chunk: `shopee-dieu-khoan-dich-vu:a8429111420cb396ca5dacd3`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 1. GIỚI THIỆU > 1.2
> 
> Shopee không bảo đảm cho việc các Người Sử Dụng sẽ thực tế hoàn thành giao dịch. Lưu ý, Shopee sẽ là bên trung gian quản lý tình trạng hàng hóa và mua bán giữa Người Mua và Người Bán và quản lý vấn đề vận chuyển, trừ khi Người Mua và Người Bán thể hiện mong muốn tự giao dịch với nhau một cách rõ ràng.

**Rank 3 — score 0.138598; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 26. BỒI THƯỜNG; clause: ``; chunk: `shopee-dieu-khoan-dich-vu:0359eb85a496d4a57f1e6542`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 26. BỒI THƯỜNG
> 
> và phí tổn có liên quan (bao gồm chi phí giải quyết tranh chấp) do Bên Được Bồi Thường gánh chịu, phát sinh từ (a) giao dịch được thực hiện trên Trang Shopee, hoặc tranh chấp liên quan đến giao dịch đó (trừ trường hợp Shopee hoặc các công ty liên kết của Shopee là Người Bán đối với giao dịch liên quan đến khiếu nại), (b) Chính Sách Đảm Bảo của Shopee, (c) việc tổ chức, hoạt động,

</details>

### Q3. Người Bán phải đảm bảo những thông tin nào trong danh mục sản phẩm là chính xác và đầy đủ?

Gold: Giá cả, chi tiết sản phẩm, số lượng tồn kho, các điều khoản và điều kiện bán hàng; không đăng thông tin sai hoặc gây nhầm lẫn.

Expected: `shopee-dieu-khoan-dich-vu`, clause `15.1`.

#### fixed_size

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=True; rubric=2/2.

Failure: None.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.781826; full support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 15. TRÁCH NHIỆM CỦA NGƯỜI BÁN > 15.1; clause: `15.1`; chunk: `shopee-dieu-khoan-dich-vu:aaf7f63e12fd8bf74fcf252f`.

> 15.1. Người Bán phải quản lý và đảm bảo độ chính xác và đầy đủ của các thông tin chẳng hạn liên quan đến giá cả và chi tiết sản phẩm, số lượng sản phẩm trong kho cũng như các điều khoản và điều kiện bán hàng được cập nhật trong danh mục sản phẩm của Người Bán và không được phép đăng tải các thông tin không chính xác hoặc gây nhầm lẫn.

**Rank 2 — score 0.416667; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 8. BÁO CÁO HÀNH VI CÓ KHẢ NĂNG XÂM PHẠM QUYỀN SỞ HỮU TRÍ TUỆ > 8.3; clause: `8.3`; chunk: `shopee-dieu-khoan-dich-vu:e2580d443ca42a5a8b5e06bf`.

> 8.3. Shopee xác nhận rằng một nhãn hàng hoặc nhà sản xuất có thể, phù hợp với quy định pháp luật có liên quan, có quyền ký kết các thỏa thuận phân phối độc quyền nhất định hoặc thỏa thuận giá tối thiểu cho sản phẩm của mình v

**Rank 3 — score 0.323113; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 15. TRÁCH NHIỆM CỦA NGƯỜI BÁN > 15.2; clause: `15.2`; chunk: `shopee-dieu-khoan-dich-vu:a89f286793fada9d4689521c`.

> 15.2. Giá sản phẩm hợp lệ được Người Bán toàn quyền quyết định phù hợp với mặt bằng giá trên thị trường và/hoặc chi phí mà Người Bán đã bỏ ra để có được sản phẩm, trừ các sản phẩm được ấn định giá bởi cơ quan có thẩm quyền. Giá sản phẩm nên bao gồm toàn bộ số tiền mà Người Mua cần thanh toán (ví dụ: các loại thuế, phí, v.v.) và Người Bán sẽ không yêu cầu Người Mua thanh toán thêm hoặc riêng bất kỳ khoản tiền nào khác.

</details>

#### recursive

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=True; rubric=2/2.

Failure: None.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.781826; full support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 15. TRÁCH NHIỆM CỦA NGƯỜI BÁN > 15.1; clause: `15.1`; chunk: `shopee-dieu-khoan-dich-vu:e5b2f6116869b758387956af`.

> 15.1. Người Bán phải quản lý và đảm bảo độ chính xác và đầy đủ của các thông tin chẳng hạn liên quan đến giá cả và chi tiết sản phẩm, số lượng sản phẩm trong kho cũng như các điều khoản và điều kiện bán hàng được cập nhật trong danh mục sản phẩm của Người Bán và không được phép đăng tải các thông tin không chính xác hoặc gây nhầm lẫn.

**Rank 2 — score 0.323113; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 15. TRÁCH NHIỆM CỦA NGƯỜI BÁN > 15.2; clause: `15.2`; chunk: `shopee-dieu-khoan-dich-vu:930de983e0c69cafb2aadd0b`.

> 15.2. Giá sản phẩm hợp lệ được Người Bán toàn quyền quyết định phù hợp với mặt bằng giá trên thị trường và/hoặc chi phí mà Người Bán đã bỏ ra để có được sản phẩm, trừ các sản phẩm được ấn định giá bởi cơ quan có thẩm quyền. Giá sản phẩm nên bao gồm toàn bộ số tiền mà Người Mua cần thanh toán (ví dụ: các loại thuế, phí, v.v.) và Người Bán sẽ không yêu cầu Người Mua thanh toán thêm hoặc riêng bất kỳ khoản tiền nào khác.

**Rank 3 — score 0.311870; none support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 2. Quy định chung về việc hoàn lại Mã giảm giá/Shopee Xu khi yêu cầu Trả hàng/Hoàn tiền; clause: ``; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:62eeb993580b1f64816362b9`.

> | Trường hợp | Loại khiếu nại | Mã giảm giá | Shopee Xu |
> | --- | --- | --- | --- |
> | Hoàn tiền ngay (không cần trả hàng) | Khiếu nại trên toàn bộ sản phẩm | Hoàn mã nếu lý do là Chưa nhận được hàng hoặc Hàng rỗng. Không hoàn mã với lý do khác. | Hoàn lại Xu theo số sản phẩm được hoàn. Nếu hoàn tất cả sản phẩm: hoàn toàn bộ Xu. |

</details>

#### header

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=True; rubric=2/2.

Failure: None.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.561195; full support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 15. TRÁCH NHIỆM CỦA NGƯỜI BÁN > 15.1; clause: `15.1`; chunk: `shopee-dieu-khoan-dich-vu:f011185db5b8b661e3f4e8d5`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 15. TRÁCH NHIỆM CỦA NGƯỜI BÁN > 15.1
> 
> 15.1. Người Bán phải quản lý và đảm bảo độ chính xác và đầy đủ của các thông tin chẳng hạn liên quan đến giá cả và chi tiết sản phẩm, số lượng sản phẩm trong kho cũng như các điều khoản và điều kiện bán hàng được cập nhật trong danh mục sản phẩm của Người Bán và không được phép đăng tải các thông tin không chính xác hoặc gây nhầm lẫn.

**Rank 2 — score 0.344939; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 9. ĐẶT HÀNG VÀ THANH TOÁN > 9.5; clause: `9.5`; chunk: `shopee-dieu-khoan-dich-vu:d1af1d849e29cdab1cbe88fc`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 9. ĐẶT HÀNG VÀ THANH TOÁN > 9.5
> 
> Thông tin bạn cung cấp phải cập nhật, đầy đủ và chính xác, đồng thời bạn phải duy trì tính đầy đủ và chính xác của các thông tin đó.

**Rank 3 — score 0.273436; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 8. BÁO CÁO HÀNH VI CÓ KHẢ NĂNG XÂM PHẠM QUYỀN SỞ HỮU TRÍ TUỆ > 8.3; clause: `8.3`; chunk: `shopee-dieu-khoan-dich-vu:95662d7c844209af94ed97f7`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 8. BÁO CÁO HÀNH VI CÓ KHẢ NĂNG XÂM PHẠM QUYỀN SỞ HỮU TRÍ TUỆ > 8.3
> 
> 8.3. Shopee xác nhận rằng một nhãn hàng hoặc nhà sản xuất có thể, phù hợp với quy định pháp luật có liên quan, có quyền ký kết các thỏa thuận phân phối độc quyền nhất định hoặc thỏa thuận giá tối thiểu cho sản phẩm của mình với bên thứ ba khác.

</details>

### Q4. Nếu hàng nhận được bị hư hỏng hoặc khác với mô tả, Người Mua có thể làm gì?

Gold: Có thể từ chối nhận hàng khi đồng kiểm (với đơn được Đồng kiểm), hoặc gửi yêu cầu Trả hàng/Hoàn tiền sau khi nhận hàng. Shopee chưa hỗ trợ đổi hàng.

Expected: `shopee-chinh-sach-doi-tra-hoan-tien`, clause `1.1`.

#### fixed_size

Hit@1=0; Hit@3=0; first rank=None; RR=0.000; correct source at top 1=True; full support=False; rubric=0/2.

Failure: No complete answer proposition retrieved.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.269739; none support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.3. Lý do Trả hàng/Hoàn tiền; clause: `1.3`; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:72e02beb627f4f68bf86992e`.

> hoặc phụ kiện, thiếu quà tặng kèm. | Tất cả sản phẩm. |
> | Người bán gửi sai hàng | Sản phẩm nhận được không phải sản phẩm đã đặt. | Tất cả sản phẩm. |
> | Hàng bể vỡ – bể/vỡ vụn | Sản phẩm bị bể vỡ nặng, không còn giá trị sử dụng. | Tất cả sản phẩm. |

**Rank 2 — score 0.197457; none support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 2. Quy định chung về việc hoàn lại Mã giảm giá/Shopee Xu khi yêu cầu Trả hàng/Hoàn tiền; clause: ``; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:3ee0394db680e88789c5d6ba`.

> | Trường hợp | Loại khiếu nại | Mã giảm giá | Shopee Xu |
> | --- | --- | --- | --- |
> | Hoàn tiền ngay (không cần trả hàng) | Khiếu nại trên toàn bộ sản phẩm | Hoàn mã nếu lý do là Chưa nhận được hàng hoặc Hàng rỗng. Không hoàn mã với lý do khác. | Hoàn lại Xu theo số sản phẩm được hoàn. Nếu hoàn tất cả sản phẩm: hoàn toàn bộ Xu. |

**Rank 3 — score 0.174173; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 10. SỐ DƯ TÀI KHOẢN SHOPEE > 10.6; clause: `10.6`; chunk: `shopee-dieu-khoan-dich-vu:b677deaeaf7ebecd437f257d`.

> (i) điều chỉnh các sai sót trong việc thực hiện bất kỳ giao dịch nào;
> (ii) trường hợp Shopee cho rằng bạn thực hiện hành vi và/hoặc giao dịch gian lận hoặc đáng ngờ;
> (iii) liên quan đến bất kỳ tổn thất, thiệt hại hoặc các khoản không chính xác nào;
> (iv) liên quan đến bất kỳ điểm thưởng hay hoàn lại nào;
> (v) liên quan đến bất kỳ loại phí chưa được thanh toán nào;
> (vi) liên quan đến việc giải quyết bất kỳ tranh chấp giao dịch nào, bao gồm bất kỳ các bồi th

</details>

#### recursive

Hit@1=0; Hit@3=0; first rank=None; RR=0.000; correct source at top 1=True; full support=False; rubric=0/2.

Failure: No complete answer proposition retrieved.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.197457; none support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 2. Quy định chung về việc hoàn lại Mã giảm giá/Shopee Xu khi yêu cầu Trả hàng/Hoàn tiền; clause: ``; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:62eeb993580b1f64816362b9`.

> | Trường hợp | Loại khiếu nại | Mã giảm giá | Shopee Xu |
> | --- | --- | --- | --- |
> | Hoàn tiền ngay (không cần trả hàng) | Khiếu nại trên toàn bộ sản phẩm | Hoàn mã nếu lý do là Chưa nhận được hàng hoặc Hàng rỗng. Không hoàn mã với lý do khác. | Hoàn lại Xu theo số sản phẩm được hoàn. Nếu hoàn tất cả sản phẩm: hoàn toàn bộ Xu. |

**Rank 2 — score 0.115736; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 10. SỐ DƯ TÀI KHOẢN SHOPEE > 10.6; clause: `10.6`; chunk: `shopee-dieu-khoan-dich-vu:d3b6ba861e6a949855dccb9d`.

> (ix) liên quan đến bất kỳ việc thay đổi thỏa thuận đã cam kết giữa Người Mua và Người Bán.

**Rank 3 — score 0.086981; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 9. ĐẶT HÀNG VÀ THANH TOÁN > 9.4; clause: `9.4`; chunk: `shopee-dieu-khoan-dich-vu:bcf8e19ecfb4add98b08c1a4`.

> 9.4. Tính khả dụng của một phương thức thanh toán nhất định hoặc khả năng tương thích của nó với Shopee có thể phụ thuộc vào phương thức thanh toán của bạn và các yếu tố khác và có thể thay đổi bất cứ lúc nào.

</details>

#### header

Hit@1=0; Hit@3=0; first rank=None; RR=0.000; correct source at top 1=False; full support=False; rubric=0/2.

Failure: No complete answer proposition retrieved.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.064693; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 18.  PHẢN HỒI; clause: ``; chunk: `shopee-dieu-khoan-dich-vu:6a4b1c7335944d10a7048c04`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 18.  PHẢN HỒI
> 
> (iii) Người Sử Dụng liên quan đến phản hồi sẽ được thông báo đầy đủ và được tạo cơ hội cải thiện tình hình.
> (iv) Những phản hồi không rõ ràng và mang tính phỉ báng sẽ không được chấp nhận.

**Rank 2 — score 0.010789; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 10. SỐ DƯ TÀI KHOẢN SHOPEE > 10.6; clause: `10.6`; chunk: `shopee-dieu-khoan-dich-vu:777557acb0272533d4371c3c`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 10. SỐ DƯ TÀI KHOẢN SHOPEE > 10.6
> 
> (iii) liên quan đến bất kỳ tổn thất, thiệt hại hoặc các khoản không chính xác nào;
> (iv) liên quan đến bất kỳ điểm thưởng hay hoàn lại nào;
> (v) liên quan đến bất kỳ loại phí chưa được thanh toán nào;
> (vi) liên quan đến việc giải quyết bất kỳ tranh chấp giao dịch nào, bao gồm bất kỳ các bồi thường cho hoặc từ phía bạn;

**Rank 3 — score -0.027658; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 9. ĐẶT HÀNG VÀ THANH TOÁN > 9.4; clause: `9.4`; chunk: `shopee-dieu-khoan-dich-vu:c14ade6bc31cc57399599fc7`.

> Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 9. ĐẶT HÀNG VÀ THANH TOÁN > 9.4
> 
> 9.4. Tính khả dụng của một phương thức thanh toán nhất định hoặc khả năng tương thích của nó với Shopee có thể phụ thuộc vào phương thức thanh toán của bạn và các yếu tố khác và có thể thay đổi bất cứ lúc nào.

</details>

### Q5. Người Mua có thể gửi yêu cầu Trả hàng/Hoàn tiền trong thời hạn nào?

Gold: Thực phẩm tươi sống/đông lạnh: 24 giờ từ “Giao hàng thành công” (trừ lý do chưa nhận hàng). Người bán tự vận chuyển: 15 ngày từ khi bấm “Đã nhận được hàng”, hoặc 20 ngày từ “Lấy hàng thành công” nếu không bấm. Đơn khác: 15 ngày từ “Giao hàng thành công”.

Expected: `shopee-chinh-sach-doi-tra-hoan-tien`, clause `1.2`.

#### fixed_size

Hit@1=1; Hit@3=1; first rank=1; RR=1.000; correct source at top 1=True; full support=False; rubric=1/2.

Failure: Answer evidence is incomplete across top 3.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.457880; partial support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.2. Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho Shopee; clause: `1.2`; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:dc273fe0fca07a3844e147d2`.

> > **Lưu ý**
> >
> > - Bạn vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền sau khi đã bấm nút “Đã nhận được hàng” và vẫn còn trong thời hạn 15 ngày Trả hàng/Hoàn tiền quy định của Shopee.
> > -

**Rank 2 — score 0.410676; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 11. CHÍNH SÁCH ĐẢM BẢO CỦA SHOPEE > 11.4; clause: `11.4`; chunk: `shopee-dieu-khoan-dich-vu:1964e9e6953f217b5dbadb57`.

> liên lạc được và sau thời hạn mười hai (12) tháng kể từ ngày Khoản Tiền Thanh Toán của Người Mua đến hạn thanh toán cho Người Bán nhưng chưa được trả cho Người Bán, Shopee sẽ xử lý Khoản Tiền Thanh Toán này theo quy định pháp luật.

**Rank 3 — score 0.314275; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 14. HỦY ĐƠN HÀNG, TRẢ HÀNG VÀ HOÀN TIỀN > 14.6; clause: `14.6`; chunk: `shopee-dieu-khoan-dich-vu:e939324144ee1376776e1d4c`.

> cầu Shopee bồi thường đối với khoản tiền hoàn lại đó, và (iii) thời hạn của phiếu mua hàng sẽ theo quyết định của Shopee tại thời điểm phát hành.

</details>

#### recursive

Hit@1=0; Hit@3=1; first rank=2; RR=0.500; correct source at top 1=False; full support=False; rubric=1/2.

Failure: Answer evidence is incomplete across top 3.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.351753; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 11. CHÍNH SÁCH ĐẢM BẢO CỦA SHOPEE > 11.2; clause: `11.2`; chunk: `shopee-dieu-khoan-dich-vu:814817bc531a4e984326e1af`.

> Tuy nhiên nếu thời gian trả hàng/hoàn tiền vẫn chưa kết thúc, và sau đó Người Mua gửi yêu cầu trả hàng/hoàn tiền và Shopee xác định được rằng yêu cầu trả hàng/hoàn tiền của Người Mua được chấp thuận, Shopee có quyền điều chỉnh Khoản Tiền Thanh Toán từ Người Mua để thực hiện hoàn tiền cho Người Mua theo Chính Sách Trả Hàng và Hoàn Tiền;

**Rank 2 — score 0.346073; partial support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.2. Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho Shopee; clause: `1.2`; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:b3ff3f5c64a02f2104a79eb5`.

> > **Lưu ý**
> >
> > - Bạn vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền sau khi đã bấm nút “Đã nhận được hàng” và vẫn còn trong thời hạn 15 ngày Trả hàng/Hoàn tiền quy định của Shopee.
> > - Yêu cầu Trả hàng/Hoàn tiền của bạn sẽ được phản hồi trong vòng 3–5 ngày làm việc. Hãy theo dõi mục thông báo trên ứng dụng Shopee để nhanh chóng cập nhật tiến trình xử lý khiếu nại Trả hàng/Hoàn tiền.

**Rank 3 — score 0.314275; none support**

Source: `data/ecommerce/shopee-dieu-khoan-dich-vu.md`; path: Điều khoản dịch vụ và Quy chế hoạt động Sàn Shopee > 14. HỦY ĐƠN HÀNG, TRẢ HÀNG VÀ HOÀN TIỀN > 14.6; clause: `14.6`; chunk: `shopee-dieu-khoan-dich-vu:756e119d29bffb26f3a7e313`.

> cầu Shopee bồi thường đối với khoản tiền hoàn lại đó, và (iii) thời hạn của phiếu mua hàng sẽ theo quyết định của Shopee tại thời điểm phát hành.

</details>

#### header

Hit@1=0; Hit@3=1; first rank=2; RR=0.500; correct source at top 1=True; full support=False; rubric=1/2.

Failure: Answer evidence is incomplete across top 3.

<details><summary>Top-3 retrieved text and provenance</summary>

**Rank 1 — score 0.346367; none support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.2. Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho Shopee; clause: `1.2`; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:62d20b21e62fbace2d1ec889`.

> Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.2. Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho Shopee
> 
> > - Yêu cầu Trả hàng/Hoàn tiền của bạn sẽ được phản hồi trong vòng 3–5 ngày làm việc. Hãy theo dõi mục thông báo trên ứng dụng Shopee để nhanh chóng cập nhật tiến trình xử lý khiếu nại Trả hàng/Hoàn tiền.

**Rank 2 — score 0.338168; partial support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.2. Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho Shopee; clause: `1.2`; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:0a2c5e8aeb9d133de20ed0b9`.

> Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.2. Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho Shopee
> 
> - Đối với đơn hàng giao thực phẩm tươi sống và đông lạnh (trừ lý do Chưa nhận được hàng): Trong vòng 24 giờ kể từ lúc đơn hàng được cập nhật trạng thái “Giao hàng thành công”.
> - Đối với đơn hàng do Người bán tự vận chuyển:
>   - 15 ngày kể từ lúc bạn bấm “Đã nhận được hàng”; hoặc

**Rank 3 — score 0.337872; partial support**

Source: `data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md`; path: Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.2. Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho Shopee; clause: `1.2`; chunk: `shopee-chinh-sach-doi-tra-hoan-tien:b61637ca000d4e5df6a4cd29`.

> Những quy định chung về Trả hàng/Hoàn tiền của Shopee > 1. Điều kiện Trả hàng/Hoàn tiền của Shopee > 1.2. Thời gian tối đa để gửi yêu cầu Trả hàng/Hoàn tiền cho Shopee
> 
> > **Lưu ý**
> >
> > - Bạn vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền sau khi đã bấm nút “Đã nhận được hàng” và vẫn còn trong thời hạn 15 ngày Trả hàng/Hoàn tiền quy định của Shopee.

</details>


## Failure analysis and conclusion

All five gold answers are fully supported by the two source documents. Missing benchmark facts therefore reflect retrieval/chunk fragmentation, not missing corpus coverage. Q5 needs several distinct deadline cases; retrieving just the general 15-day rule is incomplete.

The 128-token model budget makes full heading paths costly. Structural boundaries preserve provenance, but can fragment long clauses or reduce the amount of answer text available in each retrieved result. This tradeoff is included in the comparison rather than hidden by tokenizer truncation.

Header versus fixed_size: rubric 6/10 versus 7/10; Hit@3 delta +0.00; MRR delta -0.100.
Header versus recursive: rubric 6/10 versus 7/10; Hit@3 delta +0.00; MRR delta +0.000.

Header-based chunking did not improve retrieval in this configuration: its rubric score is lower than both baselines, and its full-support rate is also lower. It does provide clearer structural provenance.

Q4 fails for all strategies: returned chunks discuss damage, transactions, or refunds but do not establish the buyer’s options in clause 1.1. Q5 remains partial for all strategies; the response-time note is not the submission deadline. Header Q1 retrieves seller risk but misses the separate Shopee liability exclusion in the gold answer.

Only five questions and one model/configuration were tested; these results do not establish general retrieval superiority. No parameters were tuned against the five queries.

## Reproduce

```bash
python -m benchmark.run_structural
python -m pytest tests benchmark/test_structural.py -v -o cache_dir=benchmark/.pytest_cache
```

Local setup if unavailable: install `requirements-local.txt` and allow the multilingual model to download. Failure to load a semantic backend stops the benchmark with a setup message; offline unit tests remain available.
