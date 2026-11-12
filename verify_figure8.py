#!/usr/bin/env python3
"""Regenerate and check a valid 4-slot witness for visually transcribed Fig. 8.

The original figure's precise per-edge slot map is *not* claimed to have been
recovered; the generated coloring is an independently checked replacement.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import networkx as nx
from outer4aec.figure8 import figure8_graph,figure8_labeled_edges
from outer4aec.core import validate_instance,verify_coloring
from outer4aec.dp import solve_graph
ROOT=Path(__file__).resolve().parents[1]
CERT=ROOT/'data/certificates/figure8_transcribed_topology_and_validated_witness.json'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--regenerate',action='store_true',help='replace stored algorithmic certificate')
    args=parser.parse_args()
    g=figure8_graph();validate_instance(g)
    assert nx.is_connected(g) and g.number_of_nodes()==71 and g.number_of_edges()==76
    assert max(dict(g.degree()).values())==4
    assert g.number_of_edges()-g.number_of_nodes()+1==6
    stored=json.loads(CERT.read_text(encoding='utf-8'))
    assert stored['edges_1_based']==[list(e) for e in figure8_labeled_edges()]
    witnessed={tuple(u-1 for u in item['edge']):item['slot'] for item in stored['verified_color_witness_1_based']}
    assert verify_coloring(g,witnessed)[0]
    if args.regenerate:
        result=solve_graph(g,check_states=True)
        assert all(result['decision'].values())
        colors={tuple(v['edge']):v['color'] for v in result['certificates']['dominance']}
        assert verify_coloring(g,colors)[0]
        stored['verified_color_witness_1_based']=[{'edge':[u+1,v+1],'slot':c} for (u,v),c in sorted(colors.items())]
        CERT.write_text(json.dumps(stored,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Figure 8 PASS: topology transcribed from PDF, 71 vertices, 76 edges, Δ=4, 6 independent cycles, verified acyclic 4-slot certificate')

if __name__=='__main__':main()
