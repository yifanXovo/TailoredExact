"""Bind the completed independent raw/finite reviews; no solver or project import."""
from pathlib import Path
from collections import Counter
import argparse, csv, difflib, hashlib, json, math, shutil, sys, time

ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args()
root=Path(a.root).resolve();out=root/'results/unified_exact_round108';review=out/'review'
tick=time.perf_counter();read_bindings={}
def data(p):
    b=Path(p).read_bytes();read_bindings[str(Path(p).relative_to(root)).replace('\\','/')]=hashlib.sha256(b).hexdigest();return b
def obj(p):return json.loads(data(p))
def sha(p):return hashlib.sha256(data(p)).hexdigest()
def rows(p):return list(csv.DictReader(data(p).decode('utf-8-sig').splitlines()))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def norm(s):return str(s).replace('\\','/')
save(review/'confirmation_L48_finalize02_launch.json',dict(actual_command=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_read_root=str(root),source_SHA=sha(Path(__file__)),started_unix=time.time(),Optimize=0,LP_solve=0,native_environment=0,compiler=0))
rawdir=review/'confirmation_L48_raw_audit01';raw=obj(rawdir/'audit.json');receipt=obj(rawdir/'receipt.json');launch=obj(rawdir/'launch.json')
assert raw['decision']=='ACCEPT' and receipt['exit_code']==0 and receipt['audit_SHA']==sha(rawdir/'audit.json')
assert raw['reviewer_script_SHA']==receipt['source_SHA']==sha(rawdir/'source_at_execution.py')==sha(review/'campaign_raw_audit01.py')
assert launch['explicit_read_root']==str(root) and '--root' in launch['command'] and '--through' in launch['command'] and 'L48' in launch['command']
finite=obj(review/'next_leaf_partition_finite02/checks.json');finite_receipt=obj(review/'next_leaf_partition_finite02/receipt.json')
assert finite['decision']=='ACCEPT' and finite_receipt['exit_code']==0 and finite_receipt['checks_SHA']==sha(review/'next_leaf_partition_finite02/checks.json')
assert finite['source_SHA']==sha(review/'next_leaf_partition_finite_audit01.py') and finite['independent_raw_source_SHA']==raw['reviewer_script_SHA']
shutil.copyfile(review/'next_leaf_partition_finite_audit01.py',review/'next_leaf_partition_finite02/source_at_execution.py')
reader=root/'scripts/round108_reader.py';reader_sha=sha(reader)
assert reader_sha=='52cadcf5ff7ce5fcfb1f828efd1a81a1c4d14d5e31d9b6b72963f7348e8408c1'==finite['reader_source_SHA']==raw['bindings']['pure_current_campaign_reader_SHA']
three=out/'engineering/confirmation_L48_reader03_reports';four=out/'engineering/confirmation_L48_reader04_reports'
oldreader=out/'engineering/confirmation_L48_reader03/source_snapshot/scripts/round108_reader.py'
diff=list(difflib.unified_diff(data(oldreader).decode().splitlines(),data(reader).decode().splitlines(),fromfile='accepted reader03',tofile='reader04',lineterm=''))
(review/'next_leaf_reader03_to04_independent.diff').write_text('\n'.join(diff)+'\n',encoding='utf-8')
unchanged=0;fields=0
assert {p.name for p in three.glob('*.csv')}=={p.name for p in four.glob('*.csv')}
for p in four.glob('*.csv'):
    if p.name=='mechanism_summary.csv':continue
    assert data(p)==data(three/p.name),p.name
    rr=rows(p);fields+=sum(len(r) for r in rr);unchanged+=1
assert unchanged==28
for name in ['admission_decision.json','continuation_decision.json']:assert obj(three/name)==obj(four/name)
mm=rows(four/'mechanism_summary.csv');oldmm={(r['id'],r['arm']):r for r in rows(three/'mechanism_summary.csv')}
arms=raw['qualification']+raw['arms'];indexed={(r['id'],r['arm']):r for r in arms}
for r in mm:
    record=indexed[r['id'],r['arm']];k=Counter(x['solve_kind'] for x in record['native_records']);old=oldmm[r['id'],r['arm']]
    assert int(r['partial_target_MIP_calls'])==k['CHILD_BOUND_TARGET_MIP']+k['NEXT_LEAF_TARGET_MIP']
    assert int(r['child_bound_target_MIP_calls'])==k['CHILD_BOUND_TARGET_MIP'] and int(r['next_leaf_target_MIP_calls'])==k['NEXT_LEAF_TARGET_MIP']
    assert int(r['LP_calls'])==k['LP'] and int(r['terminal_MIP_calls'])==k['MIP']
    assert int(r['actual_native_Optimize'])==len(record['native_records'])
    assert json.loads(r['other_solve_kinds'])=={n:v for n,v in k.items() if n not in ['LP','CHILD_BOUND_TARGET_MIP','NEXT_LEAF_TARGET_MIP','MIP']}
    for field in old:
        if field not in {'partial_target_MIP_calls','other_solve_kinds'}:assert old[field]==r[field],(r['id'],r['arm'],field)
    assert int(r['partial_target_MIP_calls'])==int(old['partial_target_MIP_calls'])+json.loads(old['other_solve_kinds']).get('NEXT_LEAF_TARGET_MIP',0)
tablearms=rows(four/'arms.csv')+rows(four/'qualification_arms.csv')
assert len(tablearms)==len(arms)==18 and len(raw['arms'])==15
for r in tablearms:
    independent=indexed[r['id'],r['arm']]
    for key in ['U','L','gap','complete_seconds']:assert float(r[key])==independent[key],(r['id'],r['arm'],key)
    for key in ['certificate','numbers_qualified','certificate_qualified']:assert (r[key]=='True')==independent[key]
    assert r['PE_SHA']==independent['PE_SHA'] and r['DLL_SHA']==independent['DLL_SHA']
pairs={(r['id'],r['control']):r for r in rows(four/'pairs.csv')}
for p in raw['gate']['pairs']:
    r=pairs[p['id'],p['control']];assert r['classification']==p['classification'] and (r['severe_regression']=='True')==p['severe_regression']
    for key in ['UB_improvement','gap_improvement','LB_change','a_U','a_gap']:assert float(r[key])==p[key]
starts=rows(four/'starts.csv');ownstarts={norm(x['metadata_path']):x for arm in arms for x in arm['starts']}
assert len(starts)==len(ownstarts)==22
for r in starts:
    s=ownstarts[r['start_path']];assert r['start_sha256']==s['metadata_SHA'] and r['vector_sha256']==s['values_SHA'] and r['model_sha256']==s['model_SHA']
    assert int(r['rows'])==s['rows_checked'] and int(r['columns'])==s['columns']
native=rows(four/'native_calls.csv');models=rows(four/'models.csv')
assert len(native)==74==sum(len(x['native_records']) for x in arms)
assert len(models)==50==sum(len(x['model_contracts']) for x in arms)
nativeown={(x['id'],x['arm'],str(n['call'])):n for x in arms for n in x['native_records']}
for r in native:
    n=nativeown[r['id'],r['arm'],r['call']];assert r['actual_Optimize']=='True' and r['returned']=='True' and r['model_SHA']==n['model_SHA']
summary=obj(four/'summary.json');assert summary['reader_SHA']==reader_sha and summary['formal_arms']==15 and summary['failed_formal_arms']==0 and summary['actual_Optimize']==summary['Optimize_returned']==74
assert summary['conservative_starts']==raw['fees']['paid_corrected_starts']==38 and summary['outer_solver_fee_seconds']==raw['fees']['paid_outer_seconds']==15287.128604099911
primary=obj(four/'continuation_decision.json');assert primary==raw['gate']['current_positive_selection_unreachable']
assert obj(four/'admission_decision.json')['bridge_pass']==raw['gate']['bridge_pass'] is True
history=[]
for n in range(1,5):
    folder=out/f'engineering/confirmation_L48_reader{n:02d}';r=obj(folder/'receipt.json')
    src=folder/'source_snapshot/scripts/round108_reader.py'
    history.append(dict(attempt=n,receipt_path=norm((folder/'receipt.json').relative_to(root)),receipt_SHA=sha(folder/'receipt.json'),source_SHA=sha(src),exit_code=r['exit_code'],seconds=r['seconds']))
assert [r['exit_code'] for r in history]==[1,1,0,0] and history[-1]['source_SHA']==reader_sha
correction=dict(decision='ACCEPT',current_reader_SHA=reader_sha,scope='Pure inherited next-leaf provenance token, fully supported open-leaf discharge, and partial-target count disclosure',
    actual_performance_changed=False,performance_reruns=0,actual_raw_evidence_contradictions=[],primary_attempts=history,
    finite_cases=len(finite['cases']),finite_checks_SHA=sha(review/'next_leaf_partition_finite02/checks.json'),finite_source_SHA=sha(review/'next_leaf_partition_finite_audit01.py'),
    finite_actual_command=finite_receipt['command'],finite_explicit_read_root=finite_receipt['explicit_read_root'],finite_exit_code=finite_receipt['exit_code'],
    finite_first_attempt_preserved=dict(checks_SHA=sha(review/'next_leaf_partition_finite01/checks.json'),receipt_SHA=sha(review/'next_leaf_partition_finite01/receipt.json'),source_SHA=sha(review/'next_leaf_partition_finite01/source_at_execution.py'),reason='Synthetic harness supplied active-leaf bound as raw endpoint although other open leaf determined the minimum; repaired fixture input, not a production/raw evidence defect'),
    independent_complete_partition_source_SHA=raw['reviewer_script_SHA'],independent_raw_audit_SHA=sha(rawdir/'audit.json'),
    reader03_to04=dict(diff_SHA=sha(review/'next_leaf_reader03_to04_independent.diff'),unchanged_other_CSV_files=unchanged,unchanged_CSV_data_fields=fields,decision_JSON_unchanged=True,partial_count_independently_reconciled_to_actual_native_calls=True),
    source_semantics=dict(original_next_leaf_merge='src/PaperExternalGiniTree.cpp:4236-4240',whole_leaf_proof_before_discharge=True,conditional_lower_is_min_proof_L_cutoff=True,raw_published_signed_L_and_gap_preserved=True,call_model_log_leaf_return_identity_required=True,no_future_evidence=True),
    reviewer_zero_solver_calls=raw['reviewer_zero_solver_calls'])
if (review/'next_leaf_reader_correction_review01.json').exists():assert obj(review/'next_leaf_reader_correction_review01.json')==correction
else:save(review/'next_leaf_reader_correction_review01.json',correction)
l48=[x for x in raw['arms'] if x['id']=='L48'];cp=next(x for x in raw['gate']['pairs'] if x['id']=='L48' and x['control']=='P-GRB');ce=next(x for x in raw['gate']['pairs'] if x['id']=='L48' and x['control']=='ENS-C')
assert cp['classification']=='WIN' and ce['classification']=='TIE' and not cp['severe_regression']
assert raw['gate']['unseen_WIN']==2 and raw['gate']['unseen_LOSS']==0 and raw['gate']['maximum_remaining_unseen_WIN']==3 and raw['continuation_permitted']
protocol=obj(out/'confirmation_protocol.json');f5=next(p for p in protocol['roles'] if p['id']=='F5')
assert f5['method_order']==['M-B','P-GRB','ENS-C'] and f5['cap_seconds']==5400
confirmation=obj(out/'confirmation01/identity.json');future=[l for l in confirmation['launches'] if l['id'] in ['F5','N36']]
assert len(future)==6 and all(not (root/'results/unified_exact_round108'/norm(l['destination']).split('results/unified_exact_round108/')[-1]).exists() for l in future)
fees=raw['fees'];assert fees['next_total_starts']==42 and fees['full21_conservative_starts']==46 and fees['next_complete_group']=='F5'
reserve=3*f5['cap_seconds']+120;assert reserve==16320 and fees['paid_outer_seconds']+reserve<80000
values=[dict(id=x['id'],arm=x['arm'],U=x['U'],L=x['L'],signed_gap=x['gap'],relative_gap=x['relative_gap'],complete_seconds=x['complete_seconds'],certificate=x['certificate'],raw_status=x['raw_status']) for x in l48]
report=dict(decision='ACCEPT',continuation_permitted=True,permitted_next_complete_group='F5',scope='Independent current qualification plus all fifteen complete formal arms through L48; continuation admission only',
    actual_raw_evidence_contradictions=[],uniform_selection_admitted=False,reader_development_failures_are_not_solver_failures=True,**raw['bindings'],
    complete_raw_audit=dict(path=norm((rawdir/'audit.json').relative_to(root)),SHA=sha(rawdir/'audit.json'),actual_command=launch['command'],explicit_read_root=launch['explicit_read_root'],source_SHA=receipt['source_SHA'],exit_code=receipt['exit_code'],engineering_seconds=receipt['engineering_elapsed_seconds'],completed_checks=raw['completed_checks'],raw_bindings_field='read_bindings',raw_bindings_count=len(raw['read_bindings']),root_fallback=False),
    L48_own_endpoints=values,L48_primary_pair=cp,L48_ENS_contrast=ce,all_prefix_pairs=raw['gate']['pairs'],bridge_pass=raw['gate']['bridge_pass'],
    exact_four_eligibility=dict(roles=raw['gate']['exact_unseen_roles'],denominator=4,all_four_eligible_at_first_freeze=raw['four_sealed_input_eligibility'],freeze_review_SHA=sha(review/'sealed_input_eligibility.json'),measured_roles=raw['gate']['measured_unseen'],current_WIN=2,current_LOSS=0,maximum_final_WIN=3),
    no_severe_P=True,no_UNEVAL=True,early_impossibility=raw['gate']['current_positive_selection_unreachable'],remaining_required_roles=['F5','N36'],no_hidden_ENS_dominance_gate=True,
    actual_current_counts=dict(qualification_arms=3,formal_arms=15,models=50,native_Optimize=74,native_returns=74,Start_mapping_attempts=24,Start_submitted=22,Start_ineligible_outside_true_G_scope=2),
    L48_actual_scopes=[dict(arm=x['arm'],model_contracts=x['model_contracts'],cover=x['cover'],Start_attempts=x['start_attempts'],submitted_Starts=x['starts']) for x in l48 if x['cover']],
    paired_L48_native_matrices=[x for x in raw['paired_actual_interval_matrices'] if x['id']=='L48'],
    corrected_fees=fees,next_group_budget=dict(role='F5',order=f5['method_order'],each_original_cap_seconds=5400,whole_group_reserved_starts=4,next_total_starts=42,whole_group_reserved_seconds=reserve,paid_plus_reserve_seconds=fees['paid_outer_seconds']+reserve,frozen_common_budget_requires_manual_corrections=True),
    reader_correction_review_SHA=sha(review/'next_leaf_reader_correction_review01.json'),primary_reader_actual_receipt_SHA=history[-1]['receipt_SHA'],primary_table_crosscheck=dict(all_18_endpoints_and_signed_gaps_exact=True,all_10_pairs_and_thresholds_exact=True,all_actual_submitted_Start_identities_match=True,native_calls_and_models_match=True,unchanged_other_CSV_files=unchanged,unchanged_CSV_data_fields=fields),
    independent_reviewer_idle_after_this_record=True,reviewer_zero_solver_calls=raw['reviewer_zero_solver_calls'],finalizer_actual_command=[sys.executable,*sys.argv],finalizer_source_SHA=sha(Path(__file__)))
save(review/'confirmation_L48_review01.json',report)
md='''ACCEPT：资格三臂及截至 L48 的全部十五正式臂独立重构通过；允许按冻结顺序继续 F5 的完整 M-B/P-GRB/ENS-C 三臂组。未发现实际原始证据矛盾。尚不具备统一 SELECT 资格，F5/N36 均须依原协议完成并复核。

| L48 臂 | 本臂物理 U | 原始范围合格 L | signed gap | 完整时间 s | 完整证书 |
|---|---:|---:|---:|---:|---|
'''
for x in values:md+=f"| {x['arm']} | {x['U']:.17g} | {x['L']:.17g} | {x['signed_gap']:.17g} | {x['complete_seconds']:.10f} | {x['certificate']} |\n"
md+=f'''
M-B/P 为证书优先 WIN；M-B/ENS 为 TIE：慢 {(-ce['time_improvement']):.10f}s，小于完整时间门槛 {ce['a_t']:.10f}s。固定四角色 S12/B24/L48/N36 的已测分类为 TIE/WIN/WIN，当前 2 WIN、0 LOSS，最大可能最终 WIN=3，无 P 严重退化、UNEVAL 或提前不可达条件。

每臂两次实际父子分区有完整 true-G 覆盖。右叶由完整 LP 不可行证明排除；左下 saved-open 叶由实际 NEXT_LEAF_TARGET_MIP 完整范围界（ENS .21860283787862958，M-B .21871079190650766）排除改进；中叶实际原整数 terminal MIP OPTIMAL。全部界按 min(proof L, cutoff) 限定，不扩展 epigraph 范围，不裁剪发布的 signed L/gap。

L48 每臂 7 LP、2 原有 next-leaf target MIP、1 terminal MIP。每臂 3 份 Start 尝试中 2 份完整映射并实际提交；另一份真实 G=.0644761162869155 > 保存叶上限 .055933531783146154，无向量 CSV、无 native user Start。全前缀 50 模型、74 实际调用/返回、24 mapping attempts、22 submitted Starts；全部 p/d VType、原有域、逐系数 A/B、真实 G cap/floor、cutoff、journal commit/返回时序、物理车队/UB 及原生日志由独立脚本重核。

纠正后的付费为 38 starts / 15287.128604099911 外层秒。F5 预留 4 starts / 16320 秒，下一合计 42 starts / 31607.12860409991 秒；完整 21 臂保守总 starts=46≤48。冻结 common budget 不读取补充 correction，启动前须继续保存实际手工修正检查。

自身 raw 审计实际命令、explicit root、source/PE/DLL/protocol/argv/raw SHA 和 exit0 receipt 位于 confirmation_L48_raw_audit01；3,816,633 checks，通过用时约 61.77 秒。当前 pure reader SHA 52cadcf5ff7ce5fcfb1f828efd1a81a1c4d14d5e31d9b6b72963f7348e8408c1；21 个有限反例通过；03→04 独立比较 28 其他 CSV 与两份 decision JSON 一致，只修正 partial-target aggregate/subcounts。首次有限检查失败系 synthetic raw endpoint fixture 误用 active LB，原 source/command/exit1 保留后纠正，仅更正自身 fixture。

本 reviewer 零 Optimize/LP solve/native environment/IIS/compiler，无生产或性能文件改动。所有重 CPU 审查完成，后续性能组期间保持空闲。
'''
(review/'confirmation_L48_review01.md').write_text(md,encoding='utf-8')
(review/'next_leaf_reader_correction_review01.md').write_text('ACCEPT。原 next-leaf token 及已证明完整 true-G 范围的 open-leaf discharge 与继承合同一致，21 个有限反例通过；错误 leaf/model/log/failed or missing return/future evidence/missing segment/unsupported high raw bound 均被拒绝。当前 52cadcf5 的 partial-target disclosure 在本次独立全表对比中保留所有端点、signed gap、证书、pair/gate/continuation，并准确单列 CHILD 与 NEXT 数量。前两次实际 reader false rejection、两个 finite fixture attempt 与实际 source/command/exit/receipt 均保留；未作性能 rerun。详见 JSON 与独立 raw audit。\n',encoding='utf-8')
save(review/'confirmation_L48_finalize02_receipt.json',dict(actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=sha(Path(__file__)),review_SHA=sha(review/'confirmation_L48_review01.json'),review_MD_SHA=sha(review/'confirmation_L48_review01.md'),reader_review_SHA=sha(review/'next_leaf_reader_correction_review01.json'),exit_code=0,seconds=time.perf_counter()-tick,Optimize=0,LP_solve=0,native_environment=0,IIS=0,compiler=0,read_bindings=read_bindings))
print(json.dumps(dict(decision='ACCEPT',review_SHA=sha(review/'confirmation_L48_review01.json'),reader_review_SHA=sha(review/'next_leaf_reader_correction_review01.json'),formal_arms=15,native_calls=74,submitted_Starts=22,unseen_WIN=2,unseen_LOSS=0,next_group='F5',next_total_starts=42,paid_outer_seconds=fees['paid_outer_seconds'],independent_reviewer_idle=True)))
