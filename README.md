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
- `--gcap-pricing-columns N`: allow pricing to return multiple negative columns; filtered insertion is certificate-neutral.
- `--frontier-column-cache true|false`: currently logged as requested but not enabled for certificates.

Proofs and certificate cautions are in `docs/optimization_proofs.md` and `docs/certification_protocol.md`.
