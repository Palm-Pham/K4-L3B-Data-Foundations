# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Linh Linh
**Thành viên:** Phạm Đình Bảo Khôi, Phạm Thị Thùy Linh, Nguyễn Thùy Linh, Văn Thành Huy
**Ngày:** 20/09/2026
//

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Nền tảng thương mại điện tử Shopee — điều khoản dịch vụ, bảo mật, đổi trả, bảo hành, đăng bán và giải quyết tranh chấp

**Tại sao nhóm chọn chủ đề này?**

> Nhóm chọn chủ đề này vì các chính sách Shopee có nội dung thực tế, đa dạng đối tượng và nhiều loại nghiệp vụ trong thương mại điện tử. Năm tài liệu công khai bao phủ cả quyền lợi người mua, trách nhiệm người bán, bảo mật dữ liệu và quy trình xử lý khiếu nại, phù hợp để so sánh khả năng truy xuất của các chiến lược chunking.

### Danh sách tài liệu (Data Inventory)

| #   | Tên tài liệu                           | Nguồn (Source URL)                            | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                                                             |
| --- | -------------------------------------- | --------------------------------------------- | -------------------- | -------- | ------------------------------------------------------------------------------------------- |
| 1   | shopee-dieu-khoan-dich-vu.md           | https://help.shopee.vn/portal/4/article/77243 | 2026-09-20 / 2026.08 | 83,371   | audience=buyer, category=terms-of-service, language=vi, license_or_permission=public-source |
| 2   | shopee-chinh-sach-bao-mat.md           | https://help.shopee.vn/portal/4/article/77244 | 2026-09-20 / 2026.08 | 43,197   | audience=seller, category=privacy-policy, language=vi, license_or_permission=public-source  |
| 3   | shopee-chinh-sach-doi-tra-hoan-tien.md | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / 2026.08 | 77,230   | audience=buyer, category=returns-refunds, language=vi, license_or_permission=public-source  |
| 4   | shopee-chinh-sach-bao-hanh-mall.md     | https://help.shopee.vn/portal/4/article/77246 | 2026-09-20 / 2026.08 | 21,589   | audience=buyer, category=warranty, language=vi, license_or_permission=public-source         |
| 5   | shopee-quy-dinh-dang-ban-san-pham.md   | https://help.shopee.vn/portal/4/article/77247 | 2026-09-20 / 2026.08 | 13,062   | audience=seller, category=seller-rules, language=vi, license_or_permission=public-source    |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata       | Kiểu   | Ví dụ giá trị                   | Tại sao hữu ích cho truy xuất (retrieval)?                 |
| --------------------- | ------ | ------------------------------- | ---------------------------------------------------------- |
| audience              | string | seller / buyer / both           | Giúp lọc kết quả theo vai trò người dùng                   |
| category              | string | seller-policy / shipping-policy | Định nghĩa loại quy định, dễ phân nhóm                     |
| language              | string | vi                              | Chọn tài liệu theo ngôn ngữ phù hợp                        |
| source_url            | string | https://help.shopee.vn/...      | Truy dấu nguồn công khai, kiểm chứng và provenance         |
| retrieved_at          | date   | 2026-09-20                      | Ghi ngày thu thập dữ liệu                                  |
| document_version      | string | 2025-04-28                      | Theo dõi phiên bản/chính sửa chính sách                    |
| license_or_permission | string | public-source                   | Xác nhận tài liệu đến từ nguồn công khai được phép sử dụng |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu                               | Chiến lược (Strategy)   | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
| -------------------------------------- | ----------------------- | -------------- | ----------------- | ------------------------ |
| shopee-dieu-khoan-dich-vu.md           | Parent-Child Chunker    | 368            | 253.2             | Có                       |
| Có                                     | HeadingStructureChunker | 358            | 317.30            | Có                       |
|                                        | SentenceChunker         | 213            | 390.1             | Có                       |
|                                        | RecursiveChunker        | 270            | 307.36            | Có                       |
| shopee-chinh-sach-doi-tra-hoan-tien.md | Parent-Child Chunker    | 325            | 267.1             | Có                       |
|                                        | HeadingStructureChunker | 35             | 317.89            | Có                       |
|                                        | SentenceChunker         | 291            | 264.4             | Có                       |
|                                        | RecursiveChunker        | 221            | 348.30            | Có                       |

### Chiến lược của từng thành viên

> **Thành viên 1 — Văn Thành Huy**

- **Loại chiến lược:** Parent-Child Chunker (`ParentChildChunker`)
- **Mô tả & lý do chọn cho chủ đề này:**
  Dữ liệu điều khoản Shopee rất dài và phức tạp. Chiến lược Parent-Child chia văn bản thành:
  1. **Parent Chunks lớn (~1200 ký tự)**: Giữ trọn vẹn bối cảnh của cả 1 điều khoản lớn để truyền cho LLM trả lời.
  2. **Child Chunks nhỏ (~300 ký tự)**: Dùng để tính toán embedding & similarity score giúp truy xuất cực kỳ chính xác.
- **Code snippet:**

````python
class ParentChildChunker:
    """
    Parent-Child (Hierarchical) Chunking Strategy.
    Splits text into large 'Parent' chunks for full context retrieval,
    and smaller 'Child' sub-chunks for accurate vector similarity embedding search.
    """
    def __init__(self, parent_size: int = 1200, child_size: int = 300, overlap: int = 40) -> None:
        self.parent_size = parent_size
        self.child_size = child_size
        self.parent_chunker = RecursiveChunker(chunk_size=parent_size)
        self.child_chunker = FixedSizeChunker(chunk_size=child_size, overlap=overlap)

    def chunk_parent_child(self, text: str) -> list[dict[str, str]]:
        if not text:
            return []
        parents = self.parent_chunker.chunk(text)
        results = []
        for p_idx, parent_text in enumerate(parents):
            children = self.child_chunker.chunk(parent_text)
            for c_idx, child_text in enumerate(children):
                results.append({
                    "child_id_suffix": f"p{p_idx}_c{c_idx}",
                    "child_content": child_text,
                    "parent_content": parent_text,
                })
        return results

**Thành viên 2 — Phạm Đình Bảo Khôi**

- **Loại chiến lược:** HeadingStructureChunker
- **Mô tả & lý do chọn:** Cấu trúc heading giúp giữ nguyên mục lớn như "Quy định chung", "Hàng hóa bị cấm", "Vận chuyển". Đối với chính sách Shopee, mỗi section mang một ý chính nên phương pháp này giữ ngữ cảnh tốt hơn khi người dùng hỏi về một phần cụ thể của policy.
- **Code snippet (nếu custom):**

```python
class HeaderMarkdownChunker:
    """Keep heading/clauses intact when they fit; split only within an oversized unit."""

    def __init__(self, chunk_size: int = 1000, *, length_fn: Callable[[str], int] | None = None,
                 max_tokens: int | None = None, overlap: int = 0):
        if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
            raise ValueError('Require chunk_size > overlap >= 0')
        self.chunk_size, self.length_fn, self.max_tokens, self.overlap = chunk_size, length_fn, max_tokens, overlap

    def fits(self, text: str) -> bool:
        return len(text) <= self.chunk_size and (self.length_fn is None or self.max_tokens is None or self.length_fn(text) <= self.max_tokens)

    def split(self, text: str, prefix: str = '') -> list[str]:
        if self.fits(prefix + text):
            return [text]
        if not self.fits(prefix + 'x'):
            raise ValueError('Heading path exceeds the chunk budget')
        # Prefer lettered lists, Roman lists, paragraphs, then sentences. A final
        # whitespace/character split handles a single sentence or token too long.
        patterns = [r'(?m)(?=^\s*\([a-hj-uw-z]\)\s)', r'(?m)(?=^\s*\([ivxlcdm]+\)\s)',
                    r'\n\s*\n', r'\n', r'(?<=[.!?])\s+', r'\s+']

        def divide(value, depth):
            if self.fits(prefix + value):
                return [value]
            if depth == len(patterns):
                pieces = []
                while value:
                    size = min(len(value), self.chunk_size - len(prefix))
                    while size and not self.fits(prefix + value[:size]):
                        size -= 1
                    if size == 0:
                        raise ValueError('No text fits after heading prefix')
                    pieces.append(value[:size])
                    value = value[size:]
                return pieces
            # Keep separators to avoid dropping punctuation/source evidence.
            bounds = [0] + [m.end() if m.end() > m.start() else m.start() for m in re.finditer(patterns[depth], value)] + [len(value)]
            parts = [value[a:b] for a,b in zip(bounds,bounds[1:]) if b > a]
            if len(parts) <= 1:
                return divide(value, depth + 1)
            out, current = [], ''
            for part in parts:
                if self.fits(prefix + current + part):
                    current += part
                else:
                    if current.strip():
                        out.extend(divide(current.strip(), depth + 1))
                    current = part
            if current.strip():
                out.extend(divide(current.strip(), depth + 1))
            return out

        pieces = divide(text, 0)
        # Optional small overlap is confined to this unit and included only if it fits.
        if self.overlap:
            for i in range(len(pieces) - 1, 0, -1):
                tail = pieces[i-1][-self.overlap:]
        if self.fits(prefix + tail + '\n' + pieces[i]):
                    pieces[i] = tail + '\n' + pieces[i]
        return pieces

    def chunk(self, text: str) -> list[str]:
        return [d.content for d in self.chunk_document(text)]

    def chunk_document(self, text: str, source: str = '', metadata: dict | None = None) -> list[Document]:
        meta, units = parse_units(text, source, metadata)
        docs = []
        for unit in units:
            prefix = unit.heading_path + '\n\n'
            pieces = self.split(unit.text, prefix)
            for piece in pieces:
                index = len(docs)
                content = prefix + piece
                identity = json.dumps([meta['doc_id'], source, unit.heading_path, index, content], ensure_ascii=False)
                chunk_id = meta['doc_id'] + ':' + sha256(identity.encode()).hexdigest()[:24]
                docs.append(Document(chunk_id, content, {**meta, 'heading_path': unit.heading_path,
                    'section': unit.section, 'clause': unit.clause, 'chunk_index': index,
                    'chunk_id': chunk_id, 'fallback_split': len(pieces) > 1,
                    'major_section_crossings': 0, 'source_start': unit.start, 'source_end': unit.end}))
        return docs
````

#### Thành viên 3 — Nguyễn Thùy Linh

- **Loại chiến lược:** Sentence-based chunking
- **Mô tả & lý do chọn cho chủ đề này:** Chunk theo câu thích hợp vì tài liệu có cấu trúc rõ ràng, các khái niệm được phát biểu trong từng câu và đoạn. Với mục tiêu trả lời câu hỏi chính xác, việc giữ nguyên ranh giới ý và không cắt ngang giữa các câu đóng vai trò rất quan trọng.
- **Code snippet:**

```python
from src.chunking import SentenceChunker

text = "Python is a high-level programming language. It is widely used in AI."
chunker = SentenceChunker(max_sentences_per_chunk=2)
chunks = chunker.chunk(text)
print(chunks)
```

**Thành viên 4 — Phạm Thị Thùy Linh**

- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn:** Tôi chọn `RecursiveChunker` vì phương pháp này ưu tiên giữ các đoạn lớn có nghĩa, sau đó mới tách tiếp theo dòng, câu và từ khi đoạn vượt quá kích thước cho phép. Điều này phù hợp với policy Shopee vì vừa giữ được ngữ cảnh của từng mục, vừa xử lý được các mục dài hoặc danh sách nhiều điều kiện.
- **Code snippet (nếu custom):**

```python
RecursiveChunker(chunk_size=500)
```

### So Sánh Giữa Các Thành Viên

| Thành viên         | Chiến lược (Strategy)   | Điểm truy xuất (/10) | Điểm mạnh                                                                                   | Điểm yếu                                                                              |
| ------------------ | ----------------------- | -------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Văn Thành Huy      | Parent-child            | 9.0                  | Tìm kiếm bằng vector nhỏ cực kỳ nhạy, trả về context Parent lớn giúp LLM có đầy đủ ngữ cảnh | Tốn bộ nhớ index; cấu trúc quản lý quan hệ parent-child phức tạp hơn                  |
| Phạm Đình Bảo Khôi | HeadingStructureChunker | 9.0                  | Gắn kèm heading path vào chunk; giữ trọn vẹn từng điều khoản chuyên biệt, không bị vỡ ý     | Các section quá dài vẫn phải fallback split; chunk có thể có kích thước chênh lệch    |
| Nguyễn Thùy Linh   | SentenceChunker         | 8.0                  | Rất tốt cho các câu hỏi chi tiết, tra cứu điều kiện cụ thể hoặc danh sách cấm               | Dễ mất bối cảnh điều khoản lớn nếu câu đứng độc lập không có tiêu đề kèm theo         |
| Phạm Thị Thùy Linh | RecursiveChunker        | 7.5                  | Kích thước chunk đều đặn (~500 ký tự), dễ tinh chỉnh ngữ cảnh và triển khai chuẩn mực       | Đôi khi cắt ngang giữa một điều khoản con hoặc danh mục điều kiện nếu quá ngưỡng size |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> HeadingStructureChunker và Parent-Child Chunker là hai chiến lược hiệu quả nhất cho tập văn bản pháp lý và chính sách sàn Shopee. Do đặc thù tài liệu được tổ chức chặt chẽ theo các Mục, Điều và Khoản, việc duy trì cấu trúc phân cấp (hoặc kèm heading path vào chunk) giúp bộ tìm kiếm không bị mất ngữ cảnh của điều khoản lớn khi truy xuất các câu lệnh điều kiện chi tiết.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| #   | Câu hỏi (Query)                                                     | Câu trả lời chuẩn (Gold Answer)                                                                                                                                              | Chunk nào chứa thông tin?                                                                 |
| --- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1   | Người bán cần làm gì để đăng bán đúng quy định trên Shopee?         | Người bán phải đảm bảo tên sản phẩm, hình ảnh, mô tả, danh mục ngành hàng, nguồn gốc và bảo hành phù hợp; không được sử dụng hình ảnh sai, mô tả sai hoặc vi phạm pháp luật. | shopee-quy-dinh-dang-ban-san-pham.md — Mục Quy định chung / Tiêu chuẩn đăng bán           |
| 2   | Sản phẩm nào bị Shopee cấm hoặc hạn chế bán?                        | Các nhóm hàng như vũ khí, chất nguy hiểm, ma túy, thiết bị giám sát, nội dung nhạy cảm, hàng giả và các mặt hàng vi phạm pháp luật hoặc quyền sở hữu trí tuệ.                | shopee-quy-dinh-dang-ban-san-pham.md — Danh mục hàng hóa cấm kinh doanh                   |
| 3   | Nếu hàng hóa dễ vỡ hoặc nguy hiểm, Shopee có quy định gì?           | Hàng dễ vỡ, hàng hóa nguy hiểm hoặc có rủi ro vận chuyển cao cần đóng gói đặc biệt, có cảnh báo rõ ràng và có thể bị từ chối vận chuyển nếu không đủ điều kiện.              | shopee-chinh-sach-doi-tra-hoan-tien.md — Điều kiện & Thời hạn trả hàng                    |
| 4   | Người mua có thể khiếu nại khi hàng vận chuyển bị hư hỏng không?    | Có, người mua hoặc người bán có thể gửi khiếu nại trong thời hạn quy định và cần cung cấp hình ảnh/video, biên bản đồng kiểm, hóa đơn và bằng chứng liên quan.               | shopee-chinh-sach-bao-mat.md — Thu thập, sử dụng và chia sẻ thông tin                     |
| 5   | Ai chịu trách nhiệm nếu hàng hóa đóng gói sai quy cách gây hư hỏng? | Người bán chịu trách nhiệm về đóng gói sai quy cách; Shopee có thể từ chối bồi thường nếu nguyên nhân do lỗi đóng gói của người bán.                                         | shopee-chinh-sach-bao-hanh-mall.md — Quy trình & Điều kiện tiếp nhận bảo hành Shopee Mall |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| #   | Câu hỏi                                                  | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú                                                                           |
| --- | -------------------------------------------------------- | ------------------------------- | ------------------------------- | --------------------------------------------------------------------------------- |
| 1   | Người bán cần làm gì để đăng bán đúng quy định?          | HeadingStructureChunker         | Có                              | Section "Quy định đăng bán" giữ nguyên ngữ cảnh các tiêu chí hình ảnh/mô tả       |
| 2   | Sản phẩm nào bị Shopee cấm hoặc hạn chế bán?             | SentenceChunker                 | Có                              | Danh sách các gạch đầu dòng hàng cấm khớp rất mạnh theo câu                       |
| 3   | Hàng hóa dễ vỡ/ nguy hiểm có quy định gì?                | SentenceChunker                 | Có                              | Child tìm đúng mốc thời gian (3/7/15 ngày), Parent cung cấp đủ điều kiện kèm theo |
| 4   | Người mua có thể khiếu nại khi vận chuyển hư hỏng không? | HeadingStructureChunker         | Có                              |

Nhờ metadata category=privacy-policy loại trừ toàn bộ nhiễu từ các văn bản khác |
| 5 | Ai chịu trách nhiệm nếu đóng gói sai? | SentenceChunker | Có | Truy xuất chính xác quy trình bảo hành của Mall mà không bị lẫn với chính sách hoàn tiền |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Có, metadata đóng vai trò quyết định trong việc giảm nhiễu truy xuất. Cụ thể:

Câu 1 & Câu 2: Lọc theo audience=seller và category=seller-rules giúp hệ thống không bị nhầm lẫn với các điều khoản trách nhiệm chung của người mua trong shopee-dieu-khoan-dich-vu.md.

Câu 4: Lọc theo category=privacy-policy giúp nhắm thẳng vào văn bản chính sách bảo mật, loại bỏ hoàn toàn các đề cập rải rác về "bảo mật tài khoản/mật khẩu" xuất hiện trong Điều khoản dịch vụ.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> - Tầm quan trọng của Cấu trúc văn bản: Đối với tài liệu pháp lý, chính sách nền tảng (Policy documents), các phương pháp chunking tôn trọng cấu trúc cây phân cấp (HeadingStructureChunker, Parent-Child) luôn vượt trội so với cắt theo độ dài cố định (FixedSize) vì chúng bảo toàn được mối liên hệ giữa Điều luật lớn và Khoản nhỏ.
> - Chiến lược lai (Hybrid Context): Child chunk nhỏ (~300 ký tự) giúp embedding có mật độ ngữ nghĩa cao (dense), giúp vector search đạt top-1 rất chuẩn xác; trong khi Parent chunk (~1200 ký tự) cung cấp đầy đủ điều kiện loại trừ cho LLM sinh câu trả lời mà không bị ảo giác.
> - Sức mạnh của Metadata Filtering: Kết hợp lọc trước (pre-filtering) theo audience và category giúp giảm đáng kể không gian tìm kiếm, loại trừ hoàn toàn các tài liệu đồng âm khác nghĩa hoặc quy định chéo giữa Buyer và Seller.

**Bài học rút ra khi so sánh trong nhóm:**

> Không có một chiến lược chunking nào tối ưu tuyệt đối cho mọi loại truy vấn: SentenceChunker xuất sắc trong việc tìm các dữ kiện liệt kê ngắn (như danh mục hàng cấm), nhưng lại đuối sức trước các câu hỏi đòi hỏi bối cảnh quy trình (Trả hàng hoàn tiền). Việc tiền xử lý (clean markdown, chuẩn hóa heading) quyết định đến 60% chất lượng của các bộ chunker ngữ nghĩa.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> Nhóm sẽ triển khai mô hình Hybrid Chunking (Heading-aware Parent-Child): Sử dụng các thẻ Heading H1/H2/H3 để tự động định nghĩa Parent Chunks thay vì cắt Parent bằng Recursive cố định. Bổ sung thêm trường metadata clause_type (định nghĩa / chế tài / quy trình / mốc thời gian) để cho phép người dùng lọc chuyên sâu hơn nữa.

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                 | Điểm tự đánh giá |
| ---------------------------------------- | ---------------- |
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10          |
| Thiết kế chiến lược (Strategy Design)    | 15 / 15          |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10          |
| Thuyết trình (Demo)                      | 5 / 5            |
| **Tổng phần nhóm**                       | **40 / 40**      |
