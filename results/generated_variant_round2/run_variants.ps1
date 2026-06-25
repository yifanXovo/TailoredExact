$ErrorActionPreference = "Continue"
$exe = "build\ExactEBRP.exe"
$rows = @(
  @{name="regen_candidate_V12_M1_average_capinv_seed260626"; input="reference\generated_variants\regen_candidate_V12_M1_average_capinv_seed260626.txt"; limit=120},
  @{name="regen_candidate_V12_M1_average_capinv_seed260627"; input="reference\generated_variants\regen_candidate_V12_M1_average_capinv_seed260627.txt"; limit=120},
  @{name="regen_candidate_V12_M1_average_capinv_seed260628"; input="reference\generated_variants\regen_candidate_V12_M1_average_capinv_seed260628.txt"; limit=120},
  @{name="regen_candidate_V12_M2_average_capinv_seed261626"; input="reference\generated_variants\regen_candidate_V12_M2_average_capinv_seed261626.txt"; limit=120},
  @{name="regen_candidate_V12_M2_average_capinv_seed261627"; input="reference\generated_variants\regen_candidate_V12_M2_average_capinv_seed261627.txt"; limit=120},
  @{name="regen_candidate_V12_M2_average_capinv_seed261628"; input="reference\generated_variants\regen_candidate_V12_M2_average_capinv_seed261628.txt"; limit=120},
  @{name="regen_V10_M2_average_capinv_seed262626"; input="reference\generated_variants\regen_V10_M2_average_capinv_seed262626.txt"; limit=60},
  @{name="regen_V10_M2_average_capinv_seed262627"; input="reference\generated_variants\regen_V10_M2_average_capinv_seed262627.txt"; limit=60},
  @{name="regen_V8_M2_average_capinv_seed263626"; input="reference\generated_variants\regen_V8_M2_average_capinv_seed263626.txt"; limit=60},
  @{name="regen_V8_M2_average_capinv_seed263627"; input="reference\generated_variants\regen_V8_M2_average_capinv_seed263627.txt"; limit=60}
)
New-Item -ItemType Directory -Force results\generated_variant_round2\raw, results\generated_variant_round2\logs, results\generated_variant_round2\progress, results\generated_variant_round2\incumbents | Out-Null
"name,status,start,end" | Set-Content results\generated_variant_round2\run_status.csv
foreach ($row in $rows) {
  $name = $row.name
  $inputPath = $row.input
  $limit = $row.limit
  $start = Get-Date -Format o
  Add-Content results\generated_variant_round2\run_status.csv "$name,started,$start,"
  $cmd = "$exe --method gcap-frontier --algorithm-preset paper-bpc-core --input $inputPath --lambda 0.15 --T 3600 --time-limit $limit --primal-heuristic hga-tgbc --primal-heuristic-seconds 30 --primal-heuristic-runs 40 --primal-heuristic-seed 20260626 --heuristic-candidates-csv results\primal_ub_improvement_round\heuristic_candidates.csv --export-incumbent results\generated_variant_round2\incumbents\$name`_incumbent.json --progress-log results\generated_variant_round2\progress\$name.csv --progress-interval-seconds 30 --out results\generated_variant_round2\raw\$name.json"
  $cmd | Set-Content "results\generated_variant_round2\logs\$name.command.txt"
  Invoke-Expression $cmd *> "results\generated_variant_round2\logs\$name.log"
  $end = Get-Date -Format o
  Add-Content results\generated_variant_round2\run_status.csv "$name,finished,,$end"
}
