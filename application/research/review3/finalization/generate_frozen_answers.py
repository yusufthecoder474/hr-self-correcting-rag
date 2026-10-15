"""Explicit live, sequential completion of an approved frozen retrieval benchmark.
No candidate evaluation or implicit external requests. Local rules are counted separately.
"""
import argparse,csv,hashlib,json,os,random,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
def local_result(answer,outcome,status='success'):
    return dict(answer=answer,outcome=outcome,status=status,api_requests=0,retry_requests=0,input_tokens=0,cached_input_tokens=0,output_tokens=0,thinking_tokens=0,total_reported_tokens=0,estimated_input_cost_usd=0.,estimated_output_cost_usd=0.,estimated_total_cost_usd=0.,usage_known=True,cost_basis='no external request made')
def route_answer(question,context,trajectory,critic,resolution,method='review3',rules=True,generate_fn=None,question_id=None):
    from review3_safety import gate,suspicious
    from benchmark import source_rule
    from gemini_answer import extract_relevant_context
    if suspicious(question) or suspicious(context):return local_result('The evidence cannot be used safely.','abstained','safety_abstention')
    if resolution['status'] in ('unknown','ambiguous'):return local_result('Please clarify the abbreviation using the policy terminology.','abstained','acronym_abstention')
    if resolution.get('lookup_only'):
        e=resolution['entries'][0]
        return local_result(f"{e['aliases'][0]} means {e['full_form']} in this document. Policy conditions require the corresponding policy section.",'local_verified_definition')
    q=resolution['query'];state=gate(q,context,trajectory,critic)
    supported=source_rule(q,context) if rules and state!='UNSAFE_INPUT' else None
    if supported:return local_result(supported,'local_verified_policy')
    if state!='SUFFICIENT':return local_result('The retrieved policy evidence is insufficient.','abstained','evidence_abstention')
    focused=extract_relevant_context(q,context);score,decision=critic(q,focused)
    if not focused.strip() or suspicious(focused) or score<.75 or decision!='SUFFICIENT':return local_result('The selected policy evidence is insufficient.','abstained','focused_evidence_abstention')
    if generate_fn is None:
        from review3_generation import generate as generate_fn
    return generate_fn(q,focused,method=method,question_id=question_id)
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);p.add_argument('--live',action='store_true');p.add_argument('--limit',type=int,default=5);p.add_argument('--without-source-rules',action='store_true');a=p.parse_args()
    from freeze_dataset import validate_frozen
    questions=validate_frozen(ROOT)
    if not a.live or not os.getenv('GEMINI_API_KEY'):raise ValueError('Explicit --live and locally configured GEMINI_API_KEY required')
    run=Path(a.run);m=json.loads((run/'manifest.json').read_text())
    if m['mode']!='frozen' or m['status']!='COMPLETED':raise ValueError('Completed frozen retrieval run required')
    from benchmark import assets,code_hashes,sha
    if m['assets_before']!=assets() or m['code_sha256']!=code_hashes():raise ValueError('Retrieval run assets/code differ')
    if a.limit<1:raise ValueError('Positive pilot limit required')
    rows=[r for r in map(json.loads,(run/'raw_results.jsonl').read_text().splitlines()) if r['repetition']==1]
    allowed={q['question_id']:q['question'] for q in questions[:a.limit]};rows=[r for r in rows if r['question_id'] in allowed]
    if len(rows)!=4*len(allowed) or any(r['question']!=allowed[r['question_id']] for r in rows):raise ValueError('Missing/mismatched frozen observations')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    from review3_generation import PRICING,SETTINGS,SYSTEM
    from local_critic import evaluate_retrieval
    from acronym_resolver import resolve
    from research.review3.cost_analysis import compare
    conditions={'stage':'frozen_answer_completion','retrieval_manifest_sha256':sha(run/'manifest.json'),'retrieval_raw_sha256':sha(run/'raw_results.jsonl'),'freeze_sha256':sha(ROOT/'research/review3/independent_eval_30/frozen/freeze_manifest.json'),'pricing':PRICING,'settings':SETTINGS,'prompt_sha256':hashlib.sha256(SYSTEM.encode()).hexdigest(),'source_rules':not a.without_source_rules,'max_questions':a.limit,'human_validation':'PENDING','timing':'generation/authorization replay; retrieval time copied separately, not a live end-to-end rerun'}
    (out/'conditions.json').write_text(json.dumps(conditions,indent=2));results=[];rng=random.Random(42)
    for qid in allowed:
        ordered=[r for r in rows if r['question_id']==qid];rng.shuffle(ordered)
        for r in ordered:
            t=time.perf_counter();cpu=time.process_time();completion=route_answer(r['question'],r['context'],r['trajectory'],evaluate_retrieval,resolve(r['question']),method=r['policy'],rules=not a.without_source_rules,question_id=qid)
            obs=dict(question_id=qid,method=r['policy'],human_correct=None,retrieval_seconds=r['retrieval_seconds'],completion_seconds=time.perf_counter()-t,completion_cpu_seconds=time.process_time()-cpu,end_to_end_seconds=None,**completion)
            results.append(obs)
            with (out/'answers.jsonl').open('a') as f:f.write(json.dumps(obs)+'\n')
            if obs['status'] in ('api_error','empty_response','missing_credentials'):break
        if results[-1]['status'] in ('api_error','empty_response','missing_credentials'):break
    fields=sorted({k for r in results for k in r if k!='answer'})
    with (out/'question_costs.csv').open('w',newline='') as f:w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(results)
    (out/'summary.json').write_text(json.dumps({policy+'_vs_learned':compare(results,policy,'learned') for policy in ['single','critic','budget']},indent=2))
if __name__=='__main__':main()
