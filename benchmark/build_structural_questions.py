"""Rebuild gold data from verified source excerpts; never modify source documents."""
import json
from pathlib import Path
from benchmark.structural_chunking import parse_units

ROOT=Path(__file__).resolve().parents[1]
TERMS='shopee-dieu-khoan-dich-vu'
RETURNS='shopee-chinh-sach-doi-tra-hoan-tien'
ROWS=[
('Nếu hàng hóa bị hư hỏng, thất lạc hoặc không giao được trong quá trình vận chuyển thì ai chịu rủi ro?', TERMS,'13.3','Người Bán chịu toàn bộ rủi ro vận chuyển; Shopee không chịu trách nhiệm về tổn thất, chi phí phát sinh từ sự cố.', ['Người Bán chịu toàn bộ rủi ro liên quan đến việc vận chuyển hàng hóa được mua', 'Shopee sẽ không chịu trách nhiệm đối với bất kỳ tổn thất, chi phí, phí tổn hoặc bất kỳ khoản phí nào phát sinh từ sự cố đó.']),
('Khi xảy ra tranh chấp giao dịch, Người Mua và Người Bán cần làm gì trước tiên?',TERMS,'17.1','Hai bên trước tiên đối thoại, thảo luận với nhau để cố gắng giải quyết tranh chấp.', ['Người Bán và Người Mua đồng ý đầu tiên sẽ đối thoại với nhau để cố gắng giải quyết tranh chấp đó bằng thảo luận hai bên']),
('Người Bán phải đảm bảo những thông tin nào trong danh mục sản phẩm là chính xác và đầy đủ?',TERMS,'15.1','Giá cả, chi tiết sản phẩm, số lượng tồn kho, các điều khoản và điều kiện bán hàng; không đăng thông tin sai hoặc gây nhầm lẫn.', ['giá cả và chi tiết sản phẩm, số lượng sản phẩm trong kho cũng như các điều khoản và điều kiện bán hàng', 'không được phép đăng tải các thông tin không chính xác hoặc gây nhầm lẫn.']),
('Nếu hàng nhận được bị hư hỏng hoặc khác với mô tả, Người Mua có thể làm gì?',RETURNS,'1.1','Có thể từ chối nhận hàng khi đồng kiểm (với đơn được Đồng kiểm), hoặc gửi yêu cầu Trả hàng/Hoàn tiền sau khi nhận hàng. Shopee chưa hỗ trợ đổi hàng.', ['Shopee hiện chưa hỗ trợ yêu cầu đổi hàng.', 'bạn có thể từ chối nhận hàng khi đồng kiểm (đối với đơn hàng được Đồng kiểm)', 'có thể gửi yêu cầu Trả hàng/Hoàn tiền sau khi đã nhận hàng.']),
('Người Mua có thể gửi yêu cầu Trả hàng/Hoàn tiền trong thời hạn nào?',RETURNS,'1.2','Thực phẩm tươi sống/đông lạnh: 24 giờ từ “Giao hàng thành công” (trừ lý do chưa nhận hàng). Người bán tự vận chuyển: 15 ngày từ khi bấm “Đã nhận được hàng”, hoặc 20 ngày từ “Lấy hàng thành công” nếu không bấm. Đơn khác: 15 ngày từ “Giao hàng thành công”.', ['Đối với đơn hàng giao thực phẩm tươi sống và đông lạnh (trừ lý do Chưa nhận được hàng): Trong vòng 24 giờ kể từ lúc đơn hàng được cập nhật trạng thái “Giao hàng thành công”.', 'Đối với đơn hàng do Người bán tự vận chuyển:\n  - 15 ngày kể từ lúc bạn bấm “Đã nhận được hàng”; hoặc\n  - 20 ngày kể từ lúc đơn hàng được cập nhật trạng thái “Lấy hàng thành công” và bạn không bấm “Đã nhận được hàng”.', 'Đối với các đơn hàng khác: 15 ngày kể từ lúc đơn hàng được cập nhật trạng thái “Giao hàng thành công”.'])]


def main():
    rows=[]
    for query,doc,clause,answer,facts in ROWS:
        source=f'data/ecommerce/{doc}.md'
        _,units=parse_units((ROOT/source).read_text(),source)
        unit=next(u for u in units if u.clause==clause)
        assert all(' '.join(f.split()) in ' '.join(unit.text.split()) for f in facts), clause
        rows.append(dict(query=query,gold_answer=answer,expected_doc_id=doc,expected_clause=clause,expected_heading_path=unit.heading_path,evidence_facts=facts,source=source,source_excerpt=unit.text))
    rows[-1]['partial_evidence'] = ['Bạn vẫn có thể gửi yêu cầu Trả hàng/Hoàn tiền sau khi đã bấm nút “Đã nhận được hàng” và vẫn còn trong thời hạn 15 ngày Trả hàng/Hoàn tiền quy định của Shopee.']
    (ROOT/'benchmark/structural_questions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    main()
