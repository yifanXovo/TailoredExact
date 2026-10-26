"""Independent identity/fixture gate for the explicitly amended postverifier."""
from pathlib import Path
import datetime, hashlib, json, time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    tick=time.perf_counter();plan_path=OUT/'plans/postverify_handoff_repair_amendment.json'
    assert sha(plan_path)=='7501459291ac9a7a2945f0ce022f52a72d09822df21cec7eb014889f0a8e4f6b'
    plan=read(plan_path);bindings=plan['bindings']
    assert bindings['adapter_SHA']==sha(ROOT/'scripts/round133_postverify_repair.py')=='8feae1d544d92fba843f4836f0c685c2cf38151f20386cd2538396ac34af6640'
    assert bindings['fixture_driver_SHA']==sha(ROOT/'scripts/round133_postverify_repair_tests.py')=='9cff594ba9aa6a6fbfb8cb6adddf35f9a2211c7efcddb4c924d02ab86ed96e21'
    for name,digest in bindings['frozen_helpers'].items():assert sha(ROOT/name)==digest
    assert sha(OUT/'candidate_manifest.json')==plan['candidate_manifest_SHA']
    assert sha(OUT/'candidate_build.json')==bindings['candidate_build_SHA']
    for stage,digest in plan['matrix_SHA'].items():assert sha(OUT/'plans'/f'{stage}_matrix_frozen.json')==digest
    for role,record in bindings['main_roles'].items():
        assert sha(record['path'])==record['SHA']
        assert sha(record['object_path'])==record['object_SHA']
        assert sha(record['existing_main_binding'])==record['existing_main_binding_SHA']
        assert read(record['existing_main_binding'])['source']==record['SHA']
        code=Path(record['path']).read_text(encoding='utf-8-sig')
        assert all(fragment in code for fragment in record['fragments'].values())
    fixture_path=OUT/'qualification/postverify_handoff_repair/attempt_01/receipt.json'
    fixture=read(fixture_path)
    assert fixture['passed'] and fixture['check_count']==41 and len(fixture['checks'])==41
    assert all(check['passed'] for check in fixture['checks'])
    assert fixture['bindings']==bindings and fixture['driver_SHA']==bindings['fixture_driver_SHA']
    assert fixture['Optimize']==fixture['native_starts']==0 and not fixture['original_verify_invoked']
    assert fixture['real_arm_read_only'] and fixture['synthetic_folders_are_not_producer_or_performance_evidence']
    d=Path(plan['original_failure']['path']).parent
    for name,digest in fixture['real_raw_SHA'].items():assert sha(d/name)==digest
    failure=plan['original_failure']
    assert sha(failure['path'])==failure['SHA'] and sha(failure['original_fee_path'])==failure['original_fee_SHA']
    assert sha(d/'producer_receipt.json')==failure['producer_receipt_SHA']
    assert sha(d/'producer_seal.json')==failure['producer_seal_SHA']
    assert read(d/'producer_receipt.json')['T_produce']==120.17624272953253
    assert not (d/'verification_closeout.json').exists(),'First arm must remain unqualified until repaired full audit'
    fee_path=OUT/'fees/D2_postverify_handoff_fixtures_01/receipt.json';fee=read(fee_path)
    assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
    target=OUT/'review/postverify_handoff_repair_admission.json';assert not target.exists()
    gate=dict(schema='round133-independent-accepted-H-postverify-repair-admission-v1',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='/root/reliability_review',
        primary_implementer_and_unique_meter_starter='/root',decision='ACCEPT',
        policy='ACTUAL_STRICT_CONSIDER_ACCEPTED_H_POSTSEAL_ONLY_V1',amendment_SHA=sha(plan_path),
        adapter_SHA=bindings['adapter_SHA'],fixture_driver_SHA=bindings['fixture_driver_SHA'],
        controlled_fixture_receipt_SHA=sha(fixture_path),controlled_fixture_count=41,fixture_meter_receipt_SHA=sha(fee_path),
        candidate_manifest_SHA=plan['candidate_manifest_SHA'],matrix_SHA=plan['matrix_SHA'],
        original_reader_SHA=bindings['frozen_helpers']['scripts/round133_read.py'],
        independent_reason='Original final-only H comparison conflicts with bound strict-improvement production selection; accepted endpoint is uniquely reconstructed',
        PS_original_numeric_Start_audit_retained=True,cold_P_H_fields_are_null_and_no_H_read=True,
        full_H_exchange_trace_physical_and_source_predicates_retained=True,
        original_verify_function_code_unchanged=True,postseal_only_context_with_finally_restore=True,
        management_accept_skip_and_aggregate_require_unique_effective_receipt_and_four_output_SHA=True,
        original_failure_fee_native_raw_and_T_produce_preserved=True,
        first_action='Read-only full reverify of already sealed D1_01; no native retry',
        remaining_D1_native_sequence='Wait for independent inspection of actual repaired first-arm effective receipt, then original order/caps',
        D3_execution_admission=False,
        wall_time_limit='Original producer/native argv/caps and clock expressions stay fixed; wrapper imports/admission may add paid management wall and are not subtracted',
        scope='Semantic reader correction, no numerical threshold relaxation and no arbitrary fleet match',
        public_recovery_requirement='Bind original reader plus actual adapter, accepted-H source semantics, effective receipts and explicit restored attempt root',
        native_Optimize_by_reviewer=0,compilation=0,outer_review_seconds=time.perf_counter()-tick)
    target.write_text(json.dumps(gate,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(decision='ACCEPT_POSTSEAL_REVERIFY_ONLY_FIRST',fixtures=41,Optimize=0,seconds=time.perf_counter()-tick)))
if __name__=='__main__':main()
