# Round-Five Commands

Current branch:

```powershell
git status --short --branch
git rev-parse HEAD
```

CMake was attempted first and was unavailable:

```powershell
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

Fallback build commands used:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

V4 smoke diagnostics were run on `testdata/examples/gcap_smoke_V4_M1.txt`:

```powershell
build\ExactEBRP.exe --method pricing --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_pricing.json
build\ExactEBRP.exe --method pricing-branch --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_pricing-branch.json
build\ExactEBRP.exe --method cuts --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_cuts.json
build\ExactEBRP.exe --method branching --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_branching.json
build\ExactEBRP.exe --method master --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_master.json
build\ExactEBRP.exe --method cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_cg.json
build\ExactEBRP.exe --method gcap-cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_gcap-cg.json
build\ExactEBRP.exe --method gcap-tree --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_gcap-tree.json
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --frontier-intervals 2 --frontier-retry-passes 0 --max-nodes 3 --frontier-focused-min-lb-retry true --route-pool-incumbent true --pickup-drop-compat-flow true --out results\optimization_update_round5\raw\smoke_gcap-frontier.json
build\ExactEBRP.exe --method dominance-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_dominance-test.json
build\ExactEBRP.exe --method support-pruning-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_support-pruning-test.json
build\ExactEBRP.exe --method route-mask-support-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_route-mask-support-test.json
build\ExactEBRP.exe --method incumbent-import-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --out results\optimization_update_round5\raw\smoke_incumbent-import-test.json
build\ExactEBRP.exe --method route-pool-incumbent-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --route-pool-incumbent true --out results\optimization_update_round5\raw\smoke_route-pool-incumbent-test.json
build\ExactEBRP.exe --method pickup-drop-compat-flow-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 45 --pickup-drop-compat-flow true --out results\optimization_update_round5\raw\smoke_pickup-drop-compat-flow-test.json
```

The V12 ablation matrix used `reference/regen_candidate_V12_M1_average.txt` and
`reference/regen_candidate_V12_M2_average.txt` with variants:

- `round4_improved_baseline`
- `focused_retry_only`
- `route_pool_incumbent_only`
- `compat_flow_only`
- `focused_route_pool`
- `improved_full`
- `improved_full_long`

Each V12 row used the common frontier settings:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input <instance> --lambda 0.15 --T 3600 --time-limit <60-or-120> --frontier-intervals 2 --frontier-retry-passes 0 --frontier-refine-splits 0 --max-nodes 3 --bpc-incumbent <seed> --bpc-incumbent-seconds 8 --bpc-incumbent-rounds 6 --frontier-relax-seconds 0.5 --route-mask-max-v 12 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry <true-or-false> --route-pool-incumbent <true-or-false> --pickup-drop-compat-flow <true-or-false> --support-duration-pruning true --route-mask-support-duration-pruning true --support-feasibility-oracle false --gcap-pricing-columns 2 --out results\optimization_update_round5\raw\<row>.json
```

The V12 incumbent audit used modes:

```text
greedy, local, pool, pricing, portfolio, strong, compact, compact-cplex, route_pool
```

Every stdout log was scanned for:

```text
AddressSanitizer|access violation|segmentation|segfault|bad_alloc|out of memory|-1073741819|3221225477|STATUS_ACCESS_VIOLATION
```
