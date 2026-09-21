# Structural Markdown benchmark

This addition is self-contained under `benchmark/`; it reuses `src.Document`,
`src.EmbeddingStore`, the existing fixed-size/recursive chunkers, and `src.LocalEmbedder`.
No source policy file, existing benchmark file, or existing source implementation
is modified. `question.md`, `bench.py`, and `result.txt` retain their prior contents.

## Run

From the repository root:

```bash
python -m benchmark.run_structural
python -m pytest tests benchmark/test_structural.py -v -o cache_dir=benchmark/.pytest_cache --basetemp=benchmark/.test_tmp
```

The runner uses the repository's multilingual local model. It records the actual
backend, checks full token lengths (including headings and special tokens), and
stops with a setup message if the model is unavailable. It never falls back to
hash embeddings. Install `requirements-local.txt` if needed. The first run may
download weights; `.model_cache/` is ignored by Git. Unit tests remain offline.

## Reuse the chunker

```python
from pathlib import Path
from benchmark.structural_chunking import HeaderMarkdownChunker
from src import EmbeddingStore, LocalEmbedder

embedder = LocalEmbedder()
count = lambda text: len(embedder.model.tokenizer.encode(
    text, truncation=False, add_special_tokens=True, verbose=False))
chunker = HeaderMarkdownChunker(
    chunk_size=1000, length_fn=count, max_tokens=embedder.model.max_seq_length)
source = 'data/ecommerce/shopee-dieu-khoan-dich-vu.md'
docs = chunker.chunk_document(Path(source).read_text(), source=source)
store = EmbeddingStore('policies', embedding_fn=embedder)
store.add_documents(docs)
results = store.search_with_filter(
    'Ai chịu rủi ro vận chuyển?', top_k=3,
    metadata_filter={'doc_id': 'shopee-dieu-khoan-dich-vu'})
```

`chunk(text)` returns strings, matching existing chunker APIs.
`chunk_document(text, source, metadata)` returns `Document` objects with stable
content-derived IDs and scalar metadata compatible with both storage backends.
The store preserves its existing append semantics and adds an internal index to
record IDs. The benchmark exposes the canonical stable `chunk_id` as result `id`
and records the store ID separately. Reordering document ingestion does not
change canonical chunk IDs. Changing content or its location can change its ID.

Front matter supports the flat scalar YAML schema of these documents. Complex
YAML is explicitly rejected, not guessed. Ordinary ATX headings through level 6,
unmarked uppercase numbered sections, numbered clauses, lettered/Roman lists,
paragraphs and sentences are recognized. An individual sentence larger than the
model budget must ultimately be split at whitespace (or characters for one very
long token). Heading prefixes are always repeated; overlap defaults to zero.

The fixed-size and recursive baselines use shared front-matter removal and
major-section isolation, then their existing implementations, followed by the
same token-budget enforcement. They therefore compare safe, section-isolated
versions of the repository baselines, not raw document-wide chunking.

## Files

- `structural_chunking.py`: reusable parser and chunker.
- `run_structural.py`: mixed-document retrieval, evidence evaluation and reporting.
- `build_structural_questions.py`: rebuilds and verifies the separate gold dataset.
- `structural_questions.json`: five questions, gold answers, source clauses and evidence.
- `test_structural.py`: focused offline tests.
- `structural_report.md`: comparison, statistics, top-3 text and failure analysis.
- `structural_results.json`: complete chunk records, scores, judgments and source hashes.
- `structural_review.json`: manual review rationales for all 45 retrieved results.
- `structural_tests.txt`, `structural_run.log`: captured validation logs.
- `structural_completion.md`: final changes, validation and results summary.
- `.gitignore`: excludes local model, bytecode and test caches.

Gold evidence matching checks complete answer propositions, not keywords. The
review also credits the deadline reminder as partial evidence, while requiring
all deadline cases for full support. No LLM answer-generation quality is claimed.
See the report for the rubric interpretation and the five-question limitation.
