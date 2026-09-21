#!/usr/bin/env python3
"""Complete unambiguous terminal bold closers in Wimmer commentary copies.

Only rows whose current Comentario ends in '</' (or which the preserved repair-scope report lists) belong to this batch. Historical spelling and prose are never changed.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

class TagStack(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)
    def handle_startendtag(self, tag, attrs):
        pass
    def handle_endtag(self, tag):
        if tag in VOID:
            self.errors.append('closing void tag')
        elif not self.stack or self.stack[-1] != tag:
            self.errors.append('mismatched closing tag')
        else:
            self.stack.pop()

def repair_fragment(value: str) -> str | None:
    if not value.endswith('</'):
        return None
    parser = TagStack()
    parser.feed(value[:-2])
    parser.close()
    if parser.errors or parser.stack != ['b']:
        return None
    return value + 'b>'

def plan_rows(rows, scope_ids=(), operations=None):
    operations = operations or {}
    changes, ambiguous = [], []
    for index, row in enumerate(rows):
        if row.get('Fuente') != '2021 Wimmer':
            continue
        if not str(row.get('Comentario', '')).endswith('</') and row.get('record_id') not in scope_ids:
            continue
        fields = {}
        for field, value in row.items():
            if not field.startswith('Comentario') or not isinstance(value, str) or not value.endswith('</'):
                continue
            operation = operations.get((row.get('record_id'), field))
            if operation == 'remove_orphan_closer':
                parser = TagStack(); parser.feed(value[:-2]); parser.close()
                repaired = value[:-2] if not parser.errors and not parser.stack else None
            else:
                repaired = repair_fragment(value)
            if repaired is None:
                ambiguous.append({'record_id': row.get('record_id'), 'field': field})
            else:
                fields[field] = repaired
        if fields:
            changes.append((index, fields))
    return changes, ambiguous

def write_rows(path, rows):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.wimmer-html-', delete=False) as handle:
            temporary = Path(handle.name)
            with gzip.GzipFile(filename='', fileobj=handle, mode='wb', mtime=0) as compressed:
                for row in rows:
                    compressed.write((json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'data/data.jsonl.gz')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    parser.add_argument('--expected-rows', type=int)
    parser.add_argument('--expected-fields', type=int)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--scope-report', type=Path, default=ROOT/'resources/wimmer_terminal_html_2026_09_20_scope.json')
    args = parser.parse_args()
    with gzip.open(args.data, 'rt', encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    scope = json.loads(args.scope_report.read_text(encoding='utf-8'))
    scope_ids = {entry['record_id'] for entry in scope['changes']}
    operations = {(entry['record_id'], field): operation for entry in scope['changes'] for field, operation in entry.get('operations', {}).items()}
    changes, ambiguous = plan_rows(rows, scope_ids, operations)
    field_count = sum(len(fields) for _, fields in changes)
    report = {'rows': len(changes), 'fields': field_count, 'ambiguous': ambiguous,
              'changes': [{'record_id': rows[index]['record_id'], 'fields': list(fields)} for index, fields in changes]}
    if args.apply:
        if ambiguous:
            parser.error('Ambiguous markup remains; no corpus was written')
        if args.expected_rows is not None and len(changes) != args.expected_rows:
            parser.error('Reviewed row count differs; no corpus was written')
        if args.expected_fields is not None and field_count != args.expected_fields:
            parser.error('Reviewed field count differs; no corpus was written')
        for index, fields in changes:
            row = rows[index]
            for field, repaired in fields.items():
                row[field] = repaired
        if changes:
            write_rows(args.data, rows)
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'changes'}, ensure_ascii=False))
    return int(args.check and bool(changes or ambiguous))

if __name__ == '__main__':
    raise SystemExit(main())
