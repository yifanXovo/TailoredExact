$ErrorActionPreference = 'Stop'
$taskRoot = 'E:\codes\ExactEBRP-round114'
$outRoot = Join-Path $taskRoot 'results\unified_exact_round114'
$timer = [System.Diagnostics.Stopwatch]::StartNew()
function Read-Json([string]$path) { Get-Content -LiteralPath $path -Raw | ConvertFrom-Json }
function Digest([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Require([bool]$condition, [string]$reason) { if (-not $condition) { throw $reason } }
function Equal-Json($left,$right) { (ConvertTo-Json -InputObject $left -Depth 40 -Compress) -eq (ConvertTo-Json -InputObject $right -Depth 40 -Compress) }
function Bind-Map($map,[string]$root) { foreach ($property in $map.PSObject.Properties) { Require ((Digest (Join-Path $root $property.Name)) -eq $property.Value) ('SHA mismatch: '+$property.Name) } }
function Check-Map($left,$right,[string]$name) {
    Require (@($left.PSObject.Properties).Count -eq @($right.PSObject.Properties).Count) ($name+' map size')
    foreach ($property in $left.PSObject.Properties) { Require ($right.($property.Name) -eq $property.Value) ($name+' map differs: '+$property.Name) }
}
function Current-Path([string]$path) {
    $normalized=$path.Replace('\','/')
    $prefix=$taskRoot.Replace('\','/')+'/'
    Require ($normalized.StartsWith($prefix)) ('current native path is outside worktree: '+$path)
    Join-Path $taskRoot $normalized.Substring($prefix.Length)
}

$candidate=Read-Json (Join-Path $outRoot 'candidate_identity.json')
$production=Read-Json (Join-Path $outRoot 'production_identity.json')
$campaign=Read-Json (Join-Path $outRoot 'campaign\identity.json')
$qualification=Read-Json (Join-Path $outRoot 'qualification\cli01\identity.json')
$finite=Read-Json (Join-Path $outRoot 'qualification\finite02\summary.json')
$post=Read-Json (Join-Path $outRoot 'qualification\post01\summary.json')
$postReport=Read-Json (Join-Path $outRoot 'qualification\post01\reports\summary.json')
$trailer=Read-Json (Join-Path $outRoot 'qualification\cli01\qualification_trailer.json')
$protocol=Read-Json (Join-Path $outRoot 'protocol.json')
$candidateSHA=Digest (Join-Path $outRoot 'candidate_identity.json')
Require ($candidateSHA -eq '8c5a5bc25ef289f30a1d4fb1a8ee60723c41ca8a3238b00c0669605f7cd50175') 'candidate changed since independent finite review'
Require ($candidate.campaign_identity_SHA -eq (Digest (Join-Path $outRoot 'campaign\identity.json'))) 'campaign binding'
Require ($candidate.qualification_campaign_identity_SHA -eq (Digest (Join-Path $outRoot 'qualification\cli01\identity.json'))) 'qualification identity binding'
Require ($candidate.protocol_SHA -eq (Digest (Join-Path $outRoot 'protocol.json'))) 'protocol binding'
Require ($candidate.claim_policy_SHA -eq (Digest (Join-Path $outRoot 'claim_policy.md'))) 'claim policy binding'
Require (@($production.source_bindings.PSObject.Properties).Count -eq 206) 'source count'
Require (@($candidate.helpers.PSObject.Properties).Count -eq 47) 'helper count'
Bind-Map $production.source_bindings $taskRoot
Bind-Map $candidate.helpers $taskRoot
Check-Map $candidate.source_bindings $production.source_bindings 'candidate sources'
foreach ($identity in @($campaign,$qualification)) {
    Check-Map $identity.source_hashes $production.source_bindings 'campaign sources'
    Check-Map $identity.helpers $candidate.helpers 'campaign helpers'
    Require ($identity.prereg_sha256 -eq $candidate.protocol_SHA) 'preregistration SHA'
    Require ($identity.runner_sha256 -eq (Digest (Join-Path $taskRoot 'scripts\round114_campaign.py'))) 'runner SHA'
    Require ($identity.measured_source_commit -eq 'd0014a7163e3996fe120471420e56b089c9715ae') 'measured source commit'
    Require ($identity.delivery_base_commit -eq 'ea9410163aafd3877cdcde80e01ccd34d893f11b') 'delivery base'
    Require ($identity.candidate_binary_sha256 -eq $production.production_PE_SHA -and $identity.dll_sha256 -eq $production.DLL_SHA) 'campaign production identity'
}
Require ((Digest (Join-Path $taskRoot 'build\research\round114-inherited\ExactEBRP.exe')) -eq $production.production_PE_SHA) 'PE SHA'
Require ($production.production_PE_SHA -eq 'a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8') 'inherited PE'
Require ((Digest 'D:\gurobi1302\win64\bin\gurobi130.dll') -eq $production.DLL_SHA) 'DLL SHA'
Require ($production.DLL_SHA -eq '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88') 'inherited DLL'
Require ($finite.passed -and $post.passed -and $trailer.passed) 'qualification summary failed'
Check-Map $finite.performance_helpers $candidate.helpers 'finite helpers'
Check-Map $post.performance_helpers $candidate.helpers 'post helpers'
Check-Map $trailer.helpers $candidate.helpers 'CLI helpers'
Require ($finite.test_SHA -eq $candidate.qualification_test_SHA -and $finite.test_SHA -eq (Digest (Join-Path $taskRoot 'scripts\qualify_round114.py'))) 'test SHA'
Require ($post.post_driver_SHA -eq $candidate.qualification_post_driver_SHA -and $post.post_driver_SHA -eq (Digest (Join-Path $taskRoot 'scripts\qualify_round114_post.py'))) 'post driver SHA'
Require ($post.reader_SHA -eq $candidate.offline_reader_SHA -and $post.reader_SHA -eq (Digest (Join-Path $taskRoot 'scripts\read_round114.py'))) 'reader SHA'
Require ($post.OS_children -eq 0 -and $post.Optimize -eq 0 -and $finite.OS_children -eq 0 -and $finite.Optimize -eq 0) 'review drivers exposed native'
Require ($post.actual_CLI_not_synthetic -and -not $post.numerical_contradiction_reproduced) 'actual CLI provenance'
Require ($postReport.qualified_qualification_CLI -eq 2 -and $postReport.qualification_native_Optimize -eq 6 -and $postReport.formal_actual_Optimize -eq 0) 'post reader counts'
Require (-not (Test-Path -LiteralPath (Join-Path $outRoot 'campaign\summary.jsonl'))) 'formal already started'
Require (@($campaign.launches).Count -eq 4 -and ($campaign.launches.arm -join ',') -eq 'P-GRB,ENS-C,P-S,M-B') 'fixed formal order'
Require (@($qualification.launches).Count -eq 2 -and ($qualification.launches.arm -join ',') -eq 'P-GRB,M-B') 'fixed qualification order'
Require (Equal-Json (Read-Json (Join-Path $outRoot 'fixed_manifest.json')) $campaign) 'fixed manifest differs'
foreach ($launch in $campaign.launches) {
    Require ($launch.id -eq 'G100-R2' -and $launch.cap_seconds -eq 3600 -and $launch.seed -eq 0 -and $launch.hard_stop_seconds -eq 3598) 'formal settings'
    Require (-not (Test-Path -LiteralPath $launch.destination)) 'formal raw exists'
    Require ((Digest (Join-Path $taskRoot $launch.panel.input_path)) -eq 'b3f3a1270f062e9f3af64d5b00392f51821bb775818edc6cd383fcd62550618f') 'G100 input'
}

$records=@(Get-Content -LiteralPath (Join-Path $outRoot 'qualification\cli01\summary.jsonl') | ForEach-Object { $_ | ConvertFrom-Json })
$rawDirectories=@(Get-ChildItem -LiteralPath (Join-Path $outRoot 'qualification\cli01\raw') -Directory)
Require ($records.Count -eq 2 -and $rawDirectories.Count -eq 2 -and ($records.arm -join ',') -eq 'P-GRB,M-B') 'exactly two actual CLI'
$armEvidence=@()
$journalTotal=0
$nativeCallTotal=0
foreach ($launch in $qualification.launches) {
    $directory=$launch.destination
    $saved=Read-Json (Join-Path $directory 'launch.json')
    $result=Read-Json (Join-Path $directory 'result.json')
    $audit=Read-Json (Join-Path $directory 'audit.json')
    $completion=Read-Json (Join-Path $directory 'completion.json')
    $whole=Read-Json (Join-Path $directory 'whole_arm_receipt.json')
    $ind=Read-Json (Join-Path $directory 'independent_evidence.json')
    $closeout=Read-Json (Join-Path $directory 'independent_endpoint_closeout.json')
    $nativeEnd=Read-Json (Join-Path $directory 'native_end_receipt.json')
    $auditEnd=Read-Json (Join-Path $directory 'postexit_audit_receipt.json')
    $observations=@(Read-Json (Join-Path $directory 'observations.json'))
    $postArm=$post.actual_CLI | Where-Object { $_.arm -eq $launch.arm }
    Require (Equal-Json $launch.command $saved.command) 'actual argv differs'
    Require (Equal-Json $launch.command $postArm.full_argv) 'post argv differs'
    Require (Equal-Json $launch.panel $saved.panel) 'actual panel differs'
    Require ($launch.id -eq 'H100' -and $launch.seed -eq 0 -and $launch.cap_seconds -eq 120) 'qualification settings'
    Require ((Digest (Join-Path $taskRoot $launch.panel.input_path)) -eq '04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71') 'H100 input'
    Require ($completion.returncode -eq 0 -and $completion.stop_reason -eq 'normal_return' -and $completion.within_cap -and $audit.passed) 'CLI normal return/audit'
    Require ($result.process_return_code -eq 0 -and $result.process_shutdown_margin_seconds -eq 30) 'CLI process finalization'
    Require ($whole.complete_seconds -gt 0 -and $whole.complete_seconds -le 120) 'CLI whole cap'
    Require ($nativeEnd.complete_seconds_until_native_end -le $auditEnd.complete_seconds_until_audit_end -and $auditEnd.complete_seconds_until_audit_end -le $whole.complete_seconds) 'necessary work outside whole'
    Require ($whole.metrics_written_before_whole -and $whole.progress_publication_receipt_written_before_whole -and $whole.own_UB_floor_zero_evidence_written_before_whole -and $whole.claim_rejections_written_before_whole -and -not $whole.future_cohort_review_in_clock) 'whole contract'
    Require ($whole.independent_evidence_SHA -eq (Digest (Join-Path $directory 'independent_evidence.json')) -and $whole.independent_closeout_SHA -eq (Digest (Join-Path $directory 'independent_endpoint_closeout.json'))) 'whole SHA binding'
    Require ($whole.progress_receipt_SHA -eq (Digest (Join-Path $directory 'progress_publication_receipt.json'))) 'progress SHA binding'
    foreach ($binding in @(@('own_evidence_SHA','independent_evidence.json'),@('claim_records_SHA','native_claims.json'),@('rejection_SHA','claim_rejections.json'),@('cohort_SHA','cohort_check.json'),@('audit_SHA','audit.json'))) {
        Require ($closeout.($binding[0]) -eq (Digest (Join-Path $directory $binding[1]))) ('closeout SHA: '+$binding[1])
    }
    Require ($closeout.required_audit_complete -and $closeout.own_UB_floor_and_own_zero_validated_before_whole) 'closeout incomplete'
    Require ($ind.independent_floor0 -and $ind.own_physical_verified -and $ind.inside_own_whole) 'independent evidence missing'
    foreach ($key in @('identity_verified','input_verified','model_domain_verified','journal_verified','return_verified','files_verified')) { Require ($ind.$key -eq $true) ('independent predicate: '+$key) }
    Require (-not $ind.clock_valid -and -not $ind.necessary_closeout_complete -and $ind.clock_pending_until_actual_whole) 'pre-whole placeholder mutated'
    Require ($ind.result_SHA -eq (Digest (Join-Path $directory 'result.json')) -and $ind.observations_SHA -eq (Digest (Join-Path $directory 'observations.json')) -and $ind.completion_SHA -eq (Digest (Join-Path $directory 'completion.json'))) 'independent raw bindings'
    Require ($postArm.whole_SHA -eq (Digest (Join-Path $directory 'whole_arm_receipt.json')) -and $postArm.necessary_audit_SHA -eq (Digest (Join-Path $directory 'audit.json')) -and $postArm.independent_evidence_SHA -eq (Digest (Join-Path $directory 'independent_evidence.json'))) 'post actual CLI bindings'
    Require ($ind.counts.actual_Optimize -eq $ind.counts.declared -and $ind.counts.journal_returned -eq $ind.counts.actual_Optimize -and $ind.counts.independently_verified_returned -eq $ind.counts.actual_Optimize -and $ind.counts.explicit_not_started -eq 0) 'actual call counts'
    Require ($audit.native_calls_started -eq $ind.counts.actual_Optimize -and $audit.native_calls_returned -eq $ind.counts.journal_returned) 'audit call counts'
    Require (@(Get-ChildItem -LiteralPath (Join-Path $directory 'journal') -Filter '*.commit').Count -eq $observations.Count -and $completion.committed_events -eq $observations.Count) 'committed prefix count'
    $calls=@();$returns=@();$sequence=0
    foreach ($observation in $observations) {
        $sequence++
        $eventPath=Join-Path $directory ('journal\event_'+$sequence+'.json')
        $commit=(Get-Content -LiteralPath (Join-Path $directory ('journal\event_'+$sequence+'.commit')) -Raw).Trim() -split '\s+'
        $event=Read-Json $eventPath
        Require ($commit.Count -eq 5 -and $commit[0] -eq 'NEJ1' -and [int]$commit[1] -eq $sequence -and [long]$commit[3] -eq (Get-Item -LiteralPath $eventPath).Length) 'journal commit binding'
        Require ($commit[4] -eq $observation.sha256 -and $commit[4] -eq (Digest $eventPath)) 'journal raw SHA'
        Require ($event.sequence -eq $sequence -and $event.schema -eq 1 -and $event.kind -eq $observation.payload.kind) 'journal schema/sequence'
        Require ([double]$commit[2] -eq $observation.data_close_seconds -and $observation.effective_available_seconds -ge $observation.data_close_seconds -and $observation.effective_available_seconds -le 120) 'journal original availability'
        Require ($event.kind -ne 'failure' -and $event.kind -ne 'not_started') 'unexpected qualified actual call failure/cancellation'
        if ($event.kind -eq 'call') {
            $calls += $event
            Require ($event.call -eq $calls.Count -and (Digest (Current-Path $event.model_path)) -eq $event.model_sha256) 'actual call/model SHA'
            Require ($event.settings.Threads -eq 1 -and $event.settings.Seed -eq 0 -and $event.settings.Presolve -eq -1 -and $event.settings.MIPGap -eq 0 -and $event.settings.MIPGapAbs -eq 0 -and $event.settings.FeasibilityTol -eq 1e-6 -and $event.settings.OptimalityTol -eq 1e-6 -and $event.settings.IntFeasTol -eq 1e-5 -and $event.settings.read_return_code -eq 0) 'actual native settings'
            Require ($event.gmax -eq .95 -and 0 -le $event.lower_g -and $event.lower_g -le $event.upper_g -and $event.upper_g -le .95) 'actual call domain'
        }
        if ($event.kind -eq 'returned') { Require ($event.return_code -eq 0) 'actual Optimize return'; $returns += $event.call }
    }
    Require ($calls.Count -eq $ind.counts.actual_Optimize -and $returns.Count -eq $calls.Count -and (($returns -join ',') -eq ((1..$calls.Count) -join ','))) 'all actual calls returned'
    $logBindings=@();$ledger=@()
    if ($launch.arm -eq 'M-B') { $ledger=@(Import-Csv -LiteralPath (Join-Path $directory 'external\paper_optimize_ledger.csv')); Require ($ledger.Count -eq $calls.Count) 'tree ledger count' }
    foreach ($call in $calls) {
        $logPath=Current-Path $call.native_log_path
        $text=Get-Content -LiteralPath $logPath -Raw
        Require ([regex]::Matches($text,'Optimize a model with ').Count -eq 1) 'unknown extra native Optimize'
        Require ($text -match 'Gurobi Optimizer version 13\.0\.2' -and ($text -match 'Optimal objective' -or $text -match 'Best objective ')) 'actual native terminal log'
        if ($ledger.Count) {
            $row=$ledger[$call.call-1]
            Require ($row.model_sha256 -eq $call.model_sha256 -and $row.leaf_id -eq $call.leaf -and [int]$row.optimize_return_code -eq 0 -and (Current-Path $row.native_log) -eq $logPath) 'tree per-call binding'
        }
        $logBindings += [ordered]@{call=$call.call;model_SHA=$call.model_sha256;native_log=$logPath.Substring($taskRoot.Length+1).Replace('\','/');native_log_SHA=(Digest $logPath);journal_returned=$true}
    }
    if ($launch.arm -eq 'P-GRB') {
        Require ($calls.Count -eq 1 -and $result.gurobi_optimize_count -eq 1 -and $result.native_mip_mipopt_count -eq 1 -and $result.gurobi_optimize_return_code -eq 0 -and $result.native_mipopt_return_code -eq 0) 'plain true count/return'
        foreach ($key in @('gurobi_environment_count','gurobi_model_count','gurobi_model_read_count','gurobi_model_free_count','gurobi_environment_free_count','native_mip_environment_count','native_mip_problem_count','native_mip_model_read_count','native_mip_freeprob_count','native_mip_close_count')) { Require ($result.$key -eq 1) ('plain cleanup: '+$key) }
        Require ($result.gurobi_status -eq 9 -and $result.gurobi_lifecycle_valid -and $result.gurobi_native_domain_audit_passed) 'plain terminal/lifecycle'
    } else {
        Require ($result.external_gini_tree_optimize_count -eq 5 -and $result.external_gini_tree_lp_optimize_count -eq 3 -and $result.external_gini_tree_partial_mip_optimize_count -eq 1 -and $result.external_gini_tree_terminal_mip_optimize_count -eq 1) 'tree true Optimize categories'
        Require ($result.external_gini_tree_environment_count -eq 1 -and $result.external_gini_tree_environment_free_count -eq 1 -and $result.external_gini_tree_model_count -eq 3 -and $result.external_gini_tree_model_read_count -eq 3 -and $result.external_gini_tree_model_free_count -eq 3) 'tree true cleanup counts'
        Require ($result.external_gini_tree_lifecycle_complete -and $result.external_gini_tree_backend_parameter_roundtrip_valid) 'tree lifecycle/parameters'
    }
    $phase=@(Import-Csv -LiteralPath (Join-Path $directory 'phases.csv'))
    Require ($phase[0].event -eq 'process_entry' -and $phase[-1].event -eq 'process_exit' -and $phase[-1].detail -eq 'rc=0') 'serialization/process exit'
    $serializationStart=($phase | Where-Object event -eq 'final_result_serialization_start').sequence
    $serializationComplete=($phase | Where-Object event -eq 'final_result_serialization_complete').sequence
    Require ([int]$serializationStart -lt [int]$serializationComplete -and [int]$serializationComplete -lt [int]$phase[-1].sequence) 'serialization order'
    $binding=[ordered]@{}
    foreach ($name in @('launch.json','result.json','completion.json','audit.json','observations.json','phases.csv','whole_arm_receipt.json','independent_evidence.json','native_claims.json','claim_rejections.json','cohort_check.json','independent_endpoint_closeout.json','native_end_receipt.json','postexit_audit_receipt.json','audit_execution_metrics.json','progress_publication_receipt.json')) { $binding[$name]=Digest (Join-Path $directory $name) }
    $armEvidence += [ordered]@{arm=$launch.arm;input_SHA=$launch.panel.input_sha256;cap_seconds=120;seed=0;command=$launch.command;normal_return=$true;whole_seconds=$whole.complete_seconds;endpoint=$audit.endpoint;own_U=$ind.own_U;own_exact_zero=$ind.own_exact_zero;independent_floor0=$true;own_evidence_inside_original_whole=$true;prewhole_placeholder_preserved=$true;counts=$ind.counts;committed_events=$observations.Count;bindings=$binding;actual_call_bindings=$logBindings;tree_LP= $(if ($ledger.Count) { 3 } else { 0 });tree_partial_MIP= $(if ($ledger.Count) { 1 } else { 0 });tree_terminal_MIP= $(if ($ledger.Count) { 1 } else { 0 })}
    $journalTotal += $observations.Count
    $nativeCallTotal += $calls.Count
}

$fees=@();$totalStarts=0;$totalSeconds=0.
foreach ($directory in Get-ChildItem -LiteralPath (Join-Path $outRoot 'fees') -Directory) {
    $launch=Read-Json (Join-Path $directory.FullName 'launch.json')
    $receipt=Read-Json (Join-Path $directory.FullName 'receipt.json')
    $pending=Read-Json (Join-Path $directory.FullName 'pending_exit_receipt.json')
    Require ($receipt.actual_exit_observed -and $receipt.necessary_trailer_complete -and -not $receipt.nested_native_seconds_added) 'fee not actually closed'
    Require ($launch.qualification -and $receipt.qualification -and $receipt.conservative_process_starts -eq $launch.conservative_process_starts) 'fee categories/counts'
    Require ($receipt.exit_code -eq $pending.exit_code -and $receipt.actual_native_children -eq $launch.declared_native_children) 'fee exit/children'
    Require ($receipt.outer_seconds_upper -ge $receipt.outer_seconds_lower -and $receipt.outer_seconds_lower -eq $pending.outer_seconds_lower) 'fee original interval'
    Require ([math]::Abs($receipt.outer_seconds_upper-[math]::Max($receipt.outer_seconds_lower,$receipt.caller_observed_unix-$launch.wrapper_creation_unix)) -lt .01) 'fee creation/exit upper binding'
    Check-Map $launch.helpers $candidate.helpers 'fee frozen helpers'
    Require ($launch.all_remaining_fixed_reserve.starts -eq 5 -and $launch.all_remaining_fixed_reserve.nominal -eq 14400 -and $launch.all_remaining_fixed_reserve.overhead -eq 120) 'formal reserve reduced'
    $expectedExit= $(if ($directory.Name -eq 'finite01') { 1 } else { 0 })
    Require ($receipt.exit_code -eq $expectedExit) 'unexpected qualification failure'
    $fees += [ordered]@{label=$directory.Name;starts=$launch.conservative_process_starts;actual_native_children=$receipt.actual_native_children;outer_seconds_upper=$receipt.outer_seconds_upper;exit_code=$receipt.exit_code;actual_exit_observed=$true;launch_SHA=(Digest (Join-Path $directory.FullName 'launch.json'));pending_SHA=(Digest (Join-Path $directory.FullName 'pending_exit_receipt.json'));receipt_SHA=(Digest (Join-Path $directory.FullName 'receipt.json'))}
    $totalStarts += $launch.conservative_process_starts
    $totalSeconds += $receipt.outer_seconds_upper
}
Require ($fees.Count -eq 4 -and $totalStarts -eq 6 -and [math]::Abs($totalSeconds-189.472980260849) -lt 1e-6) 'fee totals'
Require ($totalStarts -le 8 -and $totalSeconds -le 900 -and 16-$totalStarts -ge 5 -and 17000-$totalSeconds -ge 14520) 'hard budget or formal reserve'
Require (Test-Path -LiteralPath (Join-Path $outRoot 'fees\finite01\failure.txt')) 'failed driver diagnostic absent'
$finiteCounterexample=Read-Json (Join-Path $outRoot 'qualification\finite02\counterexample\replay.json')
Bind-Map $finiteCounterexample.source_bindings $taskRoot
Bind-Map $finiteCounterexample.outputs $taskRoot
Require ($finiteCounterexample.script_SHA -eq (Digest (Join-Path $taskRoot 'scripts\round114_counterexample.py'))) 'counterexample helper binding'
$limited=Read-Json (Join-Path $outRoot 'inherited_return_authority\dependency_manifest.json')
Bind-Map $limited.files (Join-Path $outRoot 'inherited_return_authority')
$old=Read-Json (Join-Path $outRoot 'inherited_r113\dependency_manifest.json')
Bind-Map $old.files (Join-Path $outRoot 'inherited_r113')
$reviewFiles=[ordered]@{}
foreach ($name in @('review/preparation01/report.md','review/preparation01/preparation.json','review/preparation01/authority_binding_supplement.json','review/preparation01/static_boundary_review.json','review/preparation01/fixed_argv_static.json','review/preparation01/finite_evidence_review.json','qualification/finite02/summary.json','qualification/post01/summary.json','qualification/post01/reports/qualification_arms.csv','qualification/post01/reports/summary.json','inherited_return_authority/dependency_manifest.json','inherited_r113/dependency_manifest.json','inherited_r113/review_dependency_manifest.json')) { $reviewFiles[$name]=Digest (Join-Path $outRoot $name) }
$payload=[ordered]@{
    schema='round114-independent-performance-admission-v1';decision='ACCEPT';reviewer='/root/independent_admission';signed_utc=[DateTime]::UtcNow.ToString('o')
    scope='Prospective evidence and closeout protocol qualification for exactly four once-only G100-R2 arms; no G100 result or scientific contribution is inferred from qualification.'
    candidate_identity_SHA=$candidateSHA;campaign_identity_SHA=(Digest (Join-Path $outRoot 'campaign\identity.json'));qualification_campaign_identity_SHA=(Digest (Join-Path $outRoot 'qualification\cli01\identity.json'))
    production_identity_SHA=(Digest (Join-Path $outRoot 'production_identity.json'));production_PE_SHA=$production.production_PE_SHA;DLL_SHA=$production.DLL_SHA;source_commit='d0014a7163e3996fe120471420e56b089c9715ae';delivery_base_commit='ea9410163aafd3877cdcde80e01ccd34d893f11b'
    source_files=206;source_discrepancies=@();helpers=$candidate.helpers;helpers_count=47;helper_discrepancies=@();protocol_SHA=$candidate.protocol_SHA;claim_policy_SHA=$candidate.claim_policy_SHA
    qualification_test_SHA=$candidate.qualification_test_SHA;qualification_post_driver_SHA=$candidate.qualification_post_driver_SHA;offline_reader_SHA=$candidate.offline_reader_SHA;counterexample_helper_SHA=$finiteCounterexample.script_SHA
    qualification_finite_success='finite02';qualification_failed_driver_retained='finite01';failed_driver_reason='Synthetic test event omitted schema, causing KeyError; raw/fee retained; only test schema was corrected, with unchanged runtime helper closure.'
    qualification_actual_CLI=$armEvidence;qualification_actual_native_children=2;qualification_actual_Optimize=$nativeCallTotal;qualification_actual_journal_returned=$nativeCallTotal;qualification_actual_committed_events=$journalTotal;qualification_LP_Optimize=3;qualification_MIP_Optimize=3
    finite_mock_scope='Source-extracted in-process fake clock/child; no OS children, no native fault/cancellation reproduction. Two exact counterexample matrices were replayed only inside the billed finite driver.'
    independent_source_protocol=[ordered]@{same_domain_direct_counterexample_required=$true;damaged_call_all_native_proofs_rejected=$true;raw_numbers_and_failed_audit_preserved=$true;SOURCE_REDUCED_OPEN_own_UB_floor0_original_whole_only=$true;OWN_ZERO_CERTIFICATE_requires_own_exact_Y_equals_D_and_floor=$true;other_arm_witness_only_revokes_native_trust=$true;ordinary_missing_identity_scope_files_return_or_resource_errors_remain_fatal=$true;narrow_missing_return_gate_general_and_actual_last_MIP_only=$true;old_P17_P25_missing_returned_preserved=$true;terminal_native_zero_only_return_corroboration=$true;rejected_cover_geometry_separate_from_native_number_qualification=$true;native_internal_unique_cause='unknown'}
    old_authority=[ordered]@{qualified_measurements=15;evaluable_pairs=21;old_R113_state='BLOCKED';old_G50_cold_no_whole_still_unqualified=$true;historical_exact_clocks_not_recreated=$true;old_LP_model_reparse=0;R110_R111_fixtures=@(15,17,25,26);limited_return_files=736}
    fees=$fees;qualification_conservative_starts=$totalStarts;qualification_outer_seconds_upper=$totalSeconds;unclosed_fees=@();formal_conservative_starts_so_far=0;formal_actual_children_so_far=0
    budget=[ordered]@{total_start_limit=16;total_outer_seconds_limit=17000;qualification_start_limit=8;qualification_outer_seconds_limit=900;paid_starts=$totalStarts;paid_outer_seconds_upper=$totalSeconds;remaining_starts=16-$totalStarts;remaining_outer_seconds=17000-$totalSeconds;reserved_formal_starts=5;reserved_formal_nominal_seconds=14400;reserved_formal_administrative_seconds=120;reserved_formal_outer_seconds=14520;unreserved_starts=16-$totalStarts-5;unreserved_outer_seconds=17000-$totalSeconds-14520}
    formal_launches=@($campaign.launches | Select-Object number,id,arm,seed,cap_seconds,hard_stop_seconds,command);formal_order_frozen=@('P-GRB','ENS-C','P-S','M-B');no_formal_retry=$true;performance_helper_changes_after_admission_prohibited=$true
    evidence_bindings=$reviewFiles;all_current_own_evidence_persisted_before_actual_whole=$true;two_actual_CLI_and_post_driver_exit_closed=$true;qualification_reader_pending_marker_preserved_as_original_creation_state=$true
    independent_reviewer_native_starts=0;independent_reviewer_Optimize=0;independent_reviewer_qualification_driver_starts=0;independent_reviewer_performance_helper_mutations=0;read_only_review_engineering_seconds=$timer.Elapsed.TotalSeconds
}
$destination=Join-Path $outRoot 'review\performance_admission.json'
Require (-not (Test-Path -LiteralPath $destination)) 'admission already exists'
[System.IO.File]::WriteAllText($destination,(ConvertTo-Json -InputObject $payload -Depth 40)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
[pscustomobject]@{decision='ACCEPT';admission_SHA=(Digest $destination);candidate_identity_SHA=$candidateSHA;qualification_starts=$totalStarts;qualification_seconds=$totalSeconds;formal_reserved_starts=5;formal_reserved_seconds=14520;remaining_starts=16-$totalStarts;remaining_seconds=17000-$totalSeconds;review_engineering_seconds=$timer.Elapsed.TotalSeconds} | ConvertTo-Json -Compress
