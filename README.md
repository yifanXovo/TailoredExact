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
- `--route-mask-support-duration-pruning true|false`: apply the same exact-safe support-duration infeasibility test to complete route-mask relaxation masks.
- `--frontier-focused-min-lb-retry true|false`: spend retry time on the unresolved frontier interval with the smallest valid lower bound.
- `--frontier-focused-intensification true|false`: reserve time to rerun stronger relaxations on the current minimum-LB unresolved interval.
- `--frontier-focused-reserve-fraction x`: fraction of the time limit reserved for focused intensification.
- `--frontier-adaptive-split true|false`: split the current minimum-LB unresolved Gini interval into exactly covering child intervals.
- `--frontier-adaptive-max-depth N`: maximum adaptive split depth for a frontier leaf interval.
- `--route-mask-operation-budget-cuts true|false`: add mask-specific pickup-operation budget rows to the route-mask relaxation using depot-cycle lower bounds.
- `--route-pool-incumbent true|false`: collect verified BPC-generated route-load columns and solve a true-objective restricted route-column incumbent master for upper bounds only.
- `--route-pool-max-columns-per-vehicle N`: cap stored route-pool columns per vehicle after projection dominance.
- `--pickup-drop-compat-flow true|false`: strengthen the inventory/route/Gini relaxation with pickup-to-drop compatibility flow variables when pairs can be safely screened by route-duration lower bounds.
- `--pickup-drop-transfer-cap-flow true|false`: add safe quantity upper bounds to pickup-drop transfer variables from travel/handling lower bounds and capacities.
- `--bpc-incumbent auto|best-of-all`: run a bounded verified incumbent portfolio and select the best true-objective route plan as an upper bound.
- `--progress-log <path> --progress-interval-seconds <seconds>`: write frontier progress checkpoints for convergence reporting.
- `--support-feasibility-oracle true|false`: reserved switch for exact small-support infeasibility checking; default is false and heuristic support cuts are not generated.
- `--incumbent-json <path> --incumbent-format exact_result --incumbent-source-name <name>`: import a verified incumbent route solution as an upper-bound/cutoff source only.
- `--incumbent-format auto|exact_result|route_json|csv`: parse incumbent files as ExactEBRP result JSON, route JSON, or CSV with vehicle/order/station/pickup/drop columns.
- `--hga-incumbent <path> --hga-incumbent-format auto|route_json|csv|legacy`: import HGA/TGBC-style route outputs when a compatible route-bearing file is available. Legacy objective-only files are rejected rather than fabricated into routes.
- `--gcap-pricing-columns N`: allow pricing to return multiple negative columns; filtered insertion is certificate-neutral.
- `--frontier-column-cache true|false`: currently logged as requested but not enabled for certificates.

Round-three example with range audit, movement audit, and support pruning:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --bpc-incumbent local --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --movement-bound-audit true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --support-duration-pruning true --support-duration-max-subset-size 5 --out results\optimization_update_round3\raw\movement_audit_v12_m1_average.json
```

Round-four example with route-mask support pruning, focused retry, and verified incumbent controls:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 120 --frontier-intervals 2 --bpc-incumbent portfolio --bpc-incumbent-seconds 12 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry true --support-duration-pruning true --route-mask-support-duration-pruning true --support-feasibility-oracle false --gcap-pricing-columns 4 --out results\optimization_update_round4\raw\ablation_v12_m2_average_improved_full_long.json
```

Round-five example with executed focused retry, route-pool incumbent master, and pickup-drop compatibility flow:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 120 --frontier-intervals 2 --frontier-retry-passes 0 --max-nodes 3 --bpc-incumbent portfolio --bpc-incumbent-seconds 8 --frontier-relax-seconds 0.5 --route-mask-max-v 12 --column-dominance true --projection-bound true --penalty-domain-tightening true --movement-domain-tightening true --frontier-best-bound-scheduling true --frontier-relaxation-cache true --frontier-focused-min-lb-retry true --route-pool-incumbent true --pickup-drop-compat-flow true --support-duration-pruning true --route-mask-support-duration-pruning true --support-feasibility-oracle false --gcap-pricing-columns 2 --out results\optimization_update_round5\raw\ablation_v12_m2_average_improved_full_long.json
```

Route-pool incumbent and compatibility-flow diagnostics:

```powershell
build\ExactEBRP.exe --method route-pool-incumbent-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --route-pool-incumbent true --out results\optimization_update_round5\raw\smoke_route-pool-incumbent-test.json
build\ExactEBRP.exe --method pickup-drop-compat-flow-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --pickup-drop-compat-flow true --out results\optimization_update_round5\raw\smoke_pickup-drop-compat-flow-test.json
```

Round-six example with auto incumbent selection, route-pool harvesting, focused
relaxation intensification, transfer-cap flow, and progress logging:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 300 --frontier-intervals 2 --frontier-retry-passes 0 --max-nodes 3 --bpc-incumbent auto --bpc-incumbent-seconds 30 --route-pool-incumbent true --route-pool-max-columns-per-vehicle 5000 --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-focused-reserve-fraction 0.25 --frontier-focused-relax-seconds 4 --frontier-focused-max-passes 2 --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --progress-log results\optimization_update_round6\raw\progress_v12_m2_average_improved_full_300s.csv --out results\optimization_update_round6\raw\ablation_v12_m2_average_improved_full_300s.json
```

Transfer-cap diagnostic:

```powershell
build\ExactEBRP.exe --method pickup-drop-transfer-cap-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --out results\optimization_update_round6\raw\smoke_pickup-drop-transfer-cap-test.json
```

Round-seven example with adaptive splitting, route-mask operation budgets, and
periodic convergence trace:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 300 --frontier-intervals 2 --frontier-retry-passes 0 --max-nodes 3 --bpc-incumbent auto --bpc-incumbent-seconds 30 --route-pool-incumbent true --frontier-focused-min-lb-retry true --frontier-focused-intensification true --frontier-adaptive-split true --frontier-adaptive-max-depth 3 --route-mask-operation-budget-cuts true --pickup-drop-compat-flow true --pickup-drop-transfer-cap-flow true --progress-log results\optimization_update_round7\raw\progress_v12_m2_average_improved_full_300s.csv --progress-interval-seconds 30 --out results\optimization_update_round7\raw\ablation_v12_m2_average_improved_full_300s.json
```

Round-seven diagnostics:

```powershell
build\ExactEBRP.exe --method route-mask-operation-budget-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --route-mask-operation-budget-cuts true --out results\optimization_update_round7\raw\smoke_route-mask-operation-budget-test.json
build\ExactEBRP.exe --method adaptive-frontier-split-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --frontier-adaptive-split true --out results\optimization_update_round7\raw\smoke_adaptive-frontier-split-test.json
```

Round-eight example with vehicle-indexed operation relaxation, vehicle-indexed
transfer flow, focus-capable frontier diagnostics, and progress logging:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --threads 4 --bpc-workers 4 --pricing-threads 1 --time-limit 300 --frontier-intervals 2 --frontier-retry-passes 0 --max-nodes 3 --bpc-incumbent auto --route-pool-incumbent true --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --frontier-adaptive-split true --frontier-focused-intensification true --route-mask-operation-budget-cuts true --pickup-drop-transfer-cap-flow true --progress-log results\optimization_update_round8\raw\progress_v12_m2_average_improved_full_300s.csv --progress-interval-seconds 30 --out results\optimization_update_round8\raw\ablation_v12_m2_average_improved_full_300s.json
```

Focus-only interval diagnostic, which tightens or closes one selected frontier
interval and reports `diagnostic_interval_only` rather than an original-problem
certificate:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --bpc-incumbent auto --frontier-focus-only true --frontier-focus-interval-id auto --frontier-focus-time-limit 300 --frontier-focus-relax-seconds 30 --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --out results\optimization_update_round8\raw\ablation_v12_m2_average_focus_interval_only.json
```

Vehicle-indexed diagnostics:

```powershell
build\ExactEBRP.exe --method vehicle-indexed-relaxation-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --vehicle-indexed-operation-relaxation true --out results\optimization_update_round8\raw\smoke_vehicle-indexed-relaxation-test.json
build\ExactEBRP.exe --method vehicle-indexed-transfer-flow-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --vehicle-indexed-operation-relaxation true --vehicle-indexed-transfer-flow true --out results\optimization_update_round8\raw\smoke_vehicle-indexed-transfer-flow-test.json
```

If historical V8/V10 text inputs are unavailable, deterministic engineering
benchmarks can be regenerated with:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\generate_reference_instances.py
```

The generated files are written to `reference\generated\` with
`reference\generated\manifest.csv`. They are regression and engineering
benchmarks unless proven identical to historical paper inputs.

Round-nine focus-range and branching examples:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.465922,0.512514 --frontier-focus-time-limit 300 --frontier-focus-relax-seconds 30 --max-nodes 255 --branch-inventory true --branch-operation-mode true --branch-selection auto --progress-log results\optimization_update_round9\raw\progress_v12_m2_focus_auto_300s.csv --out results\optimization_update_round9\raw\v12_m2_focus_auto_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-import-interval-bound results\optimization_update_round9\raw\v12_m2_focus_auto_300s.json --branch-inventory true --branch-operation-mode true --branch-selection auto --out results\optimization_update_round9\raw\v12_m2_full_import_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-focus-only true --frontier-focus-range 0.465922,0.512514 --branch-selection strong --strong-branching-candidates 3 --branch-inventory true --branch-operation-mode true --out results\optimization_update_round9\raw\v12_m2_focus_strong_60s.json
```

Branching diagnostics:

```powershell
build\ExactEBRP.exe --method inventory-branching-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --branch-inventory true --out results\optimization_update_round9\raw\smoke_inventory-branching-test.json
build\ExactEBRP.exe --method operation-mode-branching-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --branch-operation-mode true --out results\optimization_update_round9\raw\smoke_operation-mode-branching-test.json
```

Proofs and certificate cautions are in `docs/optimization_proofs.md` and `docs/certification_protocol.md`.

Round-ten exact-CG continuation and resume examples:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514 --frontier-closure-mode exact-cg --closure-max-cg-iterations 96 --closure-returned-columns 16 --closure-final-exact-pricing true --progress-log results\optimization_update_round10\progress\v12_m2_exact_cg_focus_300s.progress.csv --frontier-export-state results\optimization_update_round10\raw\v12_m2_exact_cg_focus_300s.state.json --out results\optimization_update_round10\raw\v12_m2_exact_cg_focus_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-resume-state results\optimization_update_round10\raw\v12_m2_exact_cg_focus_300s.state.json --frontier-resume-mode interval-only --frontier-closure-mode exact-cg --closure-max-cg-iterations 96 --closure-returned-columns 16 --out results\optimization_update_round10\raw\v12_m2_resume_exact_cg_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-import-interval-bound results\optimization_update_round9\raw\v12_m1_focus_auto_300s.json --out results\optimization_update_round10\raw\v12_m1_full_import_focus_300s.json
```

Dual stabilization can be requested for column discovery diagnostics with
`--cg-dual-stabilization smooth --cg-dual-smoothing-alpha 0.7`, but current
certificate-producing runs still require final exact true-dual pricing closure.

Round-eleven iterative closure, partial open-node state, and pricing verifier
examples:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --bpc-incumbent auto --frontier-iterative-closure true --frontier-iterative-max-rounds 2 --frontier-iterative-round-time 90 --frontier-iterative-target-gap 0.005 --frontier-iterative-export-dir results\optimization_update_round11\raw\iterative_states --frontier-closure-mode exact-cg --closure-max-cg-iterations 32 --closure-returned-columns 8 --pricing-final-verifier true --pricing-verifier-checkpoint results\optimization_update_round11\raw\pricing_verifier_checkpoint.json --frontier-export-state results\optimization_update_round11\raw\frontier_state.json --frontier-export-open-nodes true --progress-log results\optimization_update_round11\progress\progress.csv --out results\optimization_update_round11\raw\iterative_frontier.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 120 --frontier-resume-state results\optimization_update_round11\raw\frontier_state.json --frontier-resume-open-nodes true --pricing-final-verifier true --pricing-verifier-resume results\optimization_update_round11\raw\pricing_verifier_checkpoint.json --out results\optimization_update_round11\raw\resume_frontier.json

build\ExactEBRP.exe --method certificate-basis-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\optimization_update_round11\raw\smoke_certificate-basis-test.json

build\ExactEBRP.exe --method pricing-verifier-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --pricing-verifier-checkpoint results\optimization_update_round11\raw\smoke_pricing_verifier_checkpoint.json --out results\optimization_update_round11\raw\smoke_pricing-verifier-test.json
```

Current open-node state export is a warm restart unless the result explicitly
reports `open_node_state_resume_exact=true`. Pricing-verifier checkpoints are
progress artifacts and do not certify closure unless true-dual exact pricing
completes with no negative reduced-cost route-load column.
