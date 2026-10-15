"""Render only measured development summaries; no independent-quality claims."""
import json,argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('--summary',required=True);p.add_argument('--output',required=True);a=p.parse_args();rows=json.loads(Path(a.summary).read_text());out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(11,4.5));names=[r['policy'].capitalize() for r in rows]
for ax,field,title in [(axes[0],'mean_attempts','Mean retrieval attempts'),(axes[1],'mean_retrieval_seconds','Mean local retrieval latency (ms)')]:
 values=[r[field]*(1000 if field.endswith('seconds') else 1) for r in rows];bars=ax.bar(names,values,color=['#087F88','#386B88','#7698AD','#A9BBC6']);ax.bar_label(bars,fmt='%.2f',padding=3);ax.set_title(title);ax.set_ylim(0,max(values)*1.25)
fig.suptitle('Development only: 4 known questions, 3 repetitions, 4 policies',fontweight='bold');fig.text(.5,.01,'No independent human quality or monetary-cost result. Source: development_sequential/summary.json',ha='center',fontsize=9);fig.tight_layout(rect=(0,.06,1,.92));fig.savefig(out/'development_effort_latency.png',dpi=180);fig.savefig(out/'development_effort_latency.svg');plt.close(fig)
