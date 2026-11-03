"""Limited delivery metadata audit: no archives/downloads/solver or qualification."""
from pathlib import Path
import datetime,gzip,hashlib,json,math,time
tick=time.perf_counter();ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round150'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
science='59c4e398f385aa8525fe87a4212ed97554f093e8';base='d33d47bb224ab3cd4eeacabc731b3fa8b16b7b2c'
remote=read(OUT/'review/delivery_PR_independent_readback.json');pr=read(OUT/'PR_readback.json')
pin=read(OUT/'publication_pin.json');carriers=read(OUT/'carrier_manifest.json')
restore=read(OUT/'public_restore_receipt.json');cleanup=read(OUT/'cleanup_record.json')
cost=read(OUT/'cost_report.json');reuse=read(OUT/'reuse_index.json')
for data in [pr,remote]:
    assert data['number']==212 and data['url']=='https://github.com/yifanXovo/TailoredExact/pull/212'
    assert data['draft'] and data['state']=='open' and not data['merged']
    assert data['base']=='codex/round149-penalty-product-feedback' and data['base_sha']==base
    assert data['head']=='codex/round150-gd-confirmation-conditional-feedback' and data['head_sha']==science
    assert data['title']=='Round150: confirm standalone GD and screen conditional penalty feedback'
assert pin['fixed_science_commit']==science and pin['original_delivery_base']==base
assert pin['production_source']=='380a85f866bffb914036190f8ee2700ce8b55978'
assert pin['executed_wrapper']=='c160cbc99d6bc32ba43a9f4c27871a77ee96b67e'
assert pin['frozen_design']=='50d01a4deae6ffe8ba2e728369ac59a458708880'
assert pin['actual_PR_base']==pr['base'] and not pin['main_contains_R149']
assert restore['PASS'] and restore['fixed_commit']==science and restore['credentials_used']==False
assert restore['TLS_verification_enabled'] and restore['only_public_bytes_and_members']
assert restore['Optimize']==restore['Native_load']==restore['compile']==0
assert restore['new_members_checked']==carriers['indexed_members']==31703
assert restore['inherited_members_checked']==15 and restore['old_inputs_checked']==len(reuse['inputs'])==2
assert len(restore['archives'])==len(carriers['archives'])==carriers['archive_count']==7
manifest={a['path']:a for a in carriers['archives']}
for item in restore['archives']:
    authority=manifest[item['path']]
    assert item['SHA256']==authority['SHA256'] and item['members_checked']==authority['member_count']
    assert '/'+science+'/' in item['url']
assert sum(a['member_count'] for a in carriers['archives'])==31703
assert sum(a['bytes'] for a in carriers['archives'])+carriers['member_index']['bytes']==carriers['compressed_bytes']==23526310
index=ROOT/carriers['member_index']['path'];assert sha(index)==carriers['member_index']['SHA256']
assert index.stat().st_size==carriers['member_index']['bytes']
indexed=json.loads(gzip.decompress(index.read_bytes()))
assert isinstance(indexed,dict) and set(indexed)==set(manifest)
assert all(len(entries)==manifest[path]['member_count'] for path,entries in indexed.items())
indexed_count=sum(map(len,indexed.values()))
assert indexed_count==31703
assert not carriers['old_large_history_duplicated'] and not carriers['commercial_binaries_or_licenses_published']
assert carriers['Optimize']==carriers['Native_load']==carriers['compile']==0
assert pr['public_recovery_receipt_SHA']==cleanup['public_acceptance_SHA']==sha(OUT/'public_restore_receipt.json')
assert cleanup['PR_readback_SHA']==sha(OUT/'PR_readback.json')
assert not cleanup['deleted_paths'] and cleanup['deleted_logical_bytes']==0
assert cleanup['free_bytes_before']==cleanup['free_bytes_after'] and cleanup['observed_volume_delta']==0
assert cleanup['bounded_current_round_only'] and not cleanup['old_rounds_deleted'] and not cleanup['original_user_tree_modified']
assert all(Path(v['path']).exists() for v in cleanup['retained']+cleanup['retained_runtime_files'])
receipts=[read(path) for path in (OUT/'fees').glob('*/receipt.json')]
external=read(OUT/'infra/external_costs.json')['processes']
total=math.fsum(v['G1_seconds'] for v in receipts)+math.fsum(v['outer_seconds'] for v in external)
assert abs(total-cost['charged_new_experiment_seconds'])<1e-8
assert abs(total-5560.241266800073)<1e-8 and abs(total-5543.6389105000735-16.6023563)<1e-8
assert cost['ceiling_seconds']==14400 and total<14400 and not cost['experiment']['unclosed']
assert cost['build_seconds']==cost['baseline_Optimize_new']==cost['extra_quality_Optimize']==0
assert cost['standalone_LP_Optimize']==3 and cost['complete_Native_Optimize']==cost['complete_Native_returned']==19
history=OUT/'review/history';defect=read(history/'initial_helper_defect_preservation.json')
assert sha(history/defect['initial_source'])==defect['initial_source_SHA256']=='c781ff05e8431ab31f9f5cd8d1ca41df09b49bbb74d6f94477fab0d19bbb11ae'
assert sha(history/defect['original_stdout_file'])==defect['original_stdout_SHA256']
assert defect['initial_process_exit_code']==0 and defect['actual_original_error_message'] is None
assert not defect['old_helper_executed_again']
assert 'initially incomplete' in next(v['basis'] for v in external if v['label']=='independent_final_scientific_review')
review=read(OUT/'review/final_scientific_review.json');binding_state={name:sha(OUT/name)==digest for name,digest in review['bindings'].items()}
assert all(binding_state.values()),binding_state
files=['PR_readback.json','publication_pin.json','carrier_manifest.json','public_restore_receipt.json','cleanup_record.json','cost_report.json']
value=dict(PASS=True,independent_nonimplementer_review=True,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='One read-only GitHub PR metadata observation and bounded local receipt/index/hash/ledger checks only',
    fixed_science=science,observed_Draft_PR=remote['url'],observed_base=remote['base'],observed_base_SHA=base,
    observed_head=remote['head'],observed_head_SHA=remote['head_sha'],observed_open=True,observed_draft=True,observed_merged=False,
    metadata_SHAs={name:sha(OUT/name) for name in files},science_review_bindings_unchanged=binding_state,
    public_receipt=dict(PASS=True,archive_count=7,new_members=31703,inherited_members=15,original_inputs=2,
        public_recovery_seconds=restore['seconds'],public_recovery_reexecuted=False,
        SHA_and_count_match_carriers=True,member_index_SHA_verified=True,archive_bytes_rehashed=False,
        compressed_bytes_include_member_index=True),
    cost=dict(charged_new_experiment_seconds=total,ceiling_seconds=14400,
        final_review_added_once=16.6023563,pure_delivery_IO_not_added_to_science=True),
    cleanup=dict(zero_deletion=True,retained_runtime_and_evidence_paths_exist=True,observed_volume_delta=0,
        no_old_or_user_deletion=True),
    initial_helper_undercheck_history_preserved=True,initial_helper_was_successful_exit_not_fabricated_failure=True,
    no_download=True,no_archive_open=True,no_full_matrix_or_qualification_repeated=True,Native_load=0,Optimize=0,compile=0,
    final_metadata_commit_push_pending=True,final_delivery_head_readback_still_required=True,
    no_more_scientific_work_required=True,material_issues=[],
    prior_measured_delivery_IO_seconds=remote['metadata_tool_wall_seconds']+.2491909+.2240659,
    metadata_check_script_seconds=time.perf_counter()-tick,
    timing_boundary='Pure delivery I/O, separate from the fixed experimental outer ledger; nested index/check timings are not added twice.')
(OUT/'review/delivery_metadata_review.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(PASS=True,pure_delivery_IO=True,seconds=time.perf_counter()-tick)))
