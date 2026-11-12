"""Deterministic benchmark generation with explicit, verifiable provenance."""
from __future__ import annotations
import hashlib
import json
import random
from pathlib import Path
import networkx as nx
from .core import Q_EDGES, edge, q_graph, validate_instance, make_graph, is_outerplanar

SEED=20261106
ORDERS=(12,24,48,96,192)

def zigzag_maximal(n:int)->nx.Graph:
    """A maximal polygon triangulation of arbitrary n, maximum degree <=4."""
    if n<3:raise ValueError('n must be at least three')
    g=nx.Graph();g.add_edges_from([(0,1),(1,2),(0,2)])
    for i in range(3,n):
        g.add_edges_from([(i-2,i),(i-1,i)])
    assert g.number_of_edges()==2*n-3
    assert max(dict(g.degree()).values())<=4
    assert is_outerplanar(g)
    return g

def multiblock_chain(n:int,rng:random.Random)->nx.Graph:
    g=nx.Graph();g.add_node(0)
    attachment=0
    while g.number_of_nodes()<n:
        left=n-g.number_of_nodes()
        # A cycle of length 3..5 adds 2..4 vertices. A bridge adds 1.
        count=1 if left==1 or rng.random()<.20 else min(left,rng.choice((2,3,4)))
        new=list(range(g.number_of_nodes(),g.number_of_nodes()+count))
        if count==1:
            g.add_edge(attachment,new[0])
        else:
            vs=[attachment]+new
            g.add_edges_from(zip(vs,vs[1:]+vs[:1]))
        attachment=rng.choice(new)
    validate_instance(g)
    assert len(list(nx.biconnected_components(g))) > 1 or g.number_of_edges() < 2
    return g

def nonmaximal(n:int,rng:random.Random)->nx.Graph:
    g=zigzag_maximal(n)
    # Delete some optional diagonals but keep all cycle edges to preserve connectedness.
    # Remove edges only while connectivity is preserved.
    candidates=[edge(u,v) for u,v in g.edges()]
    rng.shuffle(candidates)
    deletions=rng.randint(1,max(1,min(len(candidates)//2,int(n*.27))))
    for uv in candidates[:deletions]:
        if g.has_edge(*uv) and uv not in {edge(u,v) for u,v in nx.bridges(g)}:
            g.remove_edge(*uv)
    assert g.number_of_edges()<2*n-3 and nx.is_connected(g)
    validate_instance(g)
    return g

def shuffle_labels(g:nx.Graph,rng:random.Random)->nx.Graph:
    labels=list(range(len(g)))
    rng.shuffle(labels)
    return nx.relabel_nodes(g,dict(zip(sorted(g),labels)),copy=True)

def make_record(graph_id:str,grp:str,g:nx.Graph,meta:dict|None=None)->dict:
    validate_instance(g)
    n=len(g)
    assert set(g)==set(range(n))
    edges=[list(e) for e in sorted(edge(u,v) for u,v in g.edges())]
    payload={'graph_id':graph_id,'group':grp,'n':n,'m':len(edges),
             'max_degree':max(dict(g.degree()).values(),default=0),
             'edges':edges,'seed':SEED,'generator':(meta or {}).get('generator',grp)}
    if meta:payload.update(meta)
    payload['edge_sha256']=hashlib.sha256(json.dumps(edges,separators=(',',':')).encode()).hexdigest()
    return payload

def atlas_records()->list[dict]:
    result=[]
    for i,g in enumerate(nx.graph_atlas_g()):
        if g.number_of_edges() and max(dict(g.degree()).values())<=4 and is_outerplanar(g):
            result.append(make_record(f'atlas-G{i:04d}','graph_atlas',g,
                                      {'atlas_index':i,'generator':'networkx.graph_atlas_g'}))
    return result

def q_records()->list[dict]:
    q=q_graph()
    entries=[make_record('q-original','obstruction',q,{'deleted_edge':None,'generator':'Eq.(8)'})]
    for e in Q_EDGES:
        g=q.copy();g.remove_edge(*e)
        entries.append(make_record(f'q-delete-{e[0]}{e[1]}','obstruction',g,
                                   {'deleted_edge':list(e),'generator':'Eq.(8), edge deletion'}))
    return entries

def build_benchmarks(seed:int=SEED)->list[dict]:
    records=atlas_records()+q_records()
    for n in (5,6,7,12,24):
        records.append(make_record(f'maximal-n{n}','maximal',zigzag_maximal(n),
                                   {'generator':'zigzag_maximal'}))
    rng=random.Random(seed)
    for group,fn,per_n in [('nonmaximal',nonmaximal,40),('multiblock',multiblock_chain,20)]:
        for n in ORDERS:
            seen={}
            for k in range(per_n):
                for attempt in range(10000):
                    g=shuffle_labels(fn(n,rng),rng)
                    # Weisfeiler-Lehman is a fast shortlist; confirm isomorphism
                    # for any hash collision, so duplicate handling is exact.
                    wl=nx.weisfeiler_lehman_graph_hash(g)
                    if all(not nx.is_isomorphic(g,h) for h in seen.get(wl,[])):
                        seen.setdefault(wl,[]).append(g)
                        break
                else:raise RuntimeError(f'Cannot sample enough nonisomorphic graphs: {group} n={n}')
                records.append(make_record(f'{group}-n{n}-r{k:03d}',group,g,
                        {'generator':fn.__name__,'replicate':k,'group_seed':seed}))
    assert len(records)==len(atlas_records())+12+5+200+100
    return records

def write_jsonl(records:list[dict],out:Path):
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8',newline='\n') as f:
        for r in records:
            f.write(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n')

def read_jsonl(path:Path)->list[dict]:
    out=[]
    for raw in path.read_text(encoding='utf-8').splitlines():
        if not raw.strip():continue
        r=json.loads(raw)
        g=make_graph(r['n'],r['edges'])
        validate_instance(g)
        assert len(r['edges'])==g.number_of_edges()
        assert r['edge_sha256']==hashlib.sha256(json.dumps(r['edges'],separators=(',',':')).encode()).hexdigest()
        out.append(r)
    assert len({r['graph_id'] for r in out})==len(out)
    return out
