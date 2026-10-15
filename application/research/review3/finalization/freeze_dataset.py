"""Fail-closed freeze: actual named review is required, never auto-approved."""
import csv,json,hashlib,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def approve_and_freeze(root=ROOT):
    dev=root/'research/review3/independent_eval_30/development';dest=root/'research/review3/independent_eval_30/frozen'
    summary=json.loads((dev/'overlap_screening_summary.json').read_text());candidate=dev/'question_authoring_template.csv'
    if summary['semantic_status']!='COMPLETE' or summary['dataset_sha256']!=sha(candidate):raise ValueError('Complete current semantic screening required')
    rows=list(csv.DictReader(candidate.open(encoding='utf-8-sig')))
    if len(rows)!=30 or len({r['question_id'] for r in rows})!=30:raise ValueError('Need 30 unique candidates')
    from collections import Counter
    if sorted(Counter(r['category'] for r in rows).values())!=[6]*5:raise ValueError('Need six per category')
    approvals=list(csv.DictReader((dev/'reviewer_approval.csv').open(encoding='utf-8-sig')))
    approved={r['question_id']:r for r in approvals}
    if len(approvals)!=30 or len(approved)!=30:raise ValueError('Need one approval record per candidate')
    for r in rows:
        a=approved.get(r['question_id'],{})
        if any(not a.get(k,'').strip() for k in ['reviewer_name','reviewed_utc','source_support_notes','overlap_resolution']):raise ValueError('Named reviewer, date, support and overlap resolution required for '+r['question_id'])
        if a.get('reference_sha256')!=sha(dev/'reference_answers_candidate.jsonl') or a.get('screening_sha256')!=sha(dev/'overlap_screening_detailed.csv'):raise ValueError('Source references or screening changed after review')
        if a.get('approved')!='YES' or a.get('dataset_sha256')!=sha(candidate) or a.get('independent_of_authoring')!='YES':raise ValueError('Content-bound independent approval required')
    if (dest/'freeze_manifest.json').exists():raise ValueError('Already frozen; do not overwrite')
    from benchmark import assets,code_hashes
    dest.mkdir(parents=True,exist_ok=True)
    for name in ['question_authoring_template.csv','reference_answers_candidate.jsonl','reviewer_approval.csv','overlap_screening_detailed.csv']:
        shutil.copy2(dev/name,dest/name)
    manifest={'status':'FROZEN_BY_RECORDED_REVIEW','files':{p.name:sha(p) for p in dest.iterdir() if p.is_file() and p.suffix in ['.csv','.jsonl']},'assets':assets(),'code':code_hashes(),'budget':3,'seed':42,'generation':'RETRIEVAL_ONLY_UNLESS_EXPLICIT_COMPLETION','answer_code':{n:sha(root/n) for n in ['review3_generation.py','research/review3/pricing.json','research/review3/finalization/generate_frozen_answers.py']}}
    with (dest/'freeze_manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
    return manifest

def validate_frozen(root=ROOT):
    from benchmark import assets,code_hashes
    d=root/'research/review3/independent_eval_30/frozen';m=json.loads((d/'freeze_manifest.json').read_text())
    if m['assets']!=assets() or m['code']!=code_hashes():raise ValueError('Frozen assets or code changed')
    for name,digest in m.get('answer_code',{}).items():
        if sha(root/name)!=digest:raise ValueError('Frozen answer code changed: '+name)
    for name,digest in m['files'].items():
        if sha(d/name)!=digest:raise ValueError('Frozen file changed: '+name)
    return list(csv.DictReader((d/'question_authoring_template.csv').open()))
if __name__=='__main__':print(json.dumps(approve_and_freeze(),indent=2))
