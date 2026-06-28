# Commands

Build:

```powershell
& 'D:\msys64\ucrt64\bin\g++.exe' -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/hga_tgbc/HgaTgbcGreedy.cpp src/HgaTgbcRunner.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
```

Focused interval harness:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\v20_interval_closure_harness.py --input results\relaxation_closure_round\raw\high_imbalance_seed3202_miplight_1200s.intervals.csv --instance reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --exe build\ExactEBRP.exe --output-dir results\v20_certificate_round --target-ids 13,18 --time-limit 120 --relax-seconds 60 --portfolio-mode exhaustive --variant-mode exhaustive --max-variants 5 --compact-flow mip-light --compact-time-limit 20 --execute
```

Full priority target attempt:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --route-mask-max-v 12 --large-compact-flow-relaxation mip-light --large-compact-flow-time-limit 60 --relaxation-portfolio-mode exhaustive --relaxation-portfolio-max-variants 5 --relaxation-certificate-mode both --cutoff-feasibility-epsilon 1e-8 --out results\v20_certificate_round\raw\high_imbalance_seed3202_exhaustive_300s.json --progress-log results\v20_certificate_round\progress\high_imbalance_seed3202_exhaustive_300s.csv --progress-interval-seconds 60
```

V12 stability:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --out results\v20_certificate_round\raw\v4_smoke_30s.json --progress-log results\v20_certificate_round\progress\v4_smoke_30s.csv --progress-interval-seconds 30
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --out results\v20_certificate_round\raw\v12_m2_canonical_300s.json --progress-log results\v20_certificate_round\progress\v12_m2_canonical_300s.csv --progress-interval-seconds 60
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core-adaptive --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 600 --frontier-intervals 3 --out results\v20_certificate_round\raw\v12_m1_adaptive_600s.json --progress-log results\v20_certificate_round\progress\v12_m1_adaptive_600s.csv --progress-interval-seconds 60
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core-adaptive --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --out results\v20_certificate_round\raw\v12_m1_adaptive_300s.json --progress-log results\v20_certificate_round\progress\v12_m1_adaptive_300s.csv --progress-interval-seconds 60
```

Audit:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\v20_certificate_round\raw --csv-out results\v20_certificate_round\certificate_audit.csv --fail-on-error
```

