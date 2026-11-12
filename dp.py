"""Three exact DP variants with node-level state identities and certificates."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import permutations
from time import perf_counter_ns
from typing import Any
import networkx as nx
from .core import edge, validate_instance, verify_coloring
from .states import State, leaf, reverse, project, minimize, transition
from .decomposition import Node, decompose_blocks, serialize_tree

MODES=('full','exposed','dominance')

@dataclass
class Run:
    mode: str
    root: Node
    states: dict[int,dict[State,Any]]
    cumulative_states: int
    transitions_examined: int
    transitions_accepted: int
    candidates_unique: int
    dominated_removed: int
    elapsed_ns: int

    @property
    def feasible(self) -> bool:
        return bool(self.states[self.root.ident])


def run_tree(root:Node,mode:str) -> Run:
    if mode not in MODES:raise ValueError('Unknown DP mode')
    states={}
    count={'cumulative_states':0,'transitions_examined':0,
           'transitions_accepted':0,'candidates_unique':0,'dominated_removed':0}
    start=perf_counter_ns()
    def visit(node:Node):
        if node.op=='L':
            family={leaf(c) if mode=='full' else project(leaf(c)):('leaf',c)
                    for c in range(1,5)}
        else:
            visit(node.left);visit(node.right)
            fam_left=states[node.left.ident]
            fam_right=states[node.right.ident]
            family={}
            for xs in sorted(fam_left):
                x=xs if node.left_forward else reverse(xs)
                for ys in sorted(fam_right):
                    count['transitions_examined']+=1
                    y=ys if node.right_forward else reverse(ys)
                    z=transition(node.op,x,y,mode)
                    if z is not None:
                        count['transitions_accepted']+=1
                        family.setdefault(z,('join',xs,ys))
            count['candidates_unique']+=len(family)
            if mode=='dominance':
                keep=minimize(set(family))
                count['dominated_removed']+=len(family)-len(keep)
                family={s:family[s] for s in keep}
        states[node.ident]=family
        count['cumulative_states']+=len(family)
    visit(root)
    return Run(mode,root,states,**count,elapsed_ns=perf_counter_ns()-start)


def reconstruct_tree(run:Run) -> dict[tuple[int,int],int] | None:
    if not run.feasible:return None
    colors={}
    def walk(node:Node, sig:State):
        proof=run.states[node.ident][sig]
        if node.op=='L':
            assert proof[0]=='leaf'
            colors[node.original]=proof[1]
        else:
            assert proof[0]=='join'
            walk(node.left,proof[1]);walk(node.right,proof[2])
    walk(run.root,min(run.states[run.root.ident]))
    return colors


def node_identity(full:Run, exposed:Run, dominance:Run) -> list[dict]:
    assert full.root is exposed.root is dominance.root
    result=[]
    def visit(x:Node):
        f=set(full.states[x.ident]);e=set(exposed.states[x.ident]);d=set(dominance.states[x.ident])
        correct_e={project(st) for st in f} == e
        correct_d=minimize(e)==d
        result.append({'node_id':x.ident,'op':x.op,'full':len(f),'exposed':len(e),
                       'dominance':len(d),'projection_equal':correct_e,
                       'minimization_equal':correct_d})
        if x.left:visit(x.left);visit(x.right)
    visit(full.root)
    return result


def combine_block_colorings(g:nx.Graph, blocks:list[dict[tuple[int,int],int]]) -> dict[tuple[int,int],int]:
    """Join block witnesses along the block-cut forest using color permutations.

    Attach a block at exactly one already colored vertex whenever possible.
    Only start a new connected component if none of the remaining blocks
    attaches to the current colored region.
    """
    colored={}
    pending=list(blocks)
    while pending:
        activeverts={v for uv in colored for v in uv}
        candidates=[]
        for i,b in enumerate(pending):
            bverts={v for uv in b for v in uv}
            common=bverts & activeverts
            candidates.append((i,common))
        attach=next(((i,com) for i,com in candidates if len(com)==1),None)
        if attach is None:
            attach=next(((i,com) for i,com in candidates if len(com)==0),None)
        if attach is None:
            raise AssertionError('Block-cut composition did not find valid attachment')
        i,common=attach
        b=pending.pop(i)
        if common:
            v=next(iter(common))
            used={c for uv,c in colored.items() if v in uv}
            own={c for uv,c in b.items() if v in uv}
            assert len(used)+len(own)<=4
            mapping={x:y for x,y in zip(sorted(own),sorted(set(range(1,5))-used))}
            remaining_src=sorted(set(range(1,5))-set(mapping))
            remaining_dst=sorted(set(range(1,5))-set(mapping.values()))
            mapping.update(zip(remaining_src,remaining_dst))
        else:
            mapping={c:c for c in range(1,5)}
        assert set(colored).isdisjoint(b)
        colored.update({uv:mapping[c] for uv,c in b.items()})
    assert set(colored)=={edge(u,v) for u,v in g.edges()}
    return colored


def solve_graph(g:nx.Graph, *, modes=MODES,
                check_states:bool=True, include_trees:bool=False) -> dict:
    validate_instance(g)
    blocks=decompose_blocks(g)
    total={mode:{'cumulative_states':0,'transitions_examined':0,
                 'transitions_accepted':0,'candidates_unique':0,
                 'dominated_removed':0,'elapsed_ns':0} for mode in modes}
    decisions={m:True for m in modes}
    certs={m:[] for m in modes}
    details=[]
    for edges,root in blocks:
        runs={m:run_tree(root,m) for m in modes}
        for m, run in runs.items():
            decisions[m]&=run.feasible
            for key in total[m]:total[m][key]+=getattr(run,key)
            if run.feasible:
                colors=reconstruct_tree(run)
                h=nx.Graph();h.add_edges_from(edges)
                ok,reason=verify_coloring(h,colors)
                if not ok:raise AssertionError(f'Witness invalid: {reason}')
                certs[m].append(colors)
        if check_states and set(MODES)<=set(modes):
            identities=node_identity(runs['full'],runs['exposed'],runs['dominance'])
            bad=[t for t in identities if not (t['projection_equal'] and t['minimization_equal'])]
            if bad:
                raise AssertionError(f'Node-level state inconsistency: {bad[:3]}')
        else:identities=[]
        detail={'edges':[list(e) for e in sorted(edges)],
                'root_id':root.ident,
                'root_sizes':{m:len(runs[m].states[root.ident]) for m in modes},
                'node_count':len(next(iter(runs.values())).states),
                'node_identities':identities}
        if include_trees:detail['tree']=serialize_tree(root)
        details.append(detail)
    if len(set(decisions.values()))>1:
        raise AssertionError('DP decisions disagree')
    certificates={}
    for m in modes:
        if decisions[m]:
            colors=combine_block_colorings(g,certs[m])
            ok,reason=verify_coloring(g,colors)
            if not ok:raise AssertionError(f'Combined witness invalid: {reason}')
            certificates[m]=[{'edge':list(uv),'color':col} for uv,col in sorted(colors.items())]
        else:
            certificates[m]=None
    return {'n':g.number_of_nodes(),'m':g.number_of_edges(),
            'max_degree':max(dict(g.degree()).values(), default=0),
            'decision':decisions,'metrics':total,
            'certificates':certificates,'blocks':details}
