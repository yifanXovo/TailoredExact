# TailoredExact

Exact and portfolio solvers for the Equity-aware Bike Repositioning Problem.

## Build

Preferred:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

Fallback used on machines without CMake:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## BPC Example

```powershell
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --gcap-pricing-columns 4 --column-dominance true --column-dominance-mode exact --projection-bound true --penalty-domain-tightening true --out results\optimization_update\raw\smoke_gcap_frontier_full.json
```

## New Optimization Options

- `--column-dominance true|false`: enable exact-safe route-load projection dominance.
- `--column-dominance-mode exact|pareto|off`: use exact projection equivalence when path-independent, or Pareto filtering when path-dependent coefficients matter.
- `--projection-bound true|false`: enable the inventory-ratio interval projection lower bound.
- `--penalty-domain-tightening true|false`: tighten final-inventory domains using incumbent objective and interval floor.
- `--movement-domain-tightening true|false`: tighten final-inventory domains using station reachability from route-duration, handling-time, station, and truck-capacity necessary conditions.
- `--movement-bound-audit true|false`: compute interval relaxation bounds with and without movement-domain tightening and record/use the stronger valid bound.
- `--frontier-best-bound-scheduling true|false`: process frontier intervals by deterministic valid lower-bound priority instead of raw interval order.
- `--frontier-relaxation-cache true|false`: reuse exact-key interval relaxation bounds across retry passes.
- `--support-duration-pruning true|false`: prune exact pricing labels whose station support contains a subset proven route-duration infeasible.
- `--support-duration-max-subset-size N`: maximum station subset size used for support-duration pruning precomputation.
- `--incumbent-json <path> --incumbent-format exact_result --incumbent-source-name <name>`: import a verified incumbent route solution as an upper-bound/cutoff source only.
- `--gcap-pricing-columns N`: allow pricing to return multiple negative columns; filtered insertion is certificate-neutral.
- `--frontier-column-cache true|false`: currently logged as requested but not enabled for certificates.

Round-three example with range audit, movement audit, and support pruning:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --bpc-incumbent local --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --movement-bound-audit true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --support-duration-pruning true --support-duration-max-subset-size 5 --out results\optimization_update_round3\raw\movement_audit_v12_m1_average.json
```

Proofs and certificate cautions are in `docs/optimization_proofs.md` and `docs/certification_protocol.md`.
