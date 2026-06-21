# Round 7 Commands

## Build

CMake was attempted first and was unavailable:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

Fallback builds used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## V4 Smoke Diagnostics

Methods run on `testdata/examples/gcap_smoke_V4_M1.txt` with 30s cap:

```text
pricing, pricing-branch, cuts, branching, master, cg, gcap-cg, gcap-tree, gcap-frontier,
dominance-test, support-pruning-test, route-mask-support-test, incumbent-import-test,
route-pool-incumbent-test, pickup-drop-compat-flow-test, pickup-drop-transfer-cap-test,
route-mask-operation-budget-test, adaptive-frontier-split-test
```

Representative command:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input testdata/examples/gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 30 --frontier-intervals 2 --frontier-relax-seconds 1 --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-adaptive-split true --route-mask-operation-budget-cuts true --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --progress-log results\optimization_update_round7\raw\progress_smoke_v4_gcap-frontier_final_progress.csv --progress-interval-seconds 5 --out results\optimization_update_round7\raw\smoke_v4_gcap-frontier_final_progress.json
```

## V12 Ablation Template

All V12 ablation rows use the same base settings and vary adaptive splitting and operation-budget cuts:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input <V12-instance> --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit <60-or-300> --frontier-intervals 2 --frontier-retry-passes 0 --frontier-final-closure false --max-nodes 3 --frontier-relax-seconds 1.0 --route-mask-max-v 12 --bpc-incumbent auto --bpc-incumbent-seconds <15-or-30> --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-focused-reserve-fraction 0.25 --frontier-focused-relax-seconds <3-or-4> --frontier-focused-max-passes 2 --frontier-adaptive-split <true-or-false> --frontier-adaptive-max-depth 3 --frontier-adaptive-min-width 0.0001 --frontier-adaptive-split-factor 2 --route-mask-operation-budget-cuts <true-or-false> --route-pool-incumbent true --route-pool-max-columns-per-vehicle 5000 --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --support-duration-pruning true --route-mask-support-duration-pruning true --gcap-pricing-columns 2 --progress-log <progress.csv> --progress-interval-seconds <10-or-30> --log <log> --out <json>
```

Variants run for both `reference/regen_candidate_V12_M1_average.txt` and `reference/regen_candidate_V12_M2_average.txt`:

```text
round6_baseline: adaptive=false, operation_budget=false, 60s
operation_budget_only: adaptive=false, operation_budget=true, 60s
adaptive_split_only: adaptive=true, operation_budget=false, 60s
split_plus_budget: adaptive=true, operation_budget=true, 60s
improved_full: adaptive=true, operation_budget=true, 60s
improved_full_300s: adaptive=true, operation_budget=true, 300s
```

## 1200s Reproduction Commands

The 1200s rows were not run locally in this pass because the required smoke plus V12 60s/300s suite already consumed about 31 minutes of wall time; these commands are prepared for reproduction:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 1200 --frontier-intervals 2 --frontier-retry-passes 0 --frontier-final-closure false --max-nodes 3 --frontier-relax-seconds 1.0 --route-mask-max-v 12 --bpc-incumbent auto --bpc-incumbent-seconds 60 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-focused-reserve-fraction 0.25 --frontier-focused-relax-seconds 8 --frontier-focused-max-passes 3 --frontier-adaptive-split true --frontier-adaptive-max-depth 3 --frontier-adaptive-min-width 0.0001 --frontier-adaptive-split-factor 2 --route-mask-operation-budget-cuts true --route-pool-incumbent true --route-pool-max-columns-per-vehicle 5000 --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --support-duration-pruning true --route-mask-support-duration-pruning true --gcap-pricing-columns 2 --progress-log results\optimization_update_round7\raw\progress_v12_m1_average_improved_full_1200s.csv --progress-interval-seconds 30 --out results\optimization_update_round7\raw\ablation_v12_m1_average_improved_full_1200s.json --log results\optimization_update_round7\logs\ablation_v12_m1_average_improved_full_1200s.log
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 1200 --frontier-intervals 2 --frontier-retry-passes 0 --frontier-final-closure false --max-nodes 3 --frontier-relax-seconds 1.0 --route-mask-max-v 12 --bpc-incumbent auto --bpc-incumbent-seconds 60 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-focused-reserve-fraction 0.25 --frontier-focused-relax-seconds 8 --frontier-focused-max-passes 3 --frontier-adaptive-split true --frontier-adaptive-max-depth 3 --frontier-adaptive-min-width 0.0001 --frontier-adaptive-split-factor 2 --route-mask-operation-budget-cuts true --route-pool-incumbent true --route-pool-max-columns-per-vehicle 5000 --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --support-duration-pruning true --route-mask-support-duration-pruning true --gcap-pricing-columns 2 --progress-log results\optimization_update_round7\raw\progress_v12_m2_average_improved_full_1200s.csv --progress-interval-seconds 30 --out results\optimization_update_round7\raw\ablation_v12_m2_average_improved_full_1200s.json --log results\optimization_update_round7\logs\ablation_v12_m2_average_improved_full_1200s.log
```
