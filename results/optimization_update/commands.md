# Optimization Update Commands

Date: 2026-06-20.

## Build

CMake was unavailable on this machine, so the fallback build was used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## Smoke Tests

```powershell
build\ExactEBRP.exe --method pricing --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 10 --out results\optimization_update\raw\smoke_pricing.json
build\ExactEBRP.exe --method pricing-branch --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 10 --out results\optimization_update\raw\smoke_pricing_branch.json
build\ExactEBRP.exe --method cuts --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 10 --out results\optimization_update\raw\smoke_cuts.json
build\ExactEBRP.exe --method branching --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 10 --out results\optimization_update\raw\smoke_branching.json
build\ExactEBRP.exe --method master --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 10 --out results\optimization_update\raw\smoke_master.json
build\ExactEBRP.exe --method cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 10 --out results\optimization_update\raw\smoke_cg.json
build\ExactEBRP.exe --method gcap-cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 10 --out results\optimization_update\raw\smoke_gcap_cg.json
build\ExactEBRP.exe --method gcap-tree --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 10 --out results\optimization_update\raw\smoke_gcap_tree.json --gcap-pricing-columns 4
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --gcap-pricing-columns 4 --column-dominance true --projection-bound true --penalty-domain-tightening true --out results\optimization_update\raw\smoke_gcap_frontier_full.json
```

## Ablation

```powershell
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --gcap-pricing-columns 1 --column-dominance false --projection-bound false --penalty-domain-tightening false --out results\optimization_update\raw\ablation_v4_off.json
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --gcap-pricing-columns 1 --column-dominance true --projection-bound false --penalty-domain-tightening false --out results\optimization_update\raw\ablation_v4_dominance.json
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --gcap-pricing-columns 1 --column-dominance false --projection-bound true --penalty-domain-tightening true --out results\optimization_update\raw\ablation_v4_projection_penalty.json
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --gcap-pricing-columns 4 --column-dominance true --projection-bound true --penalty-domain-tightening true --out results\optimization_update\raw\ablation_v4_full.json
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --gcap-pricing-columns 4 --column-dominance true --projection-bound true --penalty-domain-tightening true --frontier-column-cache true --out results\optimization_update\raw\ablation_v4_cache_requested.json
```

## V12 Stress Smoke

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --bpc-workers 1 --frontier-intervals 4 --frontier-retry-passes 1 --frontier-relax-seconds 3 --route-mask-max-v 12 --gcap-pricing-columns 1 --column-dominance false --projection-bound false --penalty-domain-tightening false --bpc-incumbent greedy --bpc-incumbent-seconds 5 --out results\optimization_update\raw\stress_v12_m1_average_off_60s.json
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --bpc-workers 1 --frontier-intervals 4 --frontier-retry-passes 1 --frontier-relax-seconds 3 --route-mask-max-v 12 --gcap-pricing-columns 4 --column-dominance true --projection-bound true --penalty-domain-tightening true --bpc-incumbent greedy --bpc-incumbent-seconds 5 --out results\optimization_update\raw\stress_v12_m1_average_full_60s.json
```
