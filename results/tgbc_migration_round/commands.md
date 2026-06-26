# TGBC Migration Round Commands

Build:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
```

Final smoke and UB tests:

```powershell
.\build\ExactEBRP.exe --method primal-heuristic --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 3 --primal-heuristic-runs 12 --primal-heuristic-seed 20260626 --heuristic-candidates-csv results\tgbc_migration_round\heuristic_candidates_v6_v4.csv --export-incumbent results\tgbc_migration_round\incumbents\v4_hga_tgbc_v6.json --out results\tgbc_migration_round\raw\v4_hga_tgbc_v6.json

.\build\ExactEBRP.exe --method primal-heuristic --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 60 --primal-heuristic-runs 240 --primal-heuristic-seed 20260626 --heuristic-candidates-csv results\tgbc_migration_round\heuristic_candidates_v6_m1.csv --export-incumbent results\tgbc_migration_round\incumbents\v12_m1_hga_tgbc_60s_v6.json --out results\tgbc_migration_round\raw\v12_m1_hga_tgbc_60s_v6.json

.\build\ExactEBRP.exe --method primal-heuristic --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 60 --primal-heuristic-runs 240 --primal-heuristic-seed 20260626 --heuristic-candidates-csv results\tgbc_migration_round\heuristic_candidates_v6.csv --export-incumbent results\tgbc_migration_round\incumbents\v12_m2_hga_tgbc_60s_v6.json --out results\tgbc_migration_round\raw\v12_m2_hga_tgbc_60s_v6.json
```

Audit:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\tgbc_migration_round\raw --csv-out results\tgbc_migration_round\certificate_audit.csv --fail-on-error
```

Intermediate v1-v5 commands used the same V12 inputs and seed while incrementally testing compact inherited decoding, guided education, pair-seed construction, larger GA budgets, and quantity-beam construction.
