"""Recompute historical aggregates without loading a model or altering raw CSVs."""
import csv, json, hashlib, statistics, collections, re, difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

def read(p): return list(csv.DictReader((ROOT/p).open(encoding='utf-8-sig')))
def main():
 p='research/vit_v1/advanced_question_results_v2.csv'; rows=read(p)
 train=read('research/vit_v1/training_halting_dataset_vit.csv')
 norm=lambda s:' '.join(re.findall(r'\w+',s.lower()))
 tq={norm(r['original_question']) for r in train}
 questions=(ROOT/'research/vit_v1/questions/evaluation_questions_100.txt').read_text().splitlines()
 m={'source_commit':'a1196476591c796b106a0f4459669d10a16ade4f','source_csv':p,'source_sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),'questions':len(rows),'status':'historical CSV reaggregation; not a fresh retrieval run','training_rows':len(train),'training_questions':len(tq),'labels':dict(collections.Counter(r['halt'] for r in train)),'train_evaluation_overlap':sum(norm(r['question']) in tq for r in rows),'question_file_matches':questions==[r['question'] for r in rows],'evaluation_exact_duplicates':len(rows)-len({norm(r['question']) for r in rows}),'api_cost_conclusion':'not established; zero matched successful historical pilot pairs','human_correctness':None}
 for prefix in ['fixed','learned']:
  m[prefix]={k:statistics.mean(float(r[prefix+'_'+k]) for r in rows) for k in ['mean_attempts','success_rate','mean_wall_seconds','mean_cpu_seconds']}
  vals=sorted(float(r[prefix+'_mean_wall_seconds']) for r in rows)
  m[prefix].update(median_wall_seconds=statistics.median(vals),p95_wall_seconds=vals[94]+.05*(vals[95]-vals[94]))
 m['reductions_percent']={k:100*(m['fixed'][k]-m['learned'][k])/m['fixed'][k] for k in ['mean_attempts','mean_wall_seconds','mean_cpu_seconds']}
 (OUT/'verified_metrics.json').write_text(json.dumps(m,indent=2)+'\n')
 (ROOT/'static/research_metrics.json').write_text(json.dumps(m,indent=2)+'\n')
 (ROOT/'frontend/src/researchMetrics.ts').write_text('export const researchMetrics = '+json.dumps(m)+' as const;\n')
 with (OUT/'question_overlap.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['question_id','in_training','lexical_near_duplicate_id','similarity'])
  for r in rows:
   peers=[(difflib.SequenceMatcher(None,norm(r['question']),norm(s['question'])).ratio(),s['question_id']) for s in rows if s!=r]
   sim,qid=max(peers);w.writerow([r['question_id'],norm(r['question']) in tq,qid,round(sim,3)])
 pilot=read('research/vit_v1/api_cost_pilot_results.csv')
 groups=collections.defaultdict(list)
 for r in pilot: groups[r['question_id']].append(r)
 paired=[v for v in groups.values() if len(v)==2 and all(r['api_status']=='success' for r in v)]
 cost={'questions':len(groups),'method_observations':len(pilot),'successful_observations':sum(r['api_status']=='success' for r in pilot),'missing_usage_observations':sum(r['api_status']=='no_usage_record' for r in pilot),'matched_successful_pairs':len(paired),'cost_reduction_percent':None,'failed_usage_cost':'unknown, not zero','new_live_run':'blocked: no GEMINI_API_KEY in execution environment'}
 (OUT/'historical_cost_audit.json').write_text(json.dumps(cost,indent=2)+'\n')
 with (OUT/'historical_cost_question_level.csv').open('w',newline='') as f:
  fields=['question_id','method','status','api_requests','input_tokens','cached_input_tokens','output_tokens','thinking_tokens','total_reported_tokens','retry_requests','estimated_input_cost_usd','estimated_output_cost_usd','estimated_total_cost_usd','outcome','end_to_end_seconds','human_correct']
  w=csv.DictWriter(f,fields);w.writeheader()
  for r in pilot:
   ok=r['api_status']=='success'
   w.writerow(dict(question_id=r['question_id'],method=r['method'],status=r['api_status'],api_requests=r['gemini_api_calls'] if ok else '',input_tokens=r['prompt_tokens'] if ok else '',output_tokens=r['output_tokens'] if ok else '',thinking_tokens=r['thoughts_tokens'] if ok else '',total_reported_tokens=r['total_tokens'] if ok else '',estimated_input_cost_usd=r['estimated_input_cost_usd'] if ok else '',estimated_output_cost_usd=r['estimated_output_cost_usd'] if ok else '',estimated_total_cost_usd=r['estimated_total_cost_usd'] if ok else '',end_to_end_seconds=r['elapsed_seconds'],outcome='answer_unvalidated' if ok else 'unknown'))
 print(json.dumps(m,indent=2));print(json.dumps(cost))
if __name__=='__main__': main()
