$ErrorActionPreference='Stop'
$reviewRoot='E:/codes/ExactEBRP-round114/results/unified_exact_round114/review/preparation01'
$oldRoot='E:/codes/ExactEBRP-round110'
$newRoot='E:/codes/ExactEBRP-round114'
$authorityRoot='E:/codes/ExactEBRP-round111/results/unified_exact_round111/review/inherited_main03'
$timer=[Diagnostics.Stopwatch]::StartNew()
$dependencies=[Collections.Generic.List[object]]::new()
function Bind([string]$root,[string]$relative,[string]$purpose) {
 $target=Join-Path $root $relative
 if (!(Test-Path -LiteralPath $target -PathType Leaf)) {throw ('missing review dependency '+$target)}
 $dependencies.Add([PSCustomObject]@{source_root=$root; relative_path=$relative.Replace('\','/'); SHA256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower(); bytes=(Get-Item -LiteralPath $target).Length; purpose=$purpose})
}
function ValueFields($raw,$names) { $values=[ordered]@{}; foreach ($name in $names) {$values[$name]=$raw.$name}; return $values }
$plainFields=@('process_return_code','process_shutdown_margin_seconds','gurobi_status','gurobi_status_text','gurobi_version','gurobi_optimize_count','gurobi_optimize_return_code','native_mip_status_code','native_mip_status_text','native_mip_evidence_available','native_mip_evidence_capture_complete','native_mip_lifecycle_valid','native_mip_solver_finalization_reached','native_mip_problem_freed','native_mip_environment_closed','native_mipopt_return_code','native_mip_freeprob_return_code','native_mip_close_return_code','native_mip_environment_count','native_mip_problem_count','native_mip_model_read_count','native_mip_mipopt_count','native_mip_freeprob_count','native_mip_close_count','gurobi_environment_creation_return_code','gurobi_environment_count','gurobi_model_count','gurobi_model_read_count','gurobi_model_free_count','gurobi_environment_free_count','gurobi_solver_finalization_reached','gurobi_lifecycle_valid','gurobi_native_domain_audit_passed','gurobi_native_variable_names_match','gurobi_native_variable_types_match','gurobi_native_variable_bounds_match','gurobi_native_objective_sense_match','native_mip_status_code_text_consistent','native_mip_best_bound','native_mip_objective','gurobi_obj_bound','gurobi_obj_bound_c','gurobi_hga_start_requested','gurobi_hga_start_submitted')
$treeFields=@('process_return_code','process_shutdown_margin_seconds','external_gini_tree_backend','external_gini_tree_optimize_count','external_gini_tree_lp_optimize_count','external_gini_tree_partial_mip_optimize_count','external_gini_tree_terminal_mip_optimize_count','external_gini_tree_model_count','external_gini_tree_model_read_count','external_gini_tree_model_free_count','external_gini_tree_environment_count','external_gini_tree_environment_free_count','external_gini_tree_backend_parameter_roundtrip_valid','external_gini_tree_lifecycle_complete','external_gini_tree_integer_domain_restore_count','gurobi_optimize_count','native_mip_mipopt_count')
$cases=[Collections.Generic.List[object]]::new()
$entries=@(@{n=15;folder='15_G50-C1_S0_P-GRB';fee='main05';prior=@('13_G50-C1_S0_M-B','14_G50-C1_S0_ENS-C')},@{n=17;folder='17_G50-C2_S0_P-GRB';fee='main06';prior=@('16_G50-C2_S0_ENS-C')},@{n=25;folder='25_G100-C1_S0_M-B';fee='main09';prior=@()},@{n=26;folder='26_G100-C1_S0_P-GRB';fee='main09_tail01';prior=@()})
foreach ($entry in $entries) {
 $relative='results/unified_exact_round110/campaign/raw/'+$entry.folder
 $absolute=Join-Path $oldRoot $relative
 $side=Get-Content -LiteralPath ($authorityRoot+'/authority/recovery_'+$entry.n+'.json') -Raw | ConvertFrom-Json
 $signed=Get-Content -LiteralPath ($authorityRoot+'/authority/recovery_'+$entry.n+'_signed_audit.json') -Raw | ConvertFrom-Json
 $result=Get-Content -LiteralPath ($absolute+'/result.json') -Raw | ConvertFrom-Json
 $observations=@(Get-Content -LiteralPath ($absolute+'/observations.json') -Raw | ConvertFrom-Json)
 $calls=@($observations | Where-Object {$_.payload.kind -eq 'call'})
 $returns=@($observations | Where-Object {$_.payload.kind -eq 'returned'})
 $notStarted=@($observations | Where-Object {$_.payload.kind -eq 'not_started'})
 $failures=@($observations | Where-Object {$_.payload.kind -eq 'failure'})
 $fields=if ($entry.n -eq 25) {$treeFields} else {$plainFields}
 $parameters=[ordered]@{}
 foreach ($property in $result.PSObject.Properties) {if ($property.Name -match '^gurobi_(threads|seed|presolve|mip_gap|mip_gap_abs)_(requested|effective|set_return_code|get_return_code)$') {$parameters[$property.Name]=$property.Value}}
 $ledger=@()
 if ($entry.n -eq 25) {
  $ledger=@(Import-Csv -LiteralPath ($absolute+'/external/paper_optimize_ledger.csv'))
  foreach ($dep in @('external/paper_optimize_ledger.csv','external/lp_status_ledger.csv')) {Bind $oldRoot ($relative+'/'+$dep) 'actual per-call tree domain/return distinction'}
  foreach ($call in $calls) {
   $log=([string]$call.payload.native_log_path).Replace('\','/')
   $logRelative=$log.Substring($oldRoot.Length+1)
   Bind $oldRoot $logRelative 'matched actual per-call native final log'
   if ($call.payload.call -eq 4) {Bind $oldRoot ($logRelative+'.round68.start.json') 'already executed own terminal-MIP Start metadata; full contract inherited'}
  }
 }
 foreach ($file in @('launch.json','result.json','completion.json','audit.json','observations.json','phases.csv','native.log','native_end_receipt.json','postexit_audit_receipt.json')) {Bind $oldRoot ($relative+'/'+$file) 'finite original lifecycle/own witness/clock'}
 foreach ($file in @('launch.json','receipt.json')) {Bind $oldRoot ('results/unified_exact_round110/fees/'+$entry.fee+'/'+$file) 'original enclosing outward fee clock'}
 foreach ($prior in $entry.prior) {Bind $oldRoot ('results/unified_exact_round110/campaign/raw/'+$prior+'/whole_arm_receipt.json') 'only preceding disjoint original clock receipt'}
 for ($sequence=1;$sequence -le $observations.Count;$sequence++) {
  $row=$observations[$sequence-1]
  if ($row.sequence -ne $sequence -or $row.payload.sequence -ne $sequence) {throw 'non-contiguous original journal'}
  $data=$absolute+'/journal/event_'+$sequence+'.json'
  $commit=$absolute+'/journal/event_'+$sequence+'.commit'
  $parts=(Get-Content -LiteralPath $commit -Raw).Trim().Split(' ')
  $hash=(Get-FileHash -LiteralPath $data -Algorithm SHA256).Hash.ToLower()
  if ($parts[0] -ne 'NEJ1' -or [int]$parts[1] -ne $sequence -or [long]$parts[3] -ne (Get-Item -LiteralPath $data).Length -or $parts[4] -ne $hash -or $row.sha256 -ne $hash) {throw 'original committed byte mismatch'}
  Bind $oldRoot ($relative+'/journal/event_'+$sequence+'.json') 'finite committed prefix; no LP reparsing'
  Bind $oldRoot ($relative+'/journal/event_'+$sequence+'.commit') 'finite committed prefix receipt'
 }
 $cases.Add([PSCustomObject]@{number=$entry.n; original_key=$side.key; declared_calls=$calls.Count; actual_Optimize=$(if($entry.n -eq 25){$result.external_gini_tree_optimize_count}else{$result.gurobi_optimize_count}); journal_returned=$returns.Count; independent_verified_return_missing_count=$(if($entry.n -in @(17,25)){1}else{0}); explicit_not_started=$notStarted.Count; committed_prefix=$observations.Count; prefix_bytes_verified=$true; failure_records=@($failures | ForEach-Object {$_.payload}); call_scopes=@($calls | ForEach-Object {$_.payload}); return_events=@($returns | ForEach-Object {$_.payload}); own_committed_zero_sequences=@($observations | Where-Object {$_.payload.kind -eq 'witness' -and $_.payload.objective -eq 0 -and $_.payload.G -eq 0 -and $_.payload.P -eq 0} | ForEach-Object {$_.sequence}); raw_required_fields=(ValueFields $result $fields); raw_parameter_readbacks=$parameters; actual_tree_optimize_ledger=$ledger; original_completion=(Get-Content -LiteralPath ($absolute+'/completion.json') -Raw | ConvertFrom-Json); raw_audit=(Get-Content -LiteralPath ($absolute+'/audit.json') -Raw | ConvertFrom-Json); original_native_end=(Get-Content -LiteralPath ($absolute+'/native_end_receipt.json') -Raw | ConvertFrom-Json); original_time=$side.time; signed_own_U=$signed.own_U; signed_own_floor=$signed.own_complete_original_domain_floor; signed_zero_certificate=$signed.certificate_from_own_exact_zero; signed_missing_returned_journal=$signed.missing_returned_journal_preserved; signed_proof_SHA=$side.independent_audit_SHA; signed_exact_vector_SHA=$side.exact_vector_SHA; signed_model_SHA=$side.model_SHA; matrix_and_physical_contracts_inherited_not_reexecuted=$true})
 foreach ($name in @(('recovery_'+$entry.n+'.json'),('recovery_'+$entry.n+'_signed_audit.json'))) {Bind 'E:/codes/ExactEBRP-round111' ('results/unified_exact_round111/review/inherited_main03/authority/'+$name) 'signed R110 authority retained by R111'}
}
foreach ($name in @('audit.json','receipt.json','main36_actual_independent_records.json','main36_original_clock_evidence.json','main36_qualification_derivations.json')) {Bind 'E:/codes/ExactEBRP-round111' ('results/unified_exact_round111/review/inherited_main03/'+$name) 'final R111 finite inheritance and original clocks'}
foreach ($name in @('scripts/round110_evidence.py','scripts/round110_scoped_evidence.py','scripts/round109_main06_recovery.py','results/unified_exact_round110/current_numerical_evidence.md','results/unified_exact_round110/review/round110_independent_cold_rejection.py','results/unified_exact_round110/review/round110_independent_scoped_rejection.py')) {Bind $oldRoot $name 'original predicate source; old hardcoded keys only bind fixtures'}
$production=Get-Content -LiteralPath 'E:/codes/ExactEBRP-round113/results/unified_exact_round113/production_identity.json' -Raw | ConvertFrom-Json
$sourceDiscrepancies=@()
foreach ($binding in $production.source_bindings.PSObject.Properties) { $target=Join-Path $newRoot $binding.Name; if (!(Test-Path -LiteralPath $target)) {$sourceDiscrepancies+=@{path=$binding.Name;kind='missing'}} else { $actual=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower(); if($actual -ne $binding.Value) {$sourceDiscrepancies+=@{path=$binding.Name;kind='SHA_mismatch';expected=$binding.Value;actual=$actual}} } }
$manifest=@($dependencies | Sort-Object source_root,relative_path -Unique)
$manifestPath=$reviewRoot+'/limited_dependencies.json'
[IO.File]::WriteAllText($manifestPath,($manifest | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$timer.Stop()
$review=[ordered]@{schema='round114-independent-readonly-preparation-v1';decision='PREPARATION_ONLY_NOT_ADMISSION';reviewer='/root/independent_admission';worktree=$newRoot;engineering_seconds=$timer.Elapsed.TotalSeconds;native_starts=0;Optimize=0;compiler_starts=0;qualification_driver_starts=0;helper_mutations=0;old_LP_matrices_reparsed=0;production_source_bindings_verified=@($production.source_bindings.PSObject.Properties).Count;source_discrepancies=$sourceDiscrepancies;dependency_count=$manifest.Count;dependency_manifest_SHA=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLower();cases=@($cases);limitations=@('Original complete matrix/physical/Start proofs inherit bound signed authority; no old matrix proof repeated.','Known instance keys bind old fixtures only; they cannot route or qualify new calls.','Original absent exact whole remains absent; outward intervals belong only to original R110 observations.','R113 old cold P remains unevaluable; no qualification or final ACCEPT is signed by this preparation.')}
[IO.File]::WriteAllText(($reviewRoot+'/preparation.json'),($review | ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))
[PSCustomObject]@{review=$reviewRoot;dependencies=$manifest.Count;source_bindings=206;source_discrepancies=$sourceDiscrepancies;cases=@($cases | Select-Object number,declared_calls,actual_Optimize,journal_returned,independent_verified_return_missing_count,explicit_not_started,committed_prefix);engineering_seconds=$timer.Elapsed.TotalSeconds} | ConvertTo-Json -Depth 6