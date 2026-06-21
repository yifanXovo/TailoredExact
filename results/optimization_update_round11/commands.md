# Round 11 commands

## Build

CMake was attempted but unavailable:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

Fallback build used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\compare_main.cpp -o build\ExactEBRPCompare.exe
```

## V4 smoke diagnostics

All listed methods were run on `testdata/examples/gcap_smoke_V4_M1.txt` with `--time-limit 30` and outputs under `results/optimization_update_round11/raw` and `results/optimization_update_round11/logs`:

`pricing`, `pricing-branch`, `cuts`, `branching`, `master`, `cg`, `gcap-cg`, `gcap-tree`, `gcap-frontier`, `dominance-test`, `support-pruning-test`, `route-mask-support-test`, `route-mask-operation-budget-test`, `incumbent-import-test`, `route-pool-incumbent-test`, `pickup-drop-compat-flow-test`, `pickup-drop-transfer-cap-test`, `vehicle-indexed-relaxation-test`, `vehicle-indexed-transfer-flow-test`, `adaptive-frontier-split-test`, `inventory-branching-test`, `operation-mode-branching-test`, `pricing-closure-audit-test`, `resume-state-test`, `pricing-verifier-test`, `iterative-closure-test`, `certificate-basis-test`.

## V12 closure runs

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 300 --bpc-incumbent auto --bpc-incumbent-seconds 10 --frontier-intervals 4 --frontier-relax-seconds 5 --frontier-final-closure false --frontier-focused-min-lb-retry false --frontier-focused-intensification true --frontier-iterative-closure true --frontier-iterative-max-rounds 2 --frontier-iterative-round-time 90 --frontier-iterative-target-gap 0.005 --frontier-iterative-export-dir results/optimization_update_round11/raw/iterative_v12_m2_states_reserved --frontier-closure-mode exact-cg --closure-max-cg-iterations 32 --closure-returned-columns 8 --pricing-final-verifier true --pricing-verifier-time 30 --pricing-verifier-checkpoint results/optimization_update_round11/raw/v12_m2_iterative_reserved_pricing_verifier_checkpoint.json --frontier-export-state results/optimization_update_round11/raw/v12_m2_iterative_reserved_state.json --frontier-export-open-nodes true --progress-log results/optimization_update_round11/progress/progress_v12_m2_iterative_reserved_300s.csv --progress-interval-seconds 30 --out results/optimization_update_round11/raw/v12_m2_iterative_reserved_300s.json
```

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 300 --bpc-incumbent auto --bpc-incumbent-seconds 10 --frontier-import-interval-bound results/optimization_update_round9/raw/v12_m1_focus_auto_300s.json --frontier-iterative-closure true --frontier-iterative-max-rounds 2 --frontier-iterative-round-time 90 --frontier-closure-mode exact-cg --pricing-final-verifier true --pricing-verifier-checkpoint results/optimization_update_round11/raw/v12_m1_multifocus_pricing_verifier_checkpoint.json --frontier-export-state results/optimization_update_round11/raw/v12_m1_multifocus_state.json --frontier-export-open-nodes true --progress-log results/optimization_update_round11/progress/progress_v12_m1_multifocus_300s.csv --out results/optimization_update_round11/raw/v12_m1_multifocus_300s.json
```

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 300 --bpc-incumbent auto --bpc-incumbent-seconds 5 --frontier-intervals 2 --frontier-final-closure false --frontier-focused-min-lb-retry false --frontier-focused-intensification false --frontier-adaptive-split false --frontier-import-interval-bound results/optimization_update_round9/raw/v12_m1_focus_auto_300s.json --frontier-iterative-closure true --frontier-iterative-max-rounds 2 --frontier-iterative-round-time 90 --frontier-closure-mode exact-cg --pricing-final-verifier true --pricing-verifier-checkpoint results/optimization_update_round11/raw/v12_m1_iterative_lite_pricing_verifier_checkpoint.json --frontier-export-state results/optimization_update_round11/raw/v12_m1_iterative_lite_state.json --frontier-export-open-nodes true --progress-log results/optimization_update_round11/progress/progress_v12_m1_iterative_lite_300s.csv --out results/optimization_update_round11/raw/v12_m1_iterative_lite_300s.json
```

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 60 --bpc-incumbent auto --bpc-incumbent-seconds 5 --frontier-resume-state results/optimization_update_round11/raw/v12_m2_iterative_reserved_state.json --frontier-resume-open-nodes true --frontier-export-open-nodes true --frontier-closure-mode exact-cg --pricing-final-verifier true --pricing-verifier-checkpoint results/optimization_update_round11/raw/v12_m2_resume_pricing_verifier_checkpoint.json --frontier-export-state results/optimization_update_round11/raw/v12_m2_resume_state_out.json --progress-log results/optimization_update_round11/progress/progress_v12_m2_resume_60s.csv --out results/optimization_update_round11/raw/v12_m2_resume_60s.json
```

## Longer-run note

A 1200s V12 run was not executed in this pass because two 300s V12 closure runs plus one 300s V12 iterative-lite run were used to validate the implementation paths within the local session budget. Reproduce with the V12 M2 command above and `--time-limit 1200 --frontier-iterative-round-time 300 --frontier-iterative-max-rounds 3`.
