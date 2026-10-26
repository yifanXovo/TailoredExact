"""Seal actual independent public recovery review; evidence reads stay fresh."""
import argparse, csv, hashlib, json, sys, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root).resolve()
out=root/'results/unified_exact_round108';review=out/'review';dest=review/'public_isolated_finalize01';dest.mkdir(exist_ok=False);tick=time.perf_counter();reads={}
def data(path):
    path=Path(path).resolve();assert path.is_relative_to(root),'no original/external root fallback'
    b=path.read_bytes();reads[path.relative_to(root).as_posix()]=hashlib.sha256(b).hexdigest();return b
def sha(path):return hashlib.sha256(data(path)).hexdigest()
def obj(path):return json.loads(data(path).decode('utf-8-sig'))
def table(path):return list(csv.DictReader(data(path).decode('utf-8-sig').splitlines()))
def write(path,v):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
source=sha(Path(__file__));command=[sys.executable,*sys.argv]
write(dest/'launch.json',dict(actual_command=command,cwd=str(Path.cwd()),explicit_read_root=str(root),source_SHA=source,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
v=obj(review/'public_isolated_raw_audit01/audit.json');vr=obj(review/'public_isolated_raw_audit01/receipt.json');vl=obj(review/'public_isolated_raw_audit01/launch.json')
c=obj(review/'public_isolated_crosscheck01/crosscheck.json');cr=obj(review/'public_isolated_crosscheck01/receipt.json')
assert v['decision']==c['decision']=='ACCEPT' and vr['exit_code']==cr['exit_code']==0
assert vl['isolated_public_math'] and vl['explicit_read_root']==str(root) and vl['cwd']==str(root) and '--dll' not in vl['command']
assert sha(review/'campaign_raw_audit01.py')==v['reviewer_script_SHA']=='47cb299f4a8844ca668fab0117b035076f760041fb44ba6c4be0cd751af15adc'
assert c['source_SHA']==sha(review/'public_isolated_crosscheck01.py')
assert v['bindings']['isolated_public_math'] and all(Path(k).resolve().is_relative_to(root) for k in v['read_bindings'])
binary=v['bindings']['binary_identity'];assert binary['retained_actual_run_identity_only'] and not binary['PE_bytes_rehashed'] and not binary['DLL_bytes_rehashed']
assert not (root/'build/research/round108-frozen-mb-v1/ExactEBRP.exe').exists()
rr=obj(root/'restore_receipt.json');meta=review/'public_primary_comparison_metadata01'
assert rr==obj(meta/'public_restore_receipt.json') and sha(root/'restore_receipt.json')=='c74f401c7408df8abe8e3a0e27962a3337d2e23148e777879ad13dd51b8d2b7b'
assert rr['exit_code']==0 and rr['public_files_only'] and not rr['original_workspace_reads'] and Path(rr['restored_root']).resolve()==root
manifest=obj(meta/'public_manifest.json');export=obj(meta/'public_export_receipt.json')
assert sha(meta/'public_manifest.json')==rr['manifest_SHA']=='214bdc55cb827d7189e73525b5a954c8fd7a3ad2bdae985542a58e8e9e455cbb'
assert manifest['archive_sha256']==rr['archive_SHA']=='9ae11d97e81f9434b7ac438fe32d61341e8712ea6e1d6699b7030fa0b0f347d8'
assert manifest['archive_bytes']==rr['archive_bytes']==155012329 and len(manifest['parts'])==rr['exact_part_count']==2 and len(manifest['files'])==rr['files']==79898
assert manifest['restore_source_SHA']==rr['restorer_SHA']==sha(root/'scripts/round108_public.py')=='c35f285d76dbfba1ca16e4d73bd670de603b868337095b563eeda3e0f5786ce3'
assert export['exit_code']==0 and export['only_proposed_public_files_and_explicit_public_dependencies'] and export['archive_SHA']==rr['archive_SHA']
assert len(manifest['public_dependencies'])==15
for dep in manifest['public_dependencies']:
    path=root/dep['path'];assert path.resolve().is_relative_to(root)
    assert sha(path)==dep['sha256'] and path.stat().st_size==dep['bytes']
members={q['path']:q for q in manifest['files']};assert len(members)==79898
for name,digest in v['bindings']['source_bindings'].items():assert members[name]['sha256']==digest
for name,digest in v['bindings']['performance_helper_bindings'].items():assert members[name]['sha256']==digest
assert members['results/unified_exact_round108/review/campaign_raw_audit01.py']['sha256']==v['reviewer_script_SHA']
pc=obj(meta/'public_comparison_receipt.json');wrapper=obj(meta/'public_rebuild_wrapper_receipt.json')
assert sha(meta/'public_comparison_receipt.json')=='5addfd63ad1ab35309af334c6fdd7f405fa236f76d60cd56c8bbb18b620db682'
assert pc['exit_code']==wrapper['exit_code']==0 and Path(pc['read_root']).resolve()==root and Path(pc['rebuilt_root']).resolve()==root/'rebuilt'
assert pc['cwd']==str(root) and pc['source_SHA']==sha(root/'scripts/round108_reader.py')==v['bindings']['pure_current_campaign_reader_SHA']
assert pc['wrapper_receipt_SHA']==sha(meta/'public_rebuild_wrapper_receipt.json') and pc['launch_SHA']==sha(meta/'public_rebuild_launch.json')
assert pc['stdout_SHA']==sha(meta/'public_rebuild_stdout.log') and pc['stderr_SHA']==sha(meta/'public_rebuild_stderr.log')
stdout=data(meta/'public_rebuild_stdout.log').decode('utf-8-sig').splitlines();assert json.loads(stdout[-1])==pc['comparison']
assert pc['public_files_only'] and not pc['original_workspace_payload_reads'] and not pc['independent_engine_performance_rerun']

# Independently reread every published/rebuilt field, not only comparison flags.
expected=out/'reports_final';rebuilt=root/'rebuilt';fields=0;csvnames=sorted(x.name for x in expected.glob('*.csv'))
assert csvnames==sorted(x.name for x in rebuilt.glob('*.csv'))==sorted(pc['csv_files']) and len(csvnames)==30
for name in csvnames:
    left=table(expected/name);right=table(rebuilt/name);assert len(left)==len(right),name
    for index,(x,y) in enumerate(zip(left,right),1):assert x==y,(name,index);fields+=len(x)
jsonnames=sorted(x.name for x in expected.glob('*.json'))
assert jsonnames==sorted(x.name for x in rebuilt.glob('*.json'))==sorted(pc['comparison']['exact_JSON_files_compared'])
for name in jsonnames:assert obj(expected/name)==obj(rebuilt/name),name
assert fields==pc['comparison']['exact_csv_fields_compared']==1313668
assert obj(out/'admission_decision.json')==obj(rebuilt/'admission_decision.json') and obj(out/'selection_decision.json')==obj(rebuilt/'selection_decision.json')
assert v['selection']['stage']==c['final_stage']=='SELECT_MB_FOR_BROAD_EVALUATION' and v['selection']['unseen_WIN']==3 and v['selection']['unseen_LOSS']==0
assert v['fees']['paid_corrected_starts']==46 and v['fees']['paid_outer_seconds']==47514.073242100014 and v['fees']['next_complete_group'] is None
record=dict(schema='round108-independent-actual-isolated-public-review-v1',reviewer='independent_admission',decision='ACCEPT',stage=v['selection']['stage'],actual_public_recovery_reviewed=True,actual_public_math_reconstruction_reviewed=True,
    public_root=rr['public_root'],actual_read_root=str(root),actual_cwd=vl['cwd'],standalone_source_SHA=v['reviewer_script_SHA'],actual_standalone_command=vl['command'],actual_standalone_exit_code=vr['exit_code'],actual_standalone_engineering_seconds=vr['engineering_elapsed_seconds'],
    raw_audit_SHA=sha(review/'public_isolated_raw_audit01/audit.json'),raw_receipt_SHA=sha(review/'public_isolated_raw_audit01/receipt.json'),raw_launch_SHA=sha(review/'public_isolated_raw_audit01/launch.json'),raw_checks_at_audit_seal=v['completed_checks'],console_checks_after_two_receipt_hash_root_guards=v['completed_checks']+2,
    count_explanation='Source/audit SHA reads for receipt each add one explicit-root guard after raw audit serialization; stored raw audit is unchanged.',
    actual_crosscheck_command=cr['actual_command'],crosscheck_source_SHA=c['source_SHA'],crosscheck_checks=c['completed_crosschecks'],crosscheck_SHA=sha(review/'public_isolated_crosscheck01/crosscheck.json'),crosscheck_receipt_SHA=sha(review/'public_isolated_crosscheck01/receipt.json'),crosscheck_exit_code=cr['exit_code'],crosscheck_engineering_seconds=cr['seconds'],
    production_source_bindings=len(v['bindings']['source_bindings']),frozen_helpers=len(v['bindings']['performance_helper_bindings']),original_workspace_evidence_reads=False,external_evidence_fallback=False,all_independent_raw_read_paths_in_recovered_root=True,actual_independent_raw_read_binding_count=len(v['read_bindings']),raw_identity_details='public_isolated_raw_audit01/audit.json read_bindings and bindings; no huge maps duplicated here',
    retained_run_binary_identity=binary,PE_available=False,PE_bytes_read=False,DLL_bytes_read=False,independent_engine_performance_rerun=False,
    mathematical_evidence=dict(formal_arms=21,functional_qualification_arms=3,own_full_physical_UB_fleets=c['physical_UB_rows'],saved_models=c['models'],actual_recorded_Optimize=c['actual_Optimize'],actual_recorded_Optimize_returned=c['returned_Optimize'],actual_submitted_Starts=c['submitted_Starts'],mapping_attempts=c['mapping_attempts'],actual_checkpoints=c['checkpoints'],reliable_original_Fstar_safe_intervals=c['reliable_original_Fstar_rows'],all_final_pair_comparisons=len(c['pairs']),complete_physics_inventory_prefix_and_closed_duration=True,all_native_types_and_exact_AB=True,full_normalized_Start_vectors=True,chronological_model_leaf_call_log_return_bound_cover_provenance=True,complete_partition_and_certificate_qualification=True,signed_gaps_not_clipped=True,no_false_percentages_or_endpoint_extrapolation=True),
    pairs=c['pairs'],N36=c['N36'],ENS_losses=c['losses'],all_disclosed_P_primary_evaluable=True,no_severe_P=True,F5_primary_nonLOSS=True,exact_four_roles=['S12','B24','L48','N36'],all_four_eligible_at_first_freeze=True,unseen_WIN=3,unseen_LOSS=0,unseen_TIE=1,cancelled_arms=[],early_cancellation=v['gate']['current_positive_selection_unreachable'],fees=dict(starts=46,outer_seconds=47514.073242100014,next_reserved_starts=0,next_reserved_seconds=0,nested_seconds_added=False),
    actual_carrier=dict(combined_compressed_bytes=manifest['archive_bytes'],combined_SHA=rr['archive_SHA'],manifest_SHA=rr['manifest_SHA'],plain_members=len(manifest['files']),parts=manifest['parts'],historical_public_dependencies=len(manifest['public_dependencies']),all15_dependency_bytes_rehashed_in_fresh_root=True,exact_public_script_source_bound=True,restore_receipt_SHA=sha(root/'restore_receipt.json')),
    primary_actual_rebuild=dict(command=pc['command'],read_root=pc['read_root'],source_SHA=pc['source_SHA'],exit_code=0,engineering_seconds=pc['seconds'],comparison_receipt_SHA=sha(meta/'public_comparison_receipt.json'),csv_files=30,exact_csv_fields=fields,exact_JSON_files=jsonnames,root_admission_selection_equal=True,independent_final_field_reread_also_passed=True),
    bindings={k:v['bindings'][k] for k in ['candidate_identity_SHA','qualification_identity_SHA','development_protocol_SHA','confirmation_protocol_SHA','input_manifest_SHA','bridge_identity_SHA','confirmation_identity_SHA','performance_admission_SHA','eligibility_review_SHA','frozen_original_decision_SHA','approved_current_decision_SHA','pure_current_campaign_reader_SHA','own_parser_SHA']},
    report_writer_SHA=sha(root/'scripts/round108_report.py'),published_metadata_copy_provenance_SHA=sha(review/'public_isolated_copy_public_metadata01/receipt.json'),
    scope_limits=['Evidence and mathematical reconstruction only; native binary identities are retained actual-run records without public binary rehash.', 'Selection is for broader prospective evaluation of this exact frozen candidate; ENS default unchanged and broad stability/paper qualification not proved.', 'Known F2/C2 bridges/F5 stress and four landscape combinations are not21 independent new samples or new cities.', 'ENS losses F2/F5/N36 including severe F5 are disclosed, without hidden P veto.', 'No full native tree identity, p/d versus A/B causal speed attribution, exact first native witness times or additional mechanism exploration.'],
    unchanged_public_carrier_members=True,new_files_public_supplements_only=True,public_export_manifest_metadata_only_read_from_proposed_public_directory=True,reviewer_operations=dict(Optimize=0,LP_solve=0,IIS=0,native_environment=0,compiler=0,production_edits=0,frozen_helper_edits=0,decision_rule_edits=0,native_performance_reruns=0))
write(review/'public_isolated_review01.json',record)
md=f'''实际公共隔离复核 ACCEPT：`SELECT_MB_FOR_BROAD_EVALUATION`。读取根和实际 CWD 均为 `{root}`；standalone `{v['reviewer_script_SHA']}` 从恢复根实际执行 `--through N36 --isolated-public-math`，无 DLL 参数、PE读取、native加载或原工作目录回退，exit0，{vr['engineering_elapsed_seconds']:.9f} 工程秒。这是证据/数学重建，不是独立引擎性能重跑；PE/DLL身份仅绑定已资格核验的实际运行记录。

原始审计 `{record['raw_audit_SHA']}` 在 serialize 时封存 {v['completed_checks']:,} checks；receipt的source/audit两次root guard后控制台 {v['completed_checks']+2:,}，原审计未重写。公开原始audit/command/source/receipt和全部timeline/cover输出保留。独立额外交叉源 `{c['source_SHA']}` 实际 {c['completed_crosschecks']:,} checks、exit0、{cr['seconds']:.9f} 秒；每个原始证据读取路径均实际在恢复根内。

实际重建 21正式+3功能资格、961完整物理UB、68模型、100实际Optimize/100返回记录、30 submitted Start（32mapping attempts）、108检查点、12可靠Fstar安全发现区间、14 pairs。全库存/空车出发/整数单方向服务/容量前缀/返回卸载/闭合时间，以及原生VType/A-B、R100等Q stable normalization完整Start、真实G/cutoff范围、所有call/model/log/return和逐时全覆盖证书均独立核验。Signed gap保留，未用数值闭合单独替代证书；缺失窗口与精确native发现时间不外推。

P primary 六WIN/S12TIE，无severe P、MIXED或UNEVALUABLE；固定S12/B24/L48/N36为TIE/WIN/WIN/WIN，3WIN/0LOSS、分母4、取消0。ENS LOSS为F2/F5/N36，F5 severe且不是隐藏P veto。N36 M-B own U={c['N36']['M-B']['U']}、L={c['N36']['M-B']['L']}、gap={c['N36']['M-B']['gap']}，whole={c['N36']['M-B']['complete_seconds']}秒，无证。费用46starts/47514.073242100014外层秒，末组0预留、嵌套秒不重复加。

真实公开载体combined155,012,329字节、SHA `{rr['archive_SHA']}`，manifest `{rr['manifest_SHA']}`，79,898 plain成员、2连续精确压缩字节parts，15个明确历史依赖均在恢复根独立重哈希。实际restorer `{rr['restorer_SHA']}` 回执 `{record['actual_carrier']['restore_receipt_SHA']}` 与公开精确副本一致。分片的原超限失败与边界反例/修正49个有限案例保留，未改载体成员。

主读者从同一真实恢复根实际重建，exit0、{pc['seconds']:.9f} 工程秒，30CSV的1,313,668字段及4个决定/summary JSON所有值/file sets精确相等，rootadmission/selection相等；真实comparison receipt `{record['primary_actual_rebuild']['comparison_receipt_SHA']}` 和stdout/wrapper/source绑定核验通过。本独立finalseal又直接从fresh reports/rebuilt逐字段读取全部CSV/JSON，数目与值均再次相等，没有只复制summary。

205生产源、20冻结helpers、全部argv/输入和source/PE/DLL运行身份同封存候选。当前报告源 `{record['report_writer_SHA']}` 与精确公开restorer/reader匹配。新增本次raw/crosscheck/review/receipt是公开补充，不重写原封存本地审查或压缩载体；应完整stage公开audit（约29MiB）及源/命令/回执，无需再次打包。

本结论接受真实公共恢复和数学/证据选择。ENS默认不变；更广泛稳定性、论文资格、完整native树身份、数量域与A/B的因果速度分解、精确native first-find仍未证明。Reviewer 0 solver/LP solve/native environment/IIS/compiler，不新增实验。新draft PR及remote字节核验由交付代理继续执行。
'''
with (review/'public_isolated_review01.md').open('x',encoding='utf-8',newline='\n') as f:f.write(md)
write(dest/'receipt.json',dict(actual_command=command,cwd=str(Path.cwd()),explicit_read_root=str(root),source_SHA=source,exit_code=0,decision='ACCEPT',seconds=time.perf_counter()-tick,review_SHA=sha(review/'public_isolated_review01.json'),review_MD_SHA=sha(review/'public_isolated_review01.md'),independently_compared_csv_fields=fields,read_bindings=reads,original_workspace_reads=False,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
print(json.dumps(dict(decision='ACCEPT',review_SHA=sha(review/'public_isolated_review01.json'),audit_SHA=record['raw_audit_SHA'],raw_checks=v['completed_checks'],crosschecks=c['completed_crosschecks'],all_csv_fields=fields,stage=v['selection']['stage']),ensure_ascii=False))
