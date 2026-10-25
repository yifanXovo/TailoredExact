"""Independent post-public receipt comparison; no replay or deletion."""
from pathlib import Path
from fractions import Fraction as F
import datetime, hashlib, json, math, time

ROOT=Path('E:/codes/ExactEBRP-work/worktrees/round133')
OUT=ROOT/'results/unified_exact_round133'
tick=time.perf_counter()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

public=read(OUT/'public_restore_receipt.json')
assert sha(OUT/'public_restore_receipt.json')=='02245307f18d91d950eda3203591563e61d6060a5320455f08b27ffa989e77e1'
assert public['status']=='PASS' and public['science_commit']=='e4c6f82316f8697c6dfcf59d3a0807619b7bcae8'
restored=Path(public['destination']);attempt=Path(public['attempt'])
assert restored==Path('E:/codes/ExactEBRP-work/restore/round133-public-e4c6f823')
assert attempt==OUT/'review/public_recovery_attempts/attempt02'
assert sha(attempt/'receipt.json')==sha(OUT/'public_restore_receipt.json')
state=read(restored/'restore_state.json');owner=read(OUT/'review/round133_owned_public_recovery_root.json')
assert state['status']=='PASS' and state['initially_empty'] and owner['one_owned_root']
assert state['commit']==owner['science_commit']==public['science_commit']
assert state['destination']==owner['destination']==public['destination']
assert sha(restored/'restore_state.json')==sha(attempt/'restore_state.json')
assert public['initially_empty_owned_root'] and public['one_owned_root_only']
assert public['anonymous_fixed_commit_public_HTTPS'] and public['no_HEAD_Git_local_raw_or_old_checkout_fallback']
for key in ('Optimize','native_starts','compilation','vendor_DLL_load'):assert public[key]==0
assert public['files']==436
manifest=read(OUT/'export_manifest.json');carrier=read(OUT/'raw_archive_manifest.json')
assert sha(OUT/'export_manifest.json')==public['export_manifest_SHA']==sha(restored/'results/unified_exact_round133/export_manifest.json')
assert manifest['file_count']==436 and len(public['archives'])==len(carrier['archives'])==24
assert sum(row['members'] for row in public['archives'])==321003
archive_by={row['name']:row for row in carrier['archives']}
for row in public['archives']:
    expected=archive_by[row['name']]
    assert row['members']==expected['file_count'] and row['SHA256']==expected['SHA256']
    assert row['member_index_SHA256']==expected['member_index']['SHA256']
    assert row['ZIP_CRC_and_member_SHA_checked']

prior=attempt/'prior_receipt.json';admission=read(OUT/'review/public_resume_budget_admission.json')
assert sha(prior)==admission['prior_public_receipt_SHA']=='0eb655d2250b93984ea6a23c9628f1dde2109f7bf6929da1bd63457b2469a82f'
assert sha(OUT/'review/public_recovery_attempts/attempt01/receipt.json')==sha(prior)
assert sha(OUT/'review/public_recovery_attempts/attempt01/restore_state.json')==admission['prior_restore_state_SHA']
failed=read(prior);assert failed['status']=='FAILED_PRESERVE_SAME_ROOT'
assert 'finite public recovery limit exhausted' in failed['error'] and "'transport'" in failed['error']
assert not failed['failures'] and failed['destination']==public['destination']
fees=[read(OUT/'fees'/name/'receipt.json') for name in ('delivery_public_restore01','delivery_public_restore02')]
assert [r['exit_code'] for r in fees]==[1,0]
assert all(r['exit_observed'] and not r['timeout'] and r['supervisor_failure'] is None for r in fees)
assert all(r['G1_seconds']==0 and r['budget_category']=='delivery' for r in fees)
assert fees[0]['outer_seconds']==1800.2186158999102 and fees[1]['outer_seconds']==1443.7407627999783
assert not [p.name for p in (OUT/'fees').iterdir() if p.is_dir() and (p/'launch.json').exists() and not (p/'receipt.json').exists()]
binding=read(OUT/'review/public_budget_resume_execution.json');transport=read(OUT/'review/public_resume_transport_binding.json')
assert binding['admission_SHA']==sha(OUT/'review/public_resume_budget_admission.json')
assert binding['wrapper_SHA']==admission['wrapper_SHA']=='2357ead1c1a31d4b4be0ccb2055ba3db9fc7ff381e62bac0a1e416f704cd59b0'
assert binding['bootstrap_SHA']==admission['bootstrap_SHA']=='b8062780c069e252df5306d79fc5b1c22038d1adf4f0ec229cdaddc1cbca5aa8'
assert binding['resulting_public_receipt_SHA']==sha(OUT/'public_restore_receipt.json') and binding['resulting_status']=='PASS'
assert binding['only_wall_limits_changed'] and binding['same_failed_owned_root'] and binding['no_scientific_check_removed']
assert transport['both_downloaded_exact_SHA_verified_before_execution'] and transport['new_empty_roots']==0
assert transport['metadata_commit']=='c86044ddc67fb3dca199089497478f578b6a4bcf'
assert transport['published_wrapper_SHA']==binding['wrapper_SHA'] and transport['published_admission_SHA']==binding['admission_SHA']
assert state['budgets']==admission['new_limits_seconds']==dict(total=7200.,transport=6000.,semantic=3600.)
for key in ('total','transport','semantic'):assert state['cumulative_seconds'][key]<state['budgets'][key]
assert abs(public['cumulative_seconds']['total']-public['cumulative_seconds']['transport']-public['cumulative_seconds']['semantic'])<1e-5

checks=public['semantic_checks'];assert [r['name'] for r in checks]==['portable_formal22_unit1','J2_J3_exact','D24_exact_point']
for row in checks:
    assert row['return_code']==0 and sha(row['stdout'])==row['stdout_SHA'] and sha(row['stderr'])==row['stderr_SHA']
    assert Path(row['stderr']).stat().st_size==0 and row['Optimize']==row['native_compilation']==0
portable=read(attempt/'portable_formal22_unit1.stdout.log');local=read(OUT/'fees/delivery_portable_local_preflight_01/stdout.log')
assert portable==checks[0]['receipt']
assert portable['passed'] and not portable['local_preflight'] and portable['public_empty_root_recovery']
assert portable['formal_positions']==22 and portable['unit_positions']==1 and not portable['unit_in_formal_or_performance_denominator']
assert portable['original_measured_clocks_preserved']
assert len(portable['records'])==len(local['records'])==23
clock_pairs=[]
for current,previous in zip(portable['records'],local['records']):
    for key in ('arm_id','formal','full_replay','actual_policy','implementation_qualified','certificate','source_reduced','model_scope_qualified','role_performance_evidence_eligible'):
        assert current[key]==previous[key],(current['arm_id'],key)
    assert current['stored_clock']==previous['stored_clock'],current['arm_id']
    assert current['source_rewrite_binding']==previous['source_rewrite_binding']
    assert len(current['compared_outputs'])==len(previous['compared_outputs'])
    for a,b in zip(current['compared_outputs'],previous['compared_outputs']):
        assert a['name']==b['name'] and a['stored_SHA']==b['stored_SHA']
        assert a['normalized_semantics_SHA']==b['normalized_semantics_SHA'],(current['arm_id'],a['name'])
    if current['formal']:
        a=current['effective_management_receipt'];b=previous['effective_management_receipt']
        assert a['binding_SHA']==b['binding_SHA'] and a['success_SHA']==b['success_SHA'] and a['outputs']==b['outputs']
    clock_pairs.append(dict(arm_id=current['arm_id'],formal=current['formal'],all_original_measured_clock_fields_equal=True,
        all_derived_normalized_semantics_equal=True,source_reduced=current['source_reduced'],certificate=current['certificate']))
assert portable['source_publication_SHA']==local['source_publication_SHA']==sha(OUT/'source_publication.json')
for key in ('Optimize','compile','vendor_DLL_load','DLL_load','Git_calls','subprocess_calls'):assert portable[key]==0
assert portable['DLL_load_scope']=='solver/vendor only; Python runtime separately recorded'
assert portable['unit_oracle']==local['unit_oracle']

joint=read(attempt/'J2_J3_exact_receipt.json');old_joint=read(OUT/'math/exact_joint_receipt.json')
independent=read(OUT/'review/independent_joint_review_receipt_v2.json')
assert joint['status']=='PASS' and joint['cases']==old_joint['cases']
assert sha(attempt/'J2_J3_exact_receipt.json')==public['required_exact_checks']['J2_J3_SHA']
lam=F(5404319552844595,36028797018963968)
math_comparisons={}
for name,fleets,bounds in [('J2',59,284),('J3',66,298)]:
    row=joint['cases'][name];own=independent['cases'][name]
    assert row['proof_status']=='EXACT_LP_AND_IP' and row['complete_enumeration_matches'] and row['joint_fleets']==fleets==own['fleet_count']
    assert row['saved_joint_primal_check']['rows']==583 and row['saved_joint_primal_check']['bounds']==bounds
    assert row['saved_joint_primal_check']['status']=='EXACT_FEASIBLE' and not row['saved_joint_primal_check']['failures']
    assert F(row['objective_coefficient'])==F(row['exact_primal_objective'])==F(row['analytic_LP_lower_bound'])==lam
    assert F(row['exact_IP_optimum'])==F(own['IP_optimum'])==F(1,4)+lam
    assert F(row['exact_IP_optimum'])-F(row['analytic_LP_lower_bound'])==F(row['exact_gap'])==F(1,4)
    assert min(4*lam,F(1,4)+lam)==F(row['exact_IP_optimum'])
    math_comparisons[name]=dict(fleets=fleets,loaded_rows=583,bounds=bounds,LP=str(lam),IP=str(F(1,4)+lam),gap='1/4')
d24=read(attempt/'D24_exact_point_receipt.json');old_d24=read(OUT/'qualification/D24_portable_point_replay_04.json')
assert d24['status']=='PASS' and sha(attempt/'D24_exact_point_receipt.json')==public['required_exact_checks']['D24_SHA']
for key in ('physical','complete_serialized_point','naive_tight_point','native_claims_refuted','saved_loaded_numeric_fields_recompared','saved_loaded_signed_zero_only'):
    assert d24[key]==old_d24[key],key
assert d24['source_remains']=='REJECTED' and d24['Optimize']==d24['native_starts']==d24['compilation']==0
point=d24['complete_serialized_point'];assert point['exactly_feasible'] and (point['rows'],point['columns'],point['equalities'])==(22996,9391,601)
assert all(F.from_float(b)>F(point['objective']['exact'])+F.from_float(1e-7) for b in d24['native_claims_refuted'])

pub=read(OUT/'source_publication.json')
assert public['source_materialization']['candidate']['members']==110
assert public['source_materialization']['execution_helpers']['members']==89
assert public['source_materialization']['old_E3_named_source_count']==217
for row in [pub['candidate_source_bundle'],pub['execution_helpers']]:
    assert sha(restored/row['path'])==sha(ROOT/row['path'])==row['SHA']
assert sha(restored/'scripts/round133_portable_check.py')=='6024c92660aed5d78a6fade0f371cac4621bc822d74008296a5539319b93a37d'
assert not (restored/'.git').exists()

qa=read(OUT/'review/pdf_visual_QA.json');pdf=OUT/'manuscript.pdf';export=read(OUT/'pdf_export.json')
assert qa['status']=='PASS' and qa['page_count']==len(qa['pages'])==50 and qa['all_50_pages_actual_visual_QA']
assert sha(pdf)==qa['PDF_SHA']==export['PDF_SHA']=='0c43fd125d75fe36e7fae0bc62b714b807a827bf4135cdb6afa6102864aef4cc'
assert sha(OUT/'manuscript.md')==qa['manuscript_SHA']=='76d176cb883a88b64d27b43f1994d66f5dd337f9bcc579540b91b707324c93ff'
assert sha(OUT/'review/pdf_visual_QA.json')==export['visual_QA_SHA']
assert all(r['replacement_characters']==0 and not r['outside_page_characters'] for r in qa['pages'])
for row in qa['page_images']+qa['contact_sheets']:assert sha(row['path'])==row['SHA']
font_rows=[s.split() for s in qa['fonts'].splitlines()[2:] if s.strip()]
assert len(font_rows)==qa['fonts_embedded']==19
assert all(row[-5]=='yes' for row in font_rows)
assert set(p for row in qa['contact_sheets'] for p in row['pages'])==set(range(1,51))
assert qa['maintained_scientific_text_unchanged'] and qa['publication_ready_layout']
remote=read(OUT/'review/post_public_remote_independent_readback.json')
assert remote['all_12_blob_identities_passed'] and len(remote['files'])==12
assert remote['state']=='open' and remote['draft'] and not remote['merged']
assert remote['science_commit']==public['science_commit'] and remote['head_sha']==transport['metadata_commit']
assert sha(ROOT/'scripts/round133_cleanup.py')=='136a35cf99c66b380d2d1ee0a9c54279852cccf38ab284592f0a1488449f0072'
assert not (OUT/'cleanup_receipt.json').exists()

result=dict(schema='round133-independent-post-public-delivery-review-v1',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    reviewer='/root/reliability_review',primary_delivery_and_cleanup_launcher='/root',
    decision='ACCEPT_PUBLIC_RECOVERY_AND_GUARDED_CLEANUP',public_restore_receipt_SHA=sha(OUT/'public_restore_receipt.json'),
    science_commit=public['science_commit'],owned_destination=public['destination'],
    public_recovery=dict(status='PASS',files=436,archives=24,current_members=321003,
        export_manifest_SHA=public['export_manifest_SHA'],portable_stdout_SHA=checks[0]['stdout_SHA'],
        portable_formal_positions=22,unit_positions=1,unit_in_performance_denominator=False,
        J2_J3_receipt_SHA=public['required_exact_checks']['J2_J3_SHA'],D24_receipt_SHA=public['required_exact_checks']['D24_SHA'],
        source_members=[110,89],old_named_source_members=217,one_original_initially_empty_owned_root=True,
        internal_cumulative_seconds=public['cumulative_seconds'],final_state_cumulative_seconds=state['cumulative_seconds'],
        failed_outer_seconds=fees[0]['outer_seconds'],resume_outer_seconds=fees[1]['outer_seconds'],
        separately_paid_outer_sum_seconds=sum(r['outer_seconds'] for r in fees),G1_seconds=0.,
        zero_native_Optimize_compile_vendor_DLL=True,original_failed_attempt_preserved=True),
    same_root_resume=dict(admission_SHA=binding['admission_SHA'],wrapper_SHA=binding['wrapper_SHA'],bootstrap_SHA=binding['bootstrap_SHA'],
        metadata_commit=transport['metadata_commit'],anonymous_exact_bytes_before_execution=True,only_cumulative_limits_changed=True,
        original_and_resume_process_exit_observed=True,recorded_resume_and_supervisor_pids_independently_observed_absent=True,
        no_unclosed_fees=True),
    all_23_clock_and_scientific_receipt_comparisons=clock_pairs,exact_joint_comparisons=math_comparisons,
    D24=dict(rows=22996,columns=9391,equalities=601,objective=point['objective']['exact'],
        all_three_claims_refuted_beyond_original_tolerance=True,loaded_signed_zero_only=3,historical_source='REJECTED',
        internal_native_cause='UNKNOWN',no_historical_presolve_cut_tree_claim=True),
    PDF=dict(PDF_SHA=sha(pdf),QA_SHA=sha(OUT/'review/pdf_visual_QA.json'),pages=50,embedded_fonts=19,
        primary_actual_visual_inspection='/root: all prior/final pages and affected pages, recorded in immutable QA',
        independent_actual_visual_inspection='/root/reliability_review: all current 50 pages through nine final contact sheets; full-size pages 2,11,12,16,17,28,39,40,50',
        independent_visible_defects_found=[],images_and_contact_sheet_SHA_all_rechecked=True,
        scientific_source_unchanged=True,subpoint_2pt_table_warnings_no_visible_overhang=True),
    remote=dict(independent_readback_SHA=sha(OUT/'review/post_public_remote_independent_readback.json'),
        key_file_blob_identities=12,PR=remote['PR'],state='open',draft=True,merged=False,
        actual_head=remote['head_sha'],science_commit=remote['science_commit']),
    guarded_cleanup=dict(reviewed_source_SHA=sha(ROOT/'scripts/round133_cleanup.py'),
        scope='Only verified current owned recovery copies and hash-recorded reconstructible TEMP archive/PDF duplicates',
        required_before_first_delete='The cleanup source independently hashes the complete exact restored set and retained carrier pieces and resolves every deletion target inside the explicit permitted parent; it must stop on any mismatch.',
        retain='All original unique current raw, original failures, source/receipts, published pieces, PE/DLL, old rounds/worktrees and user content',
        record='Pre-delete exact plan plus actual deletion receipt and logical bytes; observed volume-space change separately',
        actual_cleanup='PENDING_PARENT_ONLY',final_delivery_review='REQUIRED_AFTER_ACTUAL_CLEANUP_AND_METADATA_PUBLICATION'),
    no_full_23_or_math_replay_repeated_by_this_review=True,no_Native_compile_public_recovery_or_deletion_by_this_review=True,
    final_delivery_acceptance=False,submission_readiness='Separate scoped manuscript-preparation judgment; not automatic journal submission or acceptance',
    Optimize=0,native_starts=0,compilation=0,metadata_comparison_seconds=time.perf_counter()-tick)
target=OUT/'review/post_public_delivery_review.json';assert not target.exists()
target.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(decision=result['decision'],receipt=str(target),SHA=sha(target),comparison_seconds=result['metadata_comparison_seconds'])))
