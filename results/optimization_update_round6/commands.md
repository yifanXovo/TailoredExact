# Round 6 Commands

Build attempted first with CMake:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

CMake was unavailable, so the fallback build was used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

V4 smoke diagnostics were run for:

```text
pricing, pricing-branch, cuts, branching, master, cg, gcap-cg, gcap-tree, gcap-frontier,
dominance-test, support-pruning-test, route-mask-support-test, incumbent-import-test,
route-pool-incumbent-test, pickup-drop-compat-flow-test, pickup-drop-transfer-cap-test
```

Representative smoke command:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --max-nodes 15 --gcap-pricing-columns 2 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-focused-relax-seconds 1 --route-pool-incumbent true --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --support-duration-pruning true --route-mask-support-duration-pruning true --out results\optimization_update_round6\raw\smoke_gcap-frontier.json --log results\optimization_update_round6\logs\smoke_gcap-frontier.log
```

V12 incumbent audit command template:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 45 --frontier-intervals 2 --frontier-retry-passes 0 --frontier-final-closure false --max-nodes 2 --frontier-relax-seconds 0.5 --route-mask-max-v 12 --bpc-incumbent auto --bpc-incumbent-seconds 24 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry false --frontier-focused-intensification false --route-pool-incumbent false --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --support-duration-pruning true --route-mask-support-duration-pruning true --gcap-pricing-columns 2 --out results\optimization_update_round6\raw\incumbent_v12_m1_average_auto.json --log results\optimization_update_round6\logs\incumbent_v12_m1_average_auto.log
```

V12 improved 300s command template:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 300 --frontier-intervals 2 --frontier-retry-passes 0 --frontier-final-closure false --max-nodes 3 --frontier-relax-seconds 1.0 --route-mask-max-v 12 --bpc-incumbent auto --bpc-incumbent-seconds 30 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-focused-reserve-fraction 0.25 --frontier-focused-relax-seconds 4 --frontier-focused-max-passes 2 --route-pool-incumbent true --route-pool-max-columns-per-vehicle 5000 --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --support-duration-pruning true --route-mask-support-duration-pruning true --gcap-pricing-columns 2 --progress-log results\optimization_update_round6\raw\progress_v12_m2_average_improved_full_300s.csv --progress-interval-seconds 30 --out results\optimization_update_round6\raw\ablation_v12_m2_average_improved_full_300s.json --log results\optimization_update_round6\logs\ablation_v12_m2_average_improved_full_300s.log
```

1200s reproduction command template, not run locally in round six:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 1200 --frontier-intervals 2 --frontier-retry-passes 0 --frontier-final-closure false --max-nodes 3 --frontier-relax-seconds 1.0 --route-mask-max-v 12 --bpc-incumbent auto --bpc-incumbent-seconds 60 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-focused-reserve-fraction 0.25 --frontier-focused-relax-seconds 8 --frontier-focused-max-passes 3 --route-pool-incumbent true --route-pool-max-columns-per-vehicle 5000 --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --support-duration-pruning true --route-mask-support-duration-pruning true --gcap-pricing-columns 2 --progress-log results\optimization_update_round6\raw\progress_v12_m2_average_improved_full_1200s.csv --progress-interval-seconds 30 --out results\optimization_update_round6\raw\ablation_v12_m2_average_improved_full_1200s.json --log results\optimization_update_round6\logs\ablation_v12_m2_average_improved_full_1200s.log
```
