# Round-3 Commands

## Build

CMake was unavailable in this environment, so the fallback build was used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## Smoke Diagnostics

The following methods were run on `testdata\examples\gcap_smoke_V4_M1.txt` with 30s limits:

```powershell
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
```

Raw outputs are `raw\smoke_*.json`; post-fix smoke outputs are `raw\postfix_smoke_*.json`.

## V12 Ablation Matrix

Runnable local target files were:

```powershell
reference\regen_candidate_V12_M1_average.txt
reference\regen_candidate_V12_M2_average.txt
```

Variants:

```powershell
off
current_full
movement_only
scheduling_cache_only
improved_full
```

Each run used `--method gcap-frontier`, 3 intervals, local BPC-owned incumbent, 20s time limit, and the variant option set recorded in `ablation_summary.csv`.

## Movement Audit

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-relax-seconds 2 --max-nodes 3 --bpc-incumbent local --bpc-incumbent-seconds 4 --bpc-incumbent-rounds 4 --gcap-pricing-columns 4 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --movement-bound-audit true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --support-duration-pruning true --support-duration-max-subset-size 5
```

The same command was run on `reference\regen_candidate_V12_M2_average.txt`.

## Address-Error Capture And Repro

Pre-fix failing command family:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --bpc-incumbent pricing
```

Debug capture:

```powershell
gdb --batch -ex run -ex bt --args build\ExactEBRP_debug.exe ...
```

Backtraces are in `logs\gdb_repro_v12_m1_pricing.stdout.txt` and `logs\gdb_debug_repro_v12_m1_pricing.stdout.txt`. Post-fix repros are `raw\repro_v12_m1_pricing_after_fix.json` and `raw\repro_v12_m1_portfolio_after_fix.json`.
