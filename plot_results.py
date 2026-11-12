#!/usr/bin/env python3
"""Replot *measured* Figure 6 series from the 649-entry final data.

No invented illustration-only data is used or distributed in this release.
"""
from __future__ import annotations
import argparse,csv,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
ORDERS=(12,24,48,96,192)
MODES=(('full','Full-DP'),('exposed','Exposed-DP'),('dominance','Dominance-DP'))
METRICS=(('cumulative_states','Cumulative retained states','measured_states'),
         ('median_dp_only_ms','DP-only time (ms)','measured_time'),
         ('peak_traced_MB','Peak traced Python memory (MB)','measured_memory'))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=('measured',),default='measured',help='Only measured results are supported')
    ap.add_argument('--input',type=Path,default=ROOT/'data/empirical/full_run/instance_results.csv')
    ap.add_argument('--outdir',type=Path,default=ROOT/'figures')
    a=ap.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)
    with a.input.open(encoding='utf-8',newline='') as f:
        raw=list(csv.DictReader(f))
    rows=[r for r in raw if r['group'] in ('nonmaximal','multiblock')]
    orders=sorted(set(int(r['n']) for r in rows))
    if not orders:raise ValueError('No generated nonmaximal / multiblock graph records')
    counts={n:sum(int(r['n'])==n for r in rows) for n in orders}
    if set(orders)==set(ORDERS) and len(raw)==649:
        assert all(counts[n]==60 for n in orders),'Expected 60 random instances for each size'
    grid={}
    for metric,_,_ in METRICS:
        for mode,_ in MODES:
            grid[(metric,mode)]=[statistics.fmean(float(r[f'{mode}_{metric}']) for r in rows if int(r['n'])==n) for n in orders]
    for metric,ylabel,fname in METRICS:
        fig,ax=plt.subplots(figsize=(7.3,4.8))
        for mode,label in MODES:
            ax.plot(orders,grid[(metric,mode)],marker='o',label=label)
        ax.set_xscale('log',base=2)
        ax.set_xticks(orders,list(map(str,orders)))
        ax.set_xlabel('Graph order n');ax.set_ylabel(ylabel)
        ax.set_title('Measured; unweighted mean over generated instances')
        ax.legend();fig.tight_layout()
        fig.savefig(a.outdir/f'{fname}.png',dpi=240)
        plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(15.6,4.7))
    for i,(metric,ylabel,_) in enumerate(METRICS):
        ax=axes[i]
        for mode,label in MODES:
            ax.plot(orders,grid[(metric,mode)],marker='o',label=label)
        ax.set_xscale('log',base=2)
        ax.set_xticks(orders,list(map(str,orders)))
        ax.set_xlabel('Graph order n')
        ax.set_ylabel(ylabel)
        ax.set_title(f'({chr(ord("a")+i)}) {ylabel}')
        if i==2:ax.legend(loc='best')
    fig.suptitle('Paper Figure 6 data — fresh rendering from archived measured CSV',fontsize=12)
    fig.tight_layout()
    fig.savefig(a.outdir/'paper_figure6_data_replot.png',dpi=250)
    plt.close(fig)
    with (a.outdir/'paper_figure6_plot_values.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow(['n','instances','mode','mean_cumulative_states','mean_dp_only_ms','mean_peak_traced_MB'])
        for j,n in enumerate(orders):
            for mode,_ in MODES:
                writer.writerow([n,counts[n],mode]+[grid[(metric,mode)][j] for metric,_,_ in METRICS])
    print(f'Replotted paper Figure 6 from {len(rows)} archived generated graph records across {len(orders)} sizes')

if __name__=='__main__':main()
