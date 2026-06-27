# Native HGA-TGBC Migration Commands

Repository branch:

```powershell
git branch --show-current
git rev-parse HEAD
git pull --ff-only
```

Build:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

`cmake` was not available in this local environment, so the documented fallback
compiler was used:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\hga_tgbc\HgaTgbcGreedy.cpp src\HgaTgbcRunner.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
```

V4 native HGA-TGBC smoke incumbent:

```powershell
.\build\ExactEBRP.exe --method primal-heuristic --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 3 --primal-heuristic-runs 24 --primal-heuristic-seed 20260626 --heuristic-candidates-csv results\hga_tgbc_native_round\heuristic_candidates_v4.csv --export-incumbent results\hga_tgbc_native_round\incumbents\v4_native_hga_tgbc.json --out results\hga_tgbc_native_round\raw\v4_native_hga_tgbc.json *> results\hga_tgbc_native_round\logs\v4_native_hga_tgbc.log
```

V12 M1 native HGA-TGBC incumbent:

```powershell
.\build\ExactEBRP.exe --method primal-heuristic --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 60 --primal-heuristic-runs 24 --primal-heuristic-seed 20260626 --heuristic-candidates-csv results\hga_tgbc_native_round\heuristic_candidates_v12_m1.csv --export-incumbent results\hga_tgbc_native_round\incumbents\v12_m1_native_hga_tgbc_60s.json --out results\hga_tgbc_native_round\raw\v12_m1_native_hga_tgbc_60s.json *> results\hga_tgbc_native_round\logs\v12_m1_native_hga_tgbc_60s.log
```

V12 M2 native HGA-TGBC incumbent:

```powershell
.\build\ExactEBRP.exe --method primal-heuristic --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 60 --primal-heuristic-runs 24 --primal-heuristic-seed 20260626 --heuristic-candidates-csv results\hga_tgbc_native_round\heuristic_candidates_v12_m2.csv --export-incumbent results\hga_tgbc_native_round\incumbents\v12_m2_native_hga_tgbc_60s.json --out results\hga_tgbc_native_round\raw\v12_m2_native_hga_tgbc_60s.json *> results\hga_tgbc_native_round\logs\v12_m2_native_hga_tgbc_60s.log
```

V12 M2 paper-core 600s observation with native HGA-TGBC UB:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 60 --primal-heuristic-runs 24 --primal-heuristic-seed 20260626 --heuristic-candidates-csv results\hga_tgbc_native_round\heuristic_candidates_v12_m2_bpc600.csv --export-incumbent results\hga_tgbc_native_round\incumbents\v12_m2_bpc600_native_hga_incumbent.json --progress-log results\hga_tgbc_native_round\progress\v12_m2_paper_core_native_hga_600s.csv --progress-interval-seconds 60 --out results\hga_tgbc_native_round\raw\v12_m2_paper_core_native_hga_600s.json *> results\hga_tgbc_native_round\logs\v12_m2_paper_core_native_hga_600s.log
```

Certificate audits:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\hga_tgbc_native_round\raw --csv-out results\hga_tgbc_native_round\certificate_audit.csv --fail-on-error
```
