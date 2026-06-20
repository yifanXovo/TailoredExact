# Round 4 Commands

## Build

`cmake` was not available on this machine, so the fallback builds were used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## Smoke Diagnostics

Input: `testdata/examples/gcap_smoke_V4_M1.txt`.

Methods run with `--lambda 0.15 --T 3600 --time-limit 30`:

- `pricing`
- `pricing-branch`
- `cuts`
- `branching`
- `master`
- `cg`
- `gcap-cg`
- `gcap-tree`
- `gcap-frontier`
- `dominance-test`
- `support-pruning-test`
- `route-mask-support-test`
- `incumbent-import-test`

All logs are in `logs/smoke_*.stdout.txt`; exit codes are in `logs/smoke_exit_codes.txt`.

## Incumbent Audit

Inputs:

- `reference/regen_candidate_V12_M1_average.txt`
- `reference/regen_candidate_V12_M2_average.txt`

Each mode was run with:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input <input> --lambda 0.15 --T 3600 --threads 1 --time-limit 45 --frontier-intervals 2 --frontier-retry-passes 0 --frontier-refine-splits 0 --max-nodes 7 --bpc-incumbent <mode> --bpc-incumbent-seconds 12 --bpc-incumbent-rounds 6 --frontier-relax-seconds 1 --route-mask-max-v 12 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --support-duration-pruning true --route-mask-support-duration-pruning true --frontier-focused-min-lb-retry true --gcap-pricing-columns 2 --out results\optimization_update_round4\raw\incumbent_<instance>_<mode>.json
```

Modes:

- `greedy`
- `local`
- `pool`
- `pricing`
- `portfolio`
- `strong`
- `compact`
- `compact-cplex`

Exit codes are in `logs/incumbent_exit_codes.txt`.

## Ablation Matrix

Instances:

- `testdata/examples/gcap_smoke_V4_M1.txt`
- `reference/regen_candidate_V12_M1_average.txt`
- `reference/regen_candidate_V12_M2_average.txt`

Variants:

- `baseline_round3`
- `support_pricing_only`
- `route_mask_support_only`
- `support_both`
- `strong_incumbent_only`
- `improved_full`
- `improved_full_long`

The V4 run used 30s for short rows and 45s for `improved_full_long`. The V12 runs used 60s for short rows and 120s for `improved_full_long`.

Exit codes are in:

- `logs/ablation_v4_exit_codes.txt`
- `logs/ablation_v12_m1_exit_codes.txt`
- `logs/ablation_v12_m2_exit_codes.txt`

No run returned a nonzero exit code.
