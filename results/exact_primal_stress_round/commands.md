# Exact Primal Stress Round Commands

Branch: `codex/longrun-round17-local-results`  
Start commit: `a878a5d153da5c61d877a480cdb73c6eb7d3aeb3`

Build attempted:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

CMake was unavailable on this machine, so the fallback build was used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/hga_tgbc/HgaTgbcGreedy.cpp src/HgaTgbcRunner.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
```

Representative runs:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --progress-log results\exact_primal_stress_round\progress\v4_smoke_core_30s.csv --ub-event-log results\exact_primal_stress_round\ub_events\v4_smoke_core_30s.ub_events.csv --progress-interval-seconds 10 --out results\exact_primal_stress_round\raw\v4_smoke_core_30s.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\exact_primal_stress_round\progress\v12_m2_core_300s.csv --ub-event-log results\exact_primal_stress_round\ub_events\v12_m2_core_300s.ub_events.csv --progress-interval-seconds 60 --out results\exact_primal_stress_round\raw\v12_m2_core_300s.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\exact_primal_stress_round\progress\v12_m1_core_300s.csv --ub-event-log results\exact_primal_stress_round\ub_events\v12_m1_core_300s.ub_events.csv --progress-interval-seconds 60 --out results\exact_primal_stress_round\raw\v12_m1_core_300s.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --primal-heuristic greedy --primal-heuristic-seconds 1 --primal-heuristic-runs 1 --primal-heuristic-seed 1701 --exact-phase-local-redecode-repair true --exact-phase-local-redecode-seconds 20 --progress-log results\exact_primal_stress_round\progress\v12_m2_greedy_start_300s.csv --ub-event-log results\exact_primal_stress_round\ub_events\v12_m2_greedy_start_300s.ub_events.csv --progress-interval-seconds 60 --out results\exact_primal_stress_round\raw\v12_m2_greedy_start_300s.json
```

The six V20/M3 native-HGA rows used the same paper-core command with
`reference/hard_stress/V20_M3/<instance>.txt`, 300-second limits, per-row
progress logs, and per-row UB event logs.

Additional C++ diagnostics:

```powershell
build\ExactEBRP.exe --method certificate-basis-test --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\exact_primal_stress_round\raw\certificate_basis_test.json

build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\exact_primal_stress_round\raw\option_consistency_test.json
```

Python audit command requested but not executable on this machine:

```powershell
python scripts\audit_bpc_certificate.py --self-test
python scripts\audit_bpc_certificate.py results\exact_primal_stress_round\raw --csv-out results\exact_primal_stress_round\certificate_audit.csv --fail-on-error
```

The local `python.exe` is the WindowsApps placeholder and exits without running
scripts. A PowerShell equivalent field audit was written to
`results/exact_primal_stress_round/certificate_audit.csv`.
