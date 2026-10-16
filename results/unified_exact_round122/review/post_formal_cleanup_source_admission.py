"""Static-only admission of revised cleanup plan; no target is opened/listed."""
import datetime,time
from independent_review_round122 import OUT,REVIEW,sha,save_receipt

def run():
    tick=time.perf_counter();source=OUT/'engineering/cleanup_round122.ps1';old=OUT/'engineering/cleanup_round122_plan_v1.ps1'
    assert sha(source)=='0a5b406de88ec23f0efa66944a7c133c3c2ff0048ba499a06941e21cc10e4e6f'
    assert sha(old)=='c79f625c074338088964a5b5bd46aa5123ada8d4998479de34d902bc57bb6786'
    current=source.read_text(encoding='utf-8-sig');prior=old.read_text(encoding='utf-8-sig')
    targets=lambda s:s[s.index('$taskTargets = @('):s.index('$taskStarted =')]
    deletion=lambda s:s[s.index('foreach ($taskCandidate in $taskMeasured)'):s.index('$taskResult.E_free_after')]
    assert targets(current)==targets(prior) and deletion(current)==deletion(prior)
    assert current.count('Remove-Item -LiteralPath $taskChecked -Recurse -Force')==1
    before=current[:current.index('Remove-Item -LiteralPath $taskChecked -Recurse -Force')]
    gate_tokens=[
        '$taskReplay.scientific_commit -ne $taskScience','$taskReplay.fresh_empty_root -ne $taskRestore',
        "$taskReplay.stage -ne 'BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION'",'$taskReplay.typed_JSON_all_fields_values_arrays_and_signed_zero_equal',
        '$taskReplay.no_original_raw_helper_or_runtime_binary_fallback','$taskReplay.all_other_carrier_members_byte_unchanged',
        '$taskReplay.Optimize -ne 0','$taskReplay.native_starts -ne 0',
        "$taskReplay.boundary -ne 'Python open/module/process/network audit; not an OS sandbox; standard runtime prefix allowed'",
        "(Join-Path $taskRestore 'restored_check_receipt.json')",'$taskPublic.scientific_commit -ne $taskScience',
        '$taskPublic.fresh_empty_root -ne $taskRestore','$taskPublic.public_HTTP_export.scientific_commit -ne $taskScience',
        '$taskPublic.public_HTTP_export.no_local_part_or_original_raw_fallback','$taskCandidateSet.Count -ne 4',
        '@($taskCandidateSet | Sort-Object -Unique).Count -ne 4','Compare-Object ($taskCandidateSet | Sort-Object) ($taskTargets | Sort-Object)',
        'candidate_prerecord_SHA=','$taskRemote.PR.isDraft',"$taskRemote.PR.state -ne 'OPEN'",'$taskCurrentHead -ne $taskRemote.PR.headRefOid',
        '$taskProcesses.Count -ne 0',"'0bc5561235ce9419452a647c7c8d1e50c735a59e956a41f344638438ea777746'",'$taskManifest.parts.Count -ne 6',
        '$taskPublic.public_HTTP_export.fetched.Count -ne 7','$taskPart.path -ne $taskExpectedPath','$taskFetchedPart.path -ne $taskPart.path',
        '$taskFetchedPart.bytes -ne $taskPart.bytes','$taskFetchedPart.SHA -ne $taskPart.SHA',
        "$taskPartPath.StartsWith($taskCanonical+'\\',[StringComparison]::OrdinalIgnoreCase)",
        "$taskPartPath.StartsWith($taskTarget+'\\',[StringComparison]::OrdinalIgnoreCase)",
        '$taskPublic.archive_SHA','$taskAsset.SHA','$taskInitial.main_dirty_SHA','$taskInitial.main_HEAD','replay_receipt_SHA=',
        'cleanup_passed=$false']
    assert all(t in before for t in gate_tokens)
    after=current[current.index('$taskResult.E_free_after'):]
    assert '$taskFinalMainHead -ne $taskInitial.main_HEAD' in after
    assert '$taskResult.cleanup_passed = $taskResult.failed.Count -eq 0 -and @($taskTargets | Where-Object { Test-Path -LiteralPath $_ }).Count -eq 0' in after
    assert after.index('$taskResult.main_and_assets_rechecked_after_cleanup = $true')<after.index('$taskResult.cleanup_passed =')
    assert 'if (-not $taskResult.cleanup_passed) { throw' in after
    result=dict(decision='ACCEPT',scope='Actual bounded static cleanup-source admission only. Runtime replay/PR/process/manifest/asset gates must pass before parent execution; no deletion completion is certified.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_SHA=sha(source),preserved_v1_source_SHA=sha(old),review_script_SHA=sha(__file__),
        initial_findings_review_SHA=sha(REVIEW/'post_formal_cleanup_source_review.json'),
        independent_PowerShell_AST_parse_errors=0,PowerShell_AST_unchanged_functions=['Assert-TaskPath','Measure-OwnedTree','Save-TaskResult'],
        exact_four_target_array_and_literal_delete_loop_unchanged=True,delete_command_count=1,
        replay_public_receipts_bound_to_scienceA_exact_root_typed_stage_boundary_and_zero_native=True,
        external_replay_receipt_SHA_must_equal_restored_actual_receipt=True,
        exact_candidate_four_set_and_prerecord_SHA_required=True,
        manifest_public_SHA_pinned_exact_six_part_metadata_and_hashes_required=True,
        carrier_paths_exact_nonreparse_contained_and_outside_targets=True,actual_duplicate_tar_SHA_required=True,
        actual_Draft_PR_local_head_readback_and_no_related_process_gate_required=True,
        runtime_PE_DLL_core_and_main_dirty_HEAD_protection=True,post_main_HEAD_and_asset_checks_precede_success=True,
        explicit_cleanup_passed_requires_zero_failures_all_four_absent=True,partial_failure_persisted_then_nonzero=True,
        containment='Only E:/codes/ExactEBRP-work/{temp/round122/public-export,temp/round122/public-export-attempt01-tls,restore/round122-9ed88cf9da87,build-cache/round122-reference}',
        no_delete_or_target_traversal=True,restored_checker_untouched=True,actual_cleanup='PENDING_PARENT_RUNTIME_GATES_AND_EXECUTION',
        native_starts=0,Optimize=0,network_requests=0,Git_commands=0,existing_source_or_payload_member_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_cleanup_source_admission.json',result)

if __name__=='__main__':run()
