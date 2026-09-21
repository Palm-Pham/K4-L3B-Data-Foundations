"""Offline tests; no downloaded model or API credentials required."""
from pathlib import Path
import json
import sys

import pytest

from src import EmbeddingStore, MockEmbedder
from benchmark.structural_chunking import HeaderMarkdownChunker, front_matter, parse_units
from benchmark.run_structural import make_chunks, judge, SOURCES

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def sample():
    return '''---
doc_id: example
title: Example policy
category: policy
audience: buyer
document_version: "2026.08"
source_url: https://example.test/policy
---
# Example policy
## 13. SHIPPING
13.1. First complete clause.
13.2. Second complete clause.
14. CANCELLATIONS
14.1. Cancellation clause.
21. LINKS AND INTERACTION
21.1. Link clause.
'''


def test_front_matter_separation(sample):
    meta, body=front_matter(sample)
    assert meta['document_version']=='2026.08'
    assert meta['source_url']=='https://example.test/policy'
    assert body.startswith('# Example')
    assert all('doc_id:' not in d.content and 'source_url:' not in d.content for d in HeaderMarkdownChunker().chunk_document(sample))


@pytest.mark.parametrize('text',['---\ntitle: bad', '---\ntags: [a, b]\n---\nBody', '---\n  nested: nope\n---\nBody'])
def test_unsupported_or_unterminated_front_matter_is_explicit(text):
    with pytest.raises(ValueError):
        front_matter(text)


def test_hierarchy_and_deeper_markdown_headings():
    text='# Title\n## Major\n### Sub\n#### Detail\n##### More\n###### Last\nBody\n## Next\nOther'
    _,units=parse_units(text)
    assert units[0].heading_path=='Title > Major > Sub > Detail > More > Last'
    assert units[1].heading_path=='Title > Next'
    assert units[1].section=='Next'


def test_unmarked_numbered_headings(sample):
    _,units=parse_units(sample)
    assert [u.section for u in units][-2:]==['14. CANCELLATIONS','21. LINKS AND INTERACTION']
    assert [u.clause for u in units]==['13.1','13.2','14.1','21.1']


def test_numbered_sentence_is_not_major_heading():
    _,units=parse_units('# Title\n## Section\n1. This is an ordinary list item.\n2. Another item.')
    assert len(units)==1
    assert units[0].section=='Section'


def test_metadata_and_prefix(sample):
    docs=HeaderMarkdownChunker().chunk_document(sample,'data/example.md')
    for i,doc in enumerate(docs):
        m=doc.metadata
        assert m['doc_id']=='example'
        assert m['source']=='data/example.md'
        assert m['title']=='Example policy'
        assert m['category']=='policy'
        assert m['audience']=='buyer'
        assert m['document_version']=='2026.08'
        assert m['chunk_index']==i
        assert m['chunk_id']==doc.id
        assert m['section'] and m['clause']
        assert doc.content.startswith(m['heading_path']+'\n\n')


def test_stable_unique_ids_and_document_isolation(sample):
    chunker=HeaderMarkdownChunker()
    a=chunker.chunk_document(sample,'a.md')
    b=chunker.chunk_document(sample.replace('example','second').replace('First complete','Different'),'b.md')
    assert a==chunker.chunk_document(sample,'a.md')
    assert len({d.id for d in a+b})==len(a+b)
    assert all('Different' not in d.content for d in a)
    assert all('First complete' not in d.content for d in b)
    assert {d.metadata['source'] for d in a}=={'a.md'}


def test_major_section_isolation(sample):
    docs=HeaderMarkdownChunker(chunk_size=10000).chunk_document(sample)
    for d in docs:
        assert sum(label in d.content for label in ('SHIPPING','CANCELLATIONS','LINKS AND INTERACTION'))==1
        assert d.metadata['major_section_crossings']==0


def test_oversized_clause_fallback_preserves_sentences_and_heading():
    sentences=[f'Sentence {i} contains several words.' for i in range(12)]
    text='# T\n## S\n1.1. '+' '.join(sentences)
    docs=HeaderMarkdownChunker(chunk_size=110).chunk_document(text)
    assert len(docs)>1
    assert all(d.metadata['fallback_split'] for d in docs)
    assert all(d.metadata['clause']=='1.1' and d.content.startswith('T > S > 1.1\n\n') for d in docs)
    assert all(len(d.content)<=110 for d in docs)
    assert all(any(s in d.content for d in docs) for s in sentences)


def test_list_boundaries_preserve_items():
    items=['(a) First list item with several words.', '(b) Second item with several words.', '(i) Roman first item with words.', '(ii) Roman second item with words.']
    docs=HeaderMarkdownChunker(chunk_size=75).chunk_document('# T\n## S\n1.1. Intro.\n'+'\n'.join(items))
    assert all(any(item in d.content for d in docs) for item in items)


def test_token_budget_includes_heading():
    count=lambda text: len(text.split())+2
    docs=HeaderMarkdownChunker(length_fn=count,max_tokens=15).chunk_document('# T\n## S\n1.1. '+'word '*100)
    assert len(docs)>1
    assert all(count(d.content)<=15 for d in docs)


def test_too_long_prefix_fails_explicitly():
    with pytest.raises(ValueError,match='Heading path'):
        HeaderMarkdownChunker(chunk_size=10).chunk_document('# A very long heading\nbody')


def test_long_unbroken_sentence_is_not_dropped():
    docs=HeaderMarkdownChunker(chunk_size=45).chunk_document('# T\n'+'x'*120)
    assert ''.join(d.content.split('\n\n',1)[1] for d in docs)=='x'*120
    assert all(len(d.content)<=45 for d in docs)


@pytest.mark.parametrize('text',['','   ','# Title\n## Empty'])
def test_empty_input(text):
    assert HeaderMarkdownChunker().chunk(text)==[]


def test_no_headings():
    docs=HeaderMarkdownChunker().chunk_document('Plain text without headings.','plain.md')
    assert len(docs)==1
    assert docs[0].metadata['heading_path']=='plain'
    assert docs[0].metadata['clause']==''
    assert docs[0].content.endswith('Plain text without headings.')


@pytest.mark.parametrize('fallback',[False,True])
def test_retrieval_traceability_and_metadata_filters(sample,monkeypatch,fallback):
    if fallback:
        monkeypatch.setitem(sys.modules,'chromadb',None)
    docs=HeaderMarkdownChunker().chunk_document(sample,'example.md')
    store=EmbeddingStore('traceability',MockEmbedder())
    store.add_documents(docs)
    for field,value in [('doc_id','example'),('category','policy'),('audience','buyer')]:
        results=store.search_with_filter(docs[0].content,top_k=3,metadata_filter={field:value})
        assert results
        assert all(r['metadata'][field]==value for r in results)
        assert all(r['metadata']['source']=='example.md' and r['metadata']['heading_path'] and r['metadata']['clause'] for r in results)
        assert all(r['metadata']['chunk_id'] in {d.id for d in docs} for r in results)
    assert store.search_with_filter('query',metadata_filter={'doc_id':'missing'})==[]


@pytest.mark.parametrize('strategy',['fixed_size','recursive','header'])
def test_real_corpus_boundaries_and_stable_ids(strategy):
    limiter=HeaderMarkdownChunker(chunk_size=1000)
    all_docs=[]
    for source in SOURCES:
        docs=make_chunks(strategy,source,limiter)
        assert docs==make_chunks(strategy,source,limiter)
        assert all(d.metadata['source']==source for d in docs)
        assert all(len(d.content)<=1000 for d in docs)
        assert all(d.metadata['major_section_crossings']==0 for d in docs)
        assert all('source_url:' not in d.content for d in docs)
        all_docs.extend(docs)
    assert len({d.id for d in all_docs})==len(all_docs)


def test_gold_evidence_verified_against_sources():
    questions=json.loads((ROOT/'benchmark/structural_questions.json').read_text())
    assert len(questions)==5
    for q in questions:
        _,units=parse_units((ROOT/q['source']).read_text(),q['source'])
        unit=next(u for u in units if u.clause==q['expected_clause'])
        assert unit.text==q['source_excerpt']
        assert all(' '.join(f.split()) in ' '.join(unit.text.split()) for f in q['evidence_facts'])


def test_keyword_overlap_is_not_relevance():
    q={'expected_doc_id':'a','evidence_facts':['The seller bears all shipping risk.']}
    r={'content':'seller shipping risk','metadata':{'doc_id':'a'}}
    assert judge(q,[r])['rubric_score']==0
    r['content']='The seller bears all shipping risk.'
    assert judge(q,[r])['rubric_score']==2
    r['metadata']['doc_id']='wrong'
    assert judge(q,[r])['rubric_score']==0


def test_rubric_partial_and_lower_rank():
    q={'expected_doc_id':'a','evidence_facts':['First full fact.','Second full fact.']}
    irrelevant={'content':'irrelevant','metadata':{'doc_id':'a'}}
    partial={'content':'First full fact.','metadata':{'doc_id':'a'}}
    full={'content':'First full fact. Second full fact.','metadata':{'doc_id':'a'}}
    assert judge(q,[partial])['rubric_score']==1
    result=judge(q,[irrelevant,full])
    assert result['rubric_score']==1 and result['reciprocal_rank']==0.5 and result['fully_supported']


def test_deeper_heading_inherits_numbered_clause():
    _,units=parse_units('# T\n## 1. Main\n### 1.2. Clause\n#### Detail\nBody')
    assert units[0].clause=='1.2'
    assert units[0].heading_path=='T > 1. Main > 1.2. Clause > Detail'


def test_code_fence_headings_do_not_change_hierarchy():
    _,units=parse_units('# T\n## S\n```markdown\n## Not a section\n```\nBody')
    assert len(units)==1
    assert units[0].section=='S'
    assert '## Not a section' in units[0].text


def test_partial_deadline_reminder_counts_without_full_support():
    q={'expected_doc_id':'a','evidence_facts':['Complete deadline and exception.'],
       'partial_evidence':['Requests remain possible within 15 days.']}
    result=judge(q,[{'content':'Requests remain possible within 15 days.','metadata':{'doc_id':'a'}}])
    assert result['hit_at_1'] and result['rubric_score']==1 and not result['fully_supported']


def test_no_semantic_backend_stops_without_mock(monkeypatch,tmp_path,capsys):
    import benchmark.run_structural as runner
    (tmp_path/'structural_questions.json').write_text('[]')
    monkeypatch.setattr(runner,'OUT',tmp_path)
    monkeypatch.setattr(sys,'argv',['run_structural'])
    def unavailable():
        raise ImportError('Model unavailable')
    monkeypatch.setattr(runner,'LocalEmbedder',unavailable)
    assert runner.main()==2
    assert 'No mock fallback' in capsys.readouterr().err
    assert 'setup required' in (tmp_path/'structural_report.md').read_text()
    assert not (tmp_path/'structural_results.json').exists()
