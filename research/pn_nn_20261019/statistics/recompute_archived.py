#!/usr/bin/env python3
"""Recompute paired summaries from saved labels and usage; never runs candidates.

Default reads the recorded local sources. --from-snapshot reproduces all statistics
from inputs_snapshot.json only. Requires numpy; no model, network, or scorer imports.
"""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
import argparse, csv, hashlib, json, math, platform
import numpy as np

ROOT = Path('ARCHIVE_NOT_INCLUDED')
OUT = Path(__file__).resolve().parent
PACK = ROOT / 'PN-A1-A2初稿与完整轨迹核对-20261010'
PAPER = ROOT / 'PN-配对复测与成本对照补订-20261011'
SEED = 20261012
RESAMPLES = 100000
SOURCES = {}

def read(path, csv_file=False):
    path = Path(path)
    raw = path.read_bytes()
    SOURCES[str(path)] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if csv_file:
        return list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    return json.loads(raw)

def write_json(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def write_csv(name, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT/name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def flag(value):
    if isinstance(value, bool):
        return int(value)
    assert value in ['PASS', 'FAIL'], value
    return int(value == 'PASS')

def token_cost(p, c, o):
    # Rates used in the archived GPT-4o accounting, including cache discount.
    return Decimal(p-c)*Decimal('0.0000025') + Decimal(c)*Decimal('0.00000125') + Decimal(o)*Decimal('0.000010')

def aggregate_usage(candidates):
    res = dict(calls=0, input_tokens=0, cached_input_tokens=0, output_tokens=0,
               total_tokens=0, length_finished=0, absent_code=0, missing_usage=0)
    for c in candidates:
        res['calls'] += 1
        res['length_finished'] += c.get('finish_reason') == 'length'
        res['absent_code'] += not bool(c.get('code'))
        u = c.get('usage')
        if not u:
            res['missing_usage'] += 1
            continue
        res['input_tokens'] += u['prompt_tokens']
        res['output_tokens'] += u['completion_tokens']
        res['cached_input_tokens'] += u.get('prompt_tokens_details', {}).get('cached_tokens', 0)
        assert u.get('total_tokens', u['prompt_tokens']+u['completion_tokens']) == u['prompt_tokens']+u['completion_tokens']
    res['total_tokens'] = res['input_tokens']+res['output_tokens']
    res['usd'] = str(token_cost(res['input_tokens'], res['cached_input_tokens'], res['output_tokens'])) if not res['missing_usage'] else None
    return res

def collect():
    old = read(PACK/'analysis/old_initials.json')
    lcb = read(PACK/'analysis/lcb_initials.json')
    flat = read(PACK/'05_逐题初稿与最终交付.csv', True)
    cost_table = read(PACK/'06_历史最终结果与归属成本_原表.csv', True)
    v14 = read(PAPER/'english/evidence/v14-evidence-data.json')
    us_cost = read(ROOT/'PN-USACO110-任务适配正式实验-20261003/runs/formal_repeat1_derived/costs.json')
    to_cost = read(ROOT/'PN-TACO231-OJBench-七方法单次-A2-H1-H3-20261003/reports/results.json')
    arch_path = ROOT/'explore30/private/flat-pn-ablnopn1/NOT_PAPER_EVIDENCE-pnablnopn1-archive-replay.json'
    arch = read(arch_path)
    repeat_report = read(ROOT/'explore30/private/flat-pn-ablnopn1c/NOT_PAPER_EVIDENCE-pnablnopn1c-report.json')
    pairs, resources, checks = [], [], []
    names = {'usaco':'USACO110', 'taco':'TACO231', 'ojbench':'OJBench28'}
    flat_names = {'USACO110':'USACO','TACO231':'TACO','OJBench28':'OJBench','LCB231':'LCB'}
    flat_index = {(r['dataset'],r['question_id'],r['method']):r for r in flat if r['method'] in ['A1','A2-Plan']}
    for ds, v in old['datasets'].items():
        dataset = names[ds]
        state = read(v['state_source']['package_path'])
        scored = read(v['strict_label_report_source']['package_path'], True)
        score_index = {(r['question_id'],r['method']):r for r in scored if r.get('repeat')=='1'}
        for q in v['questions']:
            qid = q['question_id']
            a, p, b = q['final_a1_and_plan']['a1'], q['final_a1_and_plan']['a2'], q['three_initial_no_addition']
            assert q['all_three_shared_candidate_records']
            assert q['a1_initial_code_sha256'] == q['a2_plan_initial_code_sha256']
            r = dict(dataset=dataset, run='retained_single_run', question_id=qid,
                     initial_pass=flag(b['strict_status']), a1_pass=flag(a['strict_status']), plan_pass=flag(p['strict_status']),
                     gate_open=int(q['archived_gate_open']), continued=int(q['archived_gate_open']),
                     initial_selected_id=b['candidate_id'], a1_selected_id=a['candidate_id'], plan_selected_id=p['candidate_id'],
                     initial_code_sha256=b['code_sha256'], a1_code_sha256=a['code_sha256'], plan_code_sha256=p['code_sha256'],
                     difficulty=score_index[(qid,'a1')].get('difficulty',''), family_id=score_index[(qid,'a1')].get('family_id',''),
                     output_limit=16384, source=str(PACK/'analysis/old_initials.json'))
            for arm, rec in [('a1',a), ('a2',p)]:
                src = score_index[(qid,arm)]
                field = 'raw_status' if ds=='usaco' else 'status'
                assert flag(src[field]) == r['a1_pass' if arm=='a1' else 'plan_pass']
                if ds=='usaco': assert src['candidate_id']==rec['candidate_id']
                else: assert src['code_sha256']==rec['code_sha256']
            source_b = b['strict_label_source']
            base_src=score_index[(qid,source_b['method'])]
            assert flag(base_src[source_b['label_field']])==r['initial_pass']
            pairs.append(r)
        candidates=list(state['candidates'].values())
        for arm, groups in [('shared_initial',{'initial'}),('A1_additions',{'a1'}),('Plan_additions',{'a2'}),('A1_total',{'initial','a1'}),('Plan_total',{'initial','a2'}),('paired_retained_union',{'initial','a1','a2'})]:
            sums=aggregate_usage([c for c in candidates if c['arm'] in groups])
            sums.update(dataset=dataset,run='retained_single_run',stage=arm,source=v['state_source']['package_path'],
                        accounting='retained request usage with archived token prices; shared initials counted once in paired union')
            resources.append(sums)
            if arm in ['A1_total','Plan_total']:
                key='a1' if arm=='A1_total' else 'a2'
                if ds=='usaco':
                    original=us_cost['standalone_method_costs'][key]['inference_by_repeat']['1']
                    expected=[original['physical_calls'], original['input_tokens'], original['output_tokens'], original['cached_input_tokens'],Decimal(original['actual_fee_usd'])]
                else:
                    original=to_cost['logical_cost']['by_dataset'][ds]['standalone_logical'][key]
                    expected=[original['calls'], original['input_tokens'], original['output_tokens'], original['cached_input_tokens'],Decimal(original['usd'])]
                actual=[sums['calls'],sums['input_tokens'],sums['output_tokens'],sums['cached_input_tokens'],Decimal(sums['usd'])]
                assert actual==expected,(dataset,arm,actual,expected)
        checks.append(f'{dataset}: selected labels and identities match archived score CSV; usage sums match existing cost report')
    pool_rows=read(lcb['source_paths']['pool_csv'],True)
    initial_labels={row['candidate_id']: row for row in pool_rows if row['source']=='INITIAL'}
    strict_added_path=Path(lcb['source_paths']['added_strict'])
    raw=strict_added_path.read_bytes();SOURCES[str(strict_added_path)]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    strict_added={r['candidate_id']:r for r in map(json.loads,raw.decode().splitlines())}
    lcb_latest=[]
    for q in lcb['questions']:
        b,a,p=q['fixed3_selected'],q['A1'],q['A2_Plan']
        for rec in [a,p]:
            cid=rec['selected_candidate_id']
            actual=initial_labels[cid]['official_pass']=='True' if cid in initial_labels else strict_added[cid]['official_pass']
            assert actual==rec['strict_pass']
        assert (initial_labels[b['candidate_id']]['official_pass']=='True')==b['strict_pass']
        row=initial_labels[b['candidate_id']]
        r=dict(dataset='LCB231',run='later_paired_rerun',question_id=q['qid'],
               initial_pass=flag(b['strict_pass']),a1_pass=flag(a['strict_pass']),plan_pass=flag(p['strict_pass']),
               gate_open=int(q['gate_open']),continued=int(q['in_96_added']),
               initial_selected_id=b['candidate_id'],a1_selected_id=a['selected_candidate_id'],plan_selected_id=p['selected_candidate_id'],
               initial_code_sha256=next(c['code_sha256'] for c in q['initials'] if c['candidate_id']==b['candidate_id']),
               a1_code_sha256=a['selected_code_sha256'],plan_code_sha256=p['selected_code_sha256'],
               difficulty=row['difficulty'],family_id='',output_limit=2000,source=str(PACK/'analysis/lcb_initials.json'))
        pairs.append(r);lcb_latest.append(r)
    for r in pairs:
        qid=r['question_id']
        for arm in ['A1','A2-Plan']:
            f=flat_index[(flat_names[r['dataset']],qid,arm)]
            assert flag(f['initial_only_existing_strict_label'])==r['initial_pass']
            assert flag(f['final_existing_strict_label'])==r['a1_pass' if arm=='A1' else 'plan_pass']
            assert f['initial_only_selected_id']==r['initial_selected_id']
            assert f['final_selected_id']==r['a1_selected_id' if arm=='A1' else 'plan_selected_id']
    checks.append('All 600 retained paired rows agree with the exported initial/final table; LCB labels agree with saved per-candidate label files')
    # The earlier LCB comparison is kept separate. Fixed rows use the same documented prefix;
    # the archive contains individual labels for all 96 changed continuation rows.
    assert set(arch['archived_on_96']['A1'])==set(r['question_id'] for r in lcb_latest if r['continued'])
    for r in lcb_latest:
        x=dict(r);x['run']='earlier_stitched_archive';x['source']=str(arch_path)
        if r['continued']:
            qid=r['question_id'];assert flag(arch['initial_official_on_96'][qid])==r['initial_pass']
            x['a1_pass']=flag(arch['archived_on_96']['A1'][qid]);x['plan_pass']=flag(arch['archived_on_96']['A2'][qid])
            for key in ['a1_selected_id','plan_selected_id','a1_code_sha256','plan_code_sha256']:x[key]=''
        pairs.append(x)
    abl=v14['ablation']
    def resource_lcb(stage,d):
        return dict(dataset='LCB231',run='later_paired_rerun',stage=stage,calls=d['calls'],input_tokens=d['prompt_tokens'],
                    cached_input_tokens=d['cached_input_tokens'],output_tokens=d['completion_tokens'],total_tokens=d['prompt_tokens']+d['completion_tokens'],
                    usd=d.get('cost_usd_exact',str(d['cost_usd'])),length_finished=None,absent_code=None,missing_usage=0,
                    source=str(PAPER/'english/evidence/v14-evidence-data.json'),
                    accounting='retained-stream attribution; excluded/discarded and unknown campaign overhead not fully assigned to arms')
    resources.append(resource_lcb('shared_initial',abl['initial_reference']))
    for s in abl['streams']:
        if s['id'] in ['A1','A2']:
            name='A1' if s['id']=='A1' else 'Plan'
            resources.append(resource_lcb(name+'_additions',s));resources.append(resource_lcb(name+'_total',s['with_initial']))
    lresources=[x for x in resources if x['dataset']=='LCB231']
    parts=[x for x in lresources if x['stage'] in ['shared_initial','A1_additions','Plan_additions']]
    union=dict(parts[0]);union['stage']='paired_retained_union'
    for key in ['calls','input_tokens','cached_input_tokens','output_tokens','total_tokens']:union[key]=sum(x[key] for x in parts)
    union['usd']=str(sum(Decimal(x['usd']) for x in parts));resources.append(union)
    resources.append(dict(dataset='LCB231',run='earlier_stitched_archive',stage='A1_and_Plan',calls=None,input_tokens=None,output_tokens=None,total_tokens=None,usd=None,
                          accounting='Not reconstructed: earlier mixed-source costs are not replaced by later rerun costs',source=str(arch_path)))
    for c in cost_table:
        if c['method'] not in ['A1','A2-Plan']:continue
        r=next(x for x in resources if x['dataset']==c['dataset'] and x['stage']==('A1_total' if c['method']=='A1' else 'Plan_total'))
        assert r['calls']==int(c['inference_calls']) and Decimal(r['usd'])==Decimal(c['inference_usd_known_or_attributed'])
    return dict(pairs=pairs,resources=resources,checks=checks,sources=SOURCES,original_lcb_repeat_report={
        k:repeat_report[k] for k in ['archived_reference','run_to_run','replication_same_batch_A2_minus_A1','replication_archived_A2_minus_A1']})

def p_exact(wins,losses):
    n=wins+losses
    return min(1.,2*sum(math.comb(n,i) for i in range(min(wins,losses)+1))/(2**n)) if n else 1.

def summary(key, rows):
    n=len(rows);d=[r['plan_pass']-r['a1_pass'] for r in rows]
    counts=Counter(d)
    derived_seed=int.from_bytes(hashlib.sha256(f'{SEED}|{key}'.encode()).digest()[:8],'big')
    # Resampling the empirical {-1,0,+1} distribution is algebraically identical
    # to independently resampling paired task rows with replacement.
    rng=np.random.Generator(np.random.PCG64(derived_seed))
    drawn=rng.multinomial(n,[counts[-1]/n,counts[0]/n,counts[1]/n],size=RESAMPLES)
    delta=100*(drawn[:,2]-drawn[:,0])/n
    lo,hi=np.quantile(delta,[.025,.975],method='inverted_cdf')
    out=dict(comparison=key,n=n,initial=sum(r['initial_pass'] for r in rows),a1=sum(r['a1_pass'] for r in rows),plan=sum(r['plan_pass'] for r in rows),
             plan_only=counts[1],a1_only=counts[-1],both_pass=sum(r['a1_pass'] and r['plan_pass'] for r in rows),
             both_fail=sum(not r['a1_pass'] and not r['plan_pass'] for r in rows),
             difference_pp=100*sum(d)/n,paired_bootstrap95_low_pp=float(lo),paired_bootstrap95_high_pp=float(hi),
             exact_mcnemar_p=p_exact(counts[1],counts[-1]),bootstrap_seed=derived_seed,bootstrap_replicates=RESAMPLES,
             unknown_labels=0,gate_open=sum(r['gate_open'] for r in rows),continued=sum(r['continued'] for r in rows))
    for arm in ['a1','plan']:
        out[arm+'_rescues']=sum(not r['initial_pass'] and r[arm+'_pass'] for r in rows)
        out[arm+'_losses']=sum(r['initial_pass'] and not r[arm+'_pass'] for r in rows)
        out[arm+'_net_gain']=out[arm+'_rescues']-out[arm+'_losses']
    return out

def analyze(data):
    order={'USACO110':0,'TACO231':1,'OJBench28':2,'LCB231':3}
    rows=sorted(data['pairs'],key=lambda r:(order[r['dataset']],r['run']=='earlier_stitched_archive',r['question_id']))
    summaries=[]
    for dataset,run in dict.fromkeys((r['dataset'],r['run']) for r in rows):
        rr=[r for r in rows if r['dataset']==dataset and r['run']==run]
        summaries.append(summary(f'{dataset}|{run}|full',rr))
        cont=[r for r in rr if r['continued']]
        summaries.append(summary(f'{dataset}|{run}|continuation',cont))
    # Cross-run changes are descriptive counts; never pooled into an average run.
    early={r['question_id']:r for r in rows if r['dataset']=='LCB231' and r['run']=='earlier_stitched_archive' and r['continued']}
    late={r['question_id']:r for r in rows if r['dataset']=='LCB231' and r['run']=='later_paired_rerun' and r['continued']}
    variation=[]
    for arm in ['a1','plan']:
        variation.append(dict(arm=arm,n=96,earlier_pass=sum(r[arm+'_pass'] for r in early.values()),later_pass=sum(r[arm+'_pass'] for r in late.values()),
            fail_to_pass=sum(not early[q][arm+'_pass'] and late[q][arm+'_pass'] for q in early),
            pass_to_fail=sum(early[q][arm+'_pass'] and not late[q][arm+'_pass'] for q in early),
            flips=sum(early[q][arm+'_pass']!=late[q][arm+'_pass'] for q in early)))
    method=dict(effect='Plan minus A1 in percentage points',unit='paired task',bootstrap='nonparametric paired percentile bootstrap; equivalent multinomial resampling of observed task-level differences',
                resamples=RESAMPLES,base_seed=SEED,per_comparison_seed='first 8 bytes, big endian, SHA256(base_seed|comparison)',
                rng='numpy Generator PCG64',percentile_rule='numpy quantile method=inverted_cdf',numpy_version=np.__version__,python_version=platform.python_version(),
                test='two-sided exact McNemar test, binomial(n=discordant, p=0.5); no continuity correction or multiplicity correction',
                limits=['Exploratory intervals conditional on retained model outputs and frozen scoring labels; not generation-run variance.',
                        'Task-level resampling assumes exchangeable independent tasks; task-family dependence is not adjusted.',
                        'With very few discordant tasks the percentile bootstrap can be discrete, under-cover, and retain a zero endpoint when one win category is unobserved; it does not show equivalence or exclusion of improvement.',
                        'Bootstrap intervals and exact McNemar tests are not inversions of the same procedure; apparent threshold disagreement must not be resolved by choosing the more favorable result.',
                        'LCB full totals include 135 fixed deliveries and are projections, not fresh independent 231-task repetitions.',
                        'LCB earlier archive mixes development batches; do not pool with the later rerun as uniform repetitions.',
                        'Known LCB grader limitations remain; this script reads labels and does not validate scoring semantics.',
                        'All requested cohorts and continuation subsets are reported; no significance-driven selection.'])
    write_csv('paired_task_labels.csv',rows)
    write_csv('paired_summary.csv',summaries)
    write_csv('resource_summary.csv',data['resources'])
    write_csv('lcb_repeat_changes.csv',variation)
    result=dict(method=method,paired=summaries,resources=data['resources'],lcb_repeat_changes=variation,source_checks=data['checks'],
                missing_fields=['Earlier stitched LCB source-specific selected IDs and retained-stream resource allocation are not reconstructed.',
                                'Length/absent-code counts for LCB resource rows were not reconstructed from the aggregate usage source.',
                                'No complete-run SD is estimated from single retained streams.'],
                new_model_calls=0,candidate_executions=0,new_scoring=0,hidden_payload_reads=0,qwen_access=False)
    write_json('paired_stats.json',result)
    write_json('sources_manifest.json',data['sources'])
    make_text(result)
    print(json.dumps({'paired_rows':len(rows),'comparisons':len(summaries),'source_files':len(data['sources']),'output':str(OUT)},ensure_ascii=False))

def make_text(result):
    full=[r for r in result['paired'] if r['comparison'].endswith('|full')]
    txt=['GPT-4o既有A1/Plan配对与资源补统计','只读既有标签/用量；不生成、不执行、不评分、不接触千问。','',
         '所有差值均为Plan减A1；95%区间为按题配对percentile bootstrap，100000重采样，基准种子20261012；各表行派生种子见JSON。',
         '这些区间是对既有题与固定输出的探索性不确定性描述，不是重复生成波动；稀少胜负、题族关联、已知开发和旧评分限制均保留。','']
    for r in full:
        txt.append(f"{r['comparison']}: 初稿{r['initial']}/{r['n']}，A1 {r['a1']}，Plan {r['plan']}；Plan独赢/A1独赢/共同通过/共同失败={r['plan_only']}/{r['a1_only']}/{r['both_pass']}/{r['both_fail']}。差{r['difference_pp']:+.2f}个百分点，95%区间[{r['paired_bootstrap95_low_pp']:.2f},{r['paired_bootstrap95_high_pp']:.2f}]，exact p={r['exact_mcnemar_p']:.6f}。A1救回/退步={r['a1_rescues']}/{r['a1_losses']}，Plan={r['plan_rescues']}/{r['plan_losses']}。")
    txt+=['','追加子集与完整队列均已独立列于CSV，不能将同一结果算两次实验。LCB旧档与后复测分开；旧档缺少可统一复原的成本，不拿后复测费用顶替。',
          '注意：旧LCB拼批的percentile区间略高于0，而exact p=.057；两种程序不是互为反演，稀少胜负时会出现此差异。不能择取较有利者宣布显著，主队列的四个区间均包含0。',
          'USACO/TACO/OJBench资源由原state.usage逐条聚合，和已保存成本报告对齐；共享初稿只在paired_retained_union计一次。LCB用稿件已有保留流统计，未分摊废弃/未知历史成本，不冒称全现金账。',
          '新统计未改变旧标签，未补入口、改I/O或重新选择。计划与独立追加的观察差异仍小，区间与p值不能判定二者等效，也不能保证新重复会维持方向。','',
          '复算：python3 recompute.py（读源）或 python3 recompute.py --from-snapshot（读本目录冻结的标量快照）。只需numpy，无模型/执行/评分依赖。']
    (OUT/'中文结果说明.txt').write_text('\n'.join(txt)+'\n')
    retained=[r for r in full if 'earlier_stitched' not in r['comparison']]
    by={r['comparison'].split('|')[0]:r for r in retained}
    s='; '.join(f"{ds}: {r['difference_pp']:+.2f} percentage points (95% paired bootstrap interval {r['paired_bootstrap95_low_pp']:.2f} to {r['paired_bootstrap95_high_pp']:.2f})" for ds,r in by.items())
    english=("We compare A1 and A2-Plan task by task from the same selected initial programs. "
      "Plan-only and A1-only successes were 1 and 4 on USACO, 3 and 1 on TACO, 0 and 1 on OJBench, and 8 and 4 in the later historical LCB comparison. "
      "The corresponding score differences were "+s+". The two-sided exact paired tests were descriptive and unadjusted for multiple comparisons. "
      "The intervals resample paired tasks from the saved outputs 100,000 times, with a fixed base seed of 20261012. They do not estimate variation across new generation runs, account for task-family dependence, or resolve the historical grader's output-validity limitations. "
      "With few discordant tasks, percentile intervals can have poor coverage; a zero endpoint does not imply equivalence.\n\n"
      "The historical LCB comparison also has an earlier continuation record: A1 and Plan delivered 6 and 14 passes on the same 96 tasks, compared with 9 and 13 in the later paired rerun. "
      "Three A1 outcomes and seven Plan outcomes changed. The earlier record combines development batches, so the two records are kept separate rather than averaged as repeated full-cohort runs. "
      "In the later run, both methods made 288 additional requests. Plan used 576,046 input and 211,232 output tokens, compared with A1's 174,474 and 202,645; attributed continuation costs were $3.178195 and $2.449675. "
      "Shared initial generation is counted once in physical resource totals and attributed once to each standalone method. These costs describe the retained streams and do not fully allocate discarded or unresolved historical campaign costs.\n")
    for banned in ['evidence','conditioned','native','conservative','audited','pillars']:
        assert banned not in english.lower()
    (OUT/'manuscript_paragraphs_en.txt').write_text(english)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--from-snapshot',action='store_true');args=p.parse_args()
    if args.from_snapshot:data=json.loads((OUT/'inputs_snapshot.json').read_text())
    else:
        data=collect();write_json('inputs_snapshot.json',data)
    analyze(data)
