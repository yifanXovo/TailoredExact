param(
    [switch]$SmokeOnly
)
$ErrorActionPreference = 'Continue'
$Root = Resolve-Path 'results/longrun_round17_local'
$Raw = Join-Path $Root 'raw'
$Logs = Join-Path $Root 'logs'
$Progress = Join-Path $Root 'progress'
$CplexDir = Join-Path $Root 'cplex'
$AblationDir = Join-Path $Root 'ablation'
$PortfolioDir = Join-Path $Root 'portfolio'
$AuditDir = Join-Path $Root 'audit'
$Exe = Resolve-Path 'build/ExactEBRP.exe'
$Sha = (git rev-parse HEAD).Trim()
$CommandFile = Join-Path $Root 'commands.md'
$ExitCsv = Join-Path $Root 'run_exit_summary.csv'
$SkippedCsv = Join-Path $Root 'skipped_or_shortened_runs.csv'
if(!(Test-Path $ExitCsv)){ 'name,group,method,requested_time_limit,actual_time_limit,exit_code,start_time,end_time,result_file,log_file,progress_log' | Set-Content $ExitCsv }
if(!(Test-Path $SkippedCsv)){ 'name,requested_time_limit,actual_time_limit,command,reason,usable_for_paper_evidence' | Set-Content $SkippedCsv }
function Q([string]$s){ if($s -match '\s'){ return '"' + $s + '"' } return $s }
function Append-CommandLine($Name, $ArgList) {
    $line = '.\build\ExactEBRP.exe ' + (($ArgList | ForEach-Object { Q $_ }) -join ' ')
    Add-Content $CommandFile ''
    Add-Content $CommandFile ("## " + $Name)
    Add-Content $CommandFile '```powershell'
    Add-Content $CommandFile $line
    Add-Content $CommandFile '```'
}
function Run-Case($Name, $Group, $Method, $InputPath, [double]$TimeLimit, $Preset, $OutDir, $ExtraArgs) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    $out = Join-Path $OutDir ($Name + '.json')
    $log = Join-Path $Logs ($Name + '.log')
    $stdout = Join-Path $Logs ($Name + '.stdout.log')
    $progress = Join-Path $Progress ($Name + '.csv')
    $argList = @('--method', $Method, '--input', $InputPath, '--lambda', '0.15', '--T', '3600', '--time-limit', ([string]$TimeLimit), '--out', $out, '--log', $log)
    if($TimeLimit -ge 300){ $argList += @('--progress-log', $progress, '--progress-interval-seconds', '60') }
    if($Preset -and $Preset.Length -gt 0){ $argList += @('--algorithm-preset', $Preset) }
    if($ExtraArgs){ $argList += $ExtraArgs }
    Append-CommandLine $Name $argList
    $start = Get-Date -Format o
    & $Exe @argList 2>&1 | Tee-Object -FilePath $stdout
    $exit = $LASTEXITCODE
    $end = Get-Date -Format o
    $csvLine = '"{0}","{1}","{2}",{3},{4},{5},"{6}","{7}","{8}","{9}","{10}"' -f $Name,$Group,$Method,$TimeLimit,$TimeLimit,$exit,$start,$end,$out,$log,$progress
    Add-Content $ExitCsv $csvLine
    return [pscustomobject]@{Name=$Name;Group=$Group;Exit=$exit;Out=$out;Log=$log;Progress=$progress}
}
function Get-Prop($obj, [string[]]$names, $default='') {
    foreach ($n in $names) {
        $prop = $obj.PSObject.Properties[$n]
        if ($null -ne $prop -and $null -ne $prop.Value -and [string]$prop.Value -ne '') {
            return $prop.Value
        }
    }
    return $default
}
function JsonRows($Dir) {
    if(!(Test-Path $Dir)){ return @() }
    return Get-ChildItem $Dir -Filter *.json -File | ForEach-Object {
        try {
            $j = Get-Content $_.FullName -Raw | ConvertFrom-Json
            $j | Add-Member -NotePropertyName result_file -NotePropertyValue $_.FullName -Force
            $j
        } catch {
            [pscustomobject]@{ instance='parse_error'; status='parse_error'; result_file=$_.FullName; parse_error=$_.Exception.Message }
        }
    }
}
function Row($j, $Variant) {
    [pscustomobject]@{
        instance=$j.instance; instance_scope=$j.instance_scope; algorithm_preset=$j.algorithm_preset; method=$j.method; variant=$Variant; status=$j.status; objective=$j.objective; lower_bound=$j.lower_bound; upper_bound=$j.upper_bound; gap=$j.gap; runtime_seconds=$j.runtime_seconds; wall_time_seconds=$j.wall_time_seconds; verifier_passed=$j.verifier_passed; certified_original_problem=$j.certified_original_problem; incumbent_archive_selected=$j.incumbent_archive_selected; incumbent_archive_best_objective=$j.incumbent_archive_best_objective; incumbent_archive_best_source=$j.incumbent_archive_best_source; unresolved_intervals=$j.unresolved_intervals; invalid_bound_intervals=$j.invalid_bound_intervals; open_nodes=$j.open_nodes; frontier_min_interval_lower_bound=$j.frontier_min_interval_lower_bound; frontier_lower_bound_source=$j.frontier_lower_bound_source; bound_time_seconds=$j.bound_time_seconds; route_mask_time_seconds=$j.route_mask_time_seconds; master_time_seconds=$j.master_time_seconds; pricing_time_seconds=$j.pricing_time_seconds; cuts_added=$j.cuts_added; nodes=$j.nodes; columns=$j.columns; compact_status=$j.compact_status; compact_LB=$j.compact_LB; compact_UB=$j.compact_UB; compact_gap=$j.compact_gap; cplex_status=($(if($j.method -eq 'cplex'){$j.status}else{''})); cplex_LB=($(if($j.method -eq 'cplex'){$j.lower_bound}else{''})); cplex_UB=($(if($j.method -eq 'cplex'){$j.upper_bound}else{''})); cplex_gap=($(if($j.method -eq 'cplex'){$j.gap}else{''})); certificate_module=$j.certificate_module; progress_log=$j.progress_log; result_file=$j.result_file; log_file=$j.log_file; notes=($j.notes -join ' | ')
    }
}
function Generate-Summaries {
    $all = @(); $all += JsonRows $Raw; $all += JsonRows $AblationDir; $all += JsonRows $PortfolioDir; $all += JsonRows $CplexDir
    $allRows = @(); foreach($j in $all){ $variant = [IO.Path]::GetFileNameWithoutExtension($j.result_file); $allRows += Row $j $variant }
    $allRows | Export-Csv (Join-Path $Root 'longrun_summary.csv') -NoTypeInformation
    $abl = @(); foreach($j in (JsonRows $AblationDir)){ $abl += Row $j ([IO.Path]::GetFileNameWithoutExtension($j.result_file)) }
    $abl | Export-Csv (Join-Path $Root 'ablation_summary.csv') -NoTypeInformation
    $cp = @(); foreach($j in (JsonRows $CplexDir)){ $cp += Row $j ([IO.Path]::GetFileNameWithoutExtension($j.result_file)) }
    $cp | Export-Csv (Join-Path $Root 'cplex_benchmark_summary.csv') -NoTypeInformation
    $port = @(); foreach($j in (JsonRows $PortfolioDir)){ $port += Row $j ([IO.Path]::GetFileNameWithoutExtension($j.result_file)) }
    $port += $cp
    $port | Export-Csv (Join-Path $Root 'portfolio_summary.csv') -NoTypeInformation
    $conv = @()
    Get-ChildItem $Progress -Filter *.csv -File -ErrorAction SilentlyContinue | ForEach-Object {
        try { $p = Import-Csv $_.FullName } catch { $p=@() }
        if($p.Count -gt 0){
            $first=$p[0]; $last=$p[$p.Count-1]
            $ubs = $p | ForEach-Object { [double](Get-Prop $_ @('incumbent_UB','upper_bound') 'NaN') } | Where-Object { -not [double]::IsNaN($_) }
            $lbs = $p | ForEach-Object { [double](Get-Prop $_ @('global_LB','lower_bound') 'NaN') } | Where-Object { -not [double]::IsNaN($_) }
            $gaps = $p | ForEach-Object { [double](Get-Prop $_ @('gap') 'NaN') } | Where-Object { -not [double]::IsNaN($_) }
            $conv += [pscustomobject]@{ progress_log=$_.FullName; checkpoints=$p.Count; initial_UB=($ubs|Select-Object -First 1); best_UB=($ubs|Measure-Object -Minimum).Minimum; initial_LB=($lbs|Select-Object -First 1); best_LB=($lbs|Measure-Object -Maximum).Maximum; final_gap=($gaps|Select-Object -Last 1); gap_still_decreasing=($(if($gaps.Count -gt 1){ [double]($gaps[-1]) -lt [double]($gaps[0]) } else { $false })); unresolved_intervals_at_end=$last.unresolved_intervals; open_nodes_at_end=$last.open_nodes; bound_time_seconds=$last.bound_time_seconds; route_mask_time_seconds=$last.route_mask_time_seconds; master_time_seconds=$last.master_time_seconds; pricing_time_seconds=$last.pricing_time_seconds }
        }
    }
    $conv | Export-Csv (Join-Path $Root 'convergence_summary.csv') -NoTypeInformation
    $audit=@()
    foreach($j in $all){
        $fail=$false; $reasons=@()
        if($j.option_audit_consistent -eq $false){$fail=$true; $reasons+='option_audit_mismatch'}
        if(($j.certified_original_problem -eq $true) -and ([double]$j.gap -gt 1e-7)){ $fail=$true; $reasons+='positive_gap_certified' }
        if(($j.certified_original_problem -eq $true) -and ($j.verifier_passed -ne $true)){ $fail=$true; $reasons+='certified_without_verifier' }
        if(($j.certified_original_problem -eq $true) -and ([int](Get-Prop $j @('unresolved_intervals') 0) -ne 0)){ $fail=$true; $reasons+='certified_with_unresolved_intervals' }
        if(($j.certified_original_problem -eq $true) -and ([int](Get-Prop $j @('invalid_bound_intervals') 0) -ne 0)){ $fail=$true; $reasons+='certified_with_invalid_bound_intervals' }
        if(($j.instance_scope -eq 'diagnostic_large') -and ($j.certified_original_problem -eq $true)){ $fail=$true; $reasons+='diagnostic_large_certified' }
        if(($j.certificate_module -eq 'compact') -and (([double](Get-Prop $j @('compact_gap') 0) -gt 1e-7) -or ($j.verifier_passed -ne $true))){ $fail=$true; $reasons+='invalid_compact_certificate' }
        if(($j.method -eq 'cplex') -and ($j.certified_original_problem -eq $true) -and ([double]$j.gap -gt 1e-7)){ $fail=$true; $reasons+='invalid_cplex_certificate' }
        if(($j.instance_source_path -match 'reference/generated') -and ($j.instance_scope -eq 'historical_target')){ $fail=$true; $reasons+='generated_labeled_historical' }
        $audit += [pscustomobject]@{ result_file=$j.result_file; instance=$j.instance; status=$j.status; certified_original_problem=$j.certified_original_problem; gap=$j.gap; verifier_passed=$j.verifier_passed; unresolved_intervals=$j.unresolved_intervals; invalid_bound_intervals=$j.invalid_bound_intervals; audit_failed=$fail; failure_reasons=($reasons -join ';') }
    }
    $audit | Export-Csv (Join-Path $Root 'result_integrity_audit.csv') -NoTypeInformation
    $audit | Export-Csv (Join-Path $AuditDir 'result_integrity_audit.csv') -NoTypeInformation
    $failed=($audit|Where-Object {$_.audit_failed}).Count
    $certs=($all|Where-Object {$_.certified_original_problem -eq $true}|ForEach-Object {$_.instance}) -join ', '
    $noncert=($all|Where-Object {$_.certified_original_problem -ne $true}|ForEach-Object {$_.instance}|Sort-Object -Unique) -join ', '
    $notes = @('# Long-run Round 17 Local Notes','',"Git SHA: $Sha",'',"Build: fallback MSYS2 g++ because CMake was unavailable.",'',"CPLEX available: $([bool](Get-Command cplex -ErrorAction SilentlyContinue))",'',"Audit failed rows: $failed",'',"Certified instances: $certs",'',"Noncertified instances: $noncert",'',"Skipped/shortened commands are listed in skipped_or_shortened_runs.csv.",'',"Suggested next experiment: rerun any row whose convergence_summary shows decreasing gap at timeout with a 7200s limit, prioritizing V12 M2 paper-bpc-core and compact fallback.")
    $notes | Set-Content (Join-Path $Root 'notes.md')
}
# Smoke preset runs
$smoke = 'testdata\examples\gcap_smoke_V4_M1.txt'
Run-Case 'v4_paper_bpc_core' 'smoke' 'gcap-frontier' $smoke 30 'paper-bpc-core' $Raw @('--incumbent-archive-dir','results') | Out-Null
Run-Case 'v4_paper_exact_portfolio' 'smoke' 'gcap-frontier' $smoke 30 'paper-exact-portfolio' $Raw @('--incumbent-archive-dir','results') | Out-Null
Run-Case 'v4_paper_bpc_experimental' 'smoke' 'gcap-frontier' $smoke 30 'paper-bpc-experimental' $Raw @('--incumbent-archive-dir','results') | Out-Null
Run-Case 'v4_diagnostic_large' 'smoke' 'large-relaxed-rmp-cg-test' $smoke 30 'diagnostic-large' $Raw @() | Out-Null
$diagMethods = @('pricing','pricing-branch','cuts','branching','master','cg','gcap-cg','gcap-tree','gcap-frontier','dominance-test','support-pruning-test','route-mask-support-test','route-mask-operation-budget-test','adaptive-frontier-split-test','inventory-branching-test','operation-mode-branching-test','pricing-closure-audit-test','resume-state-test','pricing-verifier-test','iterative-closure-test','certificate-basis-test','option-consistency-test','station-set-test','ng-dssr-pricing-test','dssr-exactness-test','dual-stabilization-test','bpc-hybrid-pricing-test','two-track-column-test','projection-safe-relaxed-column-test','non-elementary-relaxed-column-test','ng-relaxed-closure-test','relaxed-rmp-cg-test','frontier-relaxed-rmp-cg-test','relaxed-rmp-test','relaxed-pricing-closure-test','relaxed-column-incumbent-safety-test','large-relaxed-rmp-test','large-relaxed-rmp-cg-test','external-incumbent-test','large-instance-mode-test','large-lb-test','incumbent-import-test','route-pool-incumbent-test','pickup-drop-compat-flow-test','pickup-drop-transfer-cap-test','vehicle-indexed-relaxation-test','vehicle-indexed-transfer-flow-test')
foreach($m in $diagMethods){ Run-Case ('v4_' + $m) 'smoke-diagnostic' $m $smoke 60 '' $Raw @() | Out-Null }
Generate-Summaries
$core = Get-Content (Join-Path $Raw 'v4_paper_bpc_core.json') -Raw | ConvertFrom-Json
$port = Get-Content (Join-Path $Raw 'v4_paper_exact_portfolio.json') -Raw | ConvertFrom-Json
if((-not $core.certified_original_problem) -or ([double]$core.objective -ne 0) -or (-not $port.certified_original_problem) -or ([double]$port.objective -ne 0)){
    Add-Content (Join-Path $Root 'notes.md') "`nV4 smoke failed; long-run campaign stopped."
    exit 2
}
if($SmokeOnly){ Generate-Summaries; exit 0 }
# Main long runs
$v12m2='reference\regen_candidate_V12_M2_average.txt'
$v12m1='reference\regen_candidate_V12_M1_average.txt'
$archive=@('--incumbent-archive-auto','true','--incumbent-archive-dir','results')
Run-Case 'v12_m2_paper_bpc_core_3600s' 'main-longrun' 'gcap-frontier' $v12m2 3600 'paper-bpc-core' $Raw $archive | Out-Null; Generate-Summaries
Run-Case 'v12_m2_paper_exact_portfolio_3600s' 'main-longrun' 'gcap-frontier' $v12m2 3600 'paper-exact-portfolio' $PortfolioDir $archive | Out-Null; Generate-Summaries
Run-Case 'v12_m1_paper_bpc_core_3600s' 'main-longrun' 'gcap-frontier' $v12m1 3600 'paper-bpc-core' $Raw $archive | Out-Null; Generate-Summaries
Run-Case 'v12_m1_paper_exact_portfolio_3600s' 'main-longrun' 'gcap-frontier' $v12m1 3600 'paper-exact-portfolio' $PortfolioDir $archive | Out-Null; Generate-Summaries
# V12 M2 ablation 1200s
$common=@('--incumbent-archive-auto','true','--incumbent-archive-dir','results','--bpc-incumbent','auto','--pricing-engine','exact-label')
Run-Case 'v12_m2_ablation_base_bpc_1200s' 'ablation' 'gcap-frontier' $v12m2 1200 '' $AblationDir ($common + @('--column-dominance','false','--projection-bound','false','--penalty-domain-tightening','false','--movement-domain-tightening','false','--vehicle-indexed-operation-relaxation','false','--vehicle-indexed-transfer-flow','false','--route-mask-operation-budget-cuts','false','--route-pool-incumbent','false','--branch-inventory','false','--branch-operation-mode','false')) | Out-Null; Generate-Summaries
Run-Case 'v12_m2_ablation_plus_dominance_1200s' 'ablation' 'gcap-frontier' $v12m2 1200 '' $AblationDir ($common + @('--column-dominance','true','--gcap-pricing-columns','4','--projection-bound','false','--penalty-domain-tightening','false','--movement-domain-tightening','false','--vehicle-indexed-operation-relaxation','false','--vehicle-indexed-transfer-flow','false','--route-mask-operation-budget-cuts','false','--route-pool-incumbent','false','--branch-inventory','false','--branch-operation-mode','false')) | Out-Null; Generate-Summaries
Run-Case 'v12_m2_ablation_plus_movement_projection_1200s' 'ablation' 'gcap-frontier' $v12m2 1200 '' $AblationDir ($common + @('--column-dominance','true','--gcap-pricing-columns','4','--projection-bound','true','--penalty-domain-tightening','true','--movement-domain-tightening','true','--vehicle-indexed-operation-relaxation','false','--vehicle-indexed-transfer-flow','false','--route-mask-operation-budget-cuts','false','--route-pool-incumbent','false','--branch-inventory','false','--branch-operation-mode','false')) | Out-Null; Generate-Summaries
Run-Case 'v12_m2_ablation_plus_vehicle_relaxation_1200s' 'ablation' 'gcap-frontier' $v12m2 1200 '' $AblationDir ($common + @('--column-dominance','true','--gcap-pricing-columns','4','--projection-bound','true','--penalty-domain-tightening','true','--movement-domain-tightening','true','--vehicle-indexed-operation-relaxation','true','--vehicle-indexed-transfer-flow','true','--route-mask-operation-budget-cuts','false','--route-pool-incumbent','true','--branch-inventory','false','--branch-operation-mode','false')) | Out-Null; Generate-Summaries
Run-Case 'v12_m2_ablation_plus_operation_budget_1200s' 'ablation' 'gcap-frontier' $v12m2 1200 '' $AblationDir ($common + @('--column-dominance','true','--gcap-pricing-columns','4','--projection-bound','true','--penalty-domain-tightening','true','--movement-domain-tightening','true','--vehicle-indexed-operation-relaxation','true','--vehicle-indexed-transfer-flow','true','--route-mask-operation-budget-cuts','true','--route-pool-incumbent','true','--branch-inventory','false','--branch-operation-mode','false')) | Out-Null; Generate-Summaries
Run-Case 'v12_m2_ablation_plus_branching_1200s' 'ablation' 'gcap-frontier' $v12m2 1200 '' $AblationDir ($common + @('--column-dominance','true','--gcap-pricing-columns','4','--projection-bound','true','--penalty-domain-tightening','true','--movement-domain-tightening','true','--vehicle-indexed-operation-relaxation','true','--vehicle-indexed-transfer-flow','true','--route-mask-operation-budget-cuts','true','--route-pool-incumbent','true','--branch-inventory','true','--branch-operation-mode','true')) | Out-Null; Generate-Summaries
Run-Case 'v12_m2_ablation_full_paper_bpc_core_1200s' 'ablation' 'gcap-frontier' $v12m2 1200 'paper-bpc-core' $AblationDir $archive | Out-Null; Generate-Summaries
Run-Case 'v12_m2_ablation_paper_bpc_experimental_1200s' 'ablation' 'gcap-frontier' $v12m2 1200 'paper-bpc-experimental' $AblationDir $archive | Out-Null; Generate-Summaries
# V12 M1 minimum ablation rows
Run-Case 'v12_m1_ablation_full_paper_bpc_core_1200s' 'ablation' 'gcap-frontier' $v12m1 1200 'paper-bpc-core' $AblationDir $archive | Out-Null; Generate-Summaries
Run-Case 'v12_m1_ablation_paper_bpc_experimental_1200s' 'ablation' 'gcap-frontier' $v12m1 1200 'paper-bpc-experimental' $AblationDir $archive | Out-Null; Generate-Summaries
# Generated engineering rows
Run-Case 'v8_m2_paper_bpc_core_300s' 'generated' 'gcap-frontier' 'reference\generated\regen_V8_M2_average.txt' 300 'paper-bpc-core' $AblationDir $archive | Out-Null; Generate-Summaries
Run-Case 'v10_m2_paper_bpc_core_300s' 'generated' 'gcap-frontier' 'reference\generated\regen_V10_M2_average.txt' 300 'paper-bpc-core' $AblationDir $archive | Out-Null; Generate-Summaries
Run-Case 'v20_m2_paper_bpc_core_300s' 'generated' 'gcap-frontier' 'reference\generated\regen_V20_M2_average.txt' 300 'paper-bpc-core' $AblationDir $archive | Out-Null; Generate-Summaries
# CPLEX and compact rows
if(Get-Command cplex -ErrorAction SilentlyContinue){
    Run-Case 'v12_m2_plain_cplex_3600s' 'cplex' 'cplex' $v12m2 3600 '' $CplexDir @('--plain-baseline') | Out-Null; Generate-Summaries
    Run-Case 'v12_m2_strengthened_compact_3600s' 'compact' 'tailored' $v12m2 3600 'paper-exact-portfolio' $CplexDir @() | Out-Null; Generate-Summaries
    Run-Case 'v12_m1_plain_cplex_3600s' 'cplex' 'cplex' $v12m1 3600 '' $CplexDir @('--plain-baseline') | Out-Null; Generate-Summaries
    Run-Case 'v12_m1_strengthened_compact_3600s' 'compact' 'tailored' $v12m1 3600 'paper-exact-portfolio' $CplexDir @() | Out-Null; Generate-Summaries
} else {
    Add-Content $SkippedCsv ('"plain_cplex_v12_m2",3600,0,"cplex --plain-baseline","cplex not found in PATH",false')
    Add-Content $SkippedCsv ('"compact_v12_m2",3600,0,"tailored compact","cplex not found in PATH",false')
}
Generate-Summaries
