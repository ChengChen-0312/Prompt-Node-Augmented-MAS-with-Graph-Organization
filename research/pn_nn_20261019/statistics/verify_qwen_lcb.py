#!/usr/bin/env python3
"""Verify saved LCB labels and request-level token arithmetic; no model or grader."""
from pathlib import Path
import argparse, csv, hashlib, json, math
import numpy as np

ROOT=Path(__file__).resolve().parent.parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);args=ap.parse_args()
    d=ROOT/'records/qwen_lcb231'
    meta=json.loads((d/'completed_summary.json').read_text())
    rows=list(csv.DictReader((d/'paired_results.csv').open(encoding='utf-8-sig')))
    usage=list(csv.DictReader((d/'request_resources.csv').open(encoding='utf-8-sig')))
    checks={}; counts={k:sum(r[k]=='PASS' for r in rows) for k in ['shared_initial_strict','a1_strict','plan_strict']}
    checks['231_unique_tasks']=len(rows)==231 and len({r['question_id'] for r in rows})==231
    checks['693_labels_known']=all(r[k] in ['PASS','FAIL'] for r in rows for k in counts)
    checks['strict_totals']=counts=={'shared_initial_strict':141,'a1_strict':149,'plan_strict':169}
    pair={'pn_only':0,'independent_only':0,'both':0,'neither':0}
    delta=[]
    for r in rows:
        a=r['a1_strict']=='PASS';p=r['plan_strict']=='PASS'
        pair['both' if a and p else 'pn_only' if p else 'independent_only' if a else 'neither']+=1
        delta.append(int(p)-int(a))
    checks['paired_cells']=pair=={'pn_only':21,'independent_only':1,'both':148,'neither':61}
    n=pair['pn_only']+pair['independent_only'];m=min(pair['pn_only'],pair['independent_only'])
    pvalue=min(1.0,2*sum(math.comb(n,i) for i in range(m+1))/2**n)
    checks['exact_mcnemar']=math.isclose(pvalue,meta['lcb']['mcnemar_p'],rel_tol=1e-12)
    rng=np.random.default_rng(meta['paired_recalculation']['seed'])
    values=np.asarray(delta);draws=rng.choice(values,size=(100000,231),replace=True).mean(axis=1)*100
    ci=np.percentile(draws,[2.5,97.5]).tolist()
    checks['saved_interval']=np.allclose(ci,meta['paired_recalculation']['percentile95_pp'],atol=1e-12)
    archive_ids={s.strip() for s in (ROOT/'cohorts/LCB231_ids.txt').read_text().splitlines() if s.strip()}
    checks['same_231_ids']=archive_ids=={r['question_id'] for r in rows}
    checks['1101_unique_lcb_requests']=len(usage)==1101 and len({r['candidate_id'] for r in usage})==1101 and all(r['dataset']=='lcb' for r in usage)
    sums={}
    for arm,expected_name in [('initial','initial'),('a1','a1_extra'),('plan','plan_extra')]:
        selected=[r for r in usage if r['arm']==arm]
        total={'requests':len(selected),'prompt_tokens':sum(int(r['prompt_tokens']) for r in selected),'completion_tokens':sum(int(r['completion_tokens']) for r in selected),'seconds':round(sum(float(r['total_seconds']) for r in selected),1)}
        sums[expected_name]=total
        checks['usage_'+expected_name]=total==meta['lcb']['usage'][expected_name]
    for name,parts in [('actual',['initial','a1_extra','plan_extra']),('a1_attributed',['initial','a1_extra']),('plan_attributed',['initial','plan_extra'])]:
        total={k:round(sum(sums[p][k] for p in parts),1) if k=='seconds' else sum(sums[p][k] for p in parts) for k in sums['initial']}
        sums[name]=total;checks['usage_'+name]=total==meta['lcb']['usage'][name]
    checks['no_development_rows']=all(r['dataset']=='lcb' for r in rows)
    checks['shared_prefix_counted_once']=sums['actual']['requests']==1101 and sums['a1_attributed']['requests']==sums['plan_attributed']['requests']==897
    result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'strict_counts':counts,'pair':pair,'mcnemar_p':pvalue,'bootstrap95_pp':ci,'usage':sums,'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [d/'completed_summary.json',d/'paired_results.csv',d/'request_resources.csv']},'new_model_calls':0,'candidate_executions':0,'rescoring':0,'scope':'Saved labels, completed-request usage and accounting arithmetic only; final-test labels are not independently regenerated.'}
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n';print(text)
    if args.output:
        if args.output.exists():raise SystemExit('Output exists; choose a fresh file.')
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    raise SystemExit(0 if all(checks.values()) else 1)
if __name__=='__main__':main()
