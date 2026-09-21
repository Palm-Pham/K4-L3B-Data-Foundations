# Completion summary

Implemented and evaluated structural Markdown chunking for exactly the two requested documents. All additions and generated outputs are under `benchmark/`. Existing source files, the two policy documents, and `benchmark/question.md`, `bench.py`, and `result.txt` were not modified.

## Files created

- `.gitignore`
- `README_structural.md`
- `structural_chunking.py`
- `run_structural.py`
- `build_structural_questions.py`
- `structural_questions.json`
- `test_structural.py`
- `structural_report.md`
- `structural_results.json`
- `structural_review.json`
- `structural_tests.txt`
- `structural_run.log`
- `structural_completion.md`

Runtime files also exist in ignored `.model_cache/` (approximately 458 MB), `.pytest_cache/`, `.test_tmp/`, and `__pycache__/`. No dependency was added to the repository requirements. The already installed local-embedding dependencies were used; model weights were downloaded into the benchmark folder.

## Validation

Command: `python -m pytest tests benchmark/test_structural.py -v -o cache_dir=benchmark/.pytest_cache --basetemp=benchmark/.test_tmp`

Result: **73 passed** — 42 existing tests plus 31 focused cases. Coverage includes both vector-store backends, source traceability and metadata filters, front matter, heading hierarchy, unmarked sections, bounded splitting, stable IDs, document/section isolation, evidence scoring, and explicit failure when no semantic backend is available.

Semantic benchmark command: `python -m benchmark.run_structural`

Backend: **sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2**, 384 dimensions, 128-token input limit. Actual retrieval backend: **Chroma**, default squared-L2 distance; reported score is `1 - distance`. All embeddings are normalized. Both documents are indexed together for each strategy. No mock embedding is used for quality evaluation.

## Final scores

| Strategy | Total chunks | Hit@1 | Hit@3 | MRR | Full answer support | Rubric |
|---|---:|---:|---:|---:|---:|---:|
| Fixed-size | 312 | 80% | 80% | 0.800 | 60% | 7/10 |
| Recursive | 303 | 60% | 80% | 0.700 | 60% | 7/10 |
| Header-based | 393 | 60% | 80% | 0.700 | 40% | 6/10 |

Hit metrics include useful partial evidence. The report separately distinguishes complete support. Every strategy has zero major-section crossings. Source SHA-256 checks confirm that the documents are unchanged.

Header-based chunking **did not improve retrieval** under this model and budget. The heading path improves provenance but consumes tokens, causing more clause fragmentation.

All five questions are fully answerable from the corpus; none is only partially supported by the source documents. Retrieval has limitations: Q4 is unsupported by every strategy's top 3; Q5 has only partial deadline evidence for every strategy; header Q1 omits the Shopee liability exclusion included in the gold answer. Questions 2 and 3 are fully supported by every strategy.

Read `structural_report.md` for the configuration, per-document length/fallback statistics, all top-3 text and scores, rubric interpretation, and failure analysis. `structural_review.json` records manual rationales for all 45 retrieved results.
