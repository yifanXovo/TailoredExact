# Round 8 Commands

## Build

CMake was attempted first but was unavailable on this machine (`cmake` was not
recognized). The fallback builds used were:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## Generated V8/V10 Inputs

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\generate_reference_instances.py
```

Generated files and seeds are recorded in
`reference/generated/manifest.csv` and copied to
`results/optimization_update_round8/generated_instance_manifest.csv`.

## V4 Smoke Diagnostics

Each smoke command used `testdata\examples\gcap_smoke_V4_M1.txt`, `lambda=0.15`,
`T=3600`, and wrote raw JSON under `results\optimization_update_round8\raw\`
and logs under `logs\optimization_update_round8\`.

```powershell
build\ExactEBRP.exe --method pricing --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_pricing.json --log logs\optimization_update_round8\smoke_pricing.log
build\ExactEBRP.exe --method pricing-branch --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_pricing-branch.json --log logs\optimization_update_round8\smoke_pricing-branch.log
build\ExactEBRP.exe --method cuts --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_cuts.json --log logs\optimization_update_round8\smoke_cuts.log
build\ExactEBRP.exe --method branching --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_branching.json --log logs\optimization_update_round8\smoke_branching.log
build\ExactEBRP.exe --method master --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_master.json --log logs\optimization_update_round8\smoke_master.log
build\ExactEBRP.exe --method cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_cg.json --log logs\optimization_update_round8\smoke_cg.log
build\ExactEBRP.exe --method gcap-cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_gcap-cg.json --log logs\optimization_update_round8\smoke_gcap-cg.log
build\ExactEBRP.exe --method gcap-tree --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_gcap-tree.json --log logs\optimization_update_round8\smoke_gcap-tree.log
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out results\optimization_update_round8\raw\smoke_gcap-frontier.json --log logs\optimization_update_round8\smoke_gcap-frontier.log --progress-log results\optimization_update_round8\raw\progress_smoke_gcap-frontier.csv
build\ExactEBRP.exe --method dominance-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_dominance-test.json --log logs\optimization_update_round8\smoke_dominance-test.log
build\ExactEBRP.exe --method support-pruning-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_support-pruning-test.json --log logs\optimization_update_round8\smoke_support-pruning-test.log
build\ExactEBRP.exe --method route-mask-support-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_route-mask-support-test.json --log logs\optimization_update_round8\smoke_route-mask-support-test.log
build\ExactEBRP.exe --method route-mask-operation-budget-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --route-mask-operation-budget-cuts true --out results\optimization_update_round8\raw\smoke_route-mask-operation-budget-test.json --log logs\optimization_update_round8\smoke_route-mask-operation-budget-test.log
build\ExactEBRP.exe --method incumbent-import-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round8\raw\smoke_incumbent-import-test.json --log logs\optimization_update_round8\smoke_incumbent-import-test.log
build\ExactEBRP.exe --method route-pool-incumbent-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --route-pool-incumbent true --out results\optimization_update_round8\raw\smoke_route-pool-incumbent-test.json --log logs\optimization_update_round8\smoke_route-pool-incumbent-test.log
build\ExactEBRP.exe --method pickup-drop-compat-flow-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --pickup-drop-compat-flow true --out results\optimization_update_round8\raw\smoke_pickup-drop-compat-flow-test.json --log logs\optimization_update_round8\smoke_pickup-drop-compat-flow-test.log
build\ExactEBRP.exe --method pickup-drop-transfer-cap-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --out results\optimization_update_round8\raw\smoke_pickup-drop-transfer-cap-test.json --log logs\optimization_update_round8\smoke_pickup-drop-transfer-cap-test.log
build\ExactEBRP.exe --method vehicle-indexed-relaxation-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --vehicle-indexed-operation-relaxation true --out results\optimization_update_round8\raw\smoke_vehicle-indexed-relaxation-test.json --log logs\optimization_update_round8\smoke_vehicle-indexed-relaxation-test.log
build\ExactEBRP.exe --method vehicle-indexed-transfer-flow-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --out results\optimization_update_round8\raw\smoke_vehicle-indexed-transfer-flow-test.json --log logs\optimization_update_round8\smoke_vehicle-indexed-transfer-flow-test.log
build\ExactEBRP.exe --method adaptive-frontier-split-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --frontier-adaptive-split true --out results\optimization_update_round8\raw\smoke_adaptive-frontier-split-test.json --log logs\optimization_update_round8\smoke_adaptive-frontier-split-test.log
```

## V12 Ablations

The V12 matrix used `reference\regen_candidate_V12_M1_average.txt` and
`reference\regen_candidate_V12_M2_average.txt`. Variants were:

- `round7_baseline`: previous round-seven improved settings.
- `vehicle_indexed_ops_only`: vehicle-indexed operation relaxation enabled,
  vehicle-indexed transfer flow disabled.
- `vehicle_transfer_flow_only`: vehicle-indexed operation and transfer flow
  enabled.
- `focus_interval_only`: selected global-min-LB interval only; diagnostic scope.
- `improved_full`: all round-eight improvements enabled.
- `improved_full_300s`: all round-eight improvements enabled with 300s cap.
- `improved_full_1200s`: V12 M2 only, all round-eight improvements enabled.

Representative improved-full command:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 300 --frontier-intervals 2 --frontier-retry-passes 0 --max-nodes 3 --bpc-incumbent auto --route-pool-incumbent true --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --frontier-adaptive-split true --frontier-focused-intensification true --route-mask-operation-budget-cuts true --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --progress-log results\optimization_update_round8\raw\progress_v12_m2_average_improved_full_300s.csv --progress-interval-seconds 30 --out results\optimization_update_round8\raw\ablation_v12_m2_average_improved_full_300s.json --log logs\optimization_update_round8\ablation_v12_m2_average_improved_full_300s.log
```

V12 M2 1200s command:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 1200 --frontier-intervals 2 --frontier-retry-passes 0 --max-nodes 3 --bpc-incumbent auto --route-pool-incumbent true --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --frontier-adaptive-split true --frontier-focused-intensification true --route-mask-operation-budget-cuts true --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --progress-log results\optimization_update_round8\raw\progress_v12_m2_average_improved_full_1200s.csv --progress-interval-seconds 30 --out results\optimization_update_round8\raw\ablation_v12_m2_average_improved_full_1200s.json --log logs\optimization_update_round8\ablation_v12_m2_average_improved_full_1200s.log
```

V12 M1 1200s was not run locally; V12 M2 was prioritized as the required
serious row for this pass.

## Generated V8/V10 Runs

Every generated V8/V10 instance in `reference\generated\` was run for 60s with
the same improved-full switches. Raw files are named
`generated_<instance>_improved_full_60s.json`.

## Error Scan

Logs were scanned with:

```powershell
Select-String -Path logs\optimization_update_round8\*.log -Pattern 'AddressSanitizer|access violation|segmentation|segfault|bad_alloc|out of memory|-1073741819|3221225477|STATUS_ACCESS_VIOLATION' -CaseSensitive:$false
```

No matches were found.
