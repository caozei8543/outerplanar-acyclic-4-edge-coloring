"""Machine-readable validation of final 17-page article Tables 2--4 and Q."""
from __future__ import annotations
from itertools import permutations
import networkx as nx
from .core import (q_graph,Q_EDGES,Q_FIVE_CERT,Q_DELETION_CERT,verify_coloring,
                   exhaustive_4color,edge)

TABLE2_Q_FINGERPRINTS=[
    (2,4,3,1,2),(2,4,3,1,3),(4,1,4,1,2),(4,4,4,1,2),
    (4,4,3,1,2),(4,4,3,1,3),(4,1,4,3,2),(4,4,4,3,2)]
TABLE4_SIX_VERTEX_COLORINGS={
 'I':{'edges':[(0,1),(1,2),(2,3),(3,4),(4,5),(0,5),(1,5),(2,4),(2,5)],
      'colors':[1,2,3,1,2,4,3,4,1]},
 'II':{'edges':[(0,1),(1,2),(2,3),(3,4),(4,5),(0,5),(1,3),(1,5),(3,5)],
       'colors':[3,4,2,4,1,4,1,2,3]},
}

def proper_q_cases():
    q=q_graph()
    anchored={(0,6):1,(2,6):2,(0,2):3}
    remain=[e for e in Q_EDGES if e not in anchored]
    assigned=dict(anchored)
    out=[]
    def rec(i):
        if i==len(remain):
            out.append(dict(assigned));return
        u,v=remain[i]
        used={col for (a,b),col in assigned.items() if u in (a,b) or v in (a,b)}
        for c in (1,2,3,4):
            if c not in used:
                assigned[(u,v)]=c;rec(i+1);del assigned[(u,v)]
    rec(0)
    return out

def bichromatic_cycle(g:nx.Graph,colors:dict)->dict|None:
    for a in range(1,5):
        for b in range(a+1,5):
            h=nx.Graph()
            h.add_edges_from(uv for uv,c in colors.items() if c in (a,b))
            cycles=nx.cycle_basis(h)
            if cycles:return {'color_pair':[a,b],'cycle':cycles[0]+[cycles[0][0]]}
    return None

def validate_paper_certificates()->dict:
    q=q_graph()
    five=dict(zip(Q_EDGES,Q_FIVE_CERT))
    assert verify_coloring(q,five,5)[0]
    proper=proper_q_cases()
    assert len(proper)==8
    fingerprints=[]
    for colors in proper:
        fingerprint=tuple(colors[e] for e in ((0,1),(2,3),(5,6),(1,5),(3,4)))
        fingerprints.append(fingerprint)
        assert bichromatic_cycle(q,colors) is not None
    assert set(fingerprints)==set(TABLE2_Q_FINGERPRINTS)
    aut=list(nx.algorithms.isomorphism.GraphMatcher(q,q).isomorphisms_iter())
    deletions=[]
    for deleted in Q_EDGES:
        color_witness=None
        for rep,clrs in Q_DELETION_CERT.items():
            for f in aut:
                if edge(*[f[v] for v in rep]) != deleted:continue
                witness={edge(f[u],f[v]):c for (u,v),c in zip(Q_EDGES,clrs) if c is not None}
                g=q.copy();g.remove_edge(*deleted)
                if verify_coloring(g,witness)[0]:
                    color_witness=witness
                    break
            if color_witness:break
        assert color_witness is not None
        deletions.append({'deleted_edge':list(deleted),
                          'colors':[{'edge':list(e),'color':c} for e,c in sorted(color_witness.items())],
                          'verified':True})
    table5={}
    for name,v in TABLE4_SIX_VERTEX_COLORINGS.items():
        g=nx.Graph();g.add_edges_from(v['edges'])
        coloring={edge(*e):c for e,c in zip(v['edges'],v['colors'])}
        ok,reason=verify_coloring(g,coloring)
        assert ok,(name,reason)
        table5[name]={'edges':[list(e) for e in v['edges']],'colors':v['colors'],
                      'verified':ok}
    return {
        'q_edges':[list(e) for e in Q_EDGES],
        'q_five_color_certificate':[{'edge':list(e),'color':c} for e,c in five.items()],
        'q_five_certificate_verified':True,
        'q_proper_four_colorings_up_to_permutation':len(proper),
        'q_proper_colorings_all_have_bichromatic_cycle':True,
        'table2_q_proper_cases':[{'fingerprint':list(tuple(c[e] for e in ((0,1),(2,3),(5,6),(1,5),(3,4)))),
                       'cycle':bichromatic_cycle(q,c)} for c in proper],
        'table3_edge_deletion_certificates':deletions,
        'table4_six_vertex_certificates':table5,
        'q_is_isomorphic_to_networkx_G840':nx.is_isomorphic(q,nx.graph_atlas(840)),
        'independent_4color_oracle_q_returns_NO':exhaustive_4color(q) is None
    }
