"""Figure 8 topology manually transcribed from FINAL PDF p.15.

Vertex labels are 1--71 in the diagram. A computed witness may differ
from the visual edge colors; no original edge-list source was provided.
"""
from __future__ import annotations
from .core import make_graph

def figure8_labeled_edges()->list[tuple[int,int]]:
    edges=[(u,u+1) for u in range(1,20)]
    for hub,path in ((5,(21,22,23,24)),(11,(25,26,27,28)),(17,(29,30,31,32))):
        cycle=(hub,)+path+(hub,)
        edges.extend(zip(cycle,cycle[1:]))
    edges += [(3,33),(9,34),(15,35)]
    edges += [(u,u+1) for u in range(36,56)]
    for hub,path in ((40,(57,58,59,60)),(46,(61,62,63,64)),(52,(65,66,67,68))):
        cycle=(hub,)+path+(hub,)
        edges.extend(zip(cycle,cycle[1:]))
    edges += [(38,69),(44,70),(50,71),(20,36)]
    result=sorted({tuple(sorted(e)) for e in edges})
    assert len(edges)==len(result)==76
    assert set(v for e in result for v in e)==set(range(1,72))
    return result

def figure8_graph():
    return make_graph(71,[(u-1,v-1) for u,v in figure8_labeled_edges()])
