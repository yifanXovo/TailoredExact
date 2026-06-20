# Optimization Update Round 2 Commands

Initial state:

```powershell
git status --short --branch
git rev-parse HEAD
git checkout main
git pull --ff-only origin main
git checkout -b fix-frontier-ledger-movement-bounds
```

Build:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

`cmake` was not installed, so the fallback build was used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

Smoke diagnostics:

```powershell
$methods = @('pricing','pricing-branch','cuts','branching','master','cg','gcap-cg','gcap-tree','gcap-frontier','dominance-test')
foreach ($m in $methods) {
  build/ExactEBRP.exe --method $m --input testdata/examples/gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 30 --frontier-intervals 4 --frontier-relax-seconds 2 --max-nodes 31 --gcap-pricing-columns 4 --out results/optimization_update_round2/raw/smoke_${m}.json --log logs/optimization_update_round2/smoke_${m}.log
}
```

Ablation matrix:

```powershell
# Inputs used:
# testdata/examples/gcap_smoke_V4_M1.txt, reference/regen_candidate_V12_M1_average.txt,
# reference/regen_candidate_V12_M2_average.txt

# Variants:
# off:
#   --column-dominance false --projection-bound false --penalty-domain-tightening false
#   --movement-domain-tightening false --frontier-best-bound-scheduling false
#   --frontier-relaxation-cache false --gcap-pricing-columns 1
# current_full:
#   --column-dominance true --projection-bound true --penalty-domain-tightening true
#   --movement-domain-tightening false --frontier-best-bound-scheduling false
#   --frontier-relaxation-cache false --gcap-pricing-columns 4
# movement_only:
#   --column-dominance false --projection-bound true --penalty-domain-tightening true
#   --movement-domain-tightening true --frontier-best-bound-scheduling false
#   --frontier-relaxation-cache false --gcap-pricing-columns 1
# scheduling_cache_only:
#   --column-dominance false --projection-bound true --penalty-domain-tightening true
#   --movement-domain-tightening false --frontier-best-bound-scheduling true
#   --frontier-relaxation-cache true --gcap-pricing-columns 1
# improved_full:
#   --column-dominance true --projection-bound true --penalty-domain-tightening true
#   --movement-domain-tightening true --frontier-best-bound-scheduling true
#   --frontier-relaxation-cache true --gcap-pricing-columns 4
```

Summary generation:

```powershell
# Converted all raw JSON files in results/optimization_update_round2/raw
# into ablation_summary.csv, before_after_summary.csv, and interval_ledger_summary.csv.
```
