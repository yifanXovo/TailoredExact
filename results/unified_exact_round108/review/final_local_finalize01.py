"""Seal independent local Round108 final review after actual all-raw audit."""
import argparse, hashlib, json, sys, time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args()
root=Path(a.root).resolve();r=root/'results/unified_exact_round108/review';o=r.parent
dest=r/'final_local_finalize01';dest.mkdir(exist_ok=False)
tick=time.perf_counter();reads={}
def data(x):
    x=Path(x).resolve();assert x.is_relative_to(root)
    b=x.read_bytes();reads[x.relative_to(root).as_posix()]=hashlib.sha256(b).hexdigest();return b
def sha(x):return hashlib.sha256(data(x)).hexdigest()
def obj(x):return json.loads(data(x).decode('utf-8-sig'))
def write(x,v):
    with Path(x).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
source=sha(Path(__file__));command=[sys.executable,*sys.argv]
write(dest/'launch.json',dict(actual_command=command,explicit_read_root=str(root),source_SHA=source,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
raw=r/'confirmation_N36_raw_audit01';cross=r/'final_local_crosscheck04'
v=obj(raw/'audit.json');c=obj(cross/'crosscheck.json');f=obj(r/'final_public_mode_finite01/checks.json')
assert v['decision']==c['decision']==f['decision']=='ACCEPT'
assert c['root_selection_exact_copy_present'] and len(f['cases'])==33
assert v['reviewer_script_SHA']==sha(r/'campaign_raw_audit01.py')=='47cb299f4a8844ca668fab0117b035076f760041fb44ba6c4be0cd751af15adc'
assert c['source_SHA']==sha(r/'final_local_crosscheck01.py')
assert sha(o/'selection_decision.json')==sha(o/'reports_final/selection_decision.json')=='ab32e14d9e8dc66c73f2b9a9b49c8d07e01aea566505177027e4f55e61d933d5'
bindings={k:v['bindings'][k] for k in ['production_PE_SHA','DLL_SHA','candidate_identity_SHA','qualification_identity_SHA','development_protocol_SHA','confirmation_protocol_SHA','input_manifest_SHA','bridge_identity_SHA','confirmation_identity_SHA','performance_admission_SHA','eligibility_review_SHA','frozen_original_decision_SHA','approved_current_decision_SHA','pure_current_campaign_reader_SHA','own_parser_SHA']}
bindings.update(raw_audit_SHA=sha(raw/'audit.json'),raw_launch_SHA=sha(raw/'launch.json'),raw_receipt_SHA=sha(raw/'receipt.json'),raw_source_SHA=v['reviewer_script_SHA'],crosscheck_SHA=sha(cross/'crosscheck.json'),crosscheck_receipt_SHA=sha(cross/'receipt.json'),crosscheck_source_SHA=c['source_SHA'],root_selection_SHA=sha(o/'selection_decision.json'),final_primary_summary_SHA=sha(o/'reports_final/summary.json'),report_writer_SHA=sha(root/'scripts/round108_report.py'),public_tool_SHA=sha(root/'scripts/round108_public.py'),reproduce_at_local_review_SHA=sha(o/'reproduce.md'),delivery_preflight_receipt_SHA=sha(o/'engineering/delivery_preflight01/receipt.json'),root_selection_write_receipt_SHA=sha(o/'engineering/selection_write01/receipt.json'))
repair=dict(schema='round108-independent-final-reader-repair-review-v1',decision='ACCEPT',explicit_read_root=str(root),old_successful_source_SHA=sha(r/'public_math_reader_repair01/original_campaign_raw_audit01.py'),corrected_source_SHA=v['reviewer_script_SHA'],finite_source_SHA=sha(r/'final_public_mode_finite_audit01.py'),finite_checks_SHA=sha(r/'final_public_mode_finite01/checks.json'),finite_receipt_SHA=sha(r/'final_public_mode_finite01/receipt.json'),finite_cases=len(f['cases']),finite_actual_exit_code=0,
    changes=['Only an existing next full three-arm group receives four starts and 3*cap+120 seconds of reserve; after all21,46 paid starts reserve zero.', 'Explicit --isolated-public-math requires the actual fresh restoration receipt, absent PE and no DLL argument, reads evidence only inside required --root, and labels retained binary identity without rehash or performance rerun.', 'Independent exact21/exact-four final selection and conservative whole-arm checkpoint availability are independently computed before crosschecking the frozen pure decision source.'],
    preserved_failures=['final_local_crosscheck01: root selection had not yet been copied; preserved source/command/root/receipt, no raw contradiction.', 'final_local_crosscheck02: Windows path separator representation in the crosscheck key; preserved source/command/root/receipt; corrected metadata-only portable path key.', 'All earlier raw reader/audit failures and F5 original normalization omission remain preserved.'],
    scope='Pure independent reconstruction/accounting/output; no production, frozen performance helper, argv, PE, DLL, candidate, inputs or decision-rule changes.',isolated_public_root_actually_audited_yet=False,actual_public_review_still_required=True,Optimize=0,LP_solve=0,native_environment=0,compiler=0)
write(r/'final_reader_repair_review01.json',repair)
repairmd=f'''独立读者修正 ACCEPT。保留已成功的 b396a257… 源码，当前 standalone SHA `{v['reviewer_script_SHA']}`。

33 个有限合成案例已实际 exit0，覆盖末组零预留、原限额边界、错误前缀/余量、公共模式无 PE/DLL、原目录/外部路径拒绝、完整 21/固定四角色、P veto 与 ENS 损失非 veto、检查点偏移和结束后不外推。checks SHA `{repair['finite_checks_SHA']}`。这只证明有限条件和源码合同；真实公共恢复仍须实际执行。

本地全原始审计已按新源码实际 exit0；205 生产源、20 冻结 helpers、所有 argv/输入/PE/DLL 未变。公共模式必须显式使用 `--isolated-public-math --root <真实新恢复目录> --through N36`，不得传 DLL、读取 PE 或回读原目录；保留运行身份不等于重新核验二进制或独立性能复现。
'''
with (r/'final_reader_repair_review01.md').open('x',encoding='utf-8',newline='\n') as t:t.write(repairmd)
record=dict(schema='round108-independent-final-local-review-v1',reviewer='independent_admission',decision='ACCEPT',scientific_stage=v['selection']['stage'],explicit_read_root=str(root),bindings=bindings,
    independently_reconstructed=dict(formal_arms=21,functional_qualification_arms=3,actual_Optimize=c['actual_Optimize'],returned_Optimize=c['returned_Optimize'],saved_models=c['models'],actual_submitted_Starts=c['submitted_Starts'],mapping_attempts=c['mapping_attempts'],all_own_physical_UB_fleets=c['physical_UB_rows'],actual_checkpoints=c['checkpoints'],reliable_original_Fstar_intervals=c['reliable_original_Fstar_rows'],checkpoint_metadata_differences=c['checkpoint_event_time_metadata_differences'],production_source_bindings=c['production_source_binding_count'],frozen_performance_helpers=c['frozen_performance_helper_binding_count']),
    raw_checks_stored_before_receipt_hash_reads=v['completed_checks'],console_checks_after_two_receipt_root_guard_checks=6510519,
    check_count_explanation='audit.json seals6510517. Subsequent receipt source_SHA and audit_SHA byte reads each trigger one explicit-root read guard, so the console captures6510519. These are metadata read guards, not additional PE/native/solver checks; original audit is unchanged.',
    extra_final_crosschecks=c['completed_crosschecks'],N36=c['N36'],pairs=c['pairs'],all_disclosed_ENS_losses=c['losses'],selection=v['selection'],early_cancellation=v['gate']['current_positive_selection_unreachable'],exact_four_roles=['S12','B24','L48','N36'],four_first_freeze_eligibility=True,unseen_WIN=v['selection']['unseen_WIN'],unseen_LOSS=v['selection']['unseen_LOSS'],
    fees=dict(paid_conservative_starts=v['fees']['paid_corrected_starts'],paid_outer_seconds=v['fees']['paid_outer_seconds'],next_group=None,next_reserved_starts=0,next_reserved_seconds=0,max_starts=48,max_outer_seconds=80000,nested_seconds_added=False),
    evidence_detail=dict(raw_identity_file=str((raw/'audit.json').relative_to(root)),raw_identity_field='read_bindings',raw_identity_count=len(v['read_bindings']),source_bindings_field='bindings.source_bindings',helper_bindings_field='bindings.performance_helper_bindings',every_actual_full_argv_field='arms[*].actual_full_argv',all_native_model_type_Start_physics_and_scope_fields='qualification[*]/arms[*]',final_comparison_file=str((cross/'crosscheck.json').relative_to(root)),exact_public_recovery_pending=True),
    accepted_start_normalization=dict(source_SHA=sha(r/'start_normalization_finite_audit01.py'),checks_SHA=sha(r/'start_normalization_finite01/checks.json'),receipt_SHA=sha(r/'start_normalization_finite01/receipt.json'),cases=24,inherited_R100_function_and_original_call_site_exact=True,previous_F5_audit_reader_defect_preserved=True,full_normalized_fleet_vector_checked=True),
    finite_final_reader_repair=dict(review_SHA=sha(r/'final_reader_repair_review01.json'),cases=33,accepted=True,old_successful_source_preserved=True),
    mechanism_scope=dict(actual_counts=c['mechanisms'],complete_true_G_scopes_checked=True,all_call_cover_snapshots_chronological=True,terminal_logs_linked_exact_call_model_log_and_successful_return=True,open_leaf_discharge_only_after_complete_scope_supported=True,partial_targets_include_CHILD_and_NEXT=True,lookahead_is_not_committed_split=True,full_native_tree_identity_not_established=True,quantity_type_vs_AB_causal_contribution_not_identified=True,exact_native_first_discovery_not_observed=True,AM_mapping_callback_parts_without_independent_timers_remain_merged=True),
    scientific_limits=['Current identical frozen M-B qualifies only the prespecified candidate/resource selection for broader evaluation.', 'Fixed prospective denominator is four, with S12 TIE and B24/L48/N36 WIN; F2/C2 are seen development and F5 seen stress.', 'ENS losses F2/F5/N36 are disclosed; F5 severe ENS regression does not replace the explicit P veto.', 'Single landscape/draw combinations and known stress are not new-city independent samples or stable generalization proof.', 'No default ENS replacement, new mechanism layer, retuning, native rerun, cross-arm solver UB/Start sharing or causal native-speed attribution.'],
    report_writer_review=dict(F5_exact_inherited_normalization_disclosed=True,historical_and_current_source_PE_distinct=True,complete_whole_arm_times_used=True,public_recovery_claim_only_after_actual_receipts=True,current_source_SHA=bindings['report_writer_SHA']),
    root_selection_exact_copy_present=True,local_review_and_standalone_source_frozen_for_pack=True,public_recovery_actually_reviewed=False,independent_public_math_review_required_before_delivery=True,independent_engine_performance_rerun=False,
    reviewer_operations=dict(Optimize=0,LP_solve=0,IIS=0,native_environment=0,compiler=0,production_edits=0,frozen_performance_helper_edits=0,decision_rule_edits=0,packaging=0))
write(r/'final_local_review01.json',record)
table=['| 角色 | M-B / P | M-B / ENS | ENS severe |','|---|---|---|---|']
for role in ['F2','C2','S12','B24','L48','F5','N36']:
    pp=next(x for x in c['pairs'] if x['id']==role and x['control']=='P-GRB');ee=next(x for x in c['pairs'] if x['id']==role and x['control']=='ENS-C')
    table.append(f'| {role} | {pp["classification"]} | {ee["classification"]} | {ee["severe_regression"]} |')
nr=c['N36'];md=f'''独立最终本地审查 ACCEPT：`SELECT_MB_FOR_BROAD_EVALUATION`。全部 21 正式臂按同一冻结 M-B/生产 PE/DLL 完成，原始车队、模型、时序覆盖与证书独立重建；固定四角色 S12/B24/L48/N36 为 3 WIN、0 LOSS，S12 TIE。该选择只允许为同一候选投入更广评估，ENS 默认不变，未证明稳定泛化或论文资格完成。

{chr(10).join(table)}

P primary 六 WIN、S12 TIE，无 severe P/MIXED/UNEVALUABLE，F5 非 LOSS；early-impossible=false，取消 0。F2/F5/N36 对 ENS 的 LOSS 全部披露，F5 severe；ENS 优势未被加入隐藏 P veto。

N36 三臂均正常限时且无全局证：M-B own U `{nr['M-B']['U']}`、L `{nr['M-B']['L']}`、signed gap `{nr['M-B']['gap']}`、relative `{nr['M-B']['relative_gap']}`，完整时间 `{nr['M-B']['complete_seconds']}` 秒。P U `{nr['P-GRB']['U']}`、L `{nr['P-GRB']['L']}`；ENS U `{nr['ENS-C']['U']}`、L `{nr['ENS-C']['L']}`。比较采用真实 whole-arm 回执 `{nr['M-B']['complete_seconds']}`，legacy supervisor `{v['arms'][-1]['normal_completion']['fully_observed_end_to_end_seconds']}` 单独保留，不替代完整计时。

实际独立重建 24 端点（3 功能资格+21正式）、961 全物理 UB 车队、68 保存模型、100 Optimize/100返回、30 submitted Start（32 mapping attempts）、108 实际检查点、12 可靠 Fstar 安全发现区间。每个 UB 独立核算原输入、库存、空车出发、整数非零单方向操作、容量前缀/返回卸载和闭合行程处理时间；完整 normalized Start 的 x/conn/p/d/z/mode/load/ord/Y/state/G 按 R100 原等 Q 稳定车号归一化逐项匹配。24 个 normalization 有限案例和原函数/调用绑定通过。

原 LP/整数模型 scope、真实 G shared cap/floor 和 objective cutoff、实际 VType、逐行 A/B、完整父子/final 分割和逐时 call.cover/native/LP 来源均核验。最终 native log 仅在正确 call/model/log 的成功 return 后供证；conditional bound 使用 min(bound,cutoff)。保存 open leaf 只有在完整 scope 已有支持且排除改进 own U 后才消解。CHILD/NEXT 部分目标分别计数；lookahead 不冒充 committed split。未建立完整 native tree 身份或 p/d 与 A/B 的因果速度分解。微小 signed gap 不剪裁、不做非法百分比；检查点缺失/退出后窗口不外推，发现区间不声称精确 native first-find。

费用由关闭的外层回执和两个保留 qualification +1 修正独立求和：46/48 starts、47514.073242100014/80000 秒；嵌套 native 秒不重复添加，末组结束后 next reserve 为 0 starts/0秒。205 生产源、20 冻结 helpers、21 完整 argv、原输入与当前实际 PE/DLL 均重哈希绑定且未改。

实际 raw 命令/source/root/exit0/receipt：`confirmation_N36_raw_audit01`；source `{bindings['raw_source_SHA']}`，audit `{bindings['raw_audit_SHA']}`，101.72209049994126 工程秒。审计 JSON 在 receipt 哈希读取前封存 6,510,517 checks；receipt source/audit 的两次 root guard 后控制台 6,510,519，原审计未重写，这两项不是 native/PE 重核验。额外全表交叉 `final_local_crosscheck04` 实际 13,720 项 exit0，root/report selection SHA `{bindings['root_selection_SHA']}` 相同；全部检查点数值、状态和安全时刻精确一致。

当前报告 writer `{bindings['report_writer_SHA']}` 已核对 F5 原 normalization 读者失败、24 案例、历史/current 源码/PE区分、ENS损失、受限泛化/机制披露。交叉尝试 01 的 root selection 当时未复制、02 的 Windows 分隔符键，连同源码/命令/receipt 均保留，是交付/比较读取问题，无原始证据矛盾。

新 standalone 的末组零预留和显式隔离数学模式通过 33 个实际有限案例。公共恢复仍必须实际执行：从真实新恢复 root 使用同一 SHA 源码、`--isolated-public-math --through N36`，拒绝 PE/DLL、外部证据及原根回读；仅保留真实运行 binary identity，不声称二进制重哈希或独立性能复现。此次只接受本地科学/证据结论并冻结文件供 pack，实际公共重构和草稿 PR 交付尚未审查。

Reviewer 本轮 0 Optimize/LP solve/native environment/IIS/compiler，无生产、性能 helper 或决策规则修改，无打包。所有详细 file/hash/argv 在已绑定 raw audit 的 read_bindings 和 arms 中保留；这里不重复巨大绑定表。
'''
with (r/'final_local_review01.md').open('x',encoding='utf-8',newline='\n') as t:t.write(md)
write(dest/'receipt.json',dict(actual_command=command,explicit_read_root=str(root),source_SHA=source,exit_code=0,decision='ACCEPT',seconds=time.perf_counter()-tick,review_SHA=sha(r/'final_local_review01.json'),review_MD_SHA=sha(r/'final_local_review01.md'),repair_review_SHA=sha(r/'final_reader_repair_review01.json'),read_bindings=reads,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
print(json.dumps(dict(decision='ACCEPT',final_review_SHA=sha(r/'final_local_review01.json'),review_MD_SHA=sha(r/'final_local_review01.md'),standalone_SHA=v['reviewer_script_SHA'],stage=v['selection']['stage'],starts=v['fees']['paid_corrected_starts'],fee_seconds=v['fees']['paid_outer_seconds']),ensure_ascii=False))
