"""Final bounded actual-cleanup/prose corroboration; metadata-only asset checks."""
from pathlib import Path
import datetime,hashlib,ntpath,time
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt

def run():
    tick=time.perf_counter();evidence=Path('E:/codes/ExactEBRP-work/evidence/round122')
    summary_path=OUT/'cleanup_summary.json';external=evidence/'cleanup_summary.json'
    expected='72eb364e25ba35e661b12eced784980056874ab139e6dbb4fc1844562af1347c'
    assert sha(summary_path)==sha(external)==expected
    summary=read(summary_path);confirmation=read(OUT/'delivery/cleanup_execution_confirmation.json')
    source=OUT/'engineering/cleanup_round122.ps1';source_admission=read(REVIEW/'post_formal_cleanup_source_admission.json')
    assert sha(source)==source_admission['source_SHA']==confirmation['actual_executed_cleanup_source_SHA']=='0a5b406de88ec23f0efa66944a7c133c3c2ff0048ba499a06941e21cc10e4e6f'
    assert source_admission['decision']=='ACCEPT' and summary['cleanup_passed'] and confirmation['cleanup_passed']
    assert confirmation['cleanup_summary_SHA']==expected and confirmation['no_carrier_rebuild_or_second_restore']
    targets=[Path('E:/codes/ExactEBRP-work')/p for p in ['temp/round122/public-export','temp/round122/public-export-attempt01-tls','restore/round122-9ed88cf9da87','build-cache/round122-reference']]
    key=lambda p:ntpath.normcase(ntpath.normpath(str(p)))
    desired={key(p) for p in targets}
    assert len(desired)==4 and not any(p.exists() for p in targets)
    assert {key(q['path']) for q in summary['removed']}=={key(q['path']) for q in summary['candidates']}==desired
    assert len(summary['removed'])==4 and summary['failed']==[] and summary['related_processes_active']==[]
    assert all(q['no_reparse_points'] for q in summary['candidates'])
    assert sum(q['logical_bytes'] for q in summary['removed'])==summary['logical_bytes_deleted']==1784430000
    assert summary['E_free_after']-summary['E_free_before']==summary['observed_free_bytes_change']==1806864384
    assert summary['E_free_after']==216067616768 and summary['engineering_seconds']==16.3684904
    assert summary['main_and_assets_rechecked_after_cleanup'] and summary['protected_main_dirty_SHA_equal']
    assert summary['native_starts']==summary['Optimize']==0 and not summary['restore_or_export_repeated'] and not summary['carrier_rebuilt']
    assert summary['candidate_prerecord_SHA']==sha(evidence/'cleanup_candidates.json')
    candidates=read(evidence/'cleanup_candidates.json');assert {key(q['path']) for q in candidates['candidates']}==desired
    assert summary['replay_receipt_SHA']==sha(evidence/'restored_check_receipt.json')==sha(OUT/'delivery/restored_check_receipt.json')=='d5374e3af5033318bd63d2e42bf7d31ae9bc518da436a1bd47062a9f1487586d'
    assert sha(evidence/'precleanup_remote_readback.json')==sha(OUT/'delivery/precleanup_remote_readback.json')
    remote=read(evidence/'precleanup_remote_readback.json')
    assert remote['passed'] and remote['public_repository'] and remote['scienceA']==summary['scientific_commit']=='9ed88cf9da87c3ceb7aebc43694f865eacbc86a7'
    assert remote['PR']['number']==184 and remote['PR']['url']==summary['PR'] and remote['PR']['isDraft'] and remote['PR']['state']=='OPEN'
    assert remote['PR']['baseRefName']=='codex/round121-frozen-d1-confirmation'
    assert remote['PR']['headRefOid']==remote['receipt_commit_B']==confirmation['actual_source_commit']=='baf3c7e3a9fc7e263d5c7c03a69403160e030db0'
    assert remote['R121']['number']==183 and remote['R121']['headRefOid']=='65c5aaa56583bcddf9baeae7392bd94baaed9396' and remote['R121']['isDraft'] and remote['R121']['state']=='OPEN'
    assert len(remote['verified_remote_files'])==9 and all(q['actual_remote_bytes_equal'] for q in remote['verified_remote_files'])
    assert remote['carrier_finite_metadata_entries']==7 and remote['canonical_manifest_and_six_part_Git_objects_unchanged_from_public_scienceA']
    assert datetime.datetime.fromisoformat(remote['UTC'])<datetime.datetime.fromisoformat(summary['UTC'].replace('Z','+00:00'))
    # Small retained metadata only; no part/runtime/raw contents are rehashed.
    exported=read(OUT/'delivery/public_export_restore_receipt.json');parts=exported['public_HTTP_export']['fetched'][1:]
    assert len(parts)==summary['canonical_part_count']==6 and summary['retained_part_hashes_verified']
    assert summary['canonical_manifest_public_SHA']==exported['public_HTTP_export']['expected_public_manifest_SHA']=='0bc5561235ce9419452a647c7c8d1e50c735a59e956a41f344638438ea777746'
    assert (OUT/'compact_evidence/manifest.json').is_file()
    assert all((ROOT/q['path']).is_file() and (ROOT/q['path']).stat().st_size==q['bytes'] for q in parts)
    assert sum(q['bytes'] for q in parts)==176750386
    runtime=[Path('C:/Users/Administrator/.codex/worktrees/round121-frozen-d1-confirmation/ExactEBRP/build/research/round120/ExactEBRP.exe'),
        Path('D:/gurobi1302/win64/bin/gurobi130.dll'),Path('C:/Users/Administrator/.codex/worktrees/round120-native-proof-disjunction/ExactEBRP/build/research/round120/libexact_ebrp_core.a')]
    assert all(p.is_file() and p.stat().st_size>0 for p in runtime)
    assert (ROOT/'scripts/round122_reference.cpp').is_file() and (OUT/'engineering/reference_compile/launch.json').is_file()
    fixed=read(OUT/'fixed_position_status.json');assert fixed['formal_slots']==32 and fixed['all_actual_once'] and len(fixed['positions'])==32
    assert len({key(q['destination']) for q in fixed['positions']})==32
    for q in fixed['positions']:
        d=Path(q['destination']);assert d.is_dir()
        assert all((d/n).is_file() for n in ['producer_receipt.json','producer_seal.json','result.json','observations.json'])
    assert (OUT/'fees/formal08/failure.txt').is_file() and (OUT/'recovery/group08/p_sidecars/arm_total_receipt.json').is_file()
    initial=read(OUT/'initialization_receipt.json');assert summary['protected_main_HEAD']==initial['main_HEAD'] and len(initial['main_dirty_SHA'])==3
    assert all((Path('E:/codes/ExactEBRP')/p).is_file() for p in initial['main_dirty_SHA'])
    # Exact scientific prefix and previous reviewed prose stay unchanged.
    old=(OUT/'engineering/final_report_before_history_clarification.md').read_bytes()
    scientific=old.replace(b'R120 C2 Seed0 severe M-B regression is not erased by a Seed1 win.',b'R120 C2 Seed0 severe D1/M-B LOSS is not erased by a Seed1 win.')
    assert hashlib.sha256(scientific).hexdigest()==confirmation['original_scientific_report_prefix_SHA']=='84ede971c3830e003af8578541cbffc25e2931142684df11604d7eb12b8cb97e'
    report=(OUT/'final_report.md').read_bytes();assert report.startswith(scientific) and report.count(b'<!-- ROUND122_DELIVERY_START -->')==1
    assert sha(OUT/'final_report.md')==confirmation['current_final_report_SHA']
    scientific_review=read(REVIEW/'post_formal_independent.json');claims_review=read(REVIEW/'post_formal_prose_claims.json')
    for k,n in [('all32_arms_SHA','all32_arms.json'),('all48_pairs_SHA','all48_pairs.json'),('stage_decision_SHA','stage_decision.json')]:assert sha(OUT/n)==scientific_review[k]
    assert sha(OUT/'paper_result_interpretation.md')==claims_review['document_SHA']
    delivery=(OUT/'delivery_summary.md').read_text(encoding='utf-8');resume=(OUT/'RESUME.md').read_text(encoding='utf-8')
    assert all(q in delivery for q in ['BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION','M-B','ENS-C',summary['scientific_commit'],expected,'1,784,430,000','1,806,864,384','216,067,616,768','16.3684904s','not an OS sandbox','plus one local version utility'])
    assert all(q in resume for q in ['BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION','M-B','ENS-C',summary['scientific_commit'],remote['receipt_commit_B'],'1784430000','1806864384','Final completion requires that actual readback','Do not restart any producer or public recovery'])
    pack=read(OUT/'public_pack_receipt.json');assert pack['files']==62310 and pack['raw_bytes']==1455127109
    assert '1,455,127,109 raw bytes' in delivery and '176,750,386 bytes' in delivery
    result=dict(decision='ACCEPT',scope='Final bounded actual cleanup/receipt/path-absence/retained-metadata/scientific-prefix and delivery-RESUME corroboration. No future final C remote readback is certified.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),review_script_SHA=sha(__file__),
        actual_cleanup_summary_SHA=expected,external_and_working_summary_copies_byte_equal=True,
        admitted_and_actual_cleanup_source_SHA=sha(source),source_admission_review_SHA=sha(REVIEW/'post_formal_cleanup_source_admission.json'),
        execution_confirmation_SHA=sha(OUT/'delivery/cleanup_execution_confirmation.json'),
        precleanup_remote_readback_SHA=sha(evidence/'precleanup_remote_readback.json'),PR=summary['PR'],public_B=remote['receipt_commit_B'],R121_unchanged=remote['R121']['headRefOid'],
        all_four_exact_owned_targets_absent=[str(p) for p in targets],no_failed_removals=True,
        logical_bytes_deleted=summary['logical_bytes_deleted'],observed_free_bytes_change=summary['observed_free_bytes_change'],E_free_after=summary['E_free_after'],actual_cleanup_seconds=summary['engineering_seconds'],
        protected_main_HEAD_and_three_dirty_hashes_after_cleanup_attested_by_bound_successful_script_and_receipt=True,
        retained_metadata_only=dict(canonical_manifest_exists=True,six_canonical_parts_expected_sizes=True,frozen_PE_DLL_original_core_exist=True,unique_current_raw_destinations=32,original_failure_and_recovery_sidecars_exist=True,rebuild_source_and_compile_basis_exist=True),
        scientific_report_prefix_SHA=hashlib.sha256(scientific).hexdigest(),final_report_SHA=sha(OUT/'final_report.md'),frozen32_48_stage_and_interpretation_bytes_unchanged=True,
        delivery_summary_SHA=sha(OUT/'delivery_summary.md'),RESUME_SHA=sha(OUT/'RESUME.md'),actual_delivery_cleanup_claims_coherent=True,
        prior_full_scientific_review_SHA=sha(REVIEW/'post_formal_independent.json'),prior_actual_public_recovery_review_SHA=sha(REVIEW/'post_formal_public_recovery_review.json'),
        final_C_remote_readback='Explicitly pending outside the payload per RESUME; parent closes this final publication scope.',
        limits=['Retained carrier/runtime/raw checks here use existence and size metadata only; no large content rehash or recursive enumeration was repeated.',
            'Remote PR/B/R121 provenance is corroborated from the completed precleanup readback, without another network or Git request.'],
        recursive_enumerations=0,large_asset_rehashes=0,network_requests=0,Git_commands=0,native_starts=0,Optimize=0,deletions=0,
        existing_source_or_payload_member_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_cleanup_actual_review.json',result)

if __name__=='__main__':run()
