"""Markdown structure-aware chunking using the repository's Document API.

No embedding provider is needed for parsing; pass a tokenizer length function
and max_tokens to enforce a model budget including the repeated heading path.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Callable

from src.models import Document


@dataclass
class Unit:
    text: str
    heading_path: str
    section: str
    clause: str
    start: int
    end: int


def front_matter(text: str) -> tuple[dict, str]:
    """Read the flat scalar YAML metadata used by the corpus, without coercing dates.

    Complex YAML is rejected explicitly rather than silently parsed incorrectly.
    """
    lines = text.lstrip('\ufeff').splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        return {}, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() in ('---', '...')), None)
    if end is None:
        raise ValueError('Unterminated YAML front matter')
    metadata = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'([\w-]+):\s*(.*?)\s*', line.rstrip('\n'))
        if not match:
            raise ValueError('Front matter must contain flat scalar YAML fields')
        key, value = match.groups()
        if value.startswith(('"', "'")):
            if value[0] == '"':
                value = json.loads(value)
            elif value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            else:
                raise ValueError('Unterminated YAML string')
        else:
            if value.startswith(('[', '{', '|', '>', '&', '*', '!')):
                raise ValueError('Complex YAML fields are not supported')
            value = re.split(r'\s+#', value, maxsplit=1)[0]
        metadata[key] = value
    return metadata, ''.join(lines[end + 1:])


def heading(line: str) -> tuple[int, str] | None:
    match = re.match(r'^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
    if match:
        return len(match[1]), match[2]
    match = re.match(r'^\s*(\d+\.\s+(.+))$', line)
    if match and match[2].isupper() and any(c.isalpha() for c in match[2]):
        return 2, match[1].strip()
    return None


def parse_units(text: str, source: str = '', metadata: dict | None = None) -> tuple[dict, list[Unit]]:
    meta, body = front_matter(text)
    meta.update(metadata or {})
    title = meta.get('title') or next((h[1] for line in body.splitlines() if (h := heading(line)) and h[0] == 1), Path(source).stem or 'Untitled')
    meta = {**meta, 'doc_id': meta.get('doc_id') or Path(source).stem or sha256(body.encode()).hexdigest()[:16],
            'source': source, 'title': title, 'category': meta.get('category', ''),
            'audience': meta.get('audience', ''), 'document_version': meta.get('document_version', '')}
    hierarchy = {1: title}
    section = clause = ''
    units = []
    pending = []
    start = offset = 0
    fenced = False

    def flush(end):
        if pending and ''.join(pending).strip():
            path = ' > '.join(hierarchy[k] for k in sorted(hierarchy))
            if clause and not re.search(r'(?:^| > )' + re.escape(clause) + r'(?:\.|\s|$)', path):
                path += ' > ' + clause
            units.append(Unit(''.join(pending).strip(), path, section, clause, start, end))
        pending.clear()

    for line in body.splitlines(keepends=True):
        if re.match(r'^\s*(```|~~~)', line):
            fenced = not fenced
        h = None if fenced else heading(line.rstrip())
        c = None if fenced else re.match(r'^\s*(\d+(?:\.\d+)+)\.?\s+', line)
        if h:
            flush(offset)
            level, label = h
            hierarchy = {k: v for k, v in hierarchy.items() if k < level}
            hierarchy[level] = label
            if level <= 2:
                section = label if level == 2 else ''
            clause = ''
            for depth in sorted(hierarchy):
                clause_match = re.match(r'(\d+(?:\.\d+)+)', hierarchy[depth])
                if depth > 2 and clause_match:
                    clause = clause_match[1]
            start = offset + len(line)
        elif c:
            flush(offset)
            clause = c[1]
            start = offset
            pending.append(line)
        else:
            if not pending:
                start = offset
            pending.append(line)
        offset += len(line)
    flush(offset)
    return meta, units


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
