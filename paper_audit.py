#!/usr/bin/env python3
"""Summarize actual data against the final 17-page CMC manuscript (not old draft)."""
from __future__ import annotations
import argparse,csv,json,statistics
from collections import Counter
from pathlib import Path
from outer4aec.benchmarks import read_jsonl
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--instances',type=Path,default=ROOT/'data/empirical/benchmark_instances.jsonl')
    p.add_argument('--results',type=Path,default=ROOT/'data/empirical/full_run/instance_results.csv')
    p.add_argument('--output',type=Path,default=ROOT/'docs/paper_claims_vs_reproducible.json')
    a=p.parse_args()
    inputs=read_jsonl(a.instances)
    with a.results.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    c=Counter(x['group'] for x in inputs)
    rr=Counter(r['group'] for r in rows)
    atlas=Counter(r['dp_decision'] for r in rows if r['group']=='graph_atlas')
    q=Counter(r['dp_decision'] for r in rows if r['group']=='obstruction')
    complete=(len(inputs)==649 and len(rows)==649 and len({r['graph_id'] for r in rows})==649)
    report={
     'source_article':'paper/CMC_Condensed_Illustrated_Graphs_FINAL_17p.pdf',
     'source_scope':'FINAL 17-page PDF, not the withdrawn 23-page manuscript',
     'classification':'ARCHIVED_DATA_ALIGNMENT_REPORT; measured performance, not simulated',
     'canonical_benchmark_entries':649,
     'observed_benchmark_entries':len(rows),
     'graph_input_count':len(inputs),
     'graph_input_categories':dict(sorted(c.items())),
     'recorded_results_categories':dict(sorted(rr.items())),
     'full_649_result_set_present':complete,
     'atlas_reference_yes_no':dict(atlas),
     'obstruction_reference_yes_no':dict(q),
     'three_dp_variants_agree':all(r['dp_consistent']=='True' for r in rows),
     'all_reported_node_identities_agree':all(r['node_consistent']=='True' for r in rows),
     'all_reported_witnesses_valid':all(r['certificate_valid']=='True' for r in rows),
     'note':'This summary is not a substitute for scripts/verify_paper_alignment.py, which rechecks stored YES witnesses and raw CSV arithmetic.',
    }
    cohort=[r for r in rows if r['group'] in ('nonmaximal','multiblock') and int(r['n'])==192]
    if len(cohort)==60:
        def avg(k):return statistics.fmean(float(r[k]) for r in cohort)
        full=avg('full_cumulative_states');dominance=avg('dominance_cumulative_states')
        memfull=avg('full_peak_traced_MB');memdom=avg('dominance_peak_traced_MB')
        report['figure6_n192_archived']={
          'random_graph_entries':len(cohort),
          'state_reduction_percent':round((1-dominance/full)*100,2),
          'traced_memory_reduction_percent':round((1-memdom/memfull)*100,2),
          'full_dp_time_ms':round(avg('full_median_dp_only_ms'),2),
          'dominance_dp_time_ms':round(avg('dominance_median_dp_only_ms'),2)
        }
        if complete:
            assert report['figure6_n192_archived']=={'random_graph_entries':60,
              'state_reduction_percent':13.68,'traced_memory_reduction_percent':13.21,
              'full_dp_time_ms':20.68,'dominance_dp_time_ms':38.09},'Final Figure 6 mismatch'
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
