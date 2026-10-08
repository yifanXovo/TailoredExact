"""Finalize independent through-F5 raw, Start normalization and source review."""
from pathlib import Path
from collections import Counter
import argparse, csv, hashlib, json, subprocess, sys, time

ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args()
root=Path(a.root).resolve();out=root/'results/unified_exact_round108';review=out/'review';tick=time.perf_counter();reads={}
def data(p):
    b=Path(p).read_bytes();reads[str(Path(p).relative_to(root)).replace('\\','/')]=hashlib.sha256(b).hexdigest();return b
def sha(p):return hashlib.sha256(data(p)).hexdigest()
def obj(p):return json.loads(data(p))
def rows(p):return list(csv.DictReader(data(p).decode('utf-8-sig').splitlines()))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def norm(p):return str(p).replace('\\','/')
save(review/'confirmation_F5_finalize01_launch.json',dict(actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=sha(Path(__file__)),started_unix=time.time(),Optimize=0,LP_solve=0,native_environment=0,compiler=0))
d=review/'confirmation_F5_raw_audit02';raw=obj(d/'audit.json');receipt=obj(d/'receipt.json');launch=obj(d/'launch.json')
assert raw['decision']=='ACCEPT' and receipt['exit_code']==0 and receipt['audit_SHA']==sha(d/'audit.json')
assert receipt['source_SHA']==raw['reviewer_script_SHA']==sha(review/'campaign_raw_audit01.py')
(d/'source_at_execution.py').write_bytes(data(review/'campaign_raw_audit01.py'))
assert launch['explicit_read_root']==str(root) and '--root' in launch['command'] and '--through' in launch['command'] and 'F5' in launch['command']
finite=obj(review/'start_normalization_finite01/checks.json');fr=obj(review/'start_normalization_finite01/receipt.json')
assert finite['decision']=='ACCEPT' and len(finite['cases'])==24 and fr['exit_code']==0 and fr['checks_SHA']==sha(review/'start_normalization_finite01/checks.json')
assert fr['source_SHA']==sha(review/'start_normalization_finite_audit01.py') and finite['independent_raw_source_SHA']==receipt['source_SHA']
(review/'start_normalization_finite01/source_at_execution.py').write_bytes(data(review/'start_normalization_finite_audit01.py'))
bad=review/'confirmation_F5_raw_audit01';br=obj(bad/'receipt.json');ba=obj(bad/'audit.json')
assert br['exit_code']==1 and br['source_SHA']==sha(bad/'source_at_execution.py') and br['audit_SHA']==sha(bad/'audit.json')
assert ba['error']=='AssertionError: complete visited and unvisited native quantities'
diagnosis=dict(actual_raw_evidence_contradiction=False,failed_independent_source_SHA=br['source_SHA'],failed_audit_SHA=sha(bad/'audit.json'),failed_actual_command=obj(bad/'launch.json')['command'],failed_explicit_read_root=obj(bad/'launch.json')['explicit_read_root'],failed_exit_code=1,
    reason='Own reader compared raw source vehicle labels before the inherited exact normalization. In F5 equal-Q=30, source vehicle2 has 15 operations and source vehicle0 has11; original stable count ordering relabels 2->0 and0->2. Fleet, operations, inventory, closed durations and objective are unchanged.',
    production_call_site='src/GurobiBaseline.cpp:634-637',production_normalization='src/Round61Candidates.cpp:89-108',current_and_R100_binding=finite['inherited_production_binding'],corrected_independent_source_SHA=receipt['source_SHA'],corrected_actual_command=launch['command'],corrected_explicit_read_root=launch['explicit_read_root'],corrected_exit_code=0,corrected_raw_audit_SHA=sha(d/'audit.json'),finite_cases=24,finite_checks_SHA=sha(review/'start_normalization_finite01/checks.json'),Optimize=0,LP_solve=0,native_environment=0,compiler=0)
save(bad/'diagnosis.json',diagnosis)
reports=out/'engineering/confirmation_F5_reader01_reports';primaryreceipt=obj(out/'engineering/confirmation_F5_reader01/receipt.json')
assert primaryreceipt['exit_code']==0
assert sha(root/'scripts/round108_reader.py')==raw['bindings']['pure_current_campaign_reader_SHA']=='52cadcf5ff7ce5fcfb1f828efd1a81a1c4d14d5e31d9b6b72963f7348e8408c1'
arms=raw['qualification']+raw['arms'];indexed={(x['id'],x['arm']):x for x in arms}
arows=rows(reports/'arms.csv')+rows(reports/'qualification_arms.csv')
assert len(arows)==len(arms)==21 and len(raw['arms'])==18
for r in arows:
    own=indexed[r['id'],r['arm']]
    for key in ['U','L','gap','relative_gap','complete_seconds']:assert float(r[key])==own[key],(r['id'],r['arm'],key)
    for key in ['certificate','certificate_qualified','numbers_qualified']:assert (r[key]=='True')==own[key]
    assert r['PE_SHA']==own['PE_SHA'] and r['DLL_SHA']==own['DLL_SHA']
prows={(r['id'],r['control']):r for r in rows(reports/'pairs.csv')}
for p in raw['gate']['pairs']:
    r=prows[p['id'],p['control']];assert r['classification']==p['classification'] and (r['severe_regression']=='True')==p['severe_regression']
    for key in ['UB_improvement','gap_improvement','LB_change','a_U','a_gap']:assert float(r[key])==p[key]
models=sum(len(x['model_contracts']) for x in arms);calls=sum(len(x['native_records']) for x in arms)
submitted=sum(len(x['starts']) for x in arms);attempts=sum(len(x['start_attempts']) for x in arms)
nc=rows(reports/'native_calls.csv');mc=rows(reports/'models.csv');ss=rows(reports/'starts.csv')
assert len(nc)==calls and len(mc)==models and len(ss)==submitted
native={(x['id'],x['arm'],str(n['call'])):n for x in arms for n in x['native_records']}
for r in nc:
    n=native[r['id'],r['arm'],r['call']];assert r['actual_Optimize']=='True' and r['returned']=='True' and r['model_SHA']==n['model_SHA']
starts={norm(s['metadata_path']):s for x in arms for s in x['starts']}
for r in ss:
    s=starts[r['start_path']];assert r['start_sha256']==s['metadata_SHA'] and r['vector_sha256']==s['values_SHA'] and r['model_sha256']==s['model_SHA'] and int(r['rows'])==s['rows_checked'] and int(r['columns'])==s['columns']
for r in rows(reports/'mechanism_summary.csv'):
    counts=Counter(n['solve_kind'] for n in indexed[r['id'],r['arm']]['native_records'])
    assert int(r['actual_native_Optimize'])==sum(counts.values()) and int(r['LP_calls'])==counts['LP'] and int(r['partial_target_MIP_calls'])==counts['CHILD_BOUND_TARGET_MIP']+counts['NEXT_LEAF_TARGET_MIP'] and int(r['terminal_MIP_calls'])==counts['MIP']
summary=obj(reports/'summary.json');fees=raw['fees'];gate=raw['gate']
assert summary['formal_arms']==18 and summary['failed_formal_arms']==0 and summary['actual_Optimize']==summary['Optimize_returned']==calls
assert summary['conservative_starts']==fees['paid_corrected_starts']==42 and summary['outer_solver_fee_seconds']==fees['paid_outer_seconds']==31400.737309299933
assert obj(reports/'continuation_decision.json')==gate['current_positive_selection_unreachable']
assert gate['bridge_pass'] and raw['continuation_permitted'] and not gate['current_positive_selection_unreachable']['positive_selection_unreachable']
f5=[x for x in raw['arms'] if x['id']=='F5'];cp=next(p for p in gate['pairs'] if p['id']=='F5' and p['control']=='P-GRB');ce=next(p for p in gate['pairs'] if p['id']=='F5' and p['control']=='ENS-C')
assert cp['classification']=='WIN' and not cp['severe_regression'] and ce['classification']=='LOSS' and ce['severe_regression']
assert all(not p['severe_regression'] for p in gate['pairs'] if p['control']=='P-GRB')
assert gate['unseen_WIN']==2 and gate['unseen_LOSS']==0 and gate['maximum_remaining_unseen_WIN']==3 and raw['four_sealed_input_eligibility']
confirmation=obj(out/'confirmation01/identity.json');future=[l for l in confirmation['launches'] if l['id']=='N36'];assert len(future)==3
for l in future:
    value=norm(l['destination']);p=root/value[value.index('results/'):];assert not p.exists()
protocol=obj(out/'confirmation_protocol.json');n36=next(p for p in protocol['roles'] if p['id']=='N36')
assert n36['method_order']==['P-GRB','ENS-C','M-B'] and n36['cap_seconds']==5400 and fees['next_complete_group']=='N36' and fees['next_total_starts']==46
reserve=3*n36['cap_seconds']+120;assert reserve==16320 and fees['paid_outer_seconds']+reserve<80000 and fees['full21_conservative_starts']==46
# Source-only checks of pending public dependencies and truthful narrative scope.
public=data(root/'scripts/round108_public.py').decode();narrative=data(root/'scripts/round108_report.py').decode();historical=[]
base='b5db3f038f64215766a54498d8acc82e384de733'
for number in [98,99,102,105,106]:
    path=f'results/unified_exact_round{number}/final_report.md';assert repr(path) in public and path in narrative
    command=['git','show',base+':'+path];proc=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert proc.returncode==0
    historical.append(dict(commit=base,path=path,SHA=hashlib.sha256(proc.stdout).hexdigest(),bytes=len(proc.stdout),actual_command=command,exit_code=0,scope='small historical claim dependency; no old performance substitution'))
assert 'round107/review/delivery_review.md' in public and 'R107 production source' in narrative and 'R100 frozen source' in narrative
assert 'multiple open relevant leaves' in narrative and 'next-leaf targets' in narrative and 'does not reopen the stopped R107' in narrative
assert 'round68' not in public or 'no performance substitution' in public
pending=dict(review_scope='source only; no pack/export/restore/narrative generation executed',public_source_SHA=sha(root/'scripts/round108_public.py'),report_source_SHA=sha(root/'scripts/round108_report.py'),new_exact_small_historical_dependencies=historical,
    historical_current_PE_source_identities_separated=True,current_multileaf_scope_and_CHILD_NEXT_counts_disclosed=True,production_performance_unchanged=True,
    final_public_receipt_claim_requires_actual_fresh_export_restore_and_independent_reconstruction=True,isolated_current_own_audit_PE_rehash_requires_a_future_metadata_only_mode_or_explicit_external_PE='Current own raw reviewer rehashes the actual local PE; the public carrier correctly forbids PE/DLL distribution. Fresh isolated math review must bind retained PE identities without consulting the original workspace and must disclose that binary bytes are not rehashed.',full_public_reproducibility_not_yet_reviewed=True)
values=[dict(id=x['id'],arm=x['arm'],U=x['U'],L=x['L'],signed_gap=x['gap'],relative_gap=x['relative_gap'],complete_seconds=x['complete_seconds'],certificate=x['certificate'],raw_status=x['raw_status']) for x in f5]
report={'decision':'ACCEPT','continuation_permitted':True,'permitted_next_complete_group':'N36','scope':'Independent current qualification plus all eighteen complete formal arms through F5; continuation admission only','actual_raw_evidence_contradictions':[],**raw['bindings'],
    'uniform_selection_admitted':False,'actual_command':launch['command'],'own_raw_source_SHA':receipt['source_SHA'],'own_raw_exit_code':0,'own_raw_engineering_seconds':receipt['engineering_elapsed_seconds'],'completed_checks':raw['completed_checks'],
    'complete_raw_audit':{'path':norm((d/'audit.json').relative_to(root)),'SHA':sha(d/'audit.json'),'bindings_field':'read_bindings','bindings_count':len(raw['read_bindings']),'no_original_root_fallback':True},
    'F5_own_endpoints':values,'F5_primary_pair':cp,'F5_ENS_contrast':ce,'severe_ENS_regression_disclosed_without_hidden_P_veto':True,
    'F5_severity_thresholds':{'P_UB':max(.001,.05*indexed['F5','P-GRB']['U']),'P_gap':max(.005,.25*abs(indexed['F5','P-GRB']['gap'])),'ENS_UB':max(.001,.05*indexed['F5','ENS-C']['U']),'ENS_gap':max(.005,.25*abs(indexed['F5','ENS-C']['gap']))},
    'all_prefix_pairs':gate['pairs'],'bridge_pass':gate['bridge_pass'],'exact_four_eligibility':{'roles':gate['exact_unseen_roles'],'denominator':4,'all_four_eligible_at_first_freeze':True,'review_SHA':sha(review/'sealed_input_eligibility.json'),'measured':gate['measured_unseen'],'WIN':2,'LOSS':0,'maximum_final_WIN':3},
    'no_severe_P':True,'no_UNEVAL':True,'early_impossibility':gate['current_positive_selection_unreachable'],'remaining_required_roles':['N36'],
    'actual_current_counts':{'qualification_arms':3,'formal_arms':18,'models':models,'native_Optimize':calls,'native_returns':calls,'Start_mapping_attempts':attempts,'Start_submitted':submitted,'Start_ineligible_outside_true_G_scope':attempts-submitted},
    'F5_scope_Starts_and_native_proofs':[{'arm':x['arm'],'cover':x['cover'],'models':x['model_contracts'],'native':x['native_records'],'Start_attempts':x['start_attempts'],'submitted_Starts':x['starts'],'fresh_plain_cold_return_bound':x['plain_returned_final_bound']} for x in f5],
    'paired_F5_actual_interval_matrices':[x for x in raw['paired_actual_interval_matrices'] if x['id']=='F5'],
    'normalization_correction':diagnosis,'normalization_finite_cases':24,'normalization_finite_receipt_SHA':sha(review/'start_normalization_finite01/receipt.json'),
    'corrected_fees':fees,'next_group_budget':{'role':'N36','order':n36['method_order'],'each_original_cap_seconds':5400,'whole_group_reserved_starts':4,'next_total_starts':46,'whole_group_reserved_seconds':16320,'paid_plus_reserve_seconds':fees['paid_outer_seconds']+reserve,'manual_corrected_budget_check_still_required':True},
    'primary_actual_reader_receipt_SHA':sha(out/'engineering/confirmation_F5_reader01/receipt.json'),'primary_table_crosscheck':{'all_21_functional_and_formal_endpoints_signed_gaps_times_exact':True,'all_12_pairs_materiality_and_severity_exact':True,'all_actual_native_calls_models_submitted_Start_identities_exact':True},
    'pending_public_source_review':pending,'reviewer_zero_solver_calls':raw['reviewer_zero_solver_calls'],'independent_reviewer_idle_after_this_record':True,'finalizer_actual_command':[sys.executable,*sys.argv],'finalizer_source_SHA':sha(Path(__file__))}
save(review/'confirmation_F5_review01.json',report)
md='ACCEPT：截至 F5 的资格三臂和全部十八正式臂已由独立 reader 重构；允许按冻结 P-GRB/ENS-C/M-B 顺序继续 N36 完整组三臂。无实际原始证据矛盾，尚未作统一 SELECT。\n\n| F5 臂 | 本臂物理 U | 原始合格 L | signed gap | 完整时间 s | 完整证书 |\n|---|---:|---:|---:|---:|---|\n'
for x in values:md+=f"| {x['arm']} | {x['U']:.17g} | {x['L']:.17g} | {x['signed_gap']:.17g} | {x['complete_seconds']:.10f} | {x['certificate']} |\n"
md+=f'''
M-B/P 是双未证绝对实质性 WIN：UB 改进 {cp['UB_improvement']:.17g}（门槛 {cp['a_U']:.17g}），gap 改进 {cp['gap_improvement']:.17g}（门槛 {cp['a_gap']:.17g}），无严重 P 退化。M-B/ENS 是 LOSS 且严重 ENS 退化：UB 恶化 {-ce['UB_improvement']:.17g}，gap 恶化 {-ce['gap_improvement']:.17g}，分别超过严重门槛 {report['F5_severity_thresholds']['ENS_UB']:.17g} / {report['F5_severity_thresholds']['ENS_gap']:.17g}。该对照必须披露，冻结协议未将 ENS 严重退化加入 P 基准取消条件。

固定四角色 S12/B24/L48/N36 仍为已测 TIE/WIN/WIN，2 WIN、0 LOSS、最大最终 WIN=3；F5 为已知压力角色。所有 P primary 有效且无 severe，F5 非 LOSS，early-impossible=false。N36 保持未测固定第四角色，全部 21 臂和最终条件完成前不能 SELECT。

自身第一次 F5 audit01 的 extra source-label assertion 是读者缺陷：原 `GurobiBaseline.cpp:634` 在映射前调用 R100 已存在且内容相同的 `normalizeRound61Routes`。等 Q 类内先按原车号升序收集，再按服务站数降序 stable sort，赋给本类升序车号，空车省略；F5 的车 2/0 交换恰符合该规则。失败 source/command/root/exit1/receipt 和 diagnosis 均保留。第二次审计对所有 source/规范化车队独立核算，再逐项核验完整 x/conn/z/mode/p/d/load/ord/Y/state/G；全行、域、readback、目标与真实 G 均仍通过。24 个有限反例覆盖等 Q 置换、stable ties、空车、跨 Q/任意置换、改变路线/操作/向量及无效车号，实际 exit0，无 native 或算法更改。

本次 raw 审计实际 explicit-root 命令、source/hash/receipt 位于 `confirmation_F5_raw_audit02`，5,837,423 checks、exit0；全前缀 {calls} 实际 Optimize/返回、{models} 模型、{submitted} submitted Start。全部新车队/UB、原始 LP/MIP 范围、父子/最终覆盖、时序与返回日志均独立重建。

纠正预算为 42 starts / 31400.737309299933 外层秒；N36 全组预留 4 starts / 16320 秒，合计 46 starts / {fees['paid_outer_seconds']+reserve:.12f} 秒，低于 48 / 80000。继续保存启动前手工补充 correction 检查。

Public/report tooling 仅做 source review：新 R98/R99/R102/R105/R106 小报告依赖可从固定 R107 delivery commit 精确取得；历史生产/PE 与当前身份、原有 multi-leaf 暴露均明确区分。未执行打包或公共恢复；最终公共 receipt 叙述须在实际 export/隔离恢复/独立重构完成后才成立。公共载体排除 PE/DLL，与当前 reviewer 的本地 PE 重哈希模式不同，之后隔离 math 模式须显式绑定历史运行 PE 身份并披露缺少二进制重哈希，禁止回读原工作树。

Reviewer 零 Optimize/LP solve/native environment/IIS/compiler，未修改生产/性能/冻结 decision。重 CPU 审查已结束，后续正式组期间保持空闲。
'''
(review/'confirmation_F5_review01.md').write_text(md,encoding='utf-8')
save(review/'confirmation_F5_finalize01_receipt.json',dict(actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=sha(Path(__file__)),exit_code=0,seconds=time.perf_counter()-tick,review_SHA=sha(review/'confirmation_F5_review01.json'),review_MD_SHA=sha(review/'confirmation_F5_review01.md'),read_bindings=reads,Optimize=0,LP_solve=0,native_environment=0,IIS=0,compiler=0))
print(json.dumps(dict(decision='ACCEPT',review_SHA=sha(review/'confirmation_F5_review01.json'),raw_audit_SHA=sha(d/'audit.json'),source_SHA=receipt['source_SHA'],raw_exit_code=0,finite_cases=24,formal_arms=18,native_calls=calls,models=models,submitted_Starts=submitted,unseen_WIN=2,unseen_LOSS=0,F5_P=cp['classification'],F5_ENS=ce['classification'],F5_severe_ENS=True,next_group='N36',next_total_starts=46,paid_outer_seconds=fees['paid_outer_seconds'],reviewer_idle=True)))
