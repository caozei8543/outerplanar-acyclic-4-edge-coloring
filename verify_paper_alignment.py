#!/usr/bin/env python3
"""Verify 17-page CMC manuscript ↔ archived experimental evidence.

This is an integrity and data-coherence audit. It cannot establish theorem
novelty or that an image-transcribed topology is pixel-perfect.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path
from outer4aec.benchmarks import read_jsonl
from outer4aec.core import make_graph, verify_coloring, validate_instance
from outer4aec.certificates import validate_paper_certificates
from outer4aec.states import formal_enumeration

ROOT=Path(__file__).resolve().parents[1]
GROUPS={'graph_atlas':332,'obstruction':12,'maximal':5,'nonmaximal':200,'multiblock':100}
MODES=('full','exposed','dominance')
ORDERS=(12,24,48,96,192)

def ensure(test,why):
    if not test:raise AssertionError(why)

def load_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]

def load_csv(path):
    with path.open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))

def close(a,b,label,absolute_tol=1e-9):
    ensure(math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=absolute_tol),label+f': {a} != {b}')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    a=parser.parse_args()
    root=a.root
    version=json.loads((root/'docs/MANUSCRIPT_VERSION.json').read_text())
    pdf=root/version['canonical_pdf']
    ensure(pdf.is_file(),'Missing canonical PDF')
    ensure(hashlib.sha256(pdf.read_bytes()).hexdigest()==version['sha256'], 'Canonical final PDF has changed')
    inputs=read_jsonl(root/'data/empirical/benchmark_instances.jsonl')
    by_id={x['graph_id']:x for x in inputs}
    ensure(len(inputs)==649,'Incorrect total benchmark instances')
    ensure(dict(Counter(x['group'] for x in inputs))==GROUPS,'Incorrect category counts')
    for group,per_n in (('nonmaximal',40),('multiblock',20)):
        for n in ORDERS:
            ensure(sum(x['group']==group and x['n']==n for x in inputs)==per_n,f'{group} n={n} size')
    results=load_csv(root/'data/empirical/full_run/instance_results.csv')
    ensure(len(results)==len(inputs),'Wrong instance-result row count')
    res={r['graph_id']:r for r in results}
    ensure(set(res)==set(by_id),'Result IDs do not match benchmark IDs')
    assert_true_fields=('dp_consistent','node_consistent','certificate_valid')
    for gid,r in res.items():
        src=by_id[gid]
        ensure(all(r[k]=='True' for k in assert_true_fields),f'Negative validity flag: {gid}')
        for key in ('n','m','max_degree'):
            ensure(int(r[key])==src[key],f'Graph metadata mismatch {gid} {key}')
        ensure(r['group']==src['group'],f'Graph category mismatch {gid}')
        if r['group'] in ('graph_atlas','obstruction'):
            ensure(r['dp_decision']==r['oracle_decision'],f'Oracle mismatch {gid}')
        else:
            ensure(r['oracle_decision']=='',f'Unexpected exhaustive-oracle claim: {gid}')
    atlas=Counter(r['dp_decision'] for r in results if r['group']=='graph_atlas')
    obs=Counter(r['dp_decision'] for r in results if r['group']=='obstruction')
    ensure(atlas==Counter({'YES':331,'NO':1}),'Atlas 331/1 failure')
    ensure(obs==Counter({'YES':11,'NO':1}),'Q/deletions 11/1 failure')
    ensure(res['q-original']['dp_decision']=='NO','Q should be NO')
    ensure(res['atlas-G0840']['dp_decision']=='NO','G840 should be NO')

    witnesses=load_jsonl(root/'data/empirical/full_run/witnesses.jsonl')
    ensure(len(witnesses)==649,'Wrong witness count')
    ensure({x['graph_id'] for x in witnesses}==set(by_id),'Witness IDs differ')
    for w in witnesses:
        gid=w['graph_id'];rec=by_id[gid]
        ensure(w['decision']==res[gid]['dp_decision'],'Witness decision mismatch: '+gid)
        if w['decision']=='NO':
            ensure(w['dominance_coloring'] is None,'NO with coloring: '+gid)
        else:
            g=make_graph(rec['n'],rec['edges'])
            colors={tuple(x['edge']):x['color'] for x in w['dominance_coloring']}
            ensure(verify_coloring(g,colors)[0],'Invalid stored witness: '+gid)

    trees=load_jsonl(root/'data/empirical/decomposition_trees.jsonl')
    ensure(len(trees)==649,'Wrong decomposition tree count')
    ensure({x['graph_id'] for x in trees}==set(by_id),'Tree IDs differ')
    for tree in trees:
        gid=tree['graph_id'];rec=by_id[gid]
        ensure(tree['edge_sha256']==rec['edge_sha256'],'Tree input hash differs: '+gid)
        collected=[]
        def visit(node):
            if node['op']=='L':
                collected.append(tuple(sorted(node['edge'])))
            else:
                ensure(node['op'] in ('S','P'),'Unknown decomposition operation: '+gid)
                visit(node['left']);visit(node['right'])
        for block in tree['blocks']:
            visit(block['expression'])
            block_leaves=[]
            def block_visit(node):
                if node['op']=='L':block_leaves.append(tuple(sorted(node['edge'])))
                else:block_visit(node['left']);block_visit(node['right'])
            block_visit(block['expression'])
            ensure(sorted(map(tuple,block['original_edges']))==sorted(block_leaves), 'Block edge coverage mismatch: '+gid)
        ensure(sorted(collected)==sorted(map(tuple,rec['edges'])),'Tree leaf edges mismatch: '+gid)

    raw=load_csv(root/'data/empirical/full_run/raw_timing_repetitions.csv')
    ensure(len(raw)==649*3*7,'Wrong timed observations count')
    grouped=defaultdict(list)
    repetitions=defaultdict(set)
    for r in raw:
        gid=r['graph_id'];mode=r['variant'];key=(gid,mode)
        ensure(gid in by_id and mode in MODES,'Invalid timing graph/mode')
        ensure(r['group']==by_id[gid]['group'] and int(r['n'])==by_id[gid]['n'],'Timing metadata mismatch')
        idx=int(r['repeat_index'])
        ensure(idx not in repetitions[key],f'Duplicate timing repetition: {key}/{idx}')
        repetitions[key].add(idx)
        ms=float(r['dp_only_ms'])
        ensure(math.isfinite(ms) and ms>=0,'Negative/nonfinite timing')
        grouped[key].append(ms)
    ensure(len(grouped)==649*3,'Incomplete timing cells')
    for (gid,mode),values in grouped.items():
        ensure(repetitions[(gid,mode)]==set(range(1,8)),'Missing repetition indices')
        close(statistics.median(values),res[gid][f'{mode}_median_dp_only_ms'],f'Timing median {gid}/{mode}')

    nodes=load_csv(root/'data/empirical/full_run/node_level_consistency.csv')
    ensure(len(nodes)==72980,'Unexpected node-level check count')
    ensure(all(x['projection_equal']=='True' and x['minimization_equal']=='True' for x in nodes),
           'Inconsistent SP node found')
    ensure(set(x['graph_id'] for x in nodes)==set(by_id),'Node-level graph IDs differ')

    agg=load_csv(root/'data/empirical/full_run/aggregate_by_order.csv')
    ensure(len(agg)==15,'Wrong aggregate row count')
    for arow in agg:
        group=arow['group'];n=int(arow['n'])
        ensure(n in ORDERS and group in ('pooled_random','nonmaximal','multiblock'),'Unknown aggregate group')
        cohort=[r for r in results if int(r['n'])==n and
                (r['group'] in ('nonmaximal','multiblock') if group=='pooled_random' else r['group']==group)]
        ensure(int(arow['instances'])==len(cohort),'Aggregate size mismatch')
        for mode in MODES:
            for metric in ('cumulative_states','median_dp_only_ms','peak_traced_MB'):
                vals=[float(r[f'{mode}_{metric}']) for r in cohort]
                close(statistics.fmean(vals), arow[f'{mode}_{metric}_mean'],f'{group} n{n} {mode} {metric} mean')
                close(statistics.median(vals), arow[f'{mode}_{metric}_median'],f'{group} n{n} {mode} {metric} median')
        full=float(arow['full_cumulative_states_mean'])
        for mode in ('exposed','dominance'):
            reduction=100*(1-float(arow[f'{mode}_cumulative_states_mean'])/full)
            close(reduction,arow[f'{mode}_state_reduction_pct'],f'{group} n{n} reduction {mode}')
        mem=100*(1-float(arow['dominance_peak_traced_MB_mean'])/float(arow['full_peak_traced_MB_mean']))
        close(mem,arow['dominance_memory_reduction_pct'],f'{group} n{n} memory reduction')
        speed=float(arow['full_median_dp_only_ms_mean'])/float(arow['dominance_median_dp_only_ms_mean'])
        close(speed,arow['dominance_speedup_vs_full_x'],f'{group} n{n} speedup')
    r192=next(x for x in agg if x['group']=='pooled_random' and x['n']=='192')
    for field,target in [('dominance_state_reduction_pct',13.68),('dominance_memory_reduction_pct',13.21),
                         ('full_median_dp_only_ms_mean',20.68),('dominance_median_dp_only_ms_mean',38.09)]:
        ensure(round(float(r192[field]),2)==target,f'Final PDF Figure 6 numeric disagreement: {field}')

    form=formal_enumeration()
    stored=json.loads((root/'data/certificates/formal_state_enumeration.json').read_text())
    ensure(form==stored,'Formal-state checks conflict')
    paper_certs=json.loads((root/'data/certificates/paper_certificate_checks.json').read_text())
    ensure(paper_certs==validate_paper_certificates(),'Q and table certificates conflict')
    fig8=json.loads((root/'data/certificates/figure8_transcribed_topology_and_validated_witness.json').read_text())
    g=make_graph(71,[[u-1,v-1] for u,v in fig8['edges_1_based']]);validate_instance(g)
    colors={tuple(u-1 for u in x['edge']):x['slot'] for x in fig8['verified_color_witness_1_based']}
    ensure(verify_coloring(g,colors)[0],'Figure 8 recreated 4-slot witness invalid')
    ensure(nx_is_connected(g) and g.number_of_edges()==76 and max(dict(g.degree()).values())==4,
           'Figure 8 topology stats conflict')
    ensure(g.number_of_edges()-g.number_of_nodes()+1==6,'Figure 8 cycle rank invalid')

    manifest=json.loads((root/'data/empirical/full_run/run_manifest.json').read_text())
    ensure(manifest['records']==649 and manifest['warmups']==1 and manifest['timed_runs']==7,
           'Experimental protocol manifest differs')
    ensure(manifest['categories']==GROUPS and manifest['oracle_counts']=={'graph_atlas:YES':331,
           'graph_atlas:NO':1,'obstruction:YES':11,'obstruction:NO':1},'Run manifest counts mismatch')

    report={'status':'PASS','canonical_pdf_sha256':version['sha256'],'verified_benchmarks':649,
            'categories':GROUPS,'atlas_yes_no':dict(atlas),'obstruction_yes_no':dict(obs),
            'verified_witness_records':len(witnesses),'verified_sp_trees':len(trees),
            'verified_raw_timing_records':len(raw),'verified_node_checks':len(nodes),
            'figure6_n192':{field:round(float(r192[field]),2) for field in (
                    'dominance_state_reduction_pct','dominance_memory_reduction_pct',
                    'full_median_dp_only_ms_mean','dominance_median_dp_only_ms_mean')},
            'figure8':'PDF visually transcribed topology + independently validated 4-slot witness (NOT identical colors claim)',
            'limitations':'Performance is system-dependent; graph generator provenance follows scripts/benchmarks.py; figure8 image was visually transcribed.'}
    print(json.dumps(report,ensure_ascii=False,indent=2))

def nx_is_connected(g):
    import networkx as nx
    return nx.is_connected(g)

if __name__=='__main__':main()
