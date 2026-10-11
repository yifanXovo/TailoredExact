"""Sign final admission from already executed evidence and offline review only."""
from pathlib import Path
import csv, datetime, hashlib, json, sys

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round113'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    with Path(p).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
    csv.field_size_limit(67108864)
    audit=read(OUT/'review/admission04/raw_audit.json')
    candidate=read(OUT/'candidate_identity.json')
    expected='303e900baf8d6dfb6f80570a9c585aded727ef66202148df2237a900eee0ba2b'
    assert sha(OUT/'candidate_identity.json')==audit['candidate_identity_SHA']==expected
    assert not (OUT/'campaign/summary.jsonl').exists()
    assert not list((OUT/'campaign/raw').glob('*'))
    for p,h in audit['bindings'].items():assert sha(ROOT/p)==h,p
    assert candidate['offline_reader_SHA']==sha(ROOT/'scripts/read_round113.py')
    assert candidate['qualification_test_SHA']==sha(ROOT/'scripts/qualify_round113.py')
    assert candidate['qualification_post_test_SHA']==sha(ROOT/'scripts/qualify_round113_post.py')
    original_candidate=read(OUT/'engineering/pre_admission_seal02/prior_candidate_identity.json')
    assert candidate['helpers']==original_candidate['helpers']
    assert candidate['full_argv']==original_candidate['full_argv']
    assert candidate['source_bindings']==original_candidate['source_bindings']
    assert candidate['campaign_identity_SHA']==original_candidate['campaign_identity_SHA']
    summary=read(OUT/'qualification/summary.json')
    assert summary['passed'] and summary['candidate_identity_SHA']==expected and summary['no_formal_started']
    assert summary['qualification_fee']['qualification_starts']==10
    assert summary['qualification_fee']['qualification_seconds']==audit['qualification_outer_seconds_upper']
    assert summary['qualification_fee']['unclosed']==[]
    for p,h in summary['evidence_SHA'].items():assert sha(OUT/p)==h,p
    assert summary['actual_native_CLI_count']==4 and not summary['actual_native_cancellation_branch_executed']
    assert summary['driver_processes']==5 and summary['wrapper_processes']==1 and summary['native_children']==4
    assert summary['holder_processes']==summary['OS_mock_children']==0
    old=OUT/'inherited_r112';clocks=read(old/'clock_manifest.json');dep=read(old/'dependency_manifest.json')
    assert candidate['inherited_clock_manifest_SHA']==sha(old/'clock_manifest.json')
    assert len(clocks['arms'])==12 and len(clocks['files'])==146
    assert not clocks['original_clock_adjusted'] and not clocks['old_raw_reaudited'] and clocks['old_partial13_excluded']
    for p,h in dep['files'].items():assert sha(old/p)==h,p
    for p,h in clocks['files'].items():assert sha(old/p)==h,p
    historical=read(old/'review/restored_root01.json')
    historical_map={}
    for p,h in historical['bindings'].items():
        p=p.replace('\\','/')
        marker='results/unified_exact_round112/'
        if marker in p:historical_map[p.split(marker,1)[1]]=h
    inherited_signed_bindings={}
    for p,h in clocks['files'].items():
        original=p.removeprefix('authoritative/')
        if original in historical_map:
            assert historical_map[original]==h,original
            inherited_signed_bindings[p]=h
    assert len(inherited_signed_bindings)>=96
    oldrows={int(v['number']):v for v in rows(old/'reports_final/arms.csv') if v['formal_protocol_qualified']=='True'}
    assert len(oldrows)==12
    records=[]
    for retained in clocks['arms']:
        n=retained['number'];r=oldrows[n]
        w=read(old/retained['path']);a=read(old/retained['audit_path']);c=read(old/retained['completion_path'])
        native=read((old/retained['path']).parent/'native_end_receipt.json')
        post=read((old/retained['path']).parent/'postexit_audit_receipt.json')
        assert retained['original_complete_seconds']==w['complete_seconds']==float(r['complete_seconds'])<=float(r['cap_seconds'])
        assert 0<native['complete_seconds_until_native_end']<=post['complete_seconds_until_audit_end']<=w['complete_seconds']
        assert a['passed'] and c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
        assert retained['input_SHA']==r['input_SHA'] and retained['PE_SHA']==r['PE_SHA'] and retained['DLL_SHA']==r['DLL_SHA']
        assert retained['original_candidate_identity_SHA']==sha(old/'candidate_identity.json')
        assert (retained['id'],retained['arm'])==(r['id'],r['arm'])
        assert a['endpoint']['certificate']==(r['certificate']=='True')
        assert all(abs(a['endpoint'][k]-float(r[k]))<=1e-7 for k in ('U','L','gap'))
        if n==12:assert float(r['gap'])<0
        for suffix in ('whole_arm_receipt.json','result.json','audit.json','completion.json'):
            name=(old/retained['path']).parent.relative_to(old).as_posix()+'/'+suffix
            assert name in inherited_signed_bindings,name
        records.append(dict(number=n,id=r['id'],arm=r['arm'],complete_seconds=w['complete_seconds'],
            signed_U=float(r['U']),signed_L=float(r['L']),signed_gap=float(r['gap']),
            original_receipt_SHA=sha(old/retained['path']),clock_replaced_or_adjusted=False))
    assert clocks['original_R112_final_reader_SHA']==sha(old/'signed_read_round112.py')==read(old/'review/final_reader_delta01.json')['reader_SHA']
    proof_bindings=dict(audit['bindings'])
    extra=[OUT/'review/admission_audit.py',OUT/'review/admission03/failure.json',
        OUT/'review/admission04/raw_audit.json',OUT/'review/seal_admission.py',OUT/'qualification/summary.json',
        OUT/'engineering/pre_admission_seal02/receipt.json',OUT/'engineering/pre_admission_seal02/prior_candidate_identity.json',
        ROOT/'scripts/round113_pre_admission.py',old/'clock_manifest.json',old/'dependency_manifest.json']
    extra += [old/p for p in dep['files']]+[old/p for p in clocks['files']]
    for p in extra:proof_bindings[p.relative_to(ROOT).as_posix()]=sha(p)
    supplement=dict(schema='round113-independent-final-seal-supplement-v1',decision='FINAL_SEAL_AND_LIMITED_INHERITED_AUTHORITY_PASS',
        candidate_identity_SHA=expected,reader_SHA=sha(ROOT/'scripts/read_round113.py'),qualification_test_SHA=sha(ROOT/'scripts/qualify_round113.py'),
        post_test_SHA=sha(ROOT/'scripts/qualify_round113_post.py'),inherited_clock_manifest_SHA=sha(old/'clock_manifest.json'),
        inherited_files_checked=146,independently_signed_prior_byte_bindings_matched=len(inherited_signed_bindings),
        inherited12=records,old_LP_models_reparsed=0,no_original_worktree_scientific_fallback=True,
        scientific_qualification_starts_added=0,native_starts=0,Optimize=0,compiler_starts=0,
        final_performance_closure_equals_actual_CLI=True,final_argv_equals_actual_CLI_sealed_plan=True,
        final_reader_change_scope='Static inspected old12 limited result/audit/clock bindings plus reviewed 1e-7 endpoint checks and pending-own-fee boundary; no performance/helper change',
        failed_reviewer_attempt='admission03: Python tuples compared to JSON arrays; serialization normalization fixed in review code only; original failed source/receipt retained',
        bindings=proof_bindings)
    supplement_path=OUT/'review/admission04/supplement.json'
    assert not supplement_path.exists()
    supplement_path.write_text(json.dumps(supplement,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    admission=dict(schema='round113-independent-performance-admission-v1',decision='ACCEPT',
        reviewer='/root/independent_review',signed_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Exactly the eight fixed Round113 geographic arms under the admitted inherited production and new wrapper; no formal retry, default change or extra work',
        candidate_identity_SHA=expected,campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),
        production_PE_SHA=audit['production_PE_SHA'],DLL_SHA=audit['DLL_SHA'],
        measured_source_commit='d0014a7163e3996fe120471420e56b089c9715ae',production_source_bindings=206,performance_helper_bindings=42,
        production_recompiled=False,production_algorithm_or_parameters_changed=False,
        offline_reader_SHA=sha(ROOT/'scripts/read_round113.py'),qualification_test_SHA=sha(ROOT/'scripts/qualify_round113.py'),
        qualification_post_test_SHA=sha(ROOT/'scripts/qualify_round113_post.py'),
        qualification_summary_SHA=sha(OUT/'qualification/summary.json'),inherited_clock_manifest_SHA=sha(old/'clock_manifest.json'),
        inherited_dependency_manifest_SHA=sha(old/'dependency_manifest.json'),
        formal_starts_at_signature=0,formal_arms=8,formal_nominal_seconds=21600,
        formal_reserve=dict(starts=10,nominal_seconds=21600,administrative_seconds=240),
        qualification_conservative_starts=10,qualification_outer_seconds_upper=audit['qualification_outer_seconds_upper'],
        qualification_actual_native_CLI=4,qualification_actual_Optimize=12,qualification_actual_returned_Optimize=12,
        qualification_fees_all_closed=True,failed_slots_refunded=False,
        qualification_actual_H100_argv_and_whole_clocks_pass=True,qualification_H100_same_H_all25_trace_fleet_inventory_pass=True,
        P_S_full_original_matrix_column_row_Start_API_readback_pass=True,
        real_Win32_sharing_replace_failure=dict(platform=audit['actual_Windows_platform'],share_READ=True,share_WRITE=True,share_DELETE=False,errno=13,winerror=5),
        active_P_S_optional_target_fault=dict(real_campaign_target=True,holder_in_wrapper=True,extra_holder_processes=0,child_active=True,normal_return=True,
            first_failure_only=True,publication_disabled_for_arm=True,next_arm_recovered=True,authoritative_samples_and_resource_deadline_flow_preserved=True),
        source_extracted_supervisor_mock_cases=7,source_derived_legal_no_Optimize_fixture_cases=3,
        illegal_lifecycle_fixture_cases_rejected=13,pending_vs_native_activity_without_return_cases=2,
        actual_native_cancellation_branch_executed=False,
        no_Optimize_audit_preserves_already_executed_matrix_Start_parameters_but_no_native_credit=True,
        inherited_old12_clock_endpoint_pair_mapping_pass=True,inherited_old_18_pairs_preserved=True,
        inherited_old_12_missing_pair_reasons_preserved=True,inherited_partial13_endpoint_clock_certificate_rejected=True,
        prior_round112_state='BLOCKED',layer='R112_COMPLETE12_PLUS_R113_GEO8',same_role_pairs_require_same_origin_round=True,
        primary_benchmark='cold P-GRB',default_ENS_unchanged=True,M_B_unified_research_candidate_only=True,
        progress_fault_policy='One optional-publisher OSError then disable in this arm, retain necessary degradation receipt before whole; authoritative writes, caps and protection unchanged',
        signed_gap_and_original_numerical_policy_preserved=True,
        reviewer_native_starts=0,reviewer_Optimize=0,reviewer_compiler_starts=0,reviewer_qualification_driver_or_fixture_starts=0,
        reviewer_old_LP_matrices_reparsed=0,reviewer_performance_mutations=0,
        limitations=audit['limitations'][:-1]+[
            'This signature admits execution; formal geographic results, public export/restore and final research priority still require subsequent independent review.',
            'The numerical certification criterion remains the inherited 1e-7 native policy, not a rational optimality proof.',
            'The final old12 reader bindings were inspected and independently matched to signed original byte identities; this is bounded authority inheritance, not a fresh old LP/scope rebuild.',
            'Reviewer admission03 serialization-only assertion failure is preserved as offline engineering; it did not change raw, helpers, clocks or qualification.'],
        bindings={**proof_bindings,'results/unified_exact_round113/review/admission04/supplement.json':sha(supplement_path)})
    target=OUT/'review/performance_admission.json'
    assert not target.exists()
    target.write_text(json.dumps(admission,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(decision='ACCEPT',candidate_SHA=expected,admission_SHA=sha(target),formal_started=0,
        retained_signed_bytes=len(inherited_signed_bindings),qualification_starts=10,qualification_seconds=audit['qualification_outer_seconds_upper'])))

if __name__=='__main__':main()
