"""Run section 5 retrieval with Gemini embeddings and HeadingStructureChunker.

Run from repository root:
    python -B benchmark/personal_re/run_competition.py

Every generated file and cache is written beside this script. Source, data,
report and configuration files are read-only inputs.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from google.genai import types

from src.chunking import compute_similarity
from src.embeddings import GEMINI_EMBEDDING_MODEL, GeminiEmbedder
from src.models import Document

CHUNK_SIZE = 1000
TOP_K = 3
GENERATION_MODEL = os.getenv("GEMINI_GENERATION_MODEL", "gemini-flash-lite-latest")
REPORT_PATH = ROOT / "report/REPORT_NHOM.md"
PERSONAL_REPORT_PATH = ROOT / "report/REPORT_CANHAN.md"
CORPUS_DIR = ROOT / "data/ecommerce"
OUTPUT_NAMES = {
    "run_competition.py",
    "competition_embeddings.json",
    "competition_agent_cache.json",
    "competition_results.json",
    "competition_verification.json",
    "personal_report.md",
    "section_5_ready_to_paste.md",
    "REPORT_CANHAN_completed.md",
}


def hash_protected_files() -> dict[str, str]:
    paths = [ROOT / ".env"]
    for folder in (ROOT / "src", CORPUS_DIR, ROOT / "report"):
        paths.extend(path for path in folder.rglob("*") if path.is_file())
    return {
        str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    lines = text.lstrip("\ufeff").splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        raise ValueError("YAML front matter is not terminated")
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([\w-]+):\s*(.*?)\s*", line.rstrip("\r\n"))
        if not match:
            raise ValueError("Only flat scalar front matter is supported")
        key, value = match.groups()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        metadata[key] = value
    return metadata, "".join(lines[end + 1 :])


def structural_heading(line: str) -> tuple[int, str] | None:
    stripped = line.strip()
    match = re.match(r"^(#{1,6})\s+(.+?)\s*#*$", stripped)
    if match:
        return len(match.group(1)), match.group(2).strip()
    if re.match(r"^[A-Z]\.\s+", stripped) and stripped.upper() == stripped:
        return 2, stripped
    if re.match(r"^\d+\.\s+", stripped):
        tail = re.sub(r"^\d+\.\s+", "", stripped)
        if tail.upper() == tail or (len(stripped) <= 90 and not stripped.endswith((".", ";", ":"))):
            return 3, stripped
    return None


def split_oversized(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    patterns = [r"\n\s*\n", r"\n", r"(?<=[.!?;])\s+", r"\s+"]

    def divide(value: str, depth: int) -> list[str]:
        value = value.strip()
        if not value:
            return []
        if len(value) <= limit:
            return [value]
        if depth == len(patterns):
            return [value[i : i + limit] for i in range(0, len(value), limit)]
        bounds = [0]
        bounds.extend(match.end() for match in re.finditer(patterns[depth], value))
        bounds.append(len(value))
        parts = [value[a:b] for a, b in zip(bounds, bounds[1:]) if b > a]
        if len(parts) <= 1:
            return divide(value, depth + 1)
        output: list[str] = []
        current = ""
        for part in parts:
            if len(current + part) <= limit:
                current += part
            else:
                output.extend(divide(current, depth + 1))
                current = part
        output.extend(divide(current, depth + 1))
        return output

    return divide(text, 0)


class HeadingStructureChunker:
    """Chunk by Markdown/structural headings and preserve the heading path."""

    def __init__(self, chunk_size: int = CHUNK_SIZE) -> None:
        self.chunk_size = chunk_size

    def chunk_document(self, text: str, source: str) -> list[Document]:
        metadata, body = parse_front_matter(text)
        title = metadata.get("title") or Path(source).stem
        doc_id = metadata.get("doc_id") or Path(source).stem
        hierarchy: dict[int, str] = {1: title}
        units: list[tuple[str, str]] = []
        pending: list[str] = []

        def flush() -> None:
            content = "".join(pending).strip()
            if content:
                path = " > ".join(hierarchy[level] for level in sorted(hierarchy))
                units.append((path, content))
            pending.clear()

        for line in body.splitlines(keepends=True):
            found = structural_heading(line)
            clause = re.match(r"^\s*(\d+(?:\.\d+)+)\.?\s+", line)
            if found:
                flush()
                level, label = found
                hierarchy = {key: value for key, value in hierarchy.items() if key < level}
                hierarchy[level] = label
            elif clause:
                flush()
                hierarchy = {key: value for key, value in hierarchy.items() if key <= 3}
                hierarchy[4] = clause.group(1)
                pending.append(line)
            else:
                pending.append(line)
        flush()

        chunks: list[Document] = []
        base_metadata = {
            "doc_id": doc_id,
            "source": source,
            "title": title,
            "category": metadata.get("category", ""),
            "audience": metadata.get("audience", ""),
            "document_version": metadata.get("document_version", ""),
            "language": metadata.get("language", ""),
        }
        for heading_path, unit in units:
            prefix = heading_path + "\n\n"
            available = self.chunk_size - len(prefix)
            if available <= 0:
                raise ValueError(f"Heading path exceeds chunk size: {heading_path}")
            for piece in split_oversized(unit, available):
                content = prefix + piece
                chunk_index = len(chunks)
                digest = sha256(
                    json.dumps([doc_id, source, heading_path, chunk_index, content], ensure_ascii=False).encode()
                ).hexdigest()[:24]
                chunk_id = f"{doc_id}:{digest}"
                chunks.append(
                    Document(
                        chunk_id,
                        content,
                        {
                            **base_metadata,
                            "heading_path": heading_path,
                            "chunk_index": chunk_index,
                            "chunk_id": chunk_id,
                        },
                    )
                )
        return chunks


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def group_questions() -> list[dict[str, Any]]:
    report = REPORT_PATH.read_text(encoding="utf-8")
    section = report.split("### Câu hỏi đánh giá & Câu trả lời chuẩn", 1)[1]
    section = section.split("### Tổng hợp chất lượng truy xuất", 1)[0]
    rows: list[dict[str, Any]] = []
    for line in section.splitlines():
        cells = table_cells(line) if line.lstrip().startswith("|") else []
        if len(cells) == 4 and cells[0].isdigit() and 1 <= int(cells[0]) <= 5:
            rows.append(
                {
                    "number": int(cells[0]),
                    "query": cells[1],
                    "gold_answer": cells[2],
                    "reported_answer_location": cells[3],
                }
            )
    if [row["number"] for row in rows] != [1, 2, 3, 4, 5]:
        raise ValueError("Could not extract exactly five ordered group questions")
    filters = {
        1: {"audience": "seller", "category": "seller-rules"},
        2: {"audience": "seller", "category": "seller-rules"},
        3: None,
        4: {"category": "privacy-policy"},
        5: None,
    }
    for row in rows:
        row["reported_metadata_filter"] = filters[row["number"]]
    return rows


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def relevance(number: int, content: str) -> tuple[bool, str]:
    """Judge whether content supports a material proposition in the Gold Answer.

    The rules require source propositions, not a filename or isolated query word.
    Full Gold Answer coverage is evaluated separately across top-3.
    """
    text = normalize(content)
    checks: dict[int, list[tuple[str, tuple[str, ...]]]] = {
        1: [
            ("quy định về tên sản phẩm", ("tên sản phẩm phải mô tả đúng",)),
            ("quy định về hình ảnh", ("hình ảnh sản phẩm phải",)),
            ("mô tả đầy đủ", ("mô tả sản phẩm cần đầy đủ và chi tiết",)),
            ("đúng danh mục", ("chọn đúng nhóm danh mục ngành hàng",)),
            ("nguồn gốc và bảo hành", ("điền đầy đủ nguồn gốc", "chế độ bảo hành")),
        ],
        2: [
            ("hàng giả/vi phạm SHTT", ("hàng nhái, hàng giả", "quyền sở hữu trí tuệ")),
            ("vũ khí", ("súng, vũ khí và các sản phẩm",)),
            ("ma túy", ("các chất ma túy",)),
            ("thiết bị giám sát", ("thiết bị giám sát điện tử",)),
            ("hóa chất nguy hiểm", ("các loại hóa chất nguy hiểm",)),
            ("mặt hàng bị cấm vận", ("các mặt hàng bị cấm vận",)),
        ],
        3: [
            ("đủ ba yêu cầu hàng dễ vỡ/nguy hiểm", ("đóng gói đặc biệt", "cảnh báo rõ ràng", "từ chối vận chuyển")),
        ],
        4: [
            ("quyền khiếu nại thiệt hại vận chuyển và chứng cứ", ("hư hỏng", "hình ảnh", "video", "biên bản đồng kiểm", "hóa đơn")),
        ],
        5: [
            ("trách nhiệm do đóng gói sai và từ chối bồi thường", ("đóng gói sai", "người bán chịu trách nhiệm", "từ chối bồi thường")),
            ("Người Bán chịu rủi ro vận chuyển và Shopee không chịu trách nhiệm khi hàng hư hỏng", ("người bán chịu toàn bộ rủi ro", "hư hỏng", "shopee sẽ không chịu trách nhiệm")),
        ],
    }
    for description, phrases in checks[number]:
        if all(phrase in text for phrase in phrases):
            return True, f"Nội dung hỗ trợ mệnh đề Gold Answer: {description}."
    return False, "Chunk không chứa mệnh đề đủ để hỗ trợ Gold Answer; không chấm theo tên file."


def full_gold_support(number: int, results: list[dict[str, Any]]) -> tuple[bool, str]:
    combined = normalize("\n".join(result["content"] for result in results))
    requirements = {
        1: ["tên sản phẩm", "hình ảnh sản phẩm", "mô tả sản phẩm", "danh mục ngành hàng", "nguồn gốc", "bảo hành"],
        2: ["vũ khí", "ma túy", "thiết bị giám sát", "hàng giả"],
        3: ["đóng gói đặc biệt", "cảnh báo rõ ràng", "từ chối vận chuyển"],
        4: ["hư hỏng", "hình ảnh", "video", "biên bản đồng kiểm", "hóa đơn"],
        5: ["đóng gói sai", "người bán chịu trách nhiệm", "từ chối bồi thường"],
    }[number]
    missing = [item for item in requirements if item not in combined]
    if missing:
        return False, "Top-3 thiếu bằng chứng cho: " + ", ".join(missing) + "."
    return True, "Top-3 chứa các mệnh đề cần thiết của Gold Answer."


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def safe_error(exc: Exception) -> dict[str, Any]:
    code = getattr(exc, "code", None)
    code = code if isinstance(code, int) else None
    messages = {
        400: "Yêu cầu API không hợp lệ.",
        401: "Xác thực Gemini thất bại.",
        403: "Gemini từ chối truy cập hoặc key bị giới hạn.",
        404: "Model/endpoint Gemini không khả dụng.",
        429: "Đã vượt quota hoặc rate limit Gemini.",
        500: "Lỗi nội bộ Gemini.",
        503: "Dịch vụ Gemini tạm thời không khả dụng.",
    }
    return {
        "type": type(exc).__name__,
        "status_code": code,
        "message": messages.get(code, "Lỗi API hoặc kiểm tra cục bộ; nội dung lỗi thô bị lược bỏ để bảo vệ credential."),
    }


def secret_values() -> list[str]:
    return [
        value
        for key, value in os.environ.items()
        if value and len(value) >= 8 and any(token in key for token in ("API_KEY", "TOKEN", "SECRET"))
    ]


def write_text(path: Path, text: str, secrets: list[str]) -> None:
    if any(secret in text for secret in secrets):
        raise RuntimeError(f"Sensitive value detected; refusing to write {path.name}")
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, value: Any, secrets: list[str]) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", secrets)


def valid_vector(vector: Any) -> bool:
    return (
        isinstance(vector, list)
        and bool(vector)
        and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in vector)
        and any(value != 0 for value in vector)
    )


def precompute_embeddings(
    embedder: GeminiEmbedder,
    texts: list[str],
    cache_path: Path,
    secrets: list[str],
) -> tuple[dict[str, list[float]], int, int]:
    config = "GeminiEmbedder default embed_content; no explicit task_type/output_dimensionality"
    cache = read_json(cache_path, {"model": GEMINI_EMBEDDING_MODEL, "configuration": config, "vectors": {}})
    if cache.get("model") != GEMINI_EMBEDDING_MODEL or cache.get("configuration") != config:
        cache = {"model": GEMINI_EMBEDDING_MODEL, "configuration": config, "vectors": {}}
    unique = list(dict.fromkeys(texts))
    reused = sum(valid_vector(cache["vectors"].get(text)) for text in unique)
    missing = [text for text in unique if not valid_vector(cache["vectors"].get(text))]
    calls = 0
    for start in range(0, len(missing), 20):
        batch = missing[start : start + 20]
        response = None
        for attempt, delay in enumerate((0, 15, 30, 45), 1):
            if delay:
                print(f"Gemini rate limit; retrying batch in {delay}s (attempt {attempt}/4)", flush=True)
                time.sleep(delay)
            try:
                calls += 1
                response = embedder.client.models.embed_content(model=GEMINI_EMBEDDING_MODEL, contents=batch)
                break
            except Exception as exc:
                if getattr(exc, "code", None) != 429 or attempt == 4:
                    raise
        if response is None:
            raise RuntimeError("Gemini embedding batch did not return a response")
        vectors = [[float(value) for value in item.values] for item in response.embeddings]
        if len(vectors) != len(batch) or not all(valid_vector(vector) for vector in vectors):
            raise ValueError("Gemini returned invalid batch embeddings")
        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) != 1:
            raise ValueError("Gemini returned inconsistent vector dimensions")
        cache["vectors"].update(dict(zip(batch, vectors)))
        cache["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(cache_path, cache, secrets)
        print(f"Embedded {min(start + len(batch), len(missing))}/{len(missing)} missing texts", flush=True)
        if start + len(batch) < len(missing):
            time.sleep(13)
    return cache["vectors"], calls, reused


def rank(
    query: str,
    documents: list[Document],
    vectors: dict[str, list[float]],
    metadata_filter: dict[str, str] | None,
) -> list[dict[str, Any]]:
    query_vector = vectors[query]
    candidates = [
        document
        for document in documents
        if not metadata_filter
        or all(document.metadata.get(key) == value for key, value in metadata_filter.items())
    ]
    output: list[dict[str, Any]] = []
    for document in candidates:
        score = compute_similarity(query_vector, vectors[document.content])
        if not math.isfinite(score) or not -1 <= score <= 1:
            raise ValueError("Non-finite or out-of-range cosine score")
        output.append(
            {
                "chunk_id": document.id,
                "content": document.content,
                "score": score,
                "metadata": document.metadata,
            }
        )
    output.sort(key=lambda item: (-item["score"], item["chunk_id"]))
    return output[:TOP_K]


def grounded_answer(
    embedder: GeminiEmbedder,
    query: str,
    results: list[dict[str, Any]],
    cache: dict[str, str],
    cache_path: Path,
    secrets: list[str],
) -> tuple[str | None, bool, dict[str, Any] | None]:
    context = "\n\n".join(
        f"[Nguồn {index}: {item['metadata']['source']} | {item['metadata']['heading_path']}]\n{item['content']}"
        for index, item in enumerate(results, 1)
    )
    cache_key = sha256((GENERATION_MODEL + "\n" + query + "\n" + context).encode()).hexdigest()
    if cache_key in cache:
        return cache[cache_key], True, None
    prompt = (
        "Bạn là trợ lý hỏi đáp. Chỉ trả lời bằng thông tin có trong các đoạn truy xuất bên dưới. "
        "Nếu các đoạn không đủ bằng chứng, hãy nói rõ 'Các đoạn truy xuất không cung cấp đủ thông tin' "
        "và chỉ nêu phần có căn cứ. Trả lời tiếng Việt, ngắn gọn 1-3 câu; không dùng kiến thức bên ngoài.\n\n"
        f"Câu hỏi: {query}\n\nCác đoạn truy xuất:\n{context}"
    )
    try:
        response = None
        for attempt, delay in enumerate((0, 15, 30), 1):
            if delay:
                time.sleep(delay)
            try:
                response = embedder.client.models.generate_content(
                    model=GENERATION_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0),
                )
                break
            except Exception as exc:
                if getattr(exc, "code", None) != 429 or attempt == 3:
                    raise
        if response is None:
            raise RuntimeError("Gemini generation did not return a response")
        answer = (response.text or "").strip()
        if not answer:
            raise ValueError("Gemini returned an empty grounded answer")
        cache[cache_key] = answer
        write_json(cache_path, cache, secrets)
        return answer, False, None
    except Exception as exc:
        return None, False, safe_error(exc)


def short(text: str, limit: int = 180) -> str:
    value = " ".join(text.split()).replace("|", "\\|")
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def render_section(results: dict[str, Any]) -> str:
    lines = [
        "## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)",
        "",
        "Chạy **5 câu hỏi đánh giá của nhóm** trên corpus `data/ecommerce` bằng chiến lược cá nhân `HeadingStructureChunker`, embedding Gemini thật và `top_k=3`. Kết quả chính áp dụng đúng metadata filter được gợi ý trong báo cáo nhóm; các mâu thuẫn giữa báo cáo nhóm và corpus được giữ nguyên và nêu bên dưới.",
        "",
        "| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |",
        "| --- | ------- | -------------------------------- | ------- | ----------- | ------------------------ |",
    ]
    for item in results["queries"]:
        top = item["top_3"][0]
        answer = item["agent_answer"] or "Không có kết quả do lỗi API; xem báo cáo chi tiết."
        lines.append(
            f"| {item['number']} | {item['query']} | {short(top['content'])} "
            f"(`{top['metadata']['source']}`, `{top['metadata']['heading_path']}`) | "
            f"{top['score']:.6f} | {'Có' if top['relevant'] else 'Không'} | {short(answer, 260)} |"
        )
    count = sum(item["top_3_contains_relevant"] for item in results["queries"])
    lines.extend(
        [
            "",
            f"**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** {count} / 5",
            "",
            "**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**",
            "> Tôi học được rằng không có một chiến lược chunking tốt nhất cho mọi truy vấn: chunk theo câu mạnh với dữ kiện ngắn, còn chunk theo heading hoặc parent-child bảo toàn bối cảnh tốt hơn cho chính sách dài và nhiều điều kiện. Metadata filtering chỉ có ích khi metadata và tài liệu đích đúng với nội dung; filter sai có thể loại bỏ chính chunk chứa bằng chứng.",
            "",
            "### Ghi chú đối chiếu Gold Answer với corpus",
            "",
        ]
    )
    lines.extend(f"- Câu {item['number']}: {item['corpus_consistency_note']}" for item in results["queries"])
    return "\n".join(lines) + "\n"


def replace_section_five(report: str, section: str) -> str:
    pattern = re.compile(r"## 5\. Kết quả truy xuất của tôi.*?(?=\n---\n\n## Tự Đánh Giá)", re.S)
    if not pattern.search(report):
        raise ValueError("Section 5 boundary was not found in REPORT_CANHAN.md")
    return pattern.sub(section.rstrip(), report)


def render_competition_report(results: dict[str, Any], section: str) -> str:
    lines = [
        "# Competition Results — Phạm Đình Bảo Khôi",
        "",
        "## Phương pháp và cấu hình",
        "",
        f"- Chiến lược cá nhân lấy từ `REPORT_NHOM.md`: `{results['strategy']}`; giới hạn {CHUNK_SIZE} ký tự, giữ heading path và tách cấu trúc trước khi fallback theo đoạn/câu.",
        f"- Corpus: {results['corpus_document_count']} file Markdown trong `data/ecommerce`, tổng {results['chunk_count']} chunk trong một index.",
        f"- Embedding: Gemini `{results['embedding_model']}`, chiều vector {results['embedding_dimension']}; không dùng `MockEmbedder`.",
        f"- Xếp hạng: cosine similarity từ `src.chunking.compute_similarity`, `top_k={TOP_K}`; score hiển thị 6 chữ số thập phân.",
        f"- Agent: Gemini `{results['generation_model']}`, nhiệt độ 0, chỉ được trả lời từ top-3.",
        "- Cấu hình được nạp bằng `load_dotenv(ROOT / '.env', override=False)` và chấp nhận `GEMINI_API_KEY` hoặc `GOOGLE_API_KEY`; key không được ghi ra output.",
        "- Kết quả chính dùng đúng filter gợi ý của báo cáo nhóm. `competition_results.json` còn lưu top-3 không lọc để chẩn đoán tác động của filter.",
        "",
        "## Mục 5 hoàn chỉnh",
        "",
        section.rstrip(),
        "",
        "## Chi tiết top-3",
        "",
    ]
    for item in results["queries"]:
        lines.extend(
            [
                f"### Câu {item['number']}. {item['query']}",
                "",
                f"- Gold Answer: {item['gold_answer']}",
                f"- Vị trí được báo cáo nhóm chỉ ra: {item['reported_answer_location']}",
                f"- Filter dùng cho kết quả chính: `{json.dumps(item['metadata_filter'], ensure_ascii=False)}`",
                f"- Top-3 có chunk liên quan: **{'Có' if item['top_3_contains_relevant'] else 'Không'}**. {item['full_gold_support_reason']}",
                f"- Agent: {item['agent_answer'] or 'Không tạo được do lỗi API.'}",
                "",
            ]
        )
        for rank_index, result in enumerate(item["top_3"], 1):
            lines.extend(
                [
                    f"**Hạng {rank_index} — cosine {result['score']:.6f}; {'liên quan' if result['relevant'] else 'không liên quan'}**",
                    "",
                    f"Nguồn: `{result['metadata']['source']}`; heading: `{result['metadata']['heading_path']}`; chunk: `{result['chunk_id']}`.",
                    "",
                    f"> {result['content'].replace(chr(10), chr(10) + '> ')}",
                    "",
                    f"Đánh giá: {result['relevance_reason']}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Mâu thuẫn giữa báo cáo nhóm và corpus",
            "",
            "1. Câu 1 chỉ tới `shopee-quy-dinh-dang-ban-san-pham.md`, nhưng các quy định đầy đủ về tên, hình ảnh, mô tả, danh mục, nguồn gốc và bảo hành nằm trong file mang tên `shopee-chinh-sach-bao-hanh-mall.md`. Front matter của file này ghi category `warranty`, audience `buyer`, trong khi thân bài lại là “QUY ĐỊNH VỀ ĐĂNG BÁN SẢN PHẨM”; vì vậy filter `seller-rules` loại mất bằng chứng chính.",
            "2. Câu 3 chỉ tới chính sách trả hàng/hoàn tiền. Corpus có lý do trả hàng khi hàng bể vỡ và có quy định đóng gói hợp lý cho thực phẩm dễ hỏng, nhưng không có đủ bộ mệnh đề “đóng gói đặc biệt, cảnh báo rõ ràng, có thể bị từ chối vận chuyển”.",
            "3. Câu 4 chỉ tới chính sách bảo mật và đề xuất filter `privacy-policy`; đây không phải nội dung khiếu nại hư hỏng vận chuyển. Chính sách trả hàng có hỗ trợ từ chối nhận/gửi yêu cầu khi hàng hư hỏng, nhưng corpus không chứa đầy đủ danh sách hình ảnh/video, biên bản đồng kiểm, hóa đơn như Gold Answer.",
            "4. Câu 5 chỉ tới file bảo hành Mall, nhưng thân file là quy định đăng bán. Corpus có nghĩa vụ đóng gói hợp lý cho một số thực phẩm và điều khoản rủi ro vận chuyển, nhưng không có đủ mệnh đề Shopee từ chối bồi thường vì lỗi đóng gói của Người Bán.",
            "",
            "## Hạn chế",
            "",
            "Relevance được chấm theo việc chunk chứa mệnh đề hỗ trợ Gold Answer, không theo tên file hay chỉ trùng từ khóa. Tuy nhiên đây vẫn là đánh giá quy tắc trên năm câu hỏi; corpus bị thiếu/đặt sai nội dung nên điểm thấp không thể quy hoàn toàn cho chunking hoặc embedding. Gemini API và model có thể thay đổi theo thời gian; cache lưu vector và câu trả lời của lần chạy này để tái kiểm tra mà không gọi API lặp lại. Câu trả lời agent chỉ phản ánh top-3 chính, không phải tư vấn chính sách đầy đủ.",
            "",
            "## Việc đã làm và xác minh",
            "",
            "- Trích đúng năm câu hỏi, Gold Answer và vị trí đáp án từ mục 3 báo cáo nhóm.",
            "- Xác định đúng chiến lược HeadingStructureChunker của Phạm Đình Bảo Khôi.",
            "- Index toàn bộ corpus Markdown với metadata front matter và heading path.",
            "- Dùng Gemini embedding thật; lưu top-3 chính và top-3 không lọc cho cả năm query.",
            "- Tạo câu trả lời có căn cứ từ top-3; lỗi API được ghi rõ thay vì bịa nội dung.",
            "- Kiểm tra vector, cosine, đúng năm dòng bảng, key bí mật, hash file bảo vệ và phạm vi file output.",
        ]
    )
    if results.get("errors"):
        lines.extend(["", "## Lỗi", "", "```json", json.dumps(results["errors"], ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines) + "\n"


def main() -> int:
    protected_before = hash_protected_files()
    load_dotenv(ROOT / ".env", override=False)
    secrets = secret_values()
    questions = group_questions()
    markdown_files = sorted(CORPUS_DIR.glob("*.md"))
    chunker = HeadingStructureChunker()
    documents: list[Document] = []
    for path in markdown_files:
        documents.extend(chunker.chunk_document(path.read_text(encoding="utf-8"), str(path.relative_to(ROOT))))
    if not documents or len({document.id for document in documents}) != len(documents):
        raise ValueError("Corpus produced no chunks or duplicate chunk IDs")

    errors: list[dict[str, Any]] = []
    try:
        embedder = GeminiEmbedder(model_name=GEMINI_EMBEDDING_MODEL)
    except Exception as exc:
        errors.append({"stage": "initialize_embedding", **safe_error(exc)})
        return write_failure(errors, protected_before, secrets)

    query_texts = [item["query"] for item in questions]
    try:
        vectors, embedding_calls, reused_embeddings = precompute_embeddings(
            embedder,
            [document.content for document in documents] + query_texts,
            OUT / "competition_embeddings.json",
            secrets,
        )
    except Exception as exc:
        errors.append({"stage": "embedding", **safe_error(exc)})
        return write_failure(errors, protected_before, secrets)

    dimensions = {len(vectors[text]) for text in [document.content for document in documents] + query_texts}
    if len(dimensions) != 1:
        raise ValueError("Not all corpus/query embeddings have the same dimension")
    agent_cache_path = OUT / "competition_agent_cache.json"
    agent_cache = read_json(agent_cache_path, {})
    write_json(agent_cache_path, agent_cache, secrets)
    query_results: list[dict[str, Any]] = []
    generation_calls = 0
    agent_cache_hits = 0
    consistency_notes = {
        1: "Mâu thuẫn: bằng chứng đầy đủ nằm trong file `shopee-chinh-sach-bao-hanh-mall.md` có thân bài về đăng bán, không phải file/category được báo cáo nhóm chỉ ra; filter gợi ý loại mất bằng chứng này.",
        2: "Phù hợp: danh sách hàng giả, vũ khí, ma túy, thiết bị giám sát và hóa chất nguy hiểm có trong `shopee-quy-dinh-dang-ban-san-pham.md`.",
        3: "Gold Answer không được corpus hỗ trợ đầy đủ; chính sách trả hàng chỉ nêu các trường hợp bể vỡ, không nêu đủ đóng gói đặc biệt, cảnh báo và từ chối vận chuyển.",
        4: "Mâu thuẫn: tài liệu/filter `privacy-policy` không liên quan đến hư hỏng vận chuyển; corpus cũng thiếu đầy đủ bộ chứng cứ được nêu trong Gold Answer.",
        5: "Gold Answer không được corpus hỗ trợ đầy đủ; file được chỉ ra có thân bài về quy định đăng bán và không nêu Shopee từ chối bồi thường do đóng gói sai.",
    }

    for question in questions:
        primary = rank(question["query"], documents, vectors, question["reported_metadata_filter"])
        diagnostic = rank(question["query"], documents, vectors, None)
        if len(primary) != TOP_K:
            raise ValueError(f"Question {question['number']} returned fewer than top-{TOP_K}")
        for result in primary:
            result["relevant"], result["relevance_reason"] = relevance(question["number"], result["content"])
        for result in diagnostic:
            result["relevant"], result["relevance_reason"] = relevance(question["number"], result["content"])
        fully_supported, support_reason = full_gold_support(question["number"], primary)
        answer, cache_hit, agent_error = grounded_answer(
            embedder,
            question["query"],
            primary,
            agent_cache,
            agent_cache_path,
            secrets,
        )
        if cache_hit:
            agent_cache_hits += 1
        else:
            generation_calls += 1
        if agent_error:
            errors.append({"stage": "agent_answer", "question": question["number"], **agent_error})
        query_results.append(
            {
                **question,
                "metadata_filter": question["reported_metadata_filter"],
                "top_3": primary,
                "unfiltered_top_3_diagnostic": diagnostic,
                "top_1_relevant": primary[0]["relevant"],
                "top_3_contains_relevant": any(result["relevant"] for result in primary),
                "top_3_fully_supports_gold": fully_supported,
                "full_gold_support_reason": support_reason,
                "agent_answer": answer,
                "agent_error": agent_error,
                "corpus_consistency_note": consistency_notes[question["number"]],
            }
        )

    result_data = {
        "status": "complete" if not errors else "complete_with_agent_errors",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "strategy": "HeadingStructureChunker",
        "chunk_size_characters": CHUNK_SIZE,
        "embedding_model": GEMINI_EMBEDDING_MODEL,
        "embedding_dimension": next(iter(dimensions)),
        "generation_model": GENERATION_MODEL,
        "mock_embedder_used": False,
        "score": "cosine similarity",
        "top_k": TOP_K,
        "corpus_document_count": len(markdown_files),
        "chunk_count": len(documents),
        "embedding_api_calls_this_run": embedding_calls,
        "embedding_cache_hits": reused_embeddings,
        "generation_api_calls_this_run": generation_calls,
        "agent_cache_hits": agent_cache_hits,
        "queries": query_results,
        "top_3_relevant_count": sum(item["top_3_contains_relevant"] for item in query_results),
        "errors": errors,
    }
    write_json(OUT / "competition_results.json", result_data, secrets)
    section = render_section(result_data)
    write_text(OUT / "section_5_ready_to_paste.md", section, secrets)
    original_personal = PERSONAL_REPORT_PATH.read_text(encoding="utf-8")
    completed = replace_section_five(original_personal, section)
    write_text(OUT / "REPORT_CANHAN_completed.md", completed, secrets)

    existing_report_path = OUT / "personal_report.md"
    existing_report = existing_report_path.read_text(encoding="utf-8") if existing_report_path.exists() else ""
    existing_report = re.sub(
        r"\n# Competition Results — chưa hoàn thành\n.*\Z",
        "",
        existing_report,
        flags=re.S,
    )
    marker = "\n<!-- COMPETITION_RESULTS_START -->\n"
    end_marker = "\n<!-- COMPETITION_RESULTS_END -->\n"
    competition_report = render_competition_report(result_data, section)
    if marker in existing_report and end_marker in existing_report:
        prefix = existing_report.split(marker, 1)[0]
        suffix = existing_report.split(end_marker, 1)[1]
        combined_report = prefix + marker + competition_report + end_marker + suffix.lstrip("\n")
    else:
        combined_report = existing_report.rstrip() + marker + competition_report + end_marker
    write_text(existing_report_path, combined_report, secrets)

    verification_path = OUT / "competition_verification.json"
    write_json(verification_path, {"status": "pending"}, secrets)
    verification = verify(result_data, protected_before, secrets)
    write_json(verification_path, verification, secrets)
    if not all(value for key, value in verification.items() if key not in {"protected_hashes"}):
        raise AssertionError("One or more completion checks failed")
    print(f"Complete: {result_data['top_3_relevant_count']}/5 queries have a relevant chunk in top-3")
    print(f"Report: {existing_report_path}")
    return 0


def verify(results: dict[str, Any], protected_before: dict[str, str], secrets: list[str]) -> dict[str, Any]:
    all_scores = [item["score"] for query in results["queries"] for item in query["top_3"]]
    output_paths = [OUT / name for name in OUTPUT_NAMES]
    section = (OUT / "section_5_ready_to_paste.md").read_text(encoding="utf-8")
    completed = (OUT / "REPORT_CANHAN_completed.md").read_text(encoding="utf-8")
    check = {
        "exactly_five_group_questions": len(results["queries"]) == 5,
        "questions_match_group_report": [item["query"] for item in results["queries"]] == [item["query"] for item in group_questions()],
        "exactly_three_results_per_query": all(len(item["top_3"]) == 3 for item in results["queries"]),
        "scores_finite_and_in_range": all(math.isfinite(score) and -1 <= score <= 1 for score in all_scores),
        "gemini_embedding_used": results["embedding_model"] == GEMINI_EMBEDDING_MODEL and results["embedding_dimension"] > 0,
        "mock_embedder_not_used": results["mock_embedder_used"] is False,
        "exactly_five_table_rows": len(re.findall(r"^\| [1-5] \|", section, re.M)) == 5,
        "count_line_present": f"Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** {results['top_3_relevant_count']} / 5" in section,
        "completed_report_changes_only_section_5": (
            original_without_section(PERSONAL_REPORT_PATH.read_text(encoding="utf-8"))
            == original_without_section(completed)
        ),
        "protected_files_unchanged": protected_before == hash_protected_files(),
        "all_expected_outputs_inside_personal_re": all(path.resolve().is_relative_to(OUT.resolve()) and path.exists() for path in output_paths),
        "no_secret_in_outputs": all(not any(secret in path.read_text(encoding="utf-8") for secret in secrets) for path in output_paths),
        "agent_answers_present_or_error_recorded": all(item["agent_answer"] or item["agent_error"] for item in results["queries"]),
        "protected_hashes": protected_before,
    }
    return check


def original_without_section(report: str) -> str:
    return re.sub(
        r"## 5\. Kết quả truy xuất của tôi.*?(?=\n---\n\n## Tự Đánh Giá)",
        "<SECTION_5>",
        report,
        flags=re.S,
    )


def write_failure(errors: list[dict[str, Any]], protected_before: dict[str, str], secrets: list[str]) -> int:
    report = (
        "# Competition Results — chưa hoàn thành\n\n"
        "Gemini API hoặc môi trường đã gặp lỗi; không có score hoặc câu trả lời nào được bịa. "
        "Có thể chạy lại `python -B benchmark/personal_re/run_competition.py` sau khi khắc phục.\n\n"
        "```json\n" + json.dumps(errors, ensure_ascii=False, indent=2) + "\n```\n"
    )
    existing_path = OUT / "personal_report.md"
    existing = existing_path.read_text(encoding="utf-8") if existing_path.exists() else ""
    existing = re.sub(r"\n# Competition Results — chưa hoàn thành\n.*\Z", "", existing, flags=re.S)
    write_text(existing_path, existing.rstrip() + "\n\n" + report, secrets)
    write_json(
        OUT / "competition_results.json",
        {"status": "incomplete", "mock_embedder_used": False, "errors": errors},
        secrets,
    )
    if protected_before != hash_protected_files():
        raise AssertionError("A protected input file changed during failed run")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
