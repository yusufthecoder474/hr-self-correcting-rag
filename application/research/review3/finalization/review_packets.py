"""Prepare blank review packets; attach real frozen-run answers only when available."""
import argparse,csv,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def prepare(output,run=None,answer_run=None):
    dev=ROOT/'research/review3/independent_eval_30/development';questions=list(csv.DictReader((dev/'question_authoring_template.csv').open()));refs={r['question_id']:r for r in map(json.loads,(dev/'reference_answers_candidate.jsonl').read_text().splitlines())}
    answers={}
    if run:
        from freeze_dataset import validate_frozen
        questions=validate_frozen(ROOT);manifest=json.loads((Path(run)/'manifest.json').read_text())
        if manifest['mode']!='frozen' or manifest['status']!='COMPLETED':raise ValueError('Use completed frozen runs only')
        answers={(r['question_id'],r['policy']):r for r in map(json.loads,(Path(run)/'raw_results.jsonl').read_text().splitlines()) if r['repetition']==1}
    if answer_run:
        if not run:raise ValueError('A frozen retrieval run is required with answers')
        from benchmark import sha
        ad=Path(answer_run);conditions=json.loads((ad/'conditions.json').read_text())
        if conditions['retrieval_manifest_sha256']!=sha(Path(run)/'manifest.json'):raise ValueError('Answer/retrieval run mismatch')
        for a in map(json.loads,(ad/'answers.jsonl').read_text().splitlines()):
            key=(a['question_id'],a['method'])
            if key not in answers:raise ValueError('Unexpected answer observation')
            answers[key]=dict(answers[key],answer=a.get('answer'),validator_enabled_outcome=a['outcome'] if a['status']=='success' or 'abstention' in a['status'] else 'API_FAILURE_DO_NOT_SCORE')
    out=Path(output);out.mkdir(parents=True,exist_ok=False);rng=random.Random(9341);mapping=[];packets=[]
    for q in questions:
        policies=['learned','critic','single','budget'];rng.shuffle(policies)
        for label,policy in zip(['A','B','C','D'],policies):
            mapping.append(dict(question_id=q['question_id'],system_label=label,policy=policy))
            a=answers.get((q['question_id'],policy));reference=refs[q['question_id']]
            for reviewer in ['reviewer_slot_1','reviewer_slot_2']:
                packets.append(dict(question_id=q['question_id'],system_label=label,reviewer_slot=reviewer,question=q['question'],answer=a.get('answer') if a and a.get('answer') else '',observation_status=a['validator_enabled_outcome'] if a else 'NOT_RUN_DATASET_NOT_APPROVED',reference_section=q['reference_section'],reference_pdf_page=q['reference_page'],reference_answer=reference.get('reference_answer',reference.get('answer','')),reviewer_name='',correctness='',completeness='',source_support='',citation_accuracy='',appropriate_abstention='',notes=''))
    write_csv(out/'COORDINATOR_ONLY_mapping.csv',mapping,list(mapping[0]))
    for slot in ['reviewer_slot_1','reviewer_slot_2']:write_csv(out/(slot+'.csv'),[r for r in packets if r['reviewer_slot']==slot],list(packets[0]))
    (out/'README.md').write_text('''# Blind review packet — pending genuine evaluation\n\nDo not give COORDINATOR_ONLY_mapping.csv to reviewers. Labels are permuted per question. Slots are unassigned, not actual people. A blank answer marked NOT_RUN is not an abstention and must not be scored. Frozen retrieval-only output may lack generated answers; complete matched answer generation before scoring those rows. References are AI-authored drafts and need independent source validation first.\n\nUse correctness, source support and citation accuracy: 0 incorrect/unsupported, 1 partial, 2 fully correct/supported; completeness: 0 absent, 1 partial, 2 complete. Appropriate abstention: YES/NO/NA. Provide source page and material errors in notes. Two reviewers work independently; preserve original ratings before adjudication. Compute ordinal weighted kappa only on jointly observed genuine scores; report sample size and disagreements. Do not manufacture ratings or reuse developer judgments as independent review.\n''')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--run');p.add_argument('--answers');a=p.parse_args();prepare(a.output,a.run,a.answers)
