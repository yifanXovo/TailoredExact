"""Independent sealed-first-arm check and release of the unchanged suffix."""
from pathlib import Path
import datetime, hashlib, json, time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    tick=time.perf_counter();review=OUT/'review'
    policy_path=review/'postverify_handoff_repair_admission.json';policy=read(policy_path)
    amendment_path=OUT/'plans/postverify_handoff_repair_amendment.json';amendment=read(amendment_path)
    assert policy['decision']=='ACCEPT' and sha(amendment_path)==policy['amendment_SHA']
    assert sha(ROOT/'scripts/round133_postverify_repair.py')==policy['adapter_SHA']
    for name,digest in amendment['bindings']['frozen_helpers'].items():assert sha(ROOT/name)==digest
    matrix_path=OUT/'plans/D1_matrix_frozen.json';matrix=read(matrix_path)
    assert sha(matrix_path)==amendment['matrix_SHA']['D1']
    assert sha(OUT/'plans/D3_matrix_frozen.json')==amendment['matrix_SHA']['D3']
    group=matrix['groups'][0];identity_path=OUT/group['group']/'identity.json';identity=read(identity_path)
    assert sha(identity_path)==group['identity_SHA'] and identity['launches']==[group['launch']]
    launch=group['launch'];d=Path(launch['destination'])
    attempt=OUT/'repair/postverify_handoff/D1_01_postverify_repair_01'
    binding=read(attempt/'binding.json');success=read(attempt/'success.json')
    assert binding['launch']==launch and binding['identity_SHA']==group['identity_SHA']
    assert binding['gate']['SHA']==sha(policy_path) and binding['gate']['amendment_SHA']==sha(amendment_path)
    assert binding['adapter_SHA']==policy['adapter_SHA'] and binding['reader_SHA']==policy['original_reader_SHA']
    assert success['binding_SHA']==sha(attempt/'binding.json') and success['passed']
    for name,digest in success['outputs'].items():assert sha(d/name)==digest
    assert set(success['outputs'])=={'audit.json','verification_closeout.json','arm_total_receipt.json','round133_endpoint.json'}
    producer=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json')
    assert sha(d/'producer_receipt.json')==binding['producer_receipt_SHA']==amendment['original_failure']['producer_receipt_SHA']
    assert sha(d/'producer_seal.json')==producer['producer_seal_SHA']==binding['producer_seal_SHA']==amendment['original_failure']['producer_seal_SHA']
    for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,name
    assert sha(d/'round133_verification_failure.json')==binding['old_failure_SHA']==amendment['original_failure']['SHA']
    assert sha(amendment['original_failure']['original_fee_path'])==amendment['original_failure']['original_fee_SHA']
    assert success['Optimize']==success['native_starts']==0 and success['old_failure_preserved'] and success['original_producer_seal_preserved']
    assert success['effective_adapter_H_applied'] and success['accepted_H_selection']['accepted_snapshot']=='initial.json'
    assert success['accepted_H_selection']['initial_F']==success['accepted_H_selection']['final_F']==.16038610038610038
    assert success['accepted_H_fleet']!=success['exchange_final_fleet']
    arm=read(d/'round133_endpoint.json');audit=read(d/'audit.json');close=read(d/'verification_closeout.json');total=read(d/'arm_total_receipt.json')
    assert arm['audit_SHA']==close['audit_SHA']==sha(d/'audit.json')
    assert arm['verification_closeout_SHA']==sha(d/'verification_closeout.json') and arm['arm_total_receipt_SHA']==sha(d/'arm_total_receipt.json')
    assert audit['passed'] and audit['full_H']['complete'] and audit['full_H']['seed_ids']==list(range(1,26))
    assert audit['full_H']['fleet']==success['accepted_H_fleet']
    assert audit['physical']['F']==audit['physical']['G']==audit['physical']['P']==0
    assert arm['U']==arm['L']==0 and arm['certificate'] and arm['own_exact_zero']
    assert arm['implementation_qualified'] and arm['native_proof_qualified'] and arm['performance_evidence_eligible'] and not arm['source_reduced']
    assert not audit['source_rejections'] and not audit['own_source_adjudication']['rejections']
    assert len(audit['model_contracts'])==4 and arm['native_Optimize']==4 and arm['returned_calls']==4
    assert len(audit['native_quality'])==4 and all(q['sufficient'] for q in audit['independent_source_checks']['quality'])
    claims=read(d/'native_claims.json')
    for claim in claims:
        scope=claim['scope']
        if scope['full_original'] or (scope['lower_g']<=0<=scope['upper_g'] and scope['cutoff']>=0):assert claim['value']<=1e-7
    assert arm['T_produce']==arm['T_cert']==producer['T_produce']==success['T_produce']==120.17624272953253
    assert abs(arm['T_verify']-(total['t_verified_perf']-producer['t_produce_perf']))<1e-9
    assert abs(arm['T_total']-(total['t_verified_perf']-producer['t0_perf']))<1e-9
    assert arm['T_verify']>1700 and arm['T_total']>1800,'Real postverification delay must not be reset'
    assert all(not Path(g['launch']['destination']).exists() for g in matrix['groups'][1:]),'Suffix already started before this release'
    fee_path=OUT/'fees/D1_01_postverify_repair_01/receipt.json';fee=read(fee_path)
    assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
    result=dict(schema='round133-independent-repaired-D1-continuation-admission-v1',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='/root/reliability_review',decision='ACCEPT',
        matrix_SHA=sha(matrix_path),amendment_SHA=sha(amendment_path),adapter_SHA=policy['adapter_SHA'],
        original_reader_SHA=policy['original_reader_SHA'],repair_policy_admission_SHA=sha(policy_path),
        actual_effective_binding_SHA=sha(attempt/'binding.json'),actual_effective_success_SHA=sha(attempt/'success.json'),
        actual_four_outputs=success['outputs'],raw_seal_SHA=sha(d/'producer_seal.json'),
        original_failed_postverify_SHA=binding['old_failure_SHA'],repair_fee_SHA=sha(fee_path),
        full_original_verify_after_accepted_H_selection_passed=True,all_raw_seal_hashes_independently_rechecked=True,
        original_native_Optimize=4,extra_native_Optimize=0,own_U=0.,qualified_L=0.,certificate=True,
        native_proof_qualified=True,implementation_qualified=True,source_reduced=False,
        T_produce=arm['T_produce'],T_cert=arm['T_cert'],T_verify=arm['T_verify'],T_total=arm['T_total'],
        original_failed_record_and_fee_preserved=True,actual_verification_delay_preserved=True,
        approved_suffix_positions=list(range(2,15)),approved_suffix_full_cap_sum=sum(g['launch']['cap_seconds'] for g in matrix['groups'][1:]),
        execution='Use admitted new wrapper; first arm must pass effective management gate and be skipped without Native; remaining13 keep fixed order/argv/caps',
        shared_wrapper_cost='Actual imports/admission wall is included; no time subtraction; K15 methods and both D3 versions use the same driver',
        D3_execution_admission=False,public_recovery_still_requires_actual_effective_policy=True,
        native_Optimize_by_reviewer=0,outer_review_seconds=time.perf_counter()-tick)
    target=review/'D1_postverify_continuation_admission.json';assert not target.exists()
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(decision='ACCEPT_REMAINING_13_ORIGINAL_ORDER',extra_native_Optimize=0,seconds=time.perf_counter()-tick)))
if __name__=='__main__':main()
