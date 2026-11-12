"""Independent graph utilities and finite acyclic-edge-coloring oracle.

All graphs are finite, simple, undirected, with integer vertex labels.
Acyclicity is checked directly on all unordered color pairs; it does not
reuse the dynamic programming transition rules.
"""
from __future__ import annotations

from itertools import combinations
from typing import Mapping
import networkx as nx

PALETTE = (1, 2, 3, 4)
Q_EDGES = ((0, 1), (0, 2), (0, 5), (0, 6), (1, 5), (2, 3),
           (2, 4), (2, 6), (3, 4), (4, 6), (5, 6))
Q_FIVE_CERT = (4, 1, 3, 2, 1, 4, 2, 3, 1, 4, 5)
Q_DELETION_CERT = {
    (0, 1): (None, 2, 1, 3, 2, 3, 4, 1, 1, 2, 4),
    (0, 2): (3, None, 2, 1, 1, 3, 1, 2, 4, 3, 4),
    (0, 5): (1, 2, None, 3, 3, 4, 3, 1, 2, 4, 2),
    (0, 6): (2, 1, 3, None, 4, 4, 2, 3, 3, 1, 2),
    (1, 5): (4, 1, 3, 2, None, 2, 4, 3, 3, 1, 4),
    (4, 6): (4, 1, 2, 3, 1, 3, 4, 2, 1, None, 4),
}

def edge(u: int, v: int) -> tuple[int, int]:
    if u == v:
        raise ValueError('Self-loop forbidden')
    return (u, v) if u < v else (v, u)

def make_graph(n: int, edges: list[list[int]] | list[tuple[int,int]]) -> nx.Graph:
    if n < 0 or not isinstance(n, int):
        raise ValueError('n must be a nonnegative integer')
    g = nx.Graph()
    g.add_nodes_from(range(n))
    for uv in edges:
        if len(uv) != 2:
            raise ValueError('Edge must contain two endpoints')
        u, v = map(int, uv)
        if not (0 <= u < n and 0 <= v < n) or u == v or g.has_edge(u, v):
            raise ValueError('Non-simple or out-of-range edge')
        g.add_edge(u, v)
    return g

def is_outerplanar(g: nx.Graph) -> bool:
    """G is outerplanar iff adding a universal apex produces a planar graph."""
    if g.is_multigraph() or nx.number_of_selfloops(g):
        return False
    h = nx.Graph(g)
    apex = object()
    h.add_node(apex)
    h.add_edges_from((apex, v) for v in g)
    return nx.check_planarity(h, counterexample=False)[0]

def validate_instance(g: nx.Graph) -> None:
    if g.is_directed() or g.is_multigraph() or nx.number_of_selfloops(g):
        raise ValueError('A finite, undirected, simple graph is required')
    if max(dict(g.degree()).values(), default=0) > 4:
        raise ValueError('Maximum degree exceeds 4')
    if not is_outerplanar(g):
        raise ValueError('Graph is not outerplanar')

def verify_coloring(g: nx.Graph, colors: Mapping[tuple[int,int],int], k: int = 4) -> tuple[bool,str]:
    """Verify properness and acyclicity independently of all DP signatures."""
    c = {edge(*e): color for e, color in colors.items()}
    if len(c) != g.number_of_edges() or set(c) != {edge(u,v) for u,v in g.edges()}:
        return False, 'Incomplete or extraneous edge assignment'
    if any(not isinstance(color,int) or not (1 <= color <= k) for color in c.values()):
        return False, 'Color outside palette'
    for v in g:
        incident = [c[edge(u,v)] for u in g.neighbors(v)]
        if len(set(incident)) != len(incident):
            return False, f'Improper at vertex {v}'
    if g.number_of_nodes()==0:
        return True, 'valid'
    for a,b in combinations(range(1,k+1),2):
        h = nx.Graph()
        h.add_nodes_from(g)
        h.add_edges_from(uv for uv, col in c.items() if col in (a,b))
        if not nx.is_forest(h):
            return False, f'Bichromatic cycle for pair {a},{b}'
    return True, 'valid'

def exhaustive_4color(g: nx.Graph, *, k: int = 4) -> dict[tuple[int,int],int] | None:
    """Reference backtracking solver; independent of the three DP variants.

    Canonical first-appearance color labels remove global color symmetry without
    excluding any colorable graph. Incremental path tests rule out two-color
    cycles, while incident-color sets enforce properness.
    """
    if max(dict(g.degree()).values(), default=0) > k:
        return None
    edges = sorted((edge(u,v) for u,v in g.edges()),
                   key=lambda e: (-g.degree(e[0])-g.degree(e[1]), e))
    chosen: dict[tuple[int,int],int] = {}
    incident = {v:set() for v in g}
    def two_color_path(u:int, v:int, c:int, d:int) -> bool:
        adj = {}
        for (x,y), col in chosen.items():
            if col in (c,d):
                adj.setdefault(x,[]).append(y)
                adj.setdefault(y,[]).append(x)
        reached = {u}
        stack = [u]
        while stack:
            x=stack.pop()
            for y in adj.get(x,[]):
                if y == v: return True
                if y not in reached:
                    reached.add(y);stack.append(y)
        return False
    def walk(i:int, max_used:int) -> bool:
        if i == len(edges): return True
        u,v = edges[i]
        for color in range(1,min(k,max_used+1)+1):
            if color in incident[u] or color in incident[v]:
                continue
            if any(two_color_path(u,v,color,other) for other in range(1,k+1) if other != color):
                continue
            chosen[(u,v)] = color
            incident[u].add(color);incident[v].add(color)
            if walk(i+1,max(color,max_used)):
                return True
            del chosen[(u,v)]
            incident[u].remove(color);incident[v].remove(color)
        return False
    return dict(chosen) if walk(0,0) else None

def q_graph() -> nx.Graph:
    return make_graph(7,list(Q_EDGES))
