#!/usr/bin/env python3
"""Serialize every exact two-terminal decomposition to JSONL with graph provenance."""
from __future__ import annotations
import json
from pathlib import Path
from outer4aec.benchmarks import read_jsonl
from outer4aec.core import make_graph
from outer4aec.decomposition import decompose_blocks,serialize_tree,verify_tree
P=Path(__file__).resolve().parents[1]

def main():
    inp=P/'data/empirical/benchmark_instances.jsonl'
    output=P/'data/empirical/decomposition_trees.jsonl'
    rows=read_jsonl(inp)
    with output.open('w',encoding='utf-8') as out:
        for r in rows:
            g=make_graph(r['n'],r['edges'])
            blocks=[]
            for edges,root in decompose_blocks(g):
                v,es=verify_tree(root)
                assert es==edges
                blocks.append({'original_edges':[list(e) for e in sorted(edges)],
                               'terminals':[root.s,root.t],'expression':serialize_tree(root)})
            out.write(json.dumps({'graph_id':r['graph_id'],'edge_sha256':r['edge_sha256'],
                                  'blocks':blocks},sort_keys=True,separators=(',',':'))+'\n')
    print(f'{len(rows)} SP-decomposition records: {output}')

if __name__=='__main__':main()
