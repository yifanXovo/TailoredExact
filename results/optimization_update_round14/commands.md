# Round 14 Commands

Build:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

CMake was unavailable, so the fallback builds were used:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

V4 smoke diagnostics:

```powershell
pricing
pricing-branch
cuts
branching
master
cg
gcap-cg
gcap-tree
gcap-frontier
dominance-test
support-pruning-test
route-mask-support-test
route-mask-operation-budget-test
incumbent-import-test
route-pool-incumbent-test
pickup-drop-compat-flow-test
pickup-drop-transfer-cap-test
vehicle-indexed-relaxation-test
vehicle-indexed-transfer-flow-test
adaptive-frontier-split-test
inventory-branching-test
operation-mode-branching-test
pricing-closure-audit-test
resume-state-test
pricing-verifier-test
iterative-closure-test
certificate-basis-test
station-set-test
ng-dssr-pricing-test
dssr-exactness-test
dual-stabilization-test
bpc-hybrid-pricing-test
external-incumbent-test
large-instance-mode-test
large-lb-test
two-track-column-test
relaxed-rmp-test
relaxed-pricing-closure-test
relaxed-column-incumbent-safety-test
large-relaxed-rmp-test
```

Each V4 row used:

```powershell
build\ExactEBRP.exe --method <method> --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 4 --gcap-pricing-columns 4 --pricing-engine hybrid --column-tracks two-track --relaxed-columns-in-rmp true --rmp-column-space two-track --dssr-final-exact true --dssr-close-relaxed-pricing true --large-relaxed-rmp true --progress-log results\optimization_update_round14\raw\progress_v4_<method>.csv --progress-interval-seconds 10 --out results\optimization_update_round14\raw\v4_<method>.json
```

Main comparison rows:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 8 --frontier-refine-splits 1 --gcap-pricing-columns 8 --pricing-engine exact-label --column-tracks elementary-only --rmp-column-space elementary --progress-log results\optimization_update_round14\raw\progress_v4_frontier_exact.csv --out results\optimization_update_round14\raw\v4_frontier_exact.json

build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 8 --frontier-refine-splits 1 --gcap-pricing-columns 8 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --dssr-final-exact true --dssr-close-relaxed-pricing true --progress-log results\optimization_update_round14\raw\progress_v4_frontier_twotrack.csv --out results\optimization_update_round14\raw\v4_frontier_twotrack.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514 --frontier-focus-time-limit 300 --pricing-engine exact-label --column-tracks elementary-only --rmp-column-space elementary --progress-log results\optimization_update_round14\raw\progress_v12_m2_focus_exact_300s.csv --out results\optimization_update_round14\raw\v12_m2_focus_exact_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514 --frontier-focus-time-limit 300 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --dssr-final-exact true --dssr-close-relaxed-pricing true --progress-log results\optimization_update_round14\raw\progress_v12_m2_focus_twotrack_300s.csv --out results\optimization_update_round14\raw\v12_m2_focus_twotrack_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 8 --frontier-refine-splits 1 --gcap-pricing-columns 8 --pricing-engine exact-label --column-tracks elementary-only --rmp-column-space elementary --progress-log results\optimization_update_round14\raw\progress_v12_m2_full_exact_300s.csv --out results\optimization_update_round14\raw\v12_m2_full_exact_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 8 --frontier-refine-splits 1 --gcap-pricing-columns 8 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --dssr-final-exact true --dssr-close-relaxed-pricing true --progress-log results\optimization_update_round14\raw\progress_v12_m2_full_twotrack_300s.csv --out results\optimization_update_round14\raw\v12_m2_full_twotrack_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 8 --frontier-refine-splits 1 --gcap-pricing-columns 8 --pricing-engine exact-label --column-tracks elementary-only --rmp-column-space elementary --progress-log results\optimization_update_round14\raw\progress_v12_m1_full_exact_300s.csv --out results\optimization_update_round14\raw\v12_m1_full_exact_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 8 --frontier-refine-splits 1 --gcap-pricing-columns 8 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --dssr-final-exact true --dssr-close-relaxed-pricing true --progress-log results\optimization_update_round14\raw\progress_v12_m1_full_twotrack_300s.csv --out results\optimization_update_round14\raw\v12_m1_full_twotrack_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\generated\regen_V20_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 8 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --large-relaxed-rmp true --large-lb-mode movement-projection --large-instance-mode auto --progress-log results\optimization_update_round14\raw\progress_v20_twotrack_frontier_300s.csv --out results\optimization_update_round14\raw\v20_twotrack_frontier_300s.json

build\ExactEBRP.exe --method large-relaxed-rmp-test --input reference\generated\regen_V50_M3_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --large-relaxed-rmp true --large-lb-mode movement-projection --large-instance-mode force --progress-log results\optimization_update_round14\raw\progress_v50_relaxed_rmp_300s.csv --out results\optimization_update_round14\raw\v50_relaxed_rmp_300s.json

build\ExactEBRP.exe --method large-relaxed-rmp-test --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --column-tracks two-track --rmp-column-space two-track --relaxed-columns-in-rmp true --large-relaxed-rmp true --large-lb-mode movement-projection --large-instance-mode force --progress-log results\optimization_update_round14\raw\progress_v100_relaxed_rmp_300s.csv --out results\optimization_update_round14\raw\v100_relaxed_rmp_300s.json
```
