# Round 10 Commands

Build:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

CMake was skipped because `cmake` is not installed on this machine.

Smoke diagnostics used `testdata/examples/gcap_smoke_V4_M1.txt` with `--time-limit 30`.

Main round-ten diagnostics:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514 --frontier-closure-mode exact-cg --closure-max-cg-iterations 96 --closure-returned-columns 16 --cg-dual-stabilization none --progress-log results/optimization_update_round10/progress/v12_m2_exact_cg_focus_300s.progress.csv --frontier-export-state results/optimization_update_round10/raw/v12_m2_exact_cg_focus_300s.state.json --out results/optimization_update_round10/raw/v12_m2_exact_cg_focus_300s.json
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-resume-state results/optimization_update_round10/raw/v12_m2_exact_cg_focus_300s.state.json --frontier-resume-mode interval-only --frontier-closure-mode exact-cg --closure-max-cg-iterations 96 --closure-returned-columns 16 --progress-log results/optimization_update_round10/progress/v12_m2_resume_exact_cg_300s.progress.csv --frontier-export-state results/optimization_update_round10/raw/v12_m2_resume_exact_cg_300s.state.json --out results/optimization_update_round10/raw/v12_m2_resume_exact_cg_300s.json
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-import-interval-bound results/optimization_update_round9/raw/v12_m1_focus_auto_300s.json --progress-log results/optimization_update_round10/progress/v12_m1_full_import_focus_300s.progress.csv --frontier-export-state results/optimization_update_round10/raw/v12_m1_full_import_focus_300s.state.json --out results/optimization_update_round10/raw/v12_m1_full_import_focus_300s.json
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-import-interval-bound results/optimization_update_round10/raw/v12_m2_exact_cg_focus_300s.json --progress-log results/optimization_update_round10/progress/v12_m2_full_import_focus_300s.progress.csv --frontier-export-state results/optimization_update_round10/raw/v12_m2_full_import_focus_300s.state.json --out results/optimization_update_round10/raw/v12_m2_full_import_focus_300s.json
```

The requested 1200s and 3600s V12 runs were not executed in this pass because the required implementation, full smoke suite, and four 300s V12 closure/import runs already consumed the available local execution window. Reproducible commands are the 300s commands above with `--time-limit 1200` or `--time-limit 3600`.
