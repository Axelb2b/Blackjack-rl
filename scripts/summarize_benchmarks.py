"""Combine several benchmark JSON files into a human-readable result summary.

Confidence intervals are approximate: the estimates treat successive blackjack
rounds as independent although rounds within a shoe are correlated.
"""
import argparse
import csv
import json
import math
from pathlib import Path


def summarize(paths):
    groups = {}
    for p in paths:
        report = json.loads(Path(p).read_text(encoding='utf-8'))
        for r in report['results']:
            groups.setdefault(r['strategy'], []).append(r)
    rows=[]
    for strategy, results in groups.items():
        n=sum(r['rounds'] for r in results)
        mu=sum(r['ev_per_round']*r['rounds'] for r in results)/n
        # Recover unbiased sample variances from the normal 95% CI output,
        # then pool within- and between-run sum of squares.
        ss=0.0
        for r in results:
            ni=r['rounds']; m=r['ev_per_round']; se=(r['ci95_high']-r['ci95_low'])/(2*1.96)
            ss+=(ni-1)*(se*se*ni)+ni*(m-mu)**2
        sample_variance=ss/(n-1)
        se=math.sqrt(sample_variance/n)
        rows.append({'strategy':strategy,'rounds':n,'ev_per_round':mu,'ci95_low':mu-1.96*se,
                     'ci95_high':mu+1.96*se,'number_of_runs':len(results)})
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('files',nargs='+',help='Input benchmark JSON reports')
    p.add_argument('--output',default='reports/summary.csv')
    a=p.parse_args()
    rows=summarize(a.files)
    out=Path(a.output);out.parent.mkdir(exist_ok=True,parents=True)
    with out.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    for r in rows:
        print(f"{r['strategy']:24} n={r['rounds']:,} EV={r['ev_per_round']:+.5f} "+
              f"CI [{r['ci95_low']:+.5f}, {r['ci95_high']:+.5f}]")
    print(f'Wrote {out}')

if __name__=='__main__': main()
