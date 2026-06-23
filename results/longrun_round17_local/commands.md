# Long-run Round 17 Local Commands

## Preconditions
```powershell
git status
git rev-parse HEAD
git branch --show-current
```

## Build attempt: CMake
```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

Result: CMake unavailable on PATH; fallback g++ build used.

## Build fallback: main executable
```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
```

## Build fallback: compare executable
```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## v4_paper_bpc_core
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_paper_bpc_core.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_paper_bpc_core.log --algorithm-preset paper-bpc-core --incumbent-archive-dir results
```

## v4_paper_exact_portfolio
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_paper_exact_portfolio.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_paper_exact_portfolio.log --algorithm-preset paper-exact-portfolio --incumbent-archive-dir results
```

## v4_paper_bpc_experimental
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_paper_bpc_experimental.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_paper_bpc_experimental.log --algorithm-preset paper-bpc-experimental --incumbent-archive-dir results
```

## v4_diagnostic_large
```powershell
.\build\ExactEBRP.exe --method large-relaxed-rmp-cg-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_diagnostic_large.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_diagnostic_large.log --algorithm-preset diagnostic-large
```

## v4_pricing
```powershell
.\build\ExactEBRP.exe --method pricing --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_pricing.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_pricing.log
```

## v4_pricing-branch
```powershell
.\build\ExactEBRP.exe --method pricing-branch --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_pricing-branch.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_pricing-branch.log
```

## v4_cuts
```powershell
.\build\ExactEBRP.exe --method cuts --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_cuts.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_cuts.log
```

## v4_branching
```powershell
.\build\ExactEBRP.exe --method branching --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_branching.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_branching.log
```

## v4_master
```powershell
.\build\ExactEBRP.exe --method master --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_master.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_master.log
```

## v4_cg
```powershell
.\build\ExactEBRP.exe --method cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_cg.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_cg.log
```

## v4_gcap-cg
```powershell
.\build\ExactEBRP.exe --method gcap-cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_gcap-cg.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_gcap-cg.log
```

## v4_gcap-tree
```powershell
.\build\ExactEBRP.exe --method gcap-tree --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_gcap-tree.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_gcap-tree.log
```

## v4_gcap-frontier
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_gcap-frontier.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_gcap-frontier.log
```

## v4_dominance-test
```powershell
.\build\ExactEBRP.exe --method dominance-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_dominance-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_dominance-test.log
```

## v4_support-pruning-test
```powershell
.\build\ExactEBRP.exe --method support-pruning-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_support-pruning-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_support-pruning-test.log
```

## v4_route-mask-support-test
```powershell
.\build\ExactEBRP.exe --method route-mask-support-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_route-mask-support-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_route-mask-support-test.log
```

## v4_route-mask-operation-budget-test
```powershell
.\build\ExactEBRP.exe --method route-mask-operation-budget-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_route-mask-operation-budget-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_route-mask-operation-budget-test.log
```

## v4_adaptive-frontier-split-test
```powershell
.\build\ExactEBRP.exe --method adaptive-frontier-split-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_adaptive-frontier-split-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_adaptive-frontier-split-test.log
```

## v4_inventory-branching-test
```powershell
.\build\ExactEBRP.exe --method inventory-branching-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_inventory-branching-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_inventory-branching-test.log
```

## v4_operation-mode-branching-test
```powershell
.\build\ExactEBRP.exe --method operation-mode-branching-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_operation-mode-branching-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_operation-mode-branching-test.log
```

## v4_pricing-closure-audit-test
```powershell
.\build\ExactEBRP.exe --method pricing-closure-audit-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_pricing-closure-audit-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_pricing-closure-audit-test.log
```

## v4_resume-state-test
```powershell
.\build\ExactEBRP.exe --method resume-state-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_resume-state-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_resume-state-test.log
```

## v4_pricing-verifier-test
```powershell
.\build\ExactEBRP.exe --method pricing-verifier-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_pricing-verifier-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_pricing-verifier-test.log
```

## v4_iterative-closure-test
```powershell
.\build\ExactEBRP.exe --method iterative-closure-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_iterative-closure-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_iterative-closure-test.log
```

## v4_certificate-basis-test
```powershell
.\build\ExactEBRP.exe --method certificate-basis-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_certificate-basis-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_certificate-basis-test.log
```

## v4_option-consistency-test
```powershell
.\build\ExactEBRP.exe --method option-consistency-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_option-consistency-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_option-consistency-test.log
```

## v4_station-set-test
```powershell
.\build\ExactEBRP.exe --method station-set-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_station-set-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_station-set-test.log
```

## v4_ng-dssr-pricing-test
```powershell
.\build\ExactEBRP.exe --method ng-dssr-pricing-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_ng-dssr-pricing-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_ng-dssr-pricing-test.log
```

## v4_dssr-exactness-test
```powershell
.\build\ExactEBRP.exe --method dssr-exactness-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_dssr-exactness-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_dssr-exactness-test.log
```

## v4_dual-stabilization-test
```powershell
.\build\ExactEBRP.exe --method dual-stabilization-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_dual-stabilization-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_dual-stabilization-test.log
```

## v4_bpc-hybrid-pricing-test
```powershell
.\build\ExactEBRP.exe --method bpc-hybrid-pricing-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_bpc-hybrid-pricing-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_bpc-hybrid-pricing-test.log
```

## v4_two-track-column-test
```powershell
.\build\ExactEBRP.exe --method two-track-column-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_two-track-column-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_two-track-column-test.log
```

## v4_projection-safe-relaxed-column-test
```powershell
.\build\ExactEBRP.exe --method projection-safe-relaxed-column-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_projection-safe-relaxed-column-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_projection-safe-relaxed-column-test.log
```

## v4_non-elementary-relaxed-column-test
```powershell
.\build\ExactEBRP.exe --method non-elementary-relaxed-column-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_non-elementary-relaxed-column-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_non-elementary-relaxed-column-test.log
```

## v4_ng-relaxed-closure-test
```powershell
.\build\ExactEBRP.exe --method ng-relaxed-closure-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_ng-relaxed-closure-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_ng-relaxed-closure-test.log
```

## v4_relaxed-rmp-cg-test
```powershell
.\build\ExactEBRP.exe --method relaxed-rmp-cg-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_relaxed-rmp-cg-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_relaxed-rmp-cg-test.log
```

## v4_frontier-relaxed-rmp-cg-test
```powershell
.\build\ExactEBRP.exe --method frontier-relaxed-rmp-cg-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_frontier-relaxed-rmp-cg-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_frontier-relaxed-rmp-cg-test.log
```

## v4_relaxed-rmp-test
```powershell
.\build\ExactEBRP.exe --method relaxed-rmp-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_relaxed-rmp-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_relaxed-rmp-test.log
```

## v4_relaxed-pricing-closure-test
```powershell
.\build\ExactEBRP.exe --method relaxed-pricing-closure-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_relaxed-pricing-closure-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_relaxed-pricing-closure-test.log
```

## v4_relaxed-column-incumbent-safety-test
```powershell
.\build\ExactEBRP.exe --method relaxed-column-incumbent-safety-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_relaxed-column-incumbent-safety-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_relaxed-column-incumbent-safety-test.log
```

## v4_large-relaxed-rmp-test
```powershell
.\build\ExactEBRP.exe --method large-relaxed-rmp-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_large-relaxed-rmp-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_large-relaxed-rmp-test.log
```

## v4_large-relaxed-rmp-cg-test
```powershell
.\build\ExactEBRP.exe --method large-relaxed-rmp-cg-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_large-relaxed-rmp-cg-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_large-relaxed-rmp-cg-test.log
```

## v4_external-incumbent-test
```powershell
.\build\ExactEBRP.exe --method external-incumbent-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_external-incumbent-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_external-incumbent-test.log
```

## v4_large-instance-mode-test
```powershell
.\build\ExactEBRP.exe --method large-instance-mode-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_large-instance-mode-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_large-instance-mode-test.log
```

## v4_large-lb-test
```powershell
.\build\ExactEBRP.exe --method large-lb-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_large-lb-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_large-lb-test.log
```

## v4_incumbent-import-test
```powershell
.\build\ExactEBRP.exe --method incumbent-import-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_incumbent-import-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_incumbent-import-test.log
```

## v4_route-pool-incumbent-test
```powershell
.\build\ExactEBRP.exe --method route-pool-incumbent-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_route-pool-incumbent-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_route-pool-incumbent-test.log
```

## v4_pickup-drop-compat-flow-test
```powershell
.\build\ExactEBRP.exe --method pickup-drop-compat-flow-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_pickup-drop-compat-flow-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_pickup-drop-compat-flow-test.log
```

## v4_pickup-drop-transfer-cap-test
```powershell
.\build\ExactEBRP.exe --method pickup-drop-transfer-cap-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_pickup-drop-transfer-cap-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_pickup-drop-transfer-cap-test.log
```

## v4_vehicle-indexed-relaxation-test
```powershell
.\build\ExactEBRP.exe --method vehicle-indexed-relaxation-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_vehicle-indexed-relaxation-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_vehicle-indexed-relaxation-test.log
```

## v4_vehicle-indexed-transfer-flow-test
```powershell
.\build\ExactEBRP.exe --method vehicle-indexed-transfer-flow-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 60 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v4_vehicle-indexed-transfer-flow-test.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v4_vehicle-indexed-transfer-flow-test.log
```

## v12_m2_paper_bpc_core_3600s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 3600 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v12_m2_paper_bpc_core_3600s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m2_paper_bpc_core_3600s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m2_paper_bpc_core_3600s.csv --progress-interval-seconds 60 --algorithm-preset paper-bpc-core --incumbent-archive-auto true --incumbent-archive-dir results
```

## v12_m2_paper_exact_portfolio_3600s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 3600 --out E:\codes\ExactEBRP\results\longrun_round17_local\portfolio\v12_m2_paper_exact_portfolio_3600s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m2_paper_exact_portfolio_3600s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m2_paper_exact_portfolio_3600s.csv --progress-interval-seconds 60 --algorithm-preset paper-exact-portfolio --incumbent-archive-auto true --incumbent-archive-dir results
```

## v12_m1_paper_bpc_core_3600s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 3600 --out E:\codes\ExactEBRP\results\longrun_round17_local\raw\v12_m1_paper_bpc_core_3600s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m1_paper_bpc_core_3600s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m1_paper_bpc_core_3600s.csv --progress-interval-seconds 60 --algorithm-preset paper-bpc-core --incumbent-archive-auto true --incumbent-archive-dir results
```

## v12_m1_paper_exact_portfolio_3600s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 3600 --out E:\codes\ExactEBRP\results\longrun_round17_local\portfolio\v12_m1_paper_exact_portfolio_3600s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m1_paper_exact_portfolio_3600s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m1_paper_exact_portfolio_3600s.csv --progress-interval-seconds 60 --algorithm-preset paper-exact-portfolio --incumbent-archive-auto true --incumbent-archive-dir results
```

## v12_m2_ablation_base_bpc_1200s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --out E:\codes\ExactEBRP\results\longrun_round17_local\ablation\v12_m2_ablation_base_bpc_1200s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m2_ablation_base_bpc_1200s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m2_ablation_base_bpc_1200s.csv --progress-interval-seconds 60 --incumbent-archive-auto true --incumbent-archive-dir results --bpc-incumbent auto --pricing-engine exact-label --column-dominance false --projection-bound false --penalty-domain-tightening false --movement-domain-tightening false --vehicle-indexed-operation-relaxation false --vehicle-indexed-transfer-flow false --route-mask-operation-budget-cuts false --route-pool-incumbent false --branch-inventory false --branch-operation-mode false
```

## v12_m2_ablation_plus_dominance_1200s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --out E:\codes\ExactEBRP\results\longrun_round17_local\ablation\v12_m2_ablation_plus_dominance_1200s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m2_ablation_plus_dominance_1200s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m2_ablation_plus_dominance_1200s.csv --progress-interval-seconds 60 --incumbent-archive-auto true --incumbent-archive-dir results --bpc-incumbent auto --pricing-engine exact-label --column-dominance true --gcap-pricing-columns 4 --projection-bound false --penalty-domain-tightening false --movement-domain-tightening false --vehicle-indexed-operation-relaxation false --vehicle-indexed-transfer-flow false --route-mask-operation-budget-cuts false --route-pool-incumbent false --branch-inventory false --branch-operation-mode false
```

## v12_m2_ablation_plus_movement_projection_1200s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --out E:\codes\ExactEBRP\results\longrun_round17_local\ablation\v12_m2_ablation_plus_movement_projection_1200s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m2_ablation_plus_movement_projection_1200s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m2_ablation_plus_movement_projection_1200s.csv --progress-interval-seconds 60 --incumbent-archive-auto true --incumbent-archive-dir results --bpc-incumbent auto --pricing-engine exact-label --column-dominance true --gcap-pricing-columns 4 --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --vehicle-indexed-operation-relaxation false --vehicle-indexed-transfer-flow false --route-mask-operation-budget-cuts false --route-pool-incumbent false --branch-inventory false --branch-operation-mode false
```

## v12_m2_ablation_plus_vehicle_relaxation_1200s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --out E:\codes\ExactEBRP\results\longrun_round17_local\ablation\v12_m2_ablation_plus_vehicle_relaxation_1200s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m2_ablation_plus_vehicle_relaxation_1200s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m2_ablation_plus_vehicle_relaxation_1200s.csv --progress-interval-seconds 60 --incumbent-archive-auto true --incumbent-archive-dir results --bpc-incumbent auto --pricing-engine exact-label --column-dominance true --gcap-pricing-columns 4 --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --route-mask-operation-budget-cuts false --route-pool-incumbent true --branch-inventory false --branch-operation-mode false
```

## v12_m2_ablation_plus_operation_budget_1200s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --out E:\codes\ExactEBRP\results\longrun_round17_local\ablation\v12_m2_ablation_plus_operation_budget_1200s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m2_ablation_plus_operation_budget_1200s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m2_ablation_plus_operation_budget_1200s.csv --progress-interval-seconds 60 --incumbent-archive-auto true --incumbent-archive-dir results --bpc-incumbent auto --pricing-engine exact-label --column-dominance true --gcap-pricing-columns 4 --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --route-mask-operation-budget-cuts true --route-pool-incumbent true --branch-inventory false --branch-operation-mode false
```

## v12_m2_ablation_plus_branching_1200s
```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --out E:\codes\ExactEBRP\results\longrun_round17_local\ablation\v12_m2_ablation_plus_branching_1200s.json --log E:\codes\ExactEBRP\results\longrun_round17_local\logs\v12_m2_ablation_plus_branching_1200s.log --progress-log E:\codes\ExactEBRP\results\longrun_round17_local\progress\v12_m2_ablation_plus_branching_1200s.csv --progress-interval-seconds 60 --incumbent-archive-auto true --incumbent-archive-dir results --bpc-incumbent auto --pricing-engine exact-label --column-dominance true --gcap-pricing-columns 4 --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --route-mask-operation-budget-cuts true --route-pool-incumbent true --branch-inventory true --branch-operation-mode true
```
