"""Screening heuristics flag risk. They never certify independence."""
from pathlib import Path
import csv,json,re,hashlib
from difflib import SequenceMatcher
import numpy as np
ROOT=Path(__file__).resolve().parents[3];DEV=ROOT/'research/review3/independent_eval_30/development'
def norm(s):return ' '.join(re.findall(r'[a-z0-9]+',s.lower()))
def topic(s):
    s=s.lower()
    groups={'sabbatical':['sabbatical'],'medical':['medical','sick'], 'casual':['casual',' cl ','c.l.'],'earned':['earned','encash'], 'vacation':['vacation'], 'resignation':['resign','notice period','reliev','termination','retire'], 'compensatory':['compensatory'], 'on_duty':['on duty','other duty'],'long_leave':['long leave','loss of pay','lllp'],'leave_procedure':['extension','leave sanction','leave rules','leave application'],'maternity':['maternity','delivery'],'service_certificate':['service certificate','no objection','higher studies'],'stoppage':['lay-off','stoppage','closure'],'holidays':['holiday']}
    return {k for k,v in groups.items() if any(t in s for t in v)}
def references():
    found={}
    for p in ROOT.rglob('*'):
        if any(x in p.relative_to(ROOT).parts for x in ['node_modules','.git','.venv','finalization','independent_eval_30']):continue
        lines=[]
        try:
            if p.suffix=='.csv':
                for r in csv.DictReader(p.open(encoding='utf-8-sig')):
                    for k in ['question','original_question']:
                        if r.get(k):lines.append(r[k])
            elif p.suffix=='.txt' and 'question' in p.name.lower():lines=p.read_text(encoding='utf-8-sig').splitlines()
        except (UnicodeError,OSError):continue
        for q in lines:
            q=q.strip()
            if len(q)<8 or q.startswith('#'):continue
            found.setdefault(norm(q),{'question':q,'sources':[]})['sources'].append(str(p.relative_to(ROOT)))
    for q in ['What are the maternity leave eligibility conditions?','Explain CL carry forward rules.','What does CL stand for?','What is the policy for employee moon travel?']:
        found.setdefault(norm(q),{'question':q,'sources':['explicit_debugging_question']})
    return list(found.values())
def run(encoder=None):
    rows=list(csv.DictReader((DEV/'question_authoring_template.csv').open(encoding='utf-8-sig')));ref=references();qs=[r['question'] for r in rows];rq=[r['question'] for r in ref]
    status='COMPLETE';error=None
    try:
        if encoder is None:
            from sentence_transformers import SentenceTransformer
            encoder=SentenceTransformer('all-MiniLM-L6-v2')
        emb=np.asarray(encoder.encode(qs+rq,normalize_embeddings=True));scores=emb[:len(qs)]@emb.T
    except Exception as e:status='BLOCKED';error=type(e).__name__;scores=None
    details=[];families=[];edges=[]
    for i,row in enumerate(rows):
        lexical=[SequenceMatcher(None,norm(qs[i]),norm(q)).ratio() for q in rq]
        j=int(np.argmax(lexical));semantic_j=int(np.argmax(scores[i,len(qs):])) if scores is not None else None
        peers=[k for k in range(len(qs)) if k!=i];near=max(peers,key=lambda k:SequenceMatcher(None,norm(qs[i]),norm(qs[k])).ratio())
        intr=max((float(scores[i,k]),k) for k in peers) if scores is not None else (None,None)
        exact=any(norm(qs[i])==norm(q) for q in rq)
        fam=topic(qs[i]);family_matches=[r['question'] for r in ref if fam & topic(r['question'])]
        sem=float(scores[i,len(qs)+semantic_j]) if semantic_j is not None else None
        risk='HIGH' if exact or lexical[j]>=.82 or sem is not None and sem>=.85 else 'REVIEW'
        peerlex=SequenceMatcher(None,norm(qs[i]),norm(qs[near])).ratio()
        if peerlex>=.82:edges.append((row['question_id'],rows[near]['question_id'],'lexical'))
        if intr[0] is not None and intr[0]>=.85:edges.append((row['question_id'],rows[intr[1]]['question_id'],'semantic'))
        details.append(dict(question_id=row['question_id'],question=qs[i],exact_reference_match=exact,lexical_max=round(lexical[j],4),lexical_neighbor=rq[j],semantic_max=round(sem,4) if sem is not None else '',semantic_neighbor=rq[semantic_j] if semantic_j is not None else '',candidate_lexical_max=round(peerlex,4),candidate_neighbor=rows[near]['question_id'],candidate_semantic_max=round(intr[0],4) if intr[0] is not None else '',family_overlap=bool(family_matches),family_example=family_matches[0] if family_matches else '',risk=risk,semantic_status=status,human_resolution='PENDING'))
        families.append(dict(question_id=row['question_id'],semantic_family_id=row['semantic_family_id'],broad_topics=';'.join(sorted(fam)),reference_family_overlap=bool(family_matches),independence_status='NOT_ESTABLISHED'))
        row['overlap_screened']='AUTOMATED_COMPLETE_REVIEW_PENDING' if status=='COMPLETE' else 'LEXICAL_ONLY_SEMANTIC_BLOCKED'
    for name,records in [('overlap_screening_detailed.csv',details),('question_family_manifest.csv',families),('question_authoring_template.csv',rows)]:
        with (DEV/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=records[0]);w.writeheader();w.writerows(records)
    # Connected components in the candidate paraphrase graph.
    parent={r['question_id']:r['question_id'] for r in rows}
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    for a,b,_ in edges:parent[find(a)]=find(b)
    clusters={}
    for x in parent:clusters.setdefault(find(x),[]).append(x)
    summary=dict(candidates=len(rows),reference_unique_questions=len(ref),semantic_status=status,semantic_error_type=error,embedding_model='all-MiniLM-L6-v2',lexical_high_threshold=.82,semantic_high_threshold=.85,semantic_review_threshold=.72,high_risk=sum(r['risk']=='HIGH' for r in details),family_overlap=sum(r['family_overlap'] for r in details),reviewer_approved=0,independent_questions_established=0,dataset_sha256=hashlib.sha256((DEV/'question_authoring_template.csv').read_bytes()).hexdigest(),candidate_clusters=[v for v in clusters.values() if len(v)>1],claim='Thresholds are screening heuristics; family overlap can remain despite low similarity.')
    (DEV/'overlap_screening_summary.json').write_text(json.dumps(summary,indent=2));(DEV/'screening_reference_inventory.json').write_text(json.dumps(ref,indent=2))
    print(json.dumps(summary,indent=2));return summary
if __name__=='__main__':run()
