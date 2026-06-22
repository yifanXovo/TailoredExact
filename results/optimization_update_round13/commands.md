# Round 13 commands

Build attempted:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

CMake was unavailable, so fallback build used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
```

Smoke diagnostics used `testdata/examples/gcap_smoke_V4_M1.txt` with methods:
`pricing`, `pricing-branch`, `cuts`, `branching`, `master`, `cg`, `gcap-cg`,
`gcap-tree`, `gcap-frontier`, `dominance-test`, `support-pruning-test`,
`route-mask-support-test`, `route-mask-operation-budget-test`,
`incumbent-import-test`, `route-pool-incumbent-test`,
`pickup-drop-compat-flow-test`, `pickup-drop-transfer-cap-test`,
`vehicle-indexed-relaxation-test`, `vehicle-indexed-transfer-flow-test`,
`adaptive-frontier-split-test`, `inventory-branching-test`,
`operation-mode-branching-test`, `pricing-closure-audit-test`,
`resume-state-test`, `pricing-verifier-test`, `iterative-closure-test`,
`certificate-basis-test`, `station-set-test`, `ng-dssr-pricing-test`,
`dssr-exactness-test`, `dual-stabilization-test`, `external-incumbent-test`,
`large-instance-mode-test`, `bpc-hybrid-pricing-test`, and `large-lb-test`.

Key V12 commands:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514 --frontier-focus-time-limit 300 --frontier-closure-mode exact-cg --closure-max-cg-iterations 80 --pricing-engine exact-label --large-lb-mode movement-projection --progress-log results\optimization_update_round13\raw\progress_v12_m2_focus_exact_300s.csv --out results\optimization_update_round13\raw\v12_m2_focus_exact_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514 --frontier-focus-time-limit 300 --frontier-closure-mode exact-cg --closure-max-cg-iterations 80 --pricing-engine hybrid --ng-size 8 --ng-neighborhood-mode nearest --dssr-max-rounds 5 --dssr-expand-per-round 3 --dssr-time-limit 20 --dssr-final-exact true --large-lb-mode movement-projection --progress-log results\optimization_update_round13\raw\progress_v12_m2_focus_hybrid_300s.csv --out results\optimization_update_round13\raw\v12_m2_focus_hybrid_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 8 --frontier-adaptive-split true --frontier-focused-intensification true --frontier-iterative-closure true --frontier-iterative-max-rounds 2 --frontier-iterative-round-time 60 --pricing-engine hybrid --ng-size 8 --ng-neighborhood-mode dual-aware --dssr-final-exact true --cg-dual-stabilization smooth --progress-log results\optimization_update_round13\raw\progress_v12_m2_full_hybrid_300s.csv --out results\optimization_update_round13\raw\v12_m2_full_hybrid_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 8 --frontier-adaptive-split true --frontier-focused-intensification true --pricing-engine hybrid --ng-size 8 --ng-neighborhood-mode dual-aware --dssr-final-exact true --cg-dual-stabilization smooth --progress-log results\optimization_update_round13\raw\progress_v12_m1_full_hybrid_300s.csv --out results\optimization_update_round13\raw\v12_m1_full_hybrid_300s.json
```

Scale diagnostics:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\generated\regen_V20_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --large-instance-mode auto --large-lb-mode movement-projection --pricing-engine hybrid --ng-size 12 --ng-neighborhood-mode hybrid --dssr-max-rounds 5 --cg-dual-stabilization smooth --out results\optimization_update_round13\raw\v20_hybrid_300s.json

build\ExactEBRP.exe --method pricing --input reference\generated\regen_V50_M3_average.txt --lambda 0.15 --T 3600 --time-limit 300 --large-instance-mode auto --large-lb-mode movement-projection --pricing-engine hybrid --ng-size 12 --ng-neighborhood-mode hybrid --dssr-max-rounds 5 --dssr-final-exact false --out results\optimization_update_round13\raw\v50_hybrid_pricing_300s.json

build\ExactEBRP.exe --method pricing --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --time-limit 300 --large-instance-mode auto --large-lb-mode movement-projection --pricing-engine hybrid --ng-size 12 --ng-neighborhood-mode hybrid --dssr-max-rounds 5 --dssr-final-exact false --out results\optimization_update_round13\raw\v100_hybrid_pricing_300s.json
```
