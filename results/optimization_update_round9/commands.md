# Round 9 Commands

## Repo State

```powershell
git status --short
git rev-parse HEAD
```

Base HEAD before this branch's work: `89208b3babfe3888fc31769e81cf848a1fdbab23`.
Branch: `inventory-branching-focus-closure`.

Pre-existing untracked files preserved and not staged:

- `results/optimization_update_round3/raw/ablation__.json`
- `results/optimization_update_round3/raw/incumbent__greedy.json`
- `results/optimization_update_round3/raw/incumbent__local.json`
- `results/optimization_update_round3/raw/incumbent__pool.json`
- `results/optimization_update_round3/raw/incumbent__strong.json`

## Build

CMake was attempted and unavailable:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

Fallback build used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## V4 Smoke Diagnostics

The following methods were run on `testdata/examples/gcap_smoke_V4_M1.txt`; JSON and logs are listed in `smoke_summary.csv`:

```text
pricing
pricing-branch
cuts
branching
master
cg
gcap-cg
gcap-tree
gcap-frontier
dominance-test
support-pruning-test
route-mask-support-test
route-mask-operation-budget-test
incumbent-import-test
route-pool-incumbent-test
pickup-drop-compat-flow-test
pickup-drop-transfer-cap-test
vehicle-indexed-relaxation-test
vehicle-indexed-transfer-flow-test
adaptive-frontier-split-test
inventory-branching-test
operation-mode-branching-test
```

## V12 Focus And Full Frontier Runs

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.465922,0.512514 --frontier-focus-time-limit 300 --frontier-focus-relax-seconds 30 --frontier-focus-tree-nodes 2047 --frontier-intervals 2 --frontier-relax-seconds 4 --max-nodes 255 --bpc-incumbent auto --bpc-incumbent-seconds 8 --bpc-incumbent-rounds 8 --route-pool-incumbent true --gcap-pricing-columns 4 --branch-selection auto --progress-log results/optimization_update_round9/raw/progress_v12_m2_focus_auto_300s.csv --progress-interval-seconds 30 --out results/optimization_update_round9/raw/v12_m2_focus_auto_300s.json

.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.230364,0.276436 --frontier-focus-time-limit 300 --frontier-focus-relax-seconds 30 --frontier-focus-tree-nodes 2047 --frontier-intervals 2 --frontier-relax-seconds 4 --max-nodes 255 --bpc-incumbent auto --bpc-incumbent-seconds 8 --bpc-incumbent-rounds 8 --route-pool-incumbent true --gcap-pricing-columns 4 --branch-selection auto --progress-log results/optimization_update_round9/raw/progress_v12_m1_focus_auto_300s.csv --progress-interval-seconds 30 --out results/optimization_update_round9/raw/v12_m1_focus_auto_300s.json

.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 300 --frontier-import-interval-bound results/optimization_update_round9/raw/v12_m2_focus_auto_300s.json --frontier-intervals 2 --frontier-relax-seconds 4 --max-nodes 255 --frontier-retry-nodes 255 --bpc-incumbent auto --bpc-incumbent-seconds 8 --bpc-incumbent-rounds 8 --route-pool-incumbent true --gcap-pricing-columns 4 --branch-selection auto --progress-log results/optimization_update_round9/raw/progress_v12_m2_full_import_300s.csv --progress-interval-seconds 30 --out results/optimization_update_round9/raw/v12_m2_full_import_300s.json

.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 300 --frontier-intervals 2 --frontier-relax-seconds 4 --max-nodes 255 --frontier-retry-nodes 255 --bpc-incumbent auto --bpc-incumbent-seconds 8 --bpc-incumbent-rounds 8 --route-pool-incumbent true --gcap-pricing-columns 4 --branch-inventory true --branch-operation-mode true --branch-selection auto --progress-log results/optimization_update_round9/raw/progress_v12_m1_full_improved_300s.csv --progress-interval-seconds 30 --out results/optimization_update_round9/raw/v12_m1_full_improved_300s.json
```

## V12 M2 Branch Selection Diagnostics

60s focus-only runs were executed for `--branch-selection ryan-foster`, `inventory`, and `strong`; files are listed in `branch_selection_run_summary.csv`.

## Generated V8/V10 Engineering Benchmarks

60s improved-full runs were executed for:

- `reference/generated/regen_V8_M2_average.txt`
- `reference/generated/regen_V10_M1_average.txt`
- `reference/generated/regen_V10_M2_average.txt`
- `reference/generated/regen_V10_M2_low.txt`

Files are listed in `generated_v8_v10_run_summary.csv`.

## 1200s Reproduction Commands Not Run Locally

The following longer commands were not run in this pass because the smoke, generated V8/V10, V12 focus, V12 branch-selection, and V12 full 300s suite consumed the available local run budget. They are prepared for an unattended slot:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 1200 --frontier-focus-only true --frontier-focus-range 0.465922,0.512514 --frontier-focus-time-limit 1200 --frontier-focus-relax-seconds 120 --frontier-focus-tree-nodes 8191 --frontier-intervals 2 --frontier-relax-seconds 8 --max-nodes 1023 --bpc-incumbent auto --bpc-incumbent-seconds 12 --bpc-incumbent-rounds 12 --route-pool-incumbent true --gcap-pricing-columns 4 --branch-inventory true --branch-operation-mode true --branch-selection auto --progress-log results/optimization_update_round9/raw/progress_v12_m2_focus_auto_1200s.csv --progress-interval-seconds 30 --out results/optimization_update_round9/raw/v12_m2_focus_auto_1200s.json

.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 1200 --frontier-import-interval-bound results/optimization_update_round9/raw/v12_m2_focus_auto_1200s.json --frontier-intervals 2 --frontier-relax-seconds 8 --max-nodes 1023 --frontier-retry-nodes 1023 --bpc-incumbent auto --bpc-incumbent-seconds 12 --bpc-incumbent-rounds 12 --route-pool-incumbent true --gcap-pricing-columns 4 --branch-inventory true --branch-operation-mode true --branch-selection auto --progress-log results/optimization_update_round9/raw/progress_v12_m2_full_import_1200s.csv --progress-interval-seconds 30 --out results/optimization_update_round9/raw/v12_m2_full_import_1200s.json
```

## Error Scan

```powershell
Select-String -Path results\optimization_update_round9\logs\*.log -Pattern 'error|exception|access violation|segmentation|segfault|address|memory|bad_alloc|fatal' -CaseSensitive:$false
```

No matches were returned.

## Focus-From-Result Diagnostic

After fixing the ledger-note parser to isolate each `frontier_interval_ledger:` note and validate parsed ranges, this command selected the unresolved leaf from `v12_m2_full_import_300s.json`:

```powershell
.\build\ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 30 --frontier-focus-only true --frontier-focus-from-result results/optimization_update_round9/raw/v12_m2_full_import_300s.json --frontier-focus-leaf-id min-lb --frontier-focus-time-limit 30 --frontier-focus-relax-seconds 5 --frontier-focus-tree-nodes 127 --frontier-intervals 2 --frontier-relax-seconds 2 --max-nodes 63 --bpc-incumbent auto --bpc-incumbent-seconds 2 --bpc-incumbent-rounds 2 --route-pool-incumbent true --gcap-pricing-columns 2 --branch-inventory true --branch-operation-mode true --branch-selection auto --progress-log results/optimization_update_round9/raw/progress_v12_m2_focus_from_result_30s.csv --progress-interval-seconds 10 --out results/optimization_update_round9/raw/v12_m2_focus_from_result_30s.json
```

Result: selected `[0.489218,0.512514]`, kept LB `0.712948394993`, remained diagnostic and noncertified.
