"""Create a compact figure for the README from the CSV benchmark summary.
Requires matplotlib (optional)."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt

rows=list(csv.DictReader(Path('reports/summary.csv').open(encoding='utf-8')))
rows=[r for r in rows if r['strategy'] != 'Random']
rows.sort(key=lambda r:float(r['ev_per_round']))
labels=[r['strategy'] for r in rows]
means=[float(r['ev_per_round']) for r in rows]
low=[float(r['ev_per_round'])-float(r['ci95_low']) for r in rows]
high=[float(r['ci95_high'])-float(r['ev_per_round']) for r in rows]
fig,ax=plt.subplots(figsize=(9,4.4),layout='constrained')
pos=list(range(len(rows)))
ax.errorbar(means,pos,xerr=[low,high],fmt='o',capsize=5,markersize=7,linewidth=1.8)
ax.axvline(0,linestyle='--',alpha=.5)
ax.set_yticks(pos,labels)
ax.set_xlabel('Average net payout per round (initial-bet units)')
ax.set_title('Blackjack strategies — simulated performance (400k rounds per policy)')
ax.grid(axis='x',alpha=.22)
ax.tick_params(axis='y',length=0)
ax.set_xlim(-0.065,0.017)
fig.savefig('assets/benchmark_ev.png',dpi=180)
plt.close(fig)
