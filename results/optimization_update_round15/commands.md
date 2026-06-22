# Round 15 Commands

Build attempted first with CMake:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

CMake was unavailable, so fallback builds were used:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

V4 smoke diagnostics used `testdata/examples/gcap_smoke_V4_M1.txt` with methods:

```text
pricing pricing-branch cuts branching master cg gcap-cg gcap-tree gcap-frontier dominance-test support-pruning-test route-mask-support-test route-mask-operation-budget-test adaptive-frontier-split-test inventory-branching-test operation-mode-branching-test pricing-closure-audit-test resume-state-test pricing-verifier-test iterative-closure-test certificate-basis-test station-set-test ng-dssr-pricing-test dssr-exactness-test dual-stabilization-test bpc-hybrid-pricing-test two-track-column-test projection-safe-relaxed-column-test non-elementary-relaxed-column-test ng-relaxed-closure-test relaxed-rmp-cg-test frontier-relaxed-rmp-cg-test relaxed-rmp-test relaxed-pricing-closure-test relaxed-column-incumbent-safety-test large-relaxed-rmp-test large-relaxed-rmp-cg-test external-incumbent-test large-instance-mode-test large-lb-test incumbent-import-test route-pool-incumbent-test pickup-drop-compat-flow-test pickup-drop-transfer-cap-test vehicle-indexed-relaxation-test vehicle-indexed-transfer-flow-test
```

Main rows:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine exact-label --column-tracks elementary-only --relaxed-rmp-cg false --frontier-focus-only true --frontier-focus-range 0.489218,0.512514
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --allow-non-elementary-relaxed-columns true --relaxed-rmp-cg true --frontier-relaxed-rmp-cg true --ng-relaxed-closure true --gcap-pricing-columns 4 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine exact-label --column-tracks elementary-only --relaxed-rmp-cg false
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --allow-non-elementary-relaxed-columns true --relaxed-rmp-cg true --frontier-relaxed-rmp-cg true --ng-relaxed-closure true --gcap-pricing-columns 4
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine exact-label --column-tracks elementary-only --relaxed-rmp-cg false
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --allow-non-elementary-relaxed-columns true --relaxed-rmp-cg true --frontier-relaxed-rmp-cg true --ng-relaxed-closure true --gcap-pricing-columns 4
build\ExactEBRP.exe --method gcap-frontier --input reference\generated\regen_V20_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --allow-non-elementary-relaxed-columns true --relaxed-rmp-cg true --frontier-relaxed-rmp-cg true --ng-relaxed-closure true --gcap-pricing-columns 4
build\ExactEBRP.exe --method large-relaxed-rmp-cg-test --input reference\generated\regen_V50_M3_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --large-instance-mode force --large-relaxed-rmp-cg true --large-relaxed-rmp-time 300 --large-relaxed-rmp-column-budget 256 --ng-relaxed-closure true --allow-non-elementary-relaxed-columns true
build\ExactEBRP.exe --method large-relaxed-rmp-cg-test --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --large-instance-mode force --large-relaxed-rmp-cg true --large-relaxed-rmp-time 300 --large-relaxed-rmp-column-budget 256 --ng-relaxed-closure true --allow-non-elementary-relaxed-columns true
```
