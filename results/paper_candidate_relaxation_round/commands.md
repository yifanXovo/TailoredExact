# Commands

Build used on this machine because CMake was unavailable on PATH:

```powershell
& 'D:\msys64\ucrt64\bin\g++.exe' -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/hga_tgbc/HgaTgbcGreedy.cpp src/HgaTgbcRunner.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
```

Representative run commands:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core-adaptive --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --out results\paper_candidate_relaxation_round\raw\v4_smoke_adaptive_30s.json --progress-log results\paper_candidate_relaxation_round\progress\v4_smoke_adaptive_30s.csv

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --out results\paper_candidate_relaxation_round\raw\v12_m1_current_300s.json --progress-log results\paper_candidate_relaxation_round\progress\v12_m1_current_300s.csv

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core-adaptive --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --out results\paper_candidate_relaxation_round\raw\v12_m1_adaptive_300s.json --progress-log results\paper_candidate_relaxation_round\progress\v12_m1_adaptive_300s.csv

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core-adaptive --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 600 --frontier-intervals 3 --out results\paper_candidate_relaxation_round\raw\v12_m1_adaptive_600s.json --progress-log results\paper_candidate_relaxation_round\progress\v12_m1_adaptive_600s.csv

.\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core-adaptive --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --out results\paper_candidate_relaxation_round\raw\v12_m2_adaptive_300s.json --progress-log results\paper_candidate_relaxation_round\progress\v12_m2_adaptive_300s.csv
```

V20 adaptive/race rows were run for all six hard stress cases under
`reference\hard_stress\V20_M3\`.  The results are intentionally retained even
when weaker than the previous fixed LP/mip-light baselines.

Audit and summary commands:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\summarize_paper_candidate_relaxation_round.py
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_candidate_relaxation_round\raw --csv-out results\paper_candidate_relaxation_round\certificate_audit.csv --fail-on-error

.\build\ExactEBRP.exe --method certificate-basis-test --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\paper_candidate_relaxation_round\raw\certificate_basis_test.json

.\build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-bpc-core-adaptive --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\paper_candidate_relaxation_round\raw\option_consistency_test.json

.\build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-bpc-core-adaptive --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --frontier-pre-split-critical true --out results\paper_candidate_relaxation_round\raw\option_consistency_adaptive_presplit_test.json
```
