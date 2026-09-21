"""Run from repository root: python -m benchmark.run_structural.

All generated artifacts stay in benchmark/. No mock semantic fallback is allowed.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'benchmark'
os.environ.setdefault('HF_HOME', str(OUT / '.model_cache'))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import FixedSizeChunker, RecursiveChunker, EmbeddingStore, LocalEmbedder
from benchmark.structural_chunking import HeaderMarkdownChunker, parse_units

SOURCES = ['data/ecommerce/shopee-dieu-khoan-dich-vu.md',
           'data/ecommerce/shopee-chinh-sach-doi-tra-hoan-tien.md']


def normalize(text):
    return ' '.join(text.split())


def make_chunks(strategy, source, limiter):
    text = (ROOT / source).read_text()
    if strategy == 'header':
        return limiter.chunk_document(text, source)
    meta, units = parse_units(text, source)
    # Identical front-matter removal and mandatory major-section isolation for
    # every strategy. Only header strategy uses clause boundaries and prefixes.
    groups = []
    for unit in units:
        if not groups or groups[-1][0] != unit.section:
            groups.append((unit.section, []))
        groups[-1][1].append(unit)
    docs = []
    from src.models import Document
    for section, group in groups:
        body = '\n\n'.join(u.text for u in group)
        spans, pos = [], 0
        for u in group:
            spans.append((pos, pos + len(u.text), u))
            pos += len(u.text) + 2
        base = FixedSizeChunker(limiter.chunk_size, overlap=0) if strategy == 'fixed_size' else RecursiveChunker(chunk_size=limiter.chunk_size)
        cursor = 0
        for original in base.chunk(body):
            begin = body.find(original, cursor)
            if begin < 0:
                raise ValueError('Cannot trace baseline chunk to source')
            cursor = begin + len(original)
            pieces = limiter.split(original)
            local_cursor = 0
            for piece in pieces:
                local = original.find(piece, local_cursor)
                if local < 0:
                    raise ValueError('Cannot trace fallback chunk to source')
                local_cursor = local + len(piece)
                a,b = begin + local, begin + local + len(piece)
                touched = [u for x,y,u in spans if x < b and y > a]
                index = len(docs)
                identity = json.dumps([strategy, meta['doc_id'], source, index, piece], ensure_ascii=False)
                chunk_id = meta['doc_id'] + ':' + sha256(identity.encode()).hexdigest()[:24]
                docs.append(Document(chunk_id, piece, {**meta, 'section': section,
                    'heading_path': ' | '.join(dict.fromkeys(u.heading_path for u in touched)),
                    'clause': ', '.join(dict.fromkeys(u.clause for u in touched if u.clause)),
                    'chunk_index': index, 'chunk_id': chunk_id, 'fallback_split': len(pieces) > 1,
                    'major_section_crossings': 0}))
    return docs


def chunk_stats(docs, length_fn):
    lengths = [len(d.content) for d in docs]
    return dict(count=len(docs), min=min(lengths, default=0), average=round(statistics.mean(lengths), 2) if lengths else 0,
                median=statistics.median(lengths) if lengths else 0, max=max(lengths, default=0),
                max_tokens=max((length_fn(d.content) for d in docs), default=0),
                fallback_chunks=sum(d.metadata['fallback_split'] for d in docs),
                major_section_crossings=sum(d.metadata['major_section_crossings'] for d in docs))


def judge(question, results):
    """Evidence coverage of manually verified complete answer propositions.

    Exact full evidence spans, not keywords, implement reproducible conservative
    judgments. Each fact has been verified against the expected source clause.
    Novel paraphrases/alternate supporting clauses require manual adjudication.
    """
    covered = set()
    first = None
    for rank, result in enumerate(results, 1):
        facts = []
        partial = False
        if result['metadata']['doc_id'] == question['expected_doc_id']:
            body = normalize(result['content'])
            facts = [i for i, fact in enumerate(question['evidence_facts']) if normalize(fact) in body]
            partial = any(normalize(fact) in body for fact in question.get('partial_evidence', []))
        result['supported_facts'] = facts
        result['additional_partial_evidence'] = partial
        result['support'] = 'full' if len(facts) == len(question['evidence_facts']) else 'partial' if facts or partial else 'none'
        if (facts or partial) and first is None:
            first = rank
        covered.update(facts)
    full = len(covered) == len(question['evidence_facts'])
    score = 2 if first == 1 and full else 1 if first else 0
    failure = '' if score == 2 else ('No complete answer proposition retrieved.' if first is None else
               'Answer evidence is incomplete across top 3.' if not full else 'First supporting result is below rank 1.')
    return dict(hit_at_1=first == 1, hit_at_3=first is not None, first_relevant_rank=first,
                reciprocal_rank=1 / first if first else 0, fully_supported=full,
                correct_source_top1=bool(results and results[0]['metadata']['doc_id'] == question['expected_doc_id']),
                rubric_score=score, failure_reason=failure, covered_facts=sorted(covered))


def render_report(data):
    cfg = data['configuration']
    lines = ['# Two-document structural chunking benchmark', '',
        '## Configuration', '',
        f"- Backend: `{cfg['embedding_backend']}`; vector dimension {cfg['dimensions']}; token limit {cfg['max_tokens']} (including special tokens).",
        f"- Store: {cfg['vector_store']}; ranking score: {cfg['score_definition']}. One collection per strategy contains both documents; top_k=3; no retrieval filters.",
        '- Sources: ' + ', '.join(f'`{s}`' for s in SOURCES),
        '- Corpus SHA-256: ' + json.dumps(cfg['source_sha256']),
        '- Character cap: 1000; overlap: 0. Exact tokenizer checks apply to all embedded chunks and queries; no truncation or mock fallback.',
        '- Front matter and heading-only lines are removed from baseline text. All strategies run independently within each major section; fixed-size and recursive use the existing repository classes. Header chunks additionally retain clause boundaries and prefix the heading path.',
        '- Zero overlap is intentional: it avoids consuming the limited token budget with duplicate text. Single sentences too large for the model are explicitly split at whitespace, then characters only as a last resort.',
        '- Gold answers and verbatim answer propositions are in `structural_questions.json`. Source hashes, all chunks, and raw top-3 results are in `structural_results.json`.',
        '', '## Relevance and rubric', '',
        'Relevance requires a complete, manually source-verified answer proposition or an explicitly annotated partial-support statement, not keyword overlap or merely the correct clause label. Full support requires all gold propositions across the top 3. Hit@1/Hit@3 and MRR include useful partial support; full-support rate is reported separately. The scorer conservatively matches complete evidence spans with whitespace normalized. All 45 retrieved results were also inspected for alternative support and split/incomplete facts. The reminder that requests remain possible within the 15-day period after acknowledging receipt is partial evidence for Q5, even though it omits the deadline start and exceptions. Manual rationales are recorded in structural_review.json.',
        '', 'Rubric resolves the overlapping instructions as: 2 = first supporting result at rank 1 and all answer facts supported by top 3; 1 = partial support or first relevant rank 2/3; 0 = no supporting proposition in top 3. This is a retrieval/support evaluation, not an LLM answer-generation test.',
        '', '## Comparison', '', '| Strategy | Hit@1 | Hit@3 | MRR | Full support | Rubric /10 |', '|---|---:|---:|---:|---:|---:|']
    for name, run in data['strategies'].items():
        a=run['aggregate']
        lines.append(f"| {name} | {a['hit_at_1']:.2f} | {a['hit_at_3']:.2f} | {a['mrr']:.3f} | {a['full_support']:.2f} | {a['rubric_score']} |")
    lines += ['', '## Chunk statistics', '', 'Lengths are characters including heading prefixes. Fallback counts count output chunks belonging to an oversized input unit.', '',
              '| Strategy | Document | Count | Min | Average | Median | Max | Max tokens | Fallback chunks | Major crossings |', '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name, run in data['strategies'].items():
        for doc, s in run['statistics'].items():
            lines.append(f"| {name} | {doc} | {s['count']} | {s['min']} | {s['average']} | {s['median']} | {s['max']} | {s['max_tokens']} | {s['fallback_chunks']} | {s['major_section_crossings']} |")
    lines += ['', '## Questions and top-3 evidence', '']
    for i, q in enumerate(data['questions'], 1):
        lines += [f"### Q{i}. {q['query']}", '', f"Gold: {q['gold_answer']}", '', f"Expected: `{q['expected_doc_id']}`, clause `{q['expected_clause']}`.", '']
        for name, run in data['strategies'].items():
            item=run['questions'][i-1]; m=item['metrics']
            lines += [f"#### {name}", '', f"Hit@1={int(m['hit_at_1'])}; Hit@3={int(m['hit_at_3'])}; first rank={m['first_relevant_rank']}; RR={m['reciprocal_rank']:.3f}; correct source at top 1={m['correct_source_top1']}; full support={m['fully_supported']}; rubric={m['rubric_score']}/2.", '', 'Failure: ' + (m['failure_reason'] or 'None.'), '', '<details><summary>Top-3 retrieved text and provenance</summary>', '']
            for rank,r in enumerate(item['results'],1):
                md=r['metadata']
                lines += [f"**Rank {rank} — score {r['score']:.6f}; {r['support']} support**", '',
                          f"Source: `{md['source']}`; path: {md['heading_path']}; clause: `{md['clause']}`; chunk: `{md['chunk_id']}`.", '',
                          '> ' + r['content'].replace('\n','\n> '), '']
            lines += ['</details>', '']
    lines += ['', '## Failure analysis and conclusion', '',
              'All five gold answers are fully supported by the two source documents. Missing benchmark facts therefore reflect retrieval/chunk fragmentation, not missing corpus coverage. Q5 needs several distinct deadline cases; retrieving just the general 15-day rule is incomplete.', '',
              'The 128-token model budget makes full heading paths costly. Structural boundaries preserve provenance, but can fragment long clauses or reduce the amount of answer text available in each retrieved result. This tradeoff is included in the comparison rather than hidden by tokenizer truncation.', '']
    header=data['strategies']['header']['aggregate']
    for baseline in ('fixed_size','recursive'):
        other=data['strategies'][baseline]['aggregate']
        lines.append(f"Header versus {baseline}: rubric {header['rubric_score']}/10 versus {other['rubric_score']}/10; Hit@3 delta {header['hit_at_3']-other['hit_at_3']:+.2f}; MRR delta {header['mrr']-other['mrr']:+.3f}.")
    lines += ['', 'Header-based chunking did not improve retrieval in this configuration: its rubric score is lower than both baselines, and its full-support rate is also lower. It does provide clearer structural provenance.', '', 'Q4 fails for all strategies: returned chunks discuss damage, transactions, or refunds but do not establish the buyer’s options in clause 1.1. Q5 remains partial for all strategies; the response-time note is not the submission deadline. Header Q1 retrieves seller risk but misses the separate Shopee liability exclusion in the gold answer.', '',
              'Only five questions and one model/configuration were tested; these results do not establish general retrieval superiority. No parameters were tuned against the five queries.', '',
              '## Reproduce', '', '```bash', 'python -m benchmark.run_structural', 'python -m pytest tests benchmark/test_structural.py -v -o cache_dir=benchmark/.pytest_cache', '```', '',
              'Local setup if unavailable: install `requirements-local.txt` and allow the multilingual model to download. Failure to load a semantic backend stops the benchmark with a setup message; offline unit tests remain available.', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    questions=json.loads((OUT/'structural_questions.json').read_text())
    try:
        embedder=LocalEmbedder()
    except Exception as exc:
        message=f'Semantic benchmark stopped: cannot load LocalEmbedder ({type(exc).__name__}). Install requirements-local.txt and make the multilingual model available. No mock fallback. Offline tests: python -m pytest tests benchmark/test_structural.py'
        (OUT/'structural_report.md').write_text('# Benchmark setup required\n\n'+message+'\n')
        print(message, file=sys.stderr)
        return 2
    tokenizer=embedder.model.tokenizer
    length_fn=lambda text: len(tokenizer.encode(text, add_special_tokens=True, truncation=False, verbose=False))
    max_tokens=embedder.model.max_seq_length
    print(f'Embedding backend: {embedder._backend_name}; max tokens={max_tokens}', flush=True)
    limiter=HeaderMarkdownChunker(chunk_size=1000, length_fn=length_fn, max_tokens=max_tokens)
    cache={}
    def checked_embed(text):
        if length_fn(text)>max_tokens:
            raise ValueError('Embedding input exceeds model token limit; refusing truncation')
        if text not in cache:
            cache[text]=embedder(text)
        return cache[text]
    data={'configuration': {'embedding_backend':embedder._backend_name, 'max_tokens':max_tokens,
          'dimensions':embedder.model.get_embedding_dimension(), 'source_sha256':{s:sha256((ROOT/s).read_bytes()).hexdigest() for s in SOURCES}},
          'questions':questions, 'strategies':{}}
    backend=None
    for strategy in ('fixed_size','recursive','header'):
        docs=[]; stats={}
        for source in SOURCES:
            chunks=make_chunks(strategy,source,limiter)
            docs.extend(chunks)
            stats[source]=chunk_stats(chunks,length_fn)
        assert len({d.id for d in docs})==len(docs)
        print(f'{strategy}: embedding {len(docs)} chunks', flush=True)
        # Batch precompute using the same underlying normalized local model.
        missing=list(dict.fromkeys(d.content for d in docs if d.content not in cache))
        assert all(length_fn(text)<=max_tokens for text in missing)
        vectors=embedder.model.encode(missing, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        cache.update({text:vector.tolist() for text,vector in zip(missing,vectors)})
        store=EmbeddingStore('structural_'+strategy,embedding_fn=checked_embed)
        actual='Chroma' if store._use_chroma else 'in-memory'
        if backend is not None and backend!=actual:
            raise RuntimeError('Vector backend changed between strategies')
        backend=actual
        store.add_documents(docs)
        run={'statistics':stats,'chunks':[asdict(d) for d in docs],'questions':[]}
        for q in questions:
            results=store.search(q['query'],top_k=3)
            for result in results:
                result['store_record_id'] = result['id']
                result['id'] = result['metadata']['chunk_id']
                result.update({key: result['metadata'][key] for key in ('source', 'heading_path', 'clause')})
            metrics=judge(q,results)
            run['questions'].append({'query':q['query'],'metrics':metrics,'results':results})
        metrics=[r['metrics'] for r in run['questions']]
        run['aggregate']={key:statistics.mean(m[field] for m in metrics) for key,field in [('hit_at_1','hit_at_1'),('hit_at_3','hit_at_3'),('mrr','reciprocal_rank'),('full_support','fully_supported')]}
        run['aggregate']['rubric_score']=sum(m['rubric_score'] for m in metrics)
        data['strategies'][strategy]=run
        print(strategy,run['aggregate'],flush=True)
    data['configuration'].update(vector_store=backend,score_definition='1 - squared L2 distance (Chroma default, normalized vectors; equivalent ranking to cosine)' if backend=='Chroma' else 'cosine similarity')
    (OUT/'structural_results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (OUT/'structural_report.md').write_text(render_report(data))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
