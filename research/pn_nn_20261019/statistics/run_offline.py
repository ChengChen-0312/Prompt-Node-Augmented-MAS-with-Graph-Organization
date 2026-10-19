#!/usr/bin/env python3
"""Recalculate stored scalar results only. No provider, candidate, or grader calls."""
from pathlib import Path
import argparse, csv, hashlib, json, shutil, subprocess, sys

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('reproduced/statistics'))
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    out=args.output.resolve()
    if out.exists():
        raise SystemExit('Output exists. Choose a new directory; frozen outputs are never overwritten.')
    out.mkdir(parents=True)
    shutil.copy2(here/'recompute_archived.py',out/'recompute.py')
    shutil.copy2(here/'frozen/inputs_snapshot.json',out/'inputs_snapshot.json')
    result=subprocess.run([sys.executable,str(out/'recompute.py'),'--from-snapshot'],
                          cwd=out,check=True,capture_output=True,text=True)
    names=['paired_summary.csv','paired_task_labels.csv','resource_summary.csv','lcb_repeat_changes.csv','sources_manifest.json']
    checks={name:(out/name).read_bytes()==(here/'frozen'/name).read_bytes() for name in names}
    expected=json.loads((here/'frozen/paired_stats.json').read_text())
    actual=json.loads((out/'paired_stats.json').read_text())
    # Environment version strings are provenance, not numeric results.
    def drop_versions(obj):
        if isinstance(obj,dict):return {k:drop_versions(v) for k,v in obj.items() if k not in ['python_version','numpy_version']}
        if isinstance(obj,list):return [drop_versions(v) for v in obj]
        return obj
    checks['paired_stats_numeric_and_protocol_match']=drop_versions(actual)==drop_versions(expected)
    report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
            'new_model_calls':0,'candidate_executions':0,'rescoring':0,
            'scope':'Stored label and token arithmetic only; not end-to-end experiment reproduction.',
            'stdout':result.stdout.strip()}
    (out/'OFFLINE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)
if __name__=='__main__':main()
