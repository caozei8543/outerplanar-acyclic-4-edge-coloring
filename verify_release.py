#!/usr/bin/env python3
"""Verify SHA-256 for all *shipped* release files, excluding the manifest itself.

Ignore local measurements, Python caches and editable-install outputs.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def in_distribution(path:Path)->bool:
    rel=path.relative_to(ROOT)
    parts=set(rel.parts)
    if path.name=='SHA256SUMS.txt':return False
    if parts & {'__pycache__','.pytest_cache','.venv','build','dist'}:return False
    if any(x.endswith('.egg-info') or x.startswith('local_') for x in rel.parts):return False
    if path.suffix in ('.pyc','.pyo'):return False
    return True

def main():
    manifest=ROOT/'SHA256SUMS.txt'
    if not manifest.is_file():raise SystemExit('SHA256SUMS.txt is missing')
    checks={}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        digest,name=line.split('  ',1)
        if name in checks:raise SystemExit(f'Duplicate manifest entry: {name}')
        checks[name]=digest
        p=ROOT/name
        if not p.is_file():raise SystemExit(f'File missing: {name}')
        now=hashlib.sha256(p.read_bytes()).hexdigest()
        if now!=digest:raise SystemExit(f'Hash mismatch: {name}')
    real={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and in_distribution(p)}
    if set(checks)!=real:
        missing=real-set(checks)
        extra=set(checks)-real
        raise SystemExit(f'Untracked/incorrect release files: missing={sorted(missing)}, extra={sorted(extra)}')
    print(f'RELEASE INTEGRITY PASS: {len(checks)} checked files, complete inventory and SHA-256 matched')

if __name__=='__main__':main()
