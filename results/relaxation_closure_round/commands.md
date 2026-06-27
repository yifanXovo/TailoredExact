# Relaxation Closure Round Commands

Branch: `codex/longrun-round17-local-results`

Starting commit: `0c2627821415515973eccbc0e9b4d412d6e7167d`

Build command used because CMake was unavailable on PATH:

```powershell
& 'D:\msys64\ucrt64\bin\g++.exe' -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/hga_tgbc/HgaTgbcGreedy.cpp src/HgaTgbcRunner.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
```

Representative run commands:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --out results\relaxation_closure_round\raw\v4_smoke_30s.json --log results\relaxation_closure_round\logs\v4_smoke_30s.log --progress-log results\relaxation_closure_round\progress\v4_smoke_30s.csv --progress-interval-seconds 10

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --out results\relaxation_closure_round\raw\v12_m1_current_300s.json --log results\relaxation_closure_round\logs\v12_m1_current_300s.log --progress-log results\relaxation_closure_round\progress\v12_m1_current_300s.csv --ub-event-log results\relaxation_closure_round\progress\v12_m1_current_300s.ub_events.csv --progress-interval-seconds 60

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 600 --frontier-intervals 3 --out results\relaxation_closure_round\raw\v12_m1_default_600s.json --log results\relaxation_closure_round\logs\v12_m1_default_600s.log --progress-log results\relaxation_closure_round\progress\v12_m1_default_600s.csv --ub-event-log results\relaxation_closure_round\progress\v12_m1_default_600s.ub_events.csv --progress-interval-seconds 60

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --out results\relaxation_closure_round\raw\v12_m2_core_300s.json --log results\relaxation_closure_round\logs\v12_m2_core_300s.log --progress-log results\relaxation_closure_round\progress\v12_m2_core_300s.csv --ub-event-log results\relaxation_closure_round\progress\v12_m2_core_300s.ub_events.csv --progress-interval-seconds 60

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --v20-safe-relaxation-cuts true --v20-cover-cuts true --v20-cover-max-size 4 --v20-cover-max-cuts 200 --station-residual-cover-cuts true --large-compact-flow-relaxation mip-light --large-compact-flow-time-limit 20 --route-mask-max-v 12 --out results\relaxation_closure_round\raw\high_imbalance_seed3202_miplight_300s.json --log results\relaxation_closure_round\logs\high_imbalance_seed3202_miplight_300s.log --progress-log results\relaxation_closure_round\progress\high_imbalance_seed3202_miplight_300s.csv --ub-event-log results\relaxation_closure_round\progress\high_imbalance_seed3202_miplight_300s.ub_events.csv --progress-interval-seconds 60

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --lambda 0.15 --T 3600 --time-limit 1200 --frontier-intervals 3 --v20-safe-relaxation-cuts true --v20-cover-cuts true --v20-cover-max-size 4 --v20-cover-max-cuts 200 --station-residual-cover-cuts true --large-compact-flow-relaxation mip-light --route-mask-max-v 12 --out results\relaxation_closure_round\raw\high_imbalance_seed3202_miplight_1200s.json --log results\relaxation_closure_round\logs\high_imbalance_seed3202_miplight_1200s.log --progress-log results\relaxation_closure_round\progress\high_imbalance_seed3202_miplight_1200s.csv --ub-event-log results\relaxation_closure_round\progress\high_imbalance_seed3202_miplight_1200s.ub_events.csv --progress-interval-seconds 60
```

Audit:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts\audit_bpc_certificate.py --self-test
& 'D:\msys64\ucrt64\bin\python.exe' scripts\audit_bpc_certificate.py results\relaxation_closure_round\raw --csv-out results\relaxation_closure_round\certificate_audit.csv --fail-on-error
```

Skipped/failed:

- `moderate_seed3302 lp 1200s` exceeded the requested solver budget and did not
  write a raw JSON after the first 1200s row completed; the process was stopped
  and the row is recorded in `skipped_or_failed_rows.csv`.
