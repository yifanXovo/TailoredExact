# Round 12 commands

## Build

CMake was attempted first and failed because `cmake` is not installed:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

Fallback build commands used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## Smoke diagnostics

All smoke commands used `testdata\examples\gcap_smoke_V4_M1.txt`, `--lambda 0.15`, `--T 3600`, and `--time-limit 20`; outputs are in `results\optimization_update_round12\raw\smoke_*.json` and logs are in matching `.log` files.

Methods run:

```text
pricing, pricing-branch, cuts, branching, master, cg, gcap-cg, gcap-tree, gcap-frontier, dominance-test, support-pruning-test, route-mask-support-test, route-mask-operation-budget-test, incumbent-import-test, route-pool-incumbent-test, pickup-drop-compat-flow-test, pickup-drop-transfer-cap-test, vehicle-indexed-relaxation-test, vehicle-indexed-transfer-flow-test, adaptive-frontier-split-test, inventory-branching-test, operation-mode-branching-test, pricing-closure-audit-test, resume-state-test, pricing-verifier-test, iterative-closure-test, certificate-basis-test, station-set-test, ng-dssr-pricing-test, dssr-exactness-test, dual-stabilization-test, external-incumbent-test, large-instance-mode-test
```

## V12 pricing diagnostics

```powershell
build\ExactEBRP.exe --method pricing --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --pricing-engine exact-label --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization none --out results\optimization_update_round12\raw\v12_m2_pricing_exact_60s.json
build\ExactEBRP.exe --method pricing --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --pricing-engine ng-dssr --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization none --out results\optimization_update_round12\raw\v12_m2_pricing_ngdssr_60s.json
build\ExactEBRP.exe --method pricing --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --pricing-engine hybrid --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization smooth --out results\optimization_update_round12\raw\v12_m2_pricing_hybrid_smooth_60s.json
build\ExactEBRP.exe --method pricing --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --pricing-engine exact-label --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization none --out results\optimization_update_round12\raw\v12_m1_pricing_exact_60s.json
build\ExactEBRP.exe --method pricing --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --pricing-engine hybrid --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization smooth --out results\optimization_update_round12\raw\v12_m1_pricing_hybrid_smooth_60s.json
```

## V12 frontier diagnostics

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --threads 4 --bpc-workers 4 --pricing-threads 1 --frontier-intervals 8 --frontier-refine-splits 2 --frontier-final-closure true --frontier-final-nodes 31 --frontier-focused-intensification true --frontier-adaptive-split true --route-mask-operation-budget-cuts true --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --route-pool-incumbent true --bpc-incumbent auto --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --pricing-engine hybrid --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization smooth --progress-log results\optimization_update_round12\raw\v12_m2_frontier_hybrid_300s_progress.csv --progress-interval-seconds 30 --out results\optimization_update_round12\raw\v12_m2_frontier_hybrid_300s.json
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt [same options] --progress-log results\optimization_update_round12\raw\v12_m1_frontier_hybrid_300s_progress.csv --out results\optimization_update_round12\raw\v12_m1_frontier_hybrid_300s.json
```

## Scalability diagnostics

```powershell
build\ExactEBRP.exe --method large-instance-mode-test --input reference\generated\regen_V70_M5_average.txt --lambda 0.15 --T 3600 --time-limit 20 --large-instance-mode force --pricing-engine hybrid --out results\optimization_update_round12\raw\V70_large_mode.json
build\ExactEBRP.exe --method large-instance-mode-test --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --time-limit 20 --large-instance-mode force --pricing-engine hybrid --out results\optimization_update_round12\raw\V100_large_mode.json
build\ExactEBRP.exe --method pricing --input reference\generated\regen_V20_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --large-instance-mode auto --pricing-engine hybrid --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization smooth --out results\optimization_update_round12\raw\V20_pricing_hybrid_60s.json
build\ExactEBRP.exe --method pricing --input reference\generated\regen_V50_M3_average.txt --lambda 0.15 --T 3600 --time-limit 60 --large-instance-mode auto --pricing-engine hybrid --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization smooth --out results\optimization_update_round12\raw\V50_pricing_hybrid_60s.json
build\ExactEBRP.exe --method pricing --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --time-limit 60 --large-instance-mode auto --pricing-engine hybrid --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization smooth --out results\optimization_update_round12\raw\V100_pricing_hybrid_60s.json
```
