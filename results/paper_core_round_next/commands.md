# paper_core_round_next commands

## Build
CMake unavailable (`cmake` command not found). Used fallback g++ build:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
```

## v12_m2_vehicle_relaxation_repro_1200s
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v12_m2_vehicle_relaxation_repro_1200s.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v12_m2_vehicle_relaxation_repro_1200s.log --progress-log E:\codes\ExactEBRP\results\paper_core_round_next\progress\v12_m2_vehicle_relaxation_repro_1200s.csv --progress-interval-seconds 60 --incumbent-archive-auto true --incumbent-archive-dir results --bpc-incumbent auto --pricing-engine exact-label --column-dominance true --gcap-pricing-columns 4 --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --route-mask-operation-budget-cuts false --route-pool-incumbent true --branch-inventory false --branch-operation-mode false

## v4_paper_core_smoke_30s
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --progress-log E:\codes\ExactEBRP\results\paper_core_round_next\progress\v4_paper_core_smoke_30s.csv --progress-interval-seconds 5 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v4_paper_core_smoke_30s.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v4_paper_core_smoke_30s.log

## v12_m2_paper_core_300s_relax_portfolio
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --progress-log E:\codes\ExactEBRP\results\paper_core_round_next\progress\v12_m2_paper_core_300s_relax_portfolio.csv --progress-interval-seconds 60 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v12_m2_paper_core_300s_relax_portfolio.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v12_m2_paper_core_300s_relax_portfolio.log

## v12_m2_paper_core_1200s_relax_portfolio
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --progress-log E:\codes\ExactEBRP\results\paper_core_round_next\progress\v12_m2_paper_core_1200s_relax_portfolio.csv --progress-interval-seconds 60 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v12_m2_paper_core_1200s_relax_portfolio.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v12_m2_paper_core_1200s_relax_portfolio.log

## v12_m1_paper_core_300s_relax_portfolio
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --progress-log E:\codes\ExactEBRP\results\paper_core_round_next\progress\v12_m1_paper_core_300s_relax_portfolio.csv --progress-interval-seconds 60 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v12_m1_paper_core_300s_relax_portfolio.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v12_m1_paper_core_300s_relax_portfolio.log

## v12_m1_paper_core_1200s_relax_portfolio
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --progress-log E:\codes\ExactEBRP\results\paper_core_round_next\progress\v12_m1_paper_core_1200s_relax_portfolio.csv --progress-interval-seconds 60 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v12_m1_paper_core_1200s_relax_portfolio.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v12_m1_paper_core_1200s_relax_portfolio.log

## v12_m1_plain_cplex_300s
.\build\ExactEBRP.exe --method cplex --plain-baseline --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v12_m1_plain_cplex_300s.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v12_m1_plain_cplex_300s.log

## v12_m2_plain_cplex_300s
.\build\ExactEBRP.exe --method cplex --plain-baseline --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v12_m2_plain_cplex_300s.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v12_m2_plain_cplex_300s.log

## v12_m1_paper_core_1200s_relax_portfolio
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --progress-log E:\codes\ExactEBRP\results\paper_core_round_next\progress\v12_m1_paper_core_1200s_relax_portfolio.csv --progress-interval-seconds 60 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v12_m1_paper_core_1200s_relax_portfolio.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v12_m1_paper_core_1200s_relax_portfolio.log

## certificate_guard_fixtures
.\build\ExactEBRP.exe --method certificate-basis-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\certificate_guard_fixtures.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\certificate_guard_fixtures.log

## v4_paper_core_smoke_current_30s
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --progress-log E:\codes\ExactEBRP\results\paper_core_round_next\progress\v4_paper_core_smoke_current_30s.csv --progress-interval-seconds 5 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\v4_paper_core_smoke_current_30s.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\v4_paper_core_smoke_current_30s.log

## option_consistency_paper_core
.\build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out E:\codes\ExactEBRP\results\paper_core_round_next\raw\option_consistency_paper_core.json --log E:\codes\ExactEBRP\results\paper_core_round_next\logs\option_consistency_paper_core.log
