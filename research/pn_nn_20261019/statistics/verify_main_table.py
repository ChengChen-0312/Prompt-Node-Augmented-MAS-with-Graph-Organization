#!/usr/bin/env python3
"""Build the shared-start table from saved outcomes; never run candidate code."""
from pathlib import Path
import csv, hashlib, json

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent
rows = list(csv.DictReader((HERE/'frozen/paired_summary.csv').open(encoding='utf-8-sig')))
lines = [r'\begin{tabular}{@{}lrrrrr@{}}', r'\toprule',
         r'Cohort & Initial selection & \shortstack{Independent\\final} & \shortstack{PN\\final} & \shortstack{Independent\\gain} & \shortstack{PN\\gain} \\',
         r'\midrule']
checks = []
for ds in ['USACO110', 'TACO231', 'OJBench28', 'LCB231']:
    match = [r for r in rows if r['comparison'].startswith(ds+'|')
             and r['comparison'].endswith('|full') and 'earlier_stitched' not in r['comparison']]
    assert len(match) == 1
    r=match[0]; n=int(r['n']); initial=int(r['initial']); a1=int(r['a1']); pn=int(r['plan'])
    gain=lambda v: f'{v:+d}' if v else '0'
    name=ds
    lines.append(f'{name} & {initial}/{n} & {a1}/{n} & {pn}/{n} & {gain(a1-initial)} & {gain(pn-initial)} '+r'\\')
    checks.append({'dataset':ds,'n':n,'initial':initial,'A1':a1,'PN':pn})
lines.extend([r'\bottomrule',r'\end{tabular}'])
generated='\n'.join(lines)+'\n'
expected=(BUNDLE/'manuscript/english/tables/shared_start_table.tex').read_text()
out=BUNDLE/'reproduced/main_table';out.mkdir(parents=True,exist_ok=True)
(out/'shared_start_table.tex').write_text(generated)
report={'status':'PASS' if generated==expected else 'FAIL','byte_identical_to_manuscript':generated==expected,
        'rows':checks,'sha256':hashlib.sha256(generated.encode()).hexdigest(),
        'new_model_calls':0,'candidate_executions':0,'rescoring':0,
        'scope':'Primary shared-start table only. Other tables are retained source snapshots, not claimed rebuilt here.'}
(out/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
