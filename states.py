"""Exact full/exposed state machinery, mask conventions, formal enumeration."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from itertools import combinations, permutations
from math import comb

PAIRS = tuple(combinations(range(4),2))
PAIR_BITS = tuple((1<<u)|(1<<v) for u,v in PAIRS)

@dataclass(frozen=True, order=True)
class State:
    a: int
    b: int
    c: int

def eligible_mask(a:int,b:int) -> int:
    out=0
    for i,p in enumerate(PAIR_BITS):
        if (a & p).bit_count()==1 and (b & p).bit_count()==1:
            out |= (1<<i)
    return out

def project(st:State) -> State:
    return State(st.a,st.b,st.c & eligible_mask(st.a,st.b))

def reverse(st:State) -> State:
    return State(st.b,st.a,st.c)

def leaf(color:int) -> State:
    mask=1<<(color-1)
    connectivity=sum(1<<i for i,p in enumerate(PAIR_BITS) if mask & p)
    return State(mask,mask,connectivity)

def transition(op:str, x:State,y:State, mode:str) -> State | None:
    """x and y are already oriented to the parent (series or parallel)."""
    if op=='S':
        if x.b & y.a: return None
        z=State(x.a,y.b,x.c & y.c)
    elif op=='P':
        if (x.a & y.a) or (x.b & y.b) or (x.c & y.c): return None
        z=State(x.a | y.a, x.b | y.b, x.c | y.c)
    else:
        raise ValueError(op)
    return z if mode=='full' else project(z)

def minimize(states: set[State]) -> set[State]:
    grouped:dict[tuple[int,int],set[int]]={}
    for s in states:
        grouped.setdefault((s.a,s.b),set()).add(s.c)
    out=set()
    for (a,b), masks in grouped.items():
        for c in masks:
            if not any(other!=c and (other & c)==other for other in masks):
                out.add(State(a,b,c))
    return out

def formal_enumeration() -> dict:
    counts=Counter()
    formal=[]
    for a in range(16):
        for b in range(16):
            m=eligible_mask(a,b)
            bits=[i for i in range(6) if (m>>i)&1]
            counts[len(bits)]+=1
            for subset in range(1<<len(bits)):
                f=sum((1<<bit) for j,bit in enumerate(bits) if subset>>j&1)
                formal.append(State(a,b,f))
    bounds=sum(count*comb(j,j//2) for j,count in counts.items())
    fixed=Counter()
    for perm in permutations(range(4)):
        def mapp(mask):
            return sum((1<<perm[i]) for i in range(4) if (mask>>i)&1)
        pairmap={i:PAIRS.index(tuple(sorted((perm[u],perm[v])))) for i,(u,v) in enumerate(PAIRS)}
        def mapc(c):return sum(1<<pairmap[i] for i in range(6) if (c>>i)&1)
        cycle_lengths=[];seen=set()
        for i in range(4):
            if i in seen:continue
            j=i;size=0
            while j not in seen:
                seen.add(j);size+=1;j=perm[j]
            cycle_lengths.append(size)
        cycle_type=','.join(str(v) for v in sorted(cycle_lengths,reverse=True))
        fixed[cycle_type]+=sum(mapp(s.a)==s.a and mapp(s.b)==s.b and mapc(s.c)==s.c for s in formal)
    return {'table_1':{str(i):counts[i] for i in range(5)},
            'full_formal_states':16*16*64,'exposed_formal_states':len(formal),
            'antichain_upper_bound':bounds,
            'fixed_counts_by_cycle_type_totals':dict(sorted(fixed.items())),
            'orbit_count':sum(fixed.values())//24}
