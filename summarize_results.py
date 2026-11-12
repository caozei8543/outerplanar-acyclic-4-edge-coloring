#!/usr/bin/env python3
"""Aggregate archived actual per-instance medians for final Figure 6."""
from __future__ import annotations
import csv,statistics
from pathlib import Path
from collections import defaultdict
P=Path(__file__).resolve().parents[1]

def mean(xs):return statistics.fmean(xs)
def pct(xs,q):
    z=sorted(xs)
    if len(z)==1:return z[0]
    at=(len(z)-1)*q
    lo=int(at);hi=min(lo+1,len(z)-1)
    return z[lo]+(z[hi]-z[lo])*(at-lo)

def run():
    source=P/'data/empirical/full_run/instance_results.csv'
    rows=list(csv.DictReader(source.open(encoding='utf-8')))
    out=[]
    for group in ['pooled_random','nonmaximal','multiblock']:
        selected=[r for r in rows if (r['group'] in ('nonmaximal','multiblock')
                                     if group=='pooled_random' else r['group']==group)]
        for n in (12,24,48,96,192):
            cohort=[r for r in selected if int(r['n'])==n]
            if not cohort:continue
            entry={'group':group,'n':n,'instances':len(cohort),
                   'definition':'unweighted cross-instance mean of individual medians'}
            for mode in ('full','exposed','dominance'):
                for field in ('cumulative_states','median_dp_only_ms','peak_traced_MB'):
                    name=f'{mode}_{field}'
                    vals=[float(r[name]) for r in cohort]
                    entry[name+'_mean']=mean(vals)
                    entry[name+'_median']=statistics.median(vals)
                    entry[name+'_p25']=pct(vals,.25)
                    entry[name+'_p75']=pct(vals,.75)
            f=entry['full_cumulative_states_mean']
            for mode in ('exposed','dominance'):
                entry[mode+'_state_reduction_pct']=100*(1-entry[mode+'_cumulative_states_mean']/f)
            entry['dominance_speedup_vs_full_x']=(entry['full_median_dp_only_ms_mean']/
                                                   entry['dominance_median_dp_only_ms_mean'])
            entry['dominance_memory_reduction_pct']=100*(1-entry['dominance_peak_traced_MB_mean']/
                                                        entry['full_peak_traced_MB_mean'])
            out.append(entry)
    output=P/'data/empirical/full_run/aggregate_by_order.csv'
    with output.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]))
        w.writeheader();w.writerows(out)
    print('Wrote',output,'rows=',len(out))
    for row in out:
        if row['group']=='pooled_random':
            print('n=',row['n'],'count=',row['instances'],
                  'E_reduction_pct=',round(row['exposed_state_reduction_pct'],2),
                  'D_reduction_pct=',round(row['dominance_state_reduction_pct'],2),
                  'D_speedup=',round(row['dominance_speedup_vs_full_x'],3),
                  'D_memory_reduction_pct=',round(row['dominance_memory_reduction_pct'],2))

if __name__=='__main__':run()
