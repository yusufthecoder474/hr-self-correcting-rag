"""Paired costs; never compare unknown/failed use to successful zero-cost use."""
import statistics,random

def compare(rows,baseline,improved):
    index={}
    for r in rows:
        key=(r['question_id'],r['method'])
        if key in index:raise ValueError('Duplicate question-method observation; use distinct run IDs.')
        index[key]=r
    ids=sorted({r['question_id'] for r in rows})
    def valid(r):return r and r['status']=='success' and r['outcome'] in ('answer','local_verified_policy','local_verified_definition') and r.get('estimated_total_cost_usd') is not None
    pairs=[(index.get((i,baseline)),index.get((i,improved))) for i in ids]
    matched=[(a,b) for a,b in pairs if valid(a) and valid(b)]
    result={'questions':len(ids),'matched_successful_pairs':len(matched),'cost_reduction_percent':None,'paired_difference_mean_usd':None,'paired_difference_95pct_bootstrap':None,'methods':{}}
    for method in [baseline,improved]:
        obs=[r for r in rows if r['method']==method];good=[r for r in obs if valid(r)]
        joint=[a if method==baseline else b for a,b in matched]
        costs=[r['estimated_total_cost_usd'] for r in joint]
        result['methods'][method]={'observations':len(obs),'successful_known_cost':len(good),'failure_rate':sum(r['status'] in ['api_error','retrieval_error','empty_response'] for r in obs)/len(obs) if obs else None,'fallback_rate':sum(r['outcome']=='local_fallback' for r in obs)/len(obs) if obs else None,'abstention_rate':sum(r['outcome']=='abstained' for r in obs)/len(obs) if obs else None,'matched_total_cost_usd':sum(costs) if costs else None,'matched_average_cost_usd':statistics.mean(costs) if costs else None,'matched_median_cost_usd':statistics.median(costs) if costs else None}
        for field in ['input_tokens','output_tokens','api_requests','end_to_end_seconds','retrieval_seconds']:
            v=[r[field] for r in joint if r.get(field) is not None]
            result['methods'][method]['matched_average_'+field]=statistics.mean(v) if len(v)==len(joint) and v else None
    if matched:
        a=sum(x['estimated_total_cost_usd'] for x,y in matched);b=sum(y['estimated_total_cost_usd'] for x,y in matched)
        result['cost_reduction_percent']=100*(a-b)/a if a>0 else None
        delta=[y['estimated_total_cost_usd']-x['estimated_total_cost_usd'] for x,y in matched]
        result['paired_difference_mean_usd']=statistics.mean(delta)
        if len(delta)>=10:
            rng=random.Random(42);boot=sorted(statistics.mean(rng.choices(delta,k=len(delta))) for _ in range(2000));result['paired_difference_95pct_bootstrap']=[boot[49],boot[1949]]
    correct=[(a,b) for a,b in matched if a.get('human_correct') is True and b.get('human_correct') is True]
    result['both_human_correct_pairs']=len(correct)
    result['cost_on_both_correct']={baseline:sum(a['estimated_total_cost_usd'] for a,b in correct),improved:sum(b['estimated_total_cost_usd'] for a,b in correct)} if correct else None
    return result
