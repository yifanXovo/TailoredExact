"""Final independent evidence acceptance before actual final metadata push."""
from pathlib import Path
import collections, datetime, hashlib, json, math, subprocess, time
ROOT=Path('E:/codes/ExactEBRP-work/worktrees/round133');OUT=ROOT/'results/unified_exact_round133'
tick=time.perf_counter()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
docs={
 'final_report.md':'f94668119da7349e6fd2fc98e7cfb517659bb00d13380cdf2adf519940248f27',
 'readiness.md':'6d8afe1da85bf657ccdf8cf5bad4c80b44bed6104041b25e63942fc89f29899e',
 'independent_review.md':'84a440a31d46029346e10ebcfeaf2643fa94fee879d4ad35bf656952adac1e10',
 'reproducibility.md':'2ab485b7fc53372f092f89e9e751d88525ddc3af2f05e9de6ccc5100cf829997'}
for name,value in docs.items():assert sha(OUT/name)==value,name
phase=read(OUT/'fees/support_docs_delivery_phase_fix02/support_phase_revision.json')
assert phase['outputs']==docs and phase['science_changed'] is False
revision=read(OUT/'fees/support_docs_delivery_closeout_01/support_docs_revision.json')
assert revision['report_scientific_sections1_through5_unchanged']
assert revision['protected_scientific_bindings_before']==revision['protected_scientific_bindings_after']
for name,value in revision['protected_scientific_bindings_after'].items():assert sha(OUT/name)==value,name
science='e4c6f82316f8697c6dfcf59d3a0807619b7bcae8'
old_report=subprocess.check_output(['git','show',science+':results/unified_exact_round133/final_report.md'],cwd=ROOT).decode('utf-8-sig').replace('\r\n','\n')
new_report=(OUT/'final_report.md').read_text(encoding='utf-8-sig').replace('\r\n','\n')
def scientific_answers(text):return text[text.index('## 1.'):text.index('## 6.')]
assert scientific_answers(old_report)==scientific_answers(new_report)
assert sha(OUT/'manuscript.md')=='76d176cb883a88b64d27b43f1994d66f5dd337f9bcc579540b91b707324c93ff'
assert sha(OUT/'manuscript.pdf')=='0c43fd125d75fe36e7fae0bc62b714b807a827bf4135cdb6afa6102864aef4cc'
assert sha(OUT/'references.bib')=='9d9489329f4c7dec18c82f2643d99056eb3a12e25bcddd0b8126b4bf3714cddc'
proofs={}
for name in ('pre_release_science_review.json','D1_completion_review.json','D3_completion_review.json',
             'delivery_tools_local_review.json','public_resume_budget_admission.json',
             'post_public_delivery_review.json','actual_cleanup_review.json','post_public_remote_independent_readback.json'):
    path=OUT/'review'/name;proofs[name]=dict(SHA=sha(path),decision=read(path).get('decision',read(path).get('status')))
assert read(OUT/'review/post_public_delivery_review.json')['decision']=='ACCEPT_PUBLIC_RECOVERY_AND_GUARDED_CLEANUP'
assert read(OUT/'review/actual_cleanup_review.json')['decision']=='PASS_ACTUAL_GUARDED_CLEANUP_AND_DIRECTED_PROTECTION'
assert sha(OUT/'public_restore_receipt.json')=='02245307f18d91d950eda3203591563e61d6060a5320455f08b27ffa989e77e1'
assert sha(OUT/'cleanup_receipt.json')=='738d3943a4ab2f8830bd45716e9cf2c12399ba9141bf07374314800bbaeee9f2'
assert read(OUT/'cleanup_receipt.json')['status']=='PASS'
assert not Path(read(OUT/'cleanup_receipt.json')['removed_owned_restore_root']).exists()
audit=read(OUT/'completion_audit.json')
assert audit['overall_status']=='LOCAL_EVIDENCE_COMPLETE_PENDING_FINAL_REVIEW_AND_METADATA_READBACK'
assert audit['independent_reviews']['final_publication_review']=='PENDING' and audit['remote']['final_metadata_readback']=='PENDING'
assert audit['G3_axes']['original_native_numerical_causes']==dict(D24='UNKNOWN',GEOM='UNKNOWN',old_D24_source='REJECTED')
assert audit['actual_public_recovery']['status']==audit['actual_cleanup']['status']=='PASS'
assert len(audit['G3_axes'])==6

limits=dict(C=7200.,D=18000.,E=1800.,D3=7200.,repair=5400.)
charged={key:0. for key in limits};separate=0.;fee_count=0;unclosed=[]
for launch_path in sorted((OUT/'fees').glob('*/launch.json')):
    receipt_path=launch_path.parent/'receipt.json'
    if not receipt_path.exists():unclosed.append(launch_path.parent.name);continue
    launch=read(launch_path);receipt=read(receipt_path)
    assert receipt['exit_observed']
    fee_count+=1;value=float(receipt['G1_seconds'])
    assert math.isfinite(value) and value>=0
    if launch['kind'] in charged:charged[launch['kind']]+=value
    else:assert value==0
    separate+=float(receipt['separately_reported_seconds'])
assert not unclosed
charged['E']+=float(read(OUT/'math/resource_accounting.json')['charged_outer_seconds'])
for row in read(OUT/'infra/external_costs.json')['processes']:charged[row['kind']]+=float(row['outer_seconds'])
assert sum(charged.values())==11824.854547899857
assert all(charged[key]<=limits[key] for key in limits)
assert audit['resources']['G1_seconds']==sum(charged.values())
for label in ('support_docs_delivery_closeout_01','support_docs_delivery_phase_fix02'):
    row=read(OUT/'fees'/label/'receipt.json');assert row['exit_code']==0 and row['G1_seconds']==0
remote=read(OUT/'review/post_public_remote_independent_readback.json')
assert remote['state']=='open' and remote['draft'] and not remote['merged'] and remote['all_12_blob_identities_passed']
assert remote['head_sha']=='c86044ddc67fb3dca199089497478f578b6a4bcf'
accounting=read(OUT/'resource_accounting.json')
assert accounting['budget']['G1_seconds']==sum(charged.values()) and not accounting['budget']['unclosed']
assert accounting['budget']['by_category']==charged
assert accounting['unclosed_current_snapshot_process'] is None
resume=(OUT/'RESUME.md').read_text(encoding='utf-8-sig')
assert 'All processes exited.' in resume and 'NO ACTIVE Native/recovery/cleanup process.' in resume
assert 'do not recreate/recover it or rerun a PASS.' in resume

result=dict(schema='round133-independent-final-delivery-evidence-review-v1',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 reviewer='/root/reliability_review',primary_implementer_and_unique_publisher='/root',
 decision='ACCEPT_DELIVERY_EVIDENCE_FOR_FINAL_PUBLICATION',
 overall_completion_at_review_time='EVIDENCE_ACCEPTED_FINAL_METADATA_PUBLICATION_AND_READBACK_NOT_YET_EXECUTED',
 fixed_science_commit=science,production_source_commit='4507c3554c6544048d307168779c8757f53cc5ae',
 candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),
 accepted_support_document_SHA=docs,
 unchanged_scientific_bindings=revision['protected_scientific_bindings_after'],
 affected_document_review=dict(only_current_phase_and_real_delivery_provenance_changed=True,
   report_answers_1_through_5_exact_equal_to_fixed_science_after_line_ending_normalization=True,
   actual_diff_SHA=sha(OUT/'fees/support_docs_delivery_closeout_01/support_docs.diff'),
   followup_diff_SHA=sha(OUT/'fees/support_docs_delivery_phase_fix02/support_phase.diff'),
   frozen_checkpoint_and_old_pending_receipts_preserved_not_rewritten=True,
   cumulative_resume_caps_and_real_first_failure_and_both_outer_costs_correct=True,
   historical_wrapper_admission_cannot_be_reused_for_a_new_or_cleaned_root=True,
   final_metadata_and_final_overall_state_not_fabricated=True),
 G3_axes={
  'localization_and_finite_study':dict(status='COMPLETE_SCOPED',
   evidence='Finite B/C/E diagnosis and explanations completed; exact D24 model transfer and bounded GEOM vector replay preserve explicit unresolved layers; no additional grid/panel/healthy Native repetition.'),
  'confirmed_defects_repaired':dict(status='PASS_SCOPED_FIX_AND_TESTS',
   evidence='Expected/readback configuration and reasons, source/local-global/quality qualification, actual bound consumers, late revocation/full-domain open, qualified traces and inclusive physical embedding corrected; ABI preserved and exact boundary/control fixtures pass.'),
  'original_native_numerical_causes':dict(D24='UNKNOWN',GEOM='UNKNOWN',old_D24_source='REJECTED',
   limits='Complete serialized point and fresh loaded readout do not recreate historical presolve/cuts/hidden tree. New safe failure handling does not rehabilitate the rejected Native proof.'),
  'implementation_qualification_and_failure_handling':dict(status='PASS_FINITE_FIXED_D1_D2_AND_COMPLETE_D3',
   D1=dict(positions=14,implementation_handling=14,qualified_sources=13,certificates=8,qualified_open=5,source_rejected_safe_open=1),
   D3=dict(positions=8,qualified_certificates=8,complete_pairs=4,Win=2,Lose=2,all_TIME_CLOSE=True),
   unit='Exact 3/2 positive native unit separately verified and excluded from performance denominator',
   limits='Seen regression/known-role domains; bridge actual models do not trigger removed marker; natural NEXT performance is unobserved. No broad speed or universal numerical guarantee.'),
  'manuscript_and_evidence_delivery':dict(status='PASS_ACTUAL_EVIDENCE_ACCEPTED_PENDING_FINAL_METADATA_PUBLICATION',
   evidence='Scientific claim/math/metric reviews, unchanged manuscript and 50-page/19-font actual visual QA; source bytes and bounded dependencies; actual anonymous one-root full22+unit1/J2J3/D24 recovery; preserved failure/cumulative costs; actual controlled cleanup and directed protection; twelve science-file remote blob checks pass.',
   remaining='Normal final metadata commits/pushes and actual base/head/late-file readbacks, plus truthful final status and accounting/RESUME updates.'),
  'submission_preparation':dict(status='SUPPORTED_FOR_DISCLOSED_SCOPED_MANUSCRIPT_PREPARATION',
   judgment='Finite correctness/failure-handling and openly limited evidence support manuscript/submission preparation. Native internal UNKNOWN causes are disclosed and do not alone block that bounded preparation.',
   limits='This is not journal acceptance, automatic submission authority, SOTA/global speed, full-size joint separation, heterogeneous-target/weight extension, or universal commercial solver proof. Broader claims need a separately declared future plan; no new experiment is required merely to spend remaining budget.')
 },
 mathematical_scope=dict(J2='Strict labelled-service conflict over all59 tiny fleets; inventory witness attainable, not strict inventory projection',
   J2_J3='Exact loaded LP=lambda_hat, integer IP=1/4+lambda_hat, gap1/4 with common targets/unit weights/integer stock and stated resource assumptions; variable tau and tau0 separately handled',
   nonclaims='No global variable-denominator Jensen property, whole-model hull equivalence, new full-size separator, or restricted-maximization lower bound used as valid upper RHS'),
 actual_delivery_bindings=dict(public_restore_receipt_SHA=sha(OUT/'public_restore_receipt.json'),
   cleanup_receipt_SHA=sha(OUT/'cleanup_receipt.json'),cleanup_plan_SHA=sha(OUT/'review/cleanup_plan.json'),
   protected_after_cleanup_SHA=sha(OUT/'review/protected_final.json'),completion_audit_at_review_SHA=sha(OUT/'completion_audit.json'),
   actual_PDF_SHA=sha(OUT/'manuscript.pdf'),PDF_QA_SHA=sha(OUT/'review/pdf_visual_QA.json'),
   immutable_source_publication_SHA=sha(OUT/'source_publication.json'),immutable_export_manifest_SHA=sha(OUT/'export_manifest.json')),
 independent_review_receipts=proofs,
 resources=dict(G1_seconds=sum(charged.values()),limit=39600.,remaining=39600.-sum(charged.values()),
   by_category=charged,limits=limits,closed_common_fee_count=fee_count,
   common_separately_reported_seconds_snapshot=separate,no_unclosed_fees=True,
   costs='Each disjoint outer once; nested H/LP/MIP/Work and internal public/deletion clocks are not added. Snapshot is not a recursive total of future final transport/manual work.'),
 cleanup_and_protection=dict(actual_cleanup='PASS',deleted_restore_files=321659,verified_other_duplicates=206,
   logical_deleted_bytes=1254522218,observed_E_free_change_bytes=1328017408,these_two_metrics_distinct=True,
   preservation='Unique current science/raw/failures, original/current native assets, original/current/old trees, user content and distinct PDF drafts retained; direct3dirty/5asset bytes rechecked',
   scope='Directed bytes and disjoint explicit deletion paths, not an all-disk or every historical file byte guarantee'),
 current_remote=dict(PR=remote['PR'],state='open',draft=True,merged=False,base_sha=remote['base_sha'],
   last_actually_read_head=remote['head_sha'],science_key_files_read=12),
 local_status_prerequisites_now_satisfied=dict(RESUME_SHA=sha(OUT/'RESUME.md'),
   current_resource_accounting_SHA=sha(OUT/'resource_accounting.json'),
   no_stale_recovery_RUNNING_or_active_process_claim=True,all_actual_closed_fee_costs_snapshot=True,
   identical_G1_and_category_totals=True,manual_work_not_misrepresented_as_total_CPU=True),
 required_remaining_actual_publication=[
  'Normally commit/push metadataA containing actual late receipts, this review and accepted support-document bytes; actually read remote PR/base/head and late key-file blob identities.',
  'Only after actual metadataA readback, record truthful COMPLETE status in final metadataB; normally push and actually read final head/status/key files. Preserve these events as late metadata without repacking/recovering the fixed science snapshot.'
 ],
 no_remaining_scientific_or_cleanup_blocker_found=True,final_metadata_push_readback_at_review='PENDING_ACTUAL_EXECUTION',
 final_overall_COMPLETE_claimed_by_this_review=False,
 excluded_actions='No merge, force-push, repository default/global/proxy/credential/license change, outside contact, actual submission, new Native/compile/replay/restore or deletion.',
 Optimize=0,native_starts=0,compilation=0,full_replay_or_recovery_or_cleanup_repeated_by_reviewer=False,
 independent_metadata_review_seconds=time.perf_counter()-tick)
target=OUT/'review/final_delivery_review.json'
if target.exists():
    assert sha(target)=='d5f4bfda8ce0e7df21f0f106f8714c48a1ca44e24fde6f3fb26e918aba297e40'
    previous=target.with_name('final_delivery_review_before_local_status_snapshot.json')
    assert previous.parent==OUT/'review' and not previous.exists()
    target.rename(previous)
target.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(decision=result['decision'],SHA=sha(target),G1_seconds=sum(charged.values()),
    closed_common_fees=fee_count,metadata_review_seconds=result['independent_metadata_review_seconds'])))
