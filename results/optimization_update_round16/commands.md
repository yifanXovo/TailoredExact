# Round 16 Commands

Build attempted:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

CMake was unavailable, so the fallback builds were used:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

Representative runs:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --algorithm-preset paper-bpc-core --incumbent-archive-dir results\optimization_update_round15\raw --progress-log results\optimization_update_round16\progress\v4_paper_bpc_core.csv --out results\optimization_update_round16\raw\v4_paper_bpc_core.json
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --algorithm-preset paper-bpc-core --incumbent-archive-dir results\optimization_update_round15\raw --progress-log results\optimization_update_round16\progress\v12_m1_paper_bpc_core.csv --out results\optimization_update_round16\raw\v12_m1_paper_bpc_core.json
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --algorithm-preset paper-bpc-core --incumbent-archive-dir results\optimization_update_round15\raw --progress-log results\optimization_update_round16\progress\v12_m2_paper_bpc_core.csv --out results\optimization_update_round16\raw\v12_m2_paper_bpc_core.json
.\build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --algorithm-preset paper-bpc-experimental --incumbent-archive-dir results\optimization_update_round15\raw --progress-log results\optimization_update_round16\progress\v12_m2_ablation_experimental_two_track.csv --out results\optimization_update_round16\raw\v12_m2_ablation_experimental_two_track.json
.\build\ExactEBRP.exe --method large-relaxed-rmp-cg-test --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --time-limit 300 --algorithm-preset diagnostic-large --progress-log results\optimization_update_round16\progress\v100_diagnostic_large.csv --out results\optimization_update_round16\raw\v100_diagnostic_large.json
.\build\ExactEBRP.exe --method option-consistency-test --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --algorithm-preset paper-bpc-experimental --out results\optimization_update_round16\raw\v12_m2_option_consistency_twotrack.json
```

The full V4 smoke diagnostic list and V12 M2 ablation commands are represented by `raw/v4_smoke_exit_summary.csv` and `component_ablation_summary.csv`.

Summary CSVs were generated from `results\optimization_update_round16\raw\*.json` into the Round 16 directory, including `result_integrity_audit.csv`, `component_ablation_summary.csv`, `portfolio_summary.csv`, and `option_consistency_summary.csv`.
