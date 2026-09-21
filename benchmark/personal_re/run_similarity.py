"""Gemini sentence-pair experiment. Outputs stay next to this script.
Run: python -B benchmark/personal_re/run_similarity.py
Successful sentence vectors are cached so reruns do not repeat API calls.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
from src.embeddings import GeminiEmbedder, GEMINI_EMBEDDING_MODEL
from src.chunking import compute_similarity

THRESHOLD = 0.50
PAIRS = [
    ('I want to return a product bought on Shopee.', 'How can I request a refund for a Shopee order?', 'high'),
    ('The seller must properly package the goods.', 'If improper packaging causes damage to the goods, who is responsible?', 'high'),
    ('Shopee prohibits the listing and sale of drugs and weapons.', 'What is the weather like in Hanoi today?', 'low'),
    ('The privacy policy explains how Shopee collects personal data.', 'What purposes does Shopee use user information for?', 'high'),
    ('My order is currently being shipped.', 'I want to change my Shopee account password.', 'low'),
]
RELATIONSHIPS = [
    'Both sentences concern Shopee post-purchase remedies: returning goods and requesting a refund. Their intents are related, though a return and a refund are not identical actions.',
    'Both sentences concern packaging goods; the second asks about responsibility when packaging is improper. This connects a general duty with a possible consequence, rather than expressing the same proposition.',
    'The first sentence concerns prohibited e-commerce listings, while the second asks about weather. They differ in both subject matter and communicative purpose.',
    'Both sentences concern Shopee personal-information practices. Data collection and the purposes of using data are related aspects of privacy, but are distinct questions.',
    'Both could occur in an e-commerce support conversation, but shipment status and changing an account password are different user intents.',
]
CREATED = ['run_similarity.py', 'embeddings_cache.json', 'similarity_results.json', 'verification.json', 'personal_report.md']
REVIEWED = ['src/embeddings.py', 'src/chunking.py', 'report/REPORT_CANHAN.md',
            'data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md',
            'data/ecommerce/shopee-quy-dinh-dang-ban-san-pham.md',
            'data/ecommerce/shopee-chinh-sach-bao-mat.md',
            'data/ecommerce/shopee-dieu-khoan-dich-vu.md']


def valid_vector(vector):
    return (isinstance(vector, list) and bool(vector)
            and all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in vector)
            and any(x != 0 for x in vector))


def protected_manifest():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('src', 'data', 'report') for p in (ROOT / folder).rglob('*') if p.is_file()}


def safe_error(exc):
    # Do not serialize exception bodies/URLs: upstream errors can contain secrets.
    code = getattr(exc, 'code', None)
    code = code if isinstance(code, int) else None
    reasons = {400: 'Invalid API request.', 401: 'Authentication failed.', 403: 'Access denied or key restrictions.',
               404: 'Requested embedding model or endpoint unavailable.', 429: 'Rate limit or quota exhausted.',
               500: 'Gemini internal server error.', 503: 'Gemini service unavailable.'}
    return {'type': type(exc).__name__, 'status_code': code,
            'message': reasons.get(code, 'Embedding request or local validation failed; raw error omitted to protect credentials.')}


def main():
    before = protected_manifest()
    load_dotenv(ROOT / '.env', override=False)
    secrets = [v for k, v in os.environ.items() if v and ('API_KEY' in k or 'TOKEN' in k or 'SECRET' in k) and len(v) >= 8]

    def write(name, value, raw=False):
        text = value if raw else json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if any(secret in text for secret in secrets):
            raise RuntimeError('Sensitive value detected; refusing output')
        (OUT / name).write_text(text, encoding='utf-8')

    cache_path = OUT / 'embeddings_cache.json'
    cache = {'model': GEMINI_EMBEDDING_MODEL, 'provider': 'Gemini API',
             'configuration': 'Existing GeminiEmbedder defaults; no explicit task_type or output_dimensionality', 'vectors': {}}
    if cache_path.exists():
        existing = json.loads(cache_path.read_text())
        if existing.get('model') == cache['model'] and existing.get('configuration') == cache['configuration']:
            cache = existing
    calls = 0
    reused = 0
    error = None
    embedder = None
    for sentence in dict.fromkeys(s for a,b,_ in PAIRS for s in (a,b)):
        if valid_vector(cache['vectors'].get(sentence)):
            reused += 1
            continue
        try:
            if embedder is None:
                embedder = GeminiEmbedder(model_name=GEMINI_EMBEDDING_MODEL)
            calls += 1
            vector = embedder(sentence)
            if not valid_vector(vector):
                raise ValueError('Invalid or zero-norm embedding')
            cache['vectors'][sentence] = vector
            cache['updated_at_utc'] = datetime.now(timezone.utc).isoformat()
            write('embeddings_cache.json', cache)
            print(f'Embedded sentence {len(cache["vectors"])}/10; dimension={len(vector)}', flush=True)
        except Exception as exc:
            error = safe_error(exc)
            print('Embedding stopped:', error['type'], error['status_code'], error['message'], flush=True)
            break
    write('embeddings_cache.json', cache)
    dims = sorted({len(v) for v in cache['vectors'].values() if valid_vector(v)})
    rows = []
    for number, (a,b,prediction) in enumerate(PAIRS, 1):
        va, vb = cache['vectors'].get(a), cache['vectors'].get(b)
        score = None
        if valid_vector(va) and valid_vector(vb) and len(va) == len(vb):
            score = compute_similarity(va, vb)
            if not math.isfinite(score) or not -1 <= score <= 1:
                raise ValueError('Cosine score outside finite [-1,1] range')
        actual = None if score is None else 'high' if score >= THRESHOLD else 'low'
        correct = None if actual is None else prediction == actual
        explanation = RELATIONSHIPS[number-1]
        explanation += (' No measured score is available, so the prediction cannot be evaluated.' if score is None else
                        f' The measured cosine {score:.6f} is {"at or above" if actual == "high" else "below"} 0.50, so it is classified as {actual}; the initial prediction is {"correct" if correct else "incorrect"}.')
        rows.append(dict(pair=number, sentence_a=a, sentence_b=b, prediction=prediction,
                         actual_score=score, actual_classification=actual, correct=correct,
                         embedding_model=GEMINI_EMBEDDING_MODEL, classification_threshold=THRESHOLD,
                         dimension_a=len(va) if valid_vector(va) else None,
                         dimension_b=len(vb) if valid_vector(vb) else None, explanation=explanation))
    complete = all(r['actual_score'] is not None for r in rows) and len(dims) == 1
    correct_count = sum(r['correct'] is True for r in rows)
    unexpected = None
    if complete:
        wrong = [r for r in rows if not r['correct']]
        chosen = max(wrong, key=lambda r: abs(r['actual_score']-THRESHOLD)) if wrong else min(rows, key=lambda r: abs(r['actual_score']-THRESHOLD))
        unexpected = chosen['pair']
        if wrong:
            analysis = f"Pair {unexpected} was the most unexpected: its score was {chosen['actual_score']:.6f}, giving {chosen['actual_classification']} instead of the predicted {chosen['prediction']} (the largest threshold deviation among incorrect predictions). "
        else:
            analysis = f"All five predictions were correct; pair {unexpected} was the most unexpected because its score of {chosen['actual_score']:.6f} was closest to the 0.50 threshold (distance {abs(chosen['actual_score']-THRESHOLD):.6f}). "
        interpretation = {
            1: 'The two sentences share a post-purchase context but ask for different actions, returning a product versus obtaining a refund.',
            2: 'The pair links a packaging obligation with a liability question, so its conceptual connection is broader than paraphrase equivalence.',
            3: 'The unrelated prohibited-goods and weather topics make this pair useful for examining the separation of different subject areas.',
            4: 'Collection of personal data and the purposes of using it share a privacy context while addressing different aspects of that context.',
            5: 'Shipment status and password changes share a possible support setting but express different user goals.',
        }
        analysis += interpretation[unexpected] + ' This observation is consistent with embeddings reflecting overlapping topics and intents, but one cosine score does not establish why the model represented the sentences that way.'
    else:
        analysis = 'The most unexpected result cannot be identified reliably because the five-pair experiment did not complete. Missing API measurements cannot support conclusions about how embeddings represent meaning.'
    results = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), status='complete' if complete else 'incomplete',
                   embedding_model=GEMINI_EMBEDDING_MODEL, dimensions=dims, threshold=THRESHOLD,
                   configuration=cache['configuration'], api_calls_this_run=calls, cached_sentences_reused=reused,
                   mock_embedder_used=False, results=rows, correct_predictions=correct_count,
                   evaluated_pairs=sum(r['actual_score'] is not None for r in rows),
                   most_unexpected_pair=unexpected, most_unexpected_analysis=analysis,
                   error=error, reviewed_files=REVIEWED, corpus_files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/ecommerce').iterdir() if p.is_file()))
    table = ['| Pair | Sentence A | Sentence B | Prediction | Actual Score | Actual Classification | Correct? |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        score = 'N/A' if r['actual_score'] is None else f"{r['actual_score']:.6f}"
        table.append(f"| {r['pair']} | {r['sentence_a']} | {r['sentence_b']} | {r['prediction']} | {score} | {r['actual_classification'] or 'N/A'} | {'N/A' if r['correct'] is None else 'Yes' if r['correct'] else 'No'} |")
    table = '\n'.join(table)
    explanations = '\n\n'.join(f"**Pair {r['pair']}:** {r['explanation']}" for r in rows)
    summary = f'Correct predictions: **{correct_count}/5**.' if complete else f'Experiment incomplete: **{results["evaluated_pairs"]}/5** pairs measured; no accuracy claim for all five pairs.'
    snippet = ('## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)\n\n'
               f'Model: `{GEMINI_EMBEDDING_MODEL}`; dimensions: {dims or "unavailable"}; Gemini API, no MockEmbedder. '
               'Cosine = dot(A, B) / (norm(A) × norm(B)); high if cosine ≥ 0.50, otherwise low. '
               'This empirical threshold depends on the model and dataset. The supplied English sentences were embedded unchanged.\n\n'
               + table + '\n\n' + summary + '\n\n' + explanations
               + '\n\n**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**\n\n' + analysis)
    verification = {'all_5_pairs_have_valid_embeddings':complete,
                    'all_10_sentence_embeddings_present':all(valid_vector(cache['vectors'].get(s)) for a,b,_ in PAIRS for s in (a,b)),
                    'same_dimensionality':len(dims)==1 and complete,
                    'all_5_cosines_finite_and_in_range':all(r['actual_score'] is not None and math.isfinite(r['actual_score']) and -1<=r['actual_score']<=1 for r in rows),
                    'exactly_5_result_rows':len(rows)==5, 'unexpected_analysis_sentence_count':3 if complete else 2,
                    'protected_files_unchanged':before==protected_manifest(),
                    'all_created_files_within_benchmark_personal_re':all((OUT/name).resolve().is_relative_to(ROOT/'benchmark/personal_re') for name in CREATED),
                    'sensitive_value_scan_passed':True,
                    'method_checks':{'identical_vectors':compute_similarity([1,0],[1,0])==1,
                                     'orthogonal_vectors':compute_similarity([1,0],[0,1])==0,
                                     'opposite_vectors':compute_similarity([1,0],[-1,0])==-1},
                    'protected_file_sha256':before}
    report = '# Gemini Similarity Predictions — Individual Experiment\n\n'
    report += '## Objective\n\nEvaluate the five supplied high/low predictions using actual Gemini sentence embeddings and a consistent cosine threshold. Sentence wording and predictions are unchanged; the Vietnamese example sentences in the reference report are not substituted.\n\n'
    report += '## Sources reviewed and domain alignment\n\n' + '\n'.join('- `'+f+'`' for f in REVIEWED) + '\n\n'
    report += 'The ecommerce file inventory was reviewed. Return/refund clauses 1.1–1.2 align with pair 1; the product-listing rules discuss packaging and prohibited weapons/drugs (sections 4.5–4.6 and food-packaging requirements), aligning with pairs 2–3; the privacy policy covers collection and use of personal information (sections 4 and 6), aligning with pair 4; terms sections 5 and 13 cover account security and transport, aligning with pair 5. These are domain-aligned experimental sentences, not claimed verbatim quotations or independently verified policy advice. The weather sentence is an intentional unrelated control.\n\n'
    report += f'## Configuration and method\n\n`load_dotenv(ROOT / ".env", override=False)` loads repository configuration while respecting existing environment values. `GeminiEmbedder` accepts `GEMINI_API_KEY` or `GOOGLE_API_KEY`; credentials are never serialized. The model is explicitly taken from `src.embeddings.GEMINI_EMBEDDING_MODEL`: **`{GEMINI_EMBEDDING_MODEL}`**.\n\n'
    report += f'Observed vector dimensions: **{dims or "unavailable"}**. Task type and output dimensionality use the existing wrapper/API defaults; no explicit task type is sent. **MockEmbedder was not used.** There were {calls} API calls and {reused} cached sentence reuses in this run; successful vectors are cached per exact sentence and model/configuration. No chunking or retrieval is involved.\n\n'
    report += '`src.chunking.compute_similarity` computes cosine as dot(A, B) / (sqrt(dot(A, A)) × sqrt(dot(B, B))). Vectors must have equal dimensions, finite values and nonzero norms before use. Classification uses the full-precision score: **high ≥ 0.50; low < 0.50**; displayed scores use six decimals. This threshold is an empirical convention for these five pairs, not a universal embedding threshold.\n\n'
    report += '## Results\n\n' + summary + '\n\n' + table + '\n\n'
    if error:
        report += '### API error\n\n' + json.dumps(error,ensure_ascii=False) + '\n\nRaw response bodies are omitted to protect credentials. No missing similarity values were fabricated.\n\n'
    report += '## Per-pair interpretation\n\n' + explanations + '\n\n## Most unexpected result\n\n' + analysis + '\n\n'
    report += '## Copyable section 4\n\n```markdown\n' + snippet + '\n```\n\n'
    report += '## Files created\n\n' + '\n'.join('- `benchmark/personal_re/'+name+'`' for name in CREATED) + '\n\n'
    report += '## Steps and verification\n\n1. Read the existing embedder, cosine function, report template and relevant corpus excerpts.\n2. Load configuration without exposing credentials; initialize the declared Gemini model.\n3. Embed ten unique sentences, saving successful responses to avoid duplicate requests.\n4. Validate vectors, compute cosine scores and evaluate predictions with the fixed threshold.\n5. Select the most unexpected pair (incorrect predictions first; otherwise nearest threshold), and write the report and copyable snippet.\n6. Check protected file hashes, output locations and sensitive values.\n\n'
    report += '\n'.join(f'- {k}: `{v}`' for k,v in verification.items() if k != 'protected_file_sha256') + '\n\n'
    report += '## Limitations\n\nOnly five hand-selected English pairs are evaluated, so this is not a representative accuracy estimate for Vietnamese policy retrieval. The threshold depends on model, dataset, language and embedding configuration; scores are neither probabilities nor proof of equivalence, contradiction or policy correctness. Related sentences can have different intents, and shared platform vocabulary can influence similarity without making requests equivalent. API model behavior may change; the timestamp and saved vectors preserve this run. Per-pair explanations are semantic interpretations of the observations, not causal explanations of model internals.\n\n'
    report += 'Reproduce without unnecessary requests: `python -B benchmark/personal_re/run_similarity.py` (valid cached vectors are reused). Source files, corpus files and `REPORT_CANHAN.md` were not edited.\n'
    write('similarity_results.json', results)
    write('verification.json', verification)
    write('personal_report.md', report, raw=True)
    assert all(not any(secret in (OUT/name).read_text() for secret in secrets) for name in CREATED)
    assert verification['protected_files_unchanged']
    print(summary)
    print('Report:', OUT/'personal_report.md')
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
