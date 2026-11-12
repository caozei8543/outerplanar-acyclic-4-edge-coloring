"""Binary two-terminal series-parallel decompositions for outerplanar blocks.

We reduce a 2-connected outerplanar graph as a multigraph of virtual edges.
Each virtual edge carries a subtree representing *distinct original edges*.
Parallel virtual edges are merged; a degree-2 vertex is series-reduced.
A virtual multigraph is an internal data structure only: every represented
original graph is required to remain simple.
"""
from __future__ import annotations
from dataclasses import dataclass
from .core import edge
import networkx as nx

@dataclass(frozen=True,eq=False)
class Node:
    ident: int
    op: str
    s: int
    t: int
    original: tuple[int,int] | None = None
    left: 'Node | None' = None
    right: 'Node | None' = None
    left_forward: bool = True
    right_forward: bool = True
    middle: int | None = None

class Builder:
    def __init__(self):self.ident=0
    def node(self,*args,**kwargs):
        self.ident+=1
        return Node(self.ident,*args,**kwargs)

def build_block_tree(g:nx.Graph) -> Node:
    """One block only; raises if the biconnected input is unsuitable."""
    if not g.number_of_edges():raise ValueError('Empty block')
    if g.number_of_edges()==1:
        u,v=next(iter(g.edges()))
        return Builder().node('L',*edge(u,v),original=edge(u,v))
    if not nx.is_biconnected(g):
        raise ValueError('Expected a biconnected graph or one bridge')
    build=Builder()
    active={}
    next_edge=0
    for u,v in sorted(edge(u,v) for u,v in g.edges()):
        next_edge+=1
        active[next_edge]=build.node('L',u,v,original=(u,v))
    while len(active)>1:
        byends={}
        for eid,node in active.items():
            byends.setdefault(edge(node.s,node.t),[]).append(eid)
        duplicate=next(((pair,ids) for pair,ids in sorted(byends.items()) if len(ids)>1),None)
        if duplicate:
            (s,t),ids=duplicate
            i,j=sorted(ids)[:2]
            x,y=active.pop(i),active.pop(j)
            parent=build.node('P',s,t,left=x,right=y,
                              left_forward=(x.s==s),right_forward=(y.s==s))
        else:
            inc={}
            for eid, e in active.items():
                inc.setdefault(e.s,[]).append(eid)
                inc.setdefault(e.t,[]).append(eid)
            choices=sorted(v for v, ids in inc.items() if len(ids)==2)
            if not choices:
                raise ValueError('Cannot reduce block to two-terminal SP tree')
            v=choices[0]
            i,j=inc[v]
            x,y=active.pop(i),active.pop(j)
            a=x.t if x.s==v else x.s
            b=y.t if y.s==v else y.s
            if a==b:
                raise ValueError('Unexpected two-edge parallel subgraph')
            # Use deterministic ordering at new outer terminals.
            if a>b:
                a,b=b,a
                x,y=y,x
            parent=build.node('S',a,b,left=x,right=y,
                              left_forward=(x.s==a and x.t==v),
                              right_forward=(y.s==v and y.t==b),middle=v)
        next_edge+=1;active[next_edge]=parent
    root=next(iter(active.values()))
    vertices,edges=verify_tree(root)
    if edges!={edge(u,v) for u,v in g.edges()} or vertices!=set(g):
        raise AssertionError('SP decomposition reconstruction mismatch')
    return root

def verify_tree(root:Node) -> tuple[set[int],set[tuple[int,int]]]:
    """Check leaf disjointness, interface vertices, and orientation invariants."""
    if root.op=='L':
        assert root.original==edge(root.s,root.t)
        return {root.s,root.t},{root.original}
    assert root.left and root.right
    a,ae=verify_tree(root.left)
    b,be=verify_tree(root.right)
    assert ae.isdisjoint(be),'Leaves duplicated'
    if root.op=='S':
        assert a & b == {root.middle},'Series intersection is not one vertex'
        assert root.middle not in (root.s,root.t)
        la=(root.left.s,root.left.t) if root.left_forward else (root.left.t,root.left.s)
        rb=(root.right.s,root.right.t) if root.right_forward else (root.right.t,root.right.s)
        assert la==(root.s,root.middle) and rb==(root.middle,root.t)
    else:
        assert root.op=='P' and a&b=={root.s,root.t},'Parallel intersection mismatch'
        la=(root.left.s,root.left.t) if root.left_forward else (root.left.t,root.left.s)
        rb=(root.right.s,root.right.t) if root.right_forward else (root.right.t,root.right.s)
        assert la==(root.s,root.t) and rb==(root.s,root.t)
    return a|b,ae|be

def decompose_blocks(g:nx.Graph) -> list[tuple[set[tuple[int,int]],Node]]:
    blocks=[]
    for es in nx.biconnected_component_edges(g):
        h=nx.Graph();h.add_edges_from(es)
        root=build_block_tree(h)
        blocks.append(({edge(u,v) for u,v in es},root))
    blocks.sort(key=lambda be: min(be[0]))
    return blocks

def serialize_tree(node:Node) -> dict:
    d={'id':node.ident,'op':node.op,'s':node.s,'t':node.t}
    if node.op=='L':
        d['edge']=list(node.original)
    else:
        d.update({'left_forward':node.left_forward,'right_forward':node.right_forward,
                  'left':serialize_tree(node.left),'right':serialize_tree(node.right)})
        if node.op=='S':d['middle']=node.middle
    return d
