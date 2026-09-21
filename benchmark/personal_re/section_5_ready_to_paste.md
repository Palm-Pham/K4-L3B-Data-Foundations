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
