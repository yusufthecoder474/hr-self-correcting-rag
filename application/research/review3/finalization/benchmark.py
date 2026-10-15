"""Offline four-policy retrieval benchmark. Never trains or tunes the application.
Development uses known questions only. Final mode requires a content-bound freeze.
"""
import argparse,csv,hashlib,json,os,platform,random,shutil,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
POLICIES=('learned','critic','single','budget')
DEV_QUESTIONS=[{'question_id':'DEV01','question':'What are the maternity leave eligibility conditions?'},{'question_id':'DEV02','question':'Explain CL carry forward rules.'},{'question_id':'DEV03','question':'What are the casual leave rules?'},{'question_id':'DEV04','question':'What is the policy for employee moon travel?'}]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def assets():
    paths=[ROOT/'research/vit_v1/halting_policy_vit_v3.pkl',ROOT/'documents/vit/VIT_HR_Conditions_of_Service.pdf']+sorted((ROOT/'chroma_db').rglob('*'))
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()}
def code_hashes():
    names=['review3_pipeline.py','local_self_correcting_rag.py','local_critic.py','local_query_rewriter.py','halting_policy.py','review3_safety.py','acronym_resolver.py','gemini_answer.py','research/review3/finalization/benchmark.py']
    return {n:sha(ROOT/n) for n in names if (ROOT/n).exists()}
def loop(question,backend,policy,max_attempts=3):
    from review3_pipeline import feature_vector
    if policy not in POLICIES:raise ValueError('Unknown policy')
    if max_attempts not in (1,2,3):raise ValueError('Invalid budget')
    current=question;best=0.;preserved={};trajectory=[];previous=set();context=''
    for attempt in range(1,(1 if policy=='single' else max_attempts)+1):
        chunks,distances,_=backend.retrieve_chunks(current,backend.TOP_K)
        chunkset=set(chunks);union=chunkset|previous
        overlap=len(chunkset&previous)/len(union) if previous and union else 0.
        previous=chunkset
        for score,chunk in backend.build_candidates(current,chunks,distances):preserved[chunk]=max(score,preserved.get(chunk,float('-inf')))
        context=backend.select_final_context(current,[(s,c) for c,s in preserved.items()])
        score,decision=backend.evaluate_retrieval(current,context)
        f=feature_vector(attempt,score,best);best=f[2]
        if policy=='learned':action,prob=backend._halting_policy.predict(attempt=f[0],score=f[1],best_score=f[2],score_delta=f[3])
        else:action,prob=('STOP' if policy=='single' or policy=='critic' and decision=='SUFFICIENT' else 'CONTINUE'),None
        new=backend.rewrite_query(current)
        reason=('single_retrieval' if policy=='single' else 'learned_stop' if action=='STOP' and policy=='learned' else 'critic_sufficient' if action=='STOP' else 'budget_exhausted' if attempt==max_attempts else '')
        # A true budget control always makes its prescribed calls. Learned/critic
        # retain the application's no-rewrite guard. Repeated queries are reported.
        if not reason and new==current and policy!='budget':reason='no_rewrite'
        trajectory.append(dict(attempt=attempt,query=current,score=score,best_score=best,score_delta=f[3],chunk_overlap=overlap,critic_decision=decision,halting_decision=action,stop_probability=prob,stop_reason=reason,rewrite_exhausted=new==current))
        if reason:break
        current=new
    return context,trajectory

def source_rule(q,context):
    from gemini_answer import extract_relevant_context
    from review3_safety import verified_maternity_eligibility,verified_cl_carry_forward
    focused=extract_relevant_context(q,context)
    return verified_cl_carry_forward(q,focused) or verified_maternity_eligibility(q,focused)

def run(mode,out,repeats=3):
    from acronym_resolver import resolve
    from review3_safety import gate
    if repeats<1:raise ValueError('repeats must be positive')
    if mode=='frozen':
        from freeze_dataset import validate_frozen
        questions=validate_frozen(ROOT)
    else:questions=DEV_QUESTIONS
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    manifest={'mode':mode,'question_count':len(questions),'repeats':repeats,'seed':42,'policies':POLICIES,'max_attempts':3,'api_generation':'DISABLED_RETRIEVAL_ONLY','human_validation':'NOT_PERFORMED','platform':platform.platform(),'python':sys.version,'assets_before':assets(),'code_sha256':code_hashes(),'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    rows=[];oldcwd=Path.cwd()
    try:
        # Chroma may update its store on open. Run a disposable byte-copy.
        with tempfile.TemporaryDirectory(prefix='hr-rag-eval-') as tmp:
            runtime=Path(tmp);shutil.copytree(ROOT/'chroma_db',runtime/'chroma_db')
            model=Path('research/vit_v1/halting_policy_vit_v3.pkl');(runtime/model).parent.mkdir(parents=True);shutil.copy2(ROOT/model,runtime/model)
            os.chdir(runtime)
            start=time.perf_counter();import local_self_correcting_rag as backend
            manifest['load_seconds']=time.perf_counter()-start
            backend.retrieve_chunks('What are the casual leave rules?',backend.TOP_K)
            rng=random.Random(42)
            with (out/'raw_results.jsonl').open('w',encoding='utf-8') as sink:
                for rep in range(repeats):
                    order=list(questions);rng.shuffle(order)
                    for q in order:
                        policies=list(POLICIES);rng.shuffle(policies)
                        for policy in policies:
                            r=dict(question_id=q['question_id'],question=q['question'],policy=policy,repetition=rep+1,api_requests=0,api_cost=None,human_correct=None)
                            t=time.perf_counter();cpu=time.process_time()
                            try:
                                resolution=resolve(q['question']);query=resolution['query']
                                tloop=time.perf_counter();context,traj=loop(query,backend,policy);r['retrieval_seconds']=time.perf_counter()-tloop
                                status=gate(query,context,traj,backend.evaluate_retrieval)
                                answer=source_rule(query,context) if status!='UNSAFE_INPUT' else None
                                r.update(status='ok',attempts=len(traj),critic_success=traj[-1]['critic_decision']=='SUFFICIENT',evidence_status=status,validator_enabled_outcome='local_verified_policy' if answer else 'eligible_generation_not_run' if status=='SUFFICIENT' else 'abstained',validator_disabled_outcome='eligible_generation_not_run' if status=='SUFFICIENT' else 'abstained',answer=answer,context=context,trajectory=traj)
                            except Exception as e:r.update(status='error',error_type=type(e).__name__)
                            r.update(end_to_end_seconds=time.perf_counter()-t,cpu_seconds=time.process_time()-cpu)
                            rows.append(r);sink.write(json.dumps(r)+'\n');sink.flush()
        manifest['status']='COMPLETED' if all(r['status']=='ok' for r in rows) else 'PARTIAL_FAILURE'
    except Exception as e:
        manifest.update(status='BLOCKED',error_type=type(e).__name__,error_message=str(e)[:500]);raise
    finally:
        os.chdir(oldcwd);manifest['assets_after']=assets();manifest['assets_unchanged']=manifest['assets_before']==manifest['assets_after'];manifest['completed_observations']=len(rows)
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
        if rows:
            fields=['question_id','policy','repetition','status','attempts','critic_success','evidence_status','validator_enabled_outcome','validator_disabled_outcome','api_requests','api_cost','human_correct','retrieval_seconds','end_to_end_seconds','cpu_seconds']
            with (out/'question_level.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
            summary=[]
            import statistics
            for policy in POLICIES:
                rr=[r for r in rows if r['policy']==policy and r['status']=='ok']
                summary.append(dict(policy=policy,unique_questions=len({r['question_id'] for r in rr}),observations=len(rr),mean_attempts=statistics.mean(r['attempts'] for r in rr) if rr else None,critic_success_rate=statistics.mean(r['critic_success'] for r in rr) if rr else None,mean_retrieval_seconds=statistics.mean(r['retrieval_seconds'] for r in rr) if rr else None,mean_end_to_end_seconds=statistics.mean(r['end_to_end_seconds'] for r in rr) if rr else None,source_rule_answers=sum(bool(r.get('answer')) for r in rr),api_requests=0,answer_accuracy=None))
            (out/'summary.json').write_text(json.dumps(summary,indent=2))
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['development','frozen'],default='development');p.add_argument('--output',required=True);p.add_argument('--repeats',type=int,default=3);a=p.parse_args();print(json.dumps(run(a.mode,Path(a.output).resolve(),a.repeats),indent=2))
