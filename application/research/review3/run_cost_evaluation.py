"""Sequential, matched pilot. New outputs only; --live is required to incur API usage."""
import sys,os,json,csv,time,argparse,hashlib,contextlib,io,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from review3_generation import generate,PRICING,SETTINGS,SYSTEM
from review3_safety import gate
from acronym_resolver import resolve
from review3_pipeline import run as review3_run
from research.review3.cost_analysis import compare
METHODS=['standard','review2','review2_acronym','review2_gate','review3_delta','review3_critic','review3_budget','review3']
def main():
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--limit',type=int,default=5);p.add_argument('--questions',default=str(Path(__file__).with_name('cost_questions.json')));p.add_argument('--output',required=True);args=p.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    questions=json.loads(Path(args.questions).read_text())[:args.limit]
    config={'pricing':PRICING,'settings':SETTINGS,'prompt_sha256':hashlib.sha256(SYSTEM.encode()).hexdigest(),'question_file_sha256':hashlib.sha256(Path(args.questions).read_bytes()).hexdigest(),'corpus_sha256':hashlib.sha256((ROOT/'documents/vit/VIT_HR_Conditions_of_Service.pdf').read_bytes()).hexdigest(),'methods':METHODS,'live':args.live,'questions':len(questions),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() if (ROOT/'.git').exists() else 'authoritative-upload-no-git-history','code_status':'working tree; see delivered patch','retry_policy':'one request; SDK retries disabled','human_validation':'pending'}
    (out/'conditions.json').write_text(json.dumps(config,indent=2))
    if not args.live or not os.getenv('GEMINI_API_KEY'):
        (out/'blocked.json').write_text(json.dumps({'status':'not_run','reason':'--live and locally configured GEMINI_API_KEY required','successful_pairs':0,'cost_conclusion':'inconclusive'},indent=2));print('Not run: no live request made.');return
    try:
        import local_self_correcting_rag as rag
        from local_critic import evaluate_retrieval
    except Exception as e:
        (out/'blocked.json').write_text(json.dumps({'status':'not_run','reason':type(e).__name__,'stage':'retrieval_initialization'}));return
    observations=[]
    for i,q in enumerate(questions):
        methods=METHODS if i%2==0 else list(reversed(METHODS))
        for method in methods:
            start=time.perf_counter();r={'question_id':q['id'],'method':method,'status':'retrieval_error','outcome':'abstained','api_requests':0,'retry_requests':0,'estimated_total_cost_usd':None,'human_correct':None}
            try:
                resolution=resolve(q['question']) if method in ['review2_acronym','review3'] else {'query':q['question'],'status':'unchanged'}
                if resolution['status'] in ['unknown','ambiguous']:
                    r['status']='acronym_abstention';context='';trajectory=[]
                elif method=='review3' and resolution.get('lookup_only'):
                    r['status']='local_definition';context='';trajectory=[]
                else:
                    # Redirect legacy debug text in this sequential research process only.
                    with contextlib.redirect_stdout(io.StringIO()):
                        if method=='standard':
                            chunks,_,_=rag.retrieve_chunks(resolution['query'],3);context='\n\n'.join(chunks);trajectory=[]
                        elif method.startswith('review3'):
                            policy={'review3_critic':'critic','review3_budget':'budget'}.get(method,'learned')
                            context,trajectory=review3_run(resolution['query'],backend=rag,policy=policy)
                        else:context,trajectory=rag.local_self_correcting_rag(resolution['query'])
                    r['status']='retrieved'
                r['retrieval_seconds']=time.perf_counter()-start;r['retrieval_attempts']=len(trajectory) if method!='standard' else 1
                if method=='review3':
                    from research.review3.finalization.generate_frozen_answers import route_answer
                    r.update(route_answer(q['question'],context,trajectory,evaluate_retrieval,resolution,method=method,question_id=q['id']))
                else:
                    allowed=bool(context)
                    if method in ['review2_gate','review3']:allowed=allowed and gate(resolution['query'],context,trajectory,evaluate_retrieval)=='SUFFICIENT'
                    if allowed:
                        from gemini_answer import extract_relevant_context
                        context=extract_relevant_context(q['question'],context)
                        if method in ['review2_gate','review3'] and evaluate_retrieval(q['question'],context)[1]!='SUFFICIENT':
                            r['status']='focused_evidence_abstention'
                        else:r.update(generate(q['question'],context,question_id=q['id'],method=method))
                    elif r['status']=='retrieved':r['status']='evidence_abstention'
            except Exception as e:r['error_type']=type(e).__name__
            r['end_to_end_seconds']=time.perf_counter()-start;observations.append(r)
            with (out/'question_results.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
            if r['status']=='api_error':break
        if observations[-1]['status']=='api_error':break # do not expand an unstable pilot
    fields=sorted({k for r in observations for k in r if k!='answer'})
    with (out/'question_costs.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(observations)
    result={f'{a}_vs_{b}':compare(observations,a,b) for a,b in [('standard','review3'),('review2','review3'),('review2','review2_acronym'),('review2','review2_gate'),('review2','review3_delta'),('review3_budget','review3_delta'),('review3_critic','review3_delta')]}
    (out/'summary.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
