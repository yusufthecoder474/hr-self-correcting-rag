"""Canonical Review 3 retrieval loop; adapters reuse established retrieval components.
No model retraining or replacement. Delta follows the recorded training definition.
"""
def feature_vector(attempt,score,prior_best):
    return [float(attempt),float(score),max(float(prior_best),float(score)),0.0 if attempt==1 else float(score)-float(prior_best)]

def run(question,backend=None,policy='learned',max_attempts=3):
    if backend is None:
        import local_self_correcting_rag as backend
    if policy not in {'learned','critic','budget','single'}:raise ValueError('Unknown policy')
    if max_attempts not in [1,2,3]:raise ValueError('Attempt budget must be 1 to 3')
    current=question;best=0;preserved={};trajectory=[];context='';previous_chunks=set()
    for attempt in range(1,(1 if policy=='single' else max_attempts)+1):
        chunks,distances,_=backend.retrieve_chunks(current,backend.TOP_K)
        current_chunks=set(chunks)
        overlap=len(current_chunks & previous_chunks)/len(current_chunks | previous_chunks) if previous_chunks and current_chunks else 0.0
        previous_chunks=current_chunks
        for score,chunk in backend.build_candidates(current,chunks,distances):preserved[chunk]=max(score,preserved.get(chunk,float('-inf')))
        context=backend.select_final_context(current,[(s,c) for c,s in preserved.items()])
        score,decision=backend.evaluate_retrieval(current,context)
        features=feature_vector(attempt,score,best);best=features[2]
        if policy=='learned':action,prob=backend._halting_policy.predict(attempt=features[0],score=features[1],best_score=features[2],score_delta=features[3])
        else:action,prob=('STOP' if policy=='single' or policy=='critic' and decision=='SUFFICIENT' else 'CONTINUE'),None
        row=dict(attempt=attempt,query=current,decision=decision,chunk_overlap=overlap,score=score,best_score=best,score_delta=features[3],critic_decision=decision,halting_decision=action,stop_probability=prob,runtime_action=action)
        trajectory.append(row)
        if action=='STOP' or attempt==max_attempts:break
        new=backend.rewrite_query(current)
        if new==current:row['runtime_action']='STOP_NO_REWRITE';break
        current=new
    return context,trajectory
