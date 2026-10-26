"""Independently bind the sealed tiny result and prospective D1 gate.

Read-only outside review/. No native import, rerun, compilation or new
mathematical search. D3 remains conditional and is not admitted here.
"""
from pathlib import Path
import csv, datetime, hashlib, json, time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):
    assert not p.exists(),'Independent frozen admission is immutable'
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    tick=time.perf_counter();review=OUT/'review';unit_dir=OUT/'qualification/small_native01'
    unit=read(unit_dir/'fixture_manifest.json');gate=read(review/'D2_small_native_admission.json')
    assert gate['decision']=='ACCEPT' and sha(unit_dir/'fixture_manifest.json')==gate['fixture_manifest_SHA']
    candidate_path=OUT/'candidate_manifest.json';assert sha(candidate_path)==gate['candidate_manifest_SHA']
    for stage in ('D1','D3'):
        p=OUT/'plans'/f'{stage}_matrix_frozen.json';assert sha(p)==gate[stage+'_matrix_SHA']
        matrix=read(p)
        for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest
        assert all(not Path(g['launch']['destination']).exists() for g in matrix['groups']),'Formal result exists before D1 admission'
    for name,digest in unit['helpers'].items():assert sha(ROOT/name)==digest
    identity=read(unit_dir/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    run=read(unit_dir/'run_receipt.json');arm=read(d/'round133_endpoint.json');analysis=read(unit_dir/'analysis.json')
    producer=read(d/'producer_receipt.json');close=read(d/'verification_closeout.json');audit=read(d/'audit.json')
    seal=read(d/'producer_seal.json');total=read(d/'arm_total_receipt.json');fee=read(OUT/'fees'/run['meter_label']/'receipt.json')
    assert sha(d/'producer_seal.json')==producer['producer_seal_SHA']
    for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,name
    assert run['fixture_manifest_SHA']==gate['fixture_manifest_SHA']
    for filename,key in [('round133_endpoint.json','endpoint_SHA'),('producer_receipt.json','producer_receipt_SHA'),('verification_closeout.json','verification_closeout_SHA')]:
        assert sha(d/filename)==run[key]
    assert arm['audit_SHA']==close['audit_SHA']==sha(d/'audit.json')
    assert arm['verification_closeout_SHA']==sha(d/'verification_closeout.json')
    assert arm['arm_total_receipt_SHA']==sha(d/'arm_total_receipt.json')
    assert close['necessary_verification_complete'] and close['implementation_qualified'] and close['evidence_complete']
    assert audit['passed'] and audit['implementation_qualified'] and not audit['controlled_legacy_model_scope_unevaluable']
    assert not audit['source_rejections'] and not audit['own_source_adjudication']['rejections']
    assert audit['full_H']['complete'] and audit['full_H']['seed_ids']==list(range(1,26))
    assert len(audit['model_contracts'])==4 and audit['Start_checks']
    assert arm['H_complete'] and arm['native_proof_qualified'] and arm['certificate']
    assert arm['U']==arm['L']==1.5 and arm['signed_gap']==0 and not arm['own_exact_zero']
    assert audit['physical']['F']==1.5 and audit['physical']['G']==.5 and audit['physical']['P']==1
    assert audit['physical']['Y'][1:]==[1,0] and audit['physical']['maximum_duration']==0
    assert analysis['passed'] and analysis['normal_positive_certificate_observed']
    assert analysis['exact_independent_original_optimum']=='3/2' and not analysis['performance_evidence_eligible']
    assert analysis['LP_calls']==3 and analysis['MIP_calls']==1 and analysis['actual_splits']==0 and not analysis['actual_target_or_NEXT_calls']
    ledger=rows(d/'external/paper_optimize_ledger.csv')
    assert [q['solve_kind'] for q in ledger]==['LP','LP','LP','MIP']
    assert all(q['native_status']=='OPTIMAL' and q['optimize_return_code']=='0' for q in ledger)
    quality=audit['native_quality'];assert len(quality)==4
    assert all(q['native_status']==2 and q['native_status_read_return_code']==0 and q['optimize_return_code']==0 and q['solution_count_read_return_code']==0 for q in quality)
    assert len(audit['independent_source_checks']['quality'])==4
    assert all(q['sufficient'] for q in audit['independent_source_checks']['quality'])
    claims=read(d/'native_claims.json')
    for claim in claims:
        scope=claim['scope']
        if scope['full_original'] or (scope['lower_g']<=.5<=scope['upper_g'] and 1.5<=scope['cutoff']):
            assert claim['value']<=1.5+1e-7
    assert producer['required_outputs_closed'] and producer['native_stopped_no_reentry']
    assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
    assert arm['T_produce']==producer['T_produce']==arm['T_cert']
    assert abs(arm['T_produce']-(producer['t_produce_perf']-producer['t0_perf']))<1e-9
    assert abs(arm['T_total']-(total['t_verified_perf']-producer['t0_perf']))<1e-9
    assert arm['T_verify']>0 and arm['T_produce']<=45
    assert not launch['formal_performance'] and not arm['formal_performance']
    spent=0.;unfinished=[]
    for folder in (OUT/'fees').iterdir():
        if not folder.is_dir() or not (folder/'launch.json').exists():continue
        if not (folder/'receipt.json').exists():unfinished.append(folder.name);continue
        receipt=read(folder/'receipt.json')
        if receipt['budget_category']=='D':spent+=receipt['G1_seconds']
    assert not unfinished,('Unresolved metered process',unfinished)
    assert spent+15600<=18000
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary=dict(schema='round133-independent-sealed-D2-unit-review-v1',UTC=now,reviewer='/root/reliability_review',
        decision='PASS_NORMAL_POSITIVE_NATIVE_CERTIFICATE_AND_COMPLETE_EVIDENCE',
        unit_manifest_SHA=gate['fixture_manifest_SHA'],analysis_SHA=sha(unit_dir/'analysis.json'),endpoint_SHA=sha(d/'round133_endpoint.json'),
        audit_SHA=sha(d/'audit.json'),producer_seal_SHA=sha(d/'producer_seal.json'),meter_receipt_SHA=sha(OUT/'fees'/run['meter_label']/'receipt.json'),
        exact_independent_optimum='3/2',own_U=1.5,qualified_L=1.5,signed_gap=0.,normal_positive_certificate=True,
        actual_native_statuses=[q['native_status'] for q in ledger],LP_calls=3,MIP_calls=1,actual_split=0,actual_target=0,
        actual_parent_and_child_LP_then_declined_split=True,complete_own_H=True,Start_models_source_and_physical_checks=True,
        seal_and_receipt_SHA_chains_independently_checked=True,clock_identity_independently_checked=True,
        endpoint_native_status_field='Legacy result.gurobi_status is0; actual native statuses come from per-call ledger/quality',
        unit_performance_membership='Excluded: formal_performance=false and independent analysis performance_evidence_eligible=false; generic reader eligibility is not sample inclusion',
        D1_and_D3_matrices_frozen_before_unit=True,postverification_did_not_feed_any_formal_start=True,
        native_Optimize_by_reviewer=0,compilation=0,outer_review_seconds=time.perf_counter()-tick)
    write(review/'D2_small_native_review.json',summary)
    write(review/'D1_admission.json',dict(schema='round133-independent-final-D1-freeze-admission-v1',UTC=now,
        reviewer='/root/reliability_review',primary_implementer_and_unique_native_launcher='/root',decision='ACCEPT',
        matrix_SHA=gate['D1_matrix_SHA'],candidate_manifest_SHA=gate['candidate_manifest_SHA'],
        source_commit='4507c3554c6544048d307168779c8757f53cc5ae',
        frozen_D3_matrix_SHA=gate['D3_matrix_SHA'],reader_SHA=gate['reader_SHA'],
        independent_matrix_check_SHA=sha(review/'frozen_matrix_identity_checks.json'),
        candidate_pre_admission_SHA=sha(review/'pre_admission.json'),
        small_native_review_SHA=sha(review/'D2_small_native_review.json'),
        source_transport_review_SHA=sha(review/'source_manifest_transport_review.json'),
        legacy_reader_admission_SHA=sha(review/'legacy_shortcut_reader_admission.json'),
        full_arm_count=14,full_arm_cap_sum_seconds=15600,current_D_spent_seconds=spent,D_limit_seconds=18000,
        own_H_and_Start=True,threads=1,serial=True,cross_arm_information=False,
        normal_qualified_open_and_explicit_source_rejection_are_distinct=True,
        no_source_threshold_relaxation_or_instance_exception=True,
        finite_qualification_not_universal_exact_native_tree_proof=True,
        approved_execution='Only frozen D1 positions with immutable helpers and actual source/build identities under the primary meter',
        D3_execution_admission=False,D3_gate='After D1 outcome, actual budget and adoption condition review; frozen matrix may not be changed',
        no_holdout_or_full_benchmark_speed_claim=True,Optimize_by_reviewer=0))
    print(json.dumps(dict(decision='ACCEPT_D1_FROZEN_14',D3_execution=False,unit='PASS',
        D_spent=spent,D1_cap=15600,Optimize=0,seconds=time.perf_counter()-tick)))

if __name__=='__main__':main()
