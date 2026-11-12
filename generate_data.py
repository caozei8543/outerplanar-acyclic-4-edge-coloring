#!/usr/bin/env python3
"""Generate and validate all benchmark inputs; deterministic except for package version."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from outer4aec.benchmarks import build_benchmarks, write_jsonl, read_jsonl,SEED
from outer4aec.certificates import validate_paper_certificates
from outer4aec.states import formal_enumeration

P=Path(__file__).resolve().parents[1]

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--seed',type=int,default=SEED)
    a.add_argument('--out',type=Path,default=P/'data/empirical/benchmark_instances.jsonl')
    args=a.parse_args()
    result=build_benchmarks(args.seed)
    write_jsonl(result,args.out)
    assert read_jsonl(args.out)==result
    cert=validate_paper_certificates()
    (P/'data/certificates').mkdir(parents=True,exist_ok=True)
    (P/'data/certificates/paper_certificate_checks.json').write_text(
      json.dumps(cert,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (P/'data/certificates/formal_state_enumeration.json').write_text(
      json.dumps(formal_enumeration(),indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'total':len(result),'groups':dict(Counter(x['group'] for x in result)),
          'file':str(args.out)},indent=2))

if __name__=='__main__':main()
