#!/usr/bin/env python3
"""Build fully qualified graph/block/node state profiles without redoing stopwatch runs."""
from __future__ import annotations
import csv
from pathlib import Path
from outer4aec.benchmarks import read_jsonl
from outer4aec.core import make_graph
from outer4aec.dp import solve_graph
P=Path(__file__).resolve().parents[1]

def main():
    rows=read_jsonl(P/'data/empirical/benchmark_instances.jsonl')
    out=P/'data/empirical/full_run/node_level_consistency.csv'
    with out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['graph_id','block_index','block_root_id','node_id','op',
                                       'full','exposed','dominance','projection_equal','minimization_equal'])
        w.writeheader()
        for r in rows:
            g=make_graph(r['n'],r['edges'])
            result=solve_graph(g)
            for i,d in enumerate(result['blocks']):
                for n in d['node_identities']:
                    w.writerow({'graph_id':r['graph_id'],'block_index':i,
                        'block_root_id':d['root_id'],**n})
    print(f'Wrote fully-qualified node profile: {out}')

if __name__=='__main__':main()
