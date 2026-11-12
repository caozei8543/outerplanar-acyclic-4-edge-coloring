#!/usr/bin/env python3
"""Run real measured experiments, not an interpolated or simulated dataset.

Repetitions: one warm-up and seven measured runs by default. The DP-only time
is the sum of the three per-block run_tree times, excluding decomposition and
external validation. tracemalloc peak is separately measured for each variant.
"""
from __future__ import annotations
import argparse,csv,json,platform,statistics,sys,time,tracemalloc,signal
from collections import Counter
from pathlib import Path
import networkx as nx
from outer4aec.benchmarks import read_jsonl
from outer4aec.core import make_graph,exhaustive_4color, verify_coloring
from outer4aec.decomposition import decompose_blocks
from outer4aec.dp import run_tree,solve_graph,MODES

P=Path(__file__).resolve().parents[1]

class TimedOut(Exception):pass

def run_mode_trees(trees,mode,timeout_s):
    start=time.perf_counter_ns()
    if timeout_s and hasattr(signal,'setitimer'):
        old=signal.signal(signal.SIGALRM,lambda sig,frame: (_ for _ in ()).throw(TimedOut()))
        signal.setitimer(signal.ITIMER_REAL,float(timeout_s))
    else:old=None
    try:
        runs=[run_tree(tree,mode) for tree in trees]
        return sum(r.elapsed_ns for r in runs)
    finally:
        if old is not None:
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,old)

def write_csv(path:Path,rows:list[dict],columns:list[str]):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns)
        w.writeheader();w.writerows(rows)

def select(records,profile):
    if profile=='full':return records
    if profile=='atlas':return [r for r in records if r['group'] in ('graph_atlas','obstruction')]
    # quick: all Graph Atlas + Q + all 5 maximal + 2 per random order/group.
    return [r for r in records if r['group'] in ('graph_atlas','obstruction','maximal') or
            (r['group'] in ('nonmaximal','multiblock') and r['replicate']<2)]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=P/'data/empirical/benchmark_instances.jsonl')
    p.add_argument('--outdir',type=Path,default=P/'data/empirical/quick_run')
    p.add_argument('--profile',choices=('quick','full','atlas'),default='quick')
    p.add_argument('--warmups',type=int,default=1)
    p.add_argument('--repeats',type=int,default=7)
    p.add_argument('--timeout-s',type=float,default=60.0)
    p.add_argument('--no-oracle',action='store_true')
    args=p.parse_args()
    if args.repeats<1 or args.warmups<0:raise ValueError('Invalid repeats/warm-ups')
    records=select(read_jsonl(args.input),args.profile)
    args.outdir.mkdir(parents=True,exist_ok=True)
    summary=[];raw=[];nodes=[];certificates=[]
    group_counter=Counter();ref_counter=Counter()
    start=time.perf_counter()
    for idx,r in enumerate(records):
        g=make_graph(r['n'],r['edges']);gid=r['graph_id']
        decomp_started=time.perf_counter_ns()
        parts=decompose_blocks(g)
        decomposed_ns=time.perf_counter_ns()-decomp_started
        calculated=solve_graph(g,check_states=True,include_trees=False)
        decisions=calculated['decision']
        oracle=None
        if (r['group'] in ('graph_atlas','obstruction')) and not args.no_oracle:
            witness=exhaustive_4color(g)
            oracle=witness is not None
            if oracle != decisions['dominance']:
                raise AssertionError(f'Independent oracle mismatch: {gid}')
            ref_counter[f'{r["group"]}:{"YES" if oracle else "NO"}']+=1
        else:
            oracle=None
        for block_index,detail in enumerate(calculated['blocks']):
            for n in detail['node_identities']:
                nodes.append({'graph_id':gid, 'block_index':block_index,
                              'block_root_id':detail['root_id'],**n})
        cert=calculated['certificates']['dominance']
        if cert is not None:
            check={tuple(item['edge']):item['color'] for item in cert}
            assert verify_coloring(g,check)[0]
        certificates.append({'graph_id':gid,'decision':'YES' if cert is not None else 'NO',
                             'dominance_coloring':cert})
        row={'graph_id':gid,'group':r['group'],'n':r['n'],'m':r['m'],
             'max_degree':r['max_degree'],'oracle_decision':
                  ('YES' if oracle else 'NO') if oracle is not None else '',
             'dp_decision':'YES' if decisions['dominance'] else 'NO',
             'dp_consistent':len(set(decisions.values()))==1,
             'node_consistent':all(t['projection_equal'] and t['minimization_equal']
                                   for d in calculated['blocks'] for t in d['node_identities']),
             'certificate_valid':True,'decomposition_ms':decomposed_ns/1e6,
             'num_blocks':len(parts)}
        trees=[root for _,root in parts]
        for mode in MODES:
            metrics=calculated['metrics'][mode]
            for metric in ('cumulative_states','transitions_examined',
                           'transitions_accepted','candidates_unique','dominated_removed'):
                row[f'{mode}_{metric}']=metrics[metric]
            for _ in range(args.warmups):
                run_mode_trees(trees,mode,args.timeout_s)
            measurements=[]
            for rep in range(args.repeats):
                try:elapsed_ns=run_mode_trees(trees,mode,args.timeout_s)
                except TimedOut:
                    raise RuntimeError(f'60-second per-run timeout exceeded: {gid}/{mode}')
                measurements.append(elapsed_ns/1e6)
                raw.append({'graph_id':gid,'group':r['group'],'n':r['n'],
                            'variant':mode,'repeat_index':rep+1,'dp_only_ms':elapsed_ns/1e6})
            row[f'{mode}_median_dp_only_ms']=statistics.median(measurements)
            # Peak traced Python allocation is measured separately; not included in DP time.
            tracemalloc.start()
            run_mode_trees(trees,mode,args.timeout_s)
            _,peak=tracemalloc.get_traced_memory()
            tracemalloc.stop()
            row[f'{mode}_peak_traced_MB']=peak/1e6
        summary.append(row)
        group_counter[r['group']]+=1
        if idx%50==0:
            print(f'completed {idx+1}/{len(records)}: {gid}',flush=True)
    stem=summary[0].keys() if summary else []
    write_csv(args.outdir/'instance_results.csv',summary,list(stem))
    write_csv(args.outdir/'raw_timing_repetitions.csv',raw,
              ['graph_id','group','n','variant','repeat_index','dp_only_ms'])
    write_csv(args.outdir/'node_level_consistency.csv',nodes,
              ['graph_id','block_index','block_root_id','node_id','op','full','exposed','dominance',
               'projection_equal','minimization_equal'])
    with (args.outdir/'witnesses.jsonl').open('w',encoding='utf-8') as f:
        for x in certificates:f.write(json.dumps(x,sort_keys=True)+'\n')
    metadata={'status':'ACTUAL_EXECUTION_NOT_SIMULATED','benchmark_file':str(args.input.name),
              'profile':args.profile,'records':len(records),'seed':20261106,
              'categories':dict(sorted(group_counter.items())),
              'oracle_counts':dict(sorted(ref_counter.items())),
              'warmups':args.warmups,'timed_runs':args.repeats,'timeout_s':args.timeout_s,
              'dp_time_unit':'milliseconds','peak_memory_unit':'decimal MB (1,000,000 bytes)',
              'dp_time_scope':'sum of run_tree.elapsed_ns over blocks; excludes decomposition, testing, tracing',
              'memory_scope':'tracemalloc peak of run_tree across precomputed block trees',
              'graph_atlas_filter':'nonempty, outerplanar and max_degree<=4',
              'python_version':platform.python_version(),
              'networkx_version':nx.__version__,
              'platform':platform.platform(),
              'run_wall_seconds':round(time.perf_counter()-start,3)}
    (args.outdir/'run_manifest.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metadata,indent=2))

if __name__=='__main__':main()
