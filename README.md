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
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/hga_tgbc/HgaTgbcGreedy.cpp src/HgaTgbcRunner.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/hga_tgbc/HgaTgbcGreedy.cpp src/HgaTgbcRunner.cpp src/Logger.cpp src/compare_main.cpp -o build/ExactEBRPCompare.exe
```

## BPC Example

```powershell
build\ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --gcap-pricing-columns 4 --column-dominance true --column-dominance-mode exact --projection-bound true --penalty-domain-tightening true --out results\optimization_update\raw\smoke_gcap_frontier_full.json
```

V20-safe relaxation and controlled BPC fallback examples:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --v20-safe-relaxation-cuts true --out results\relaxation_bound_round\raw\high_imbalance_seed3202_improved_relax_300s.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --v20-safe-relaxation-cuts true --v20-cover-cuts true --v20-cover-max-size 4 --station-residual-cover-cuts true --large-compact-flow-relaxation mip-light --route-mask-max-v 12 --out results\relaxation_closure_round\raw\high_imbalance_seed3202_miplight_300s.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --frontier-bpc-fallback-mode controlling-intervals --frontier-bpc-fallback-reserve-fraction 0.30 --frontier-bpc-fallback-min-seconds 90 --frontier-bpc-fallback-max-intervals 2 --frontier-final-nodes 63 --out results\relaxation_bound_round\raw\v12_m1_bpc_fallback_300s.json
```

`--v20-safe-relaxation-cuts` adds continuous vehicle-indexed operation,
duration-cover, load-balance, and transfer-cap necessary conditions without
complete route-mask enumeration. These are lower-bound-only cuts. BPC fallback
uses the existing exact-pricing closure guards; incomplete fallback rows remain
noncertified.

Additional lower-bound and scheduling options:

- `--v20-cover-cuts true --v20-cover-max-size 4 --v20-cover-max-cuts 200`;
- `--station-residual-cover-cuts true`;
- `--large-compact-flow-relaxation off|lp|mip-light`;
- `--large-compact-flow-connectivity true|false`;
- `--service-operation-min-handling-cuts true|false`;
- `--penalty-movement-lb-cuts true|false`;
- `--relaxation-portfolio-mode fixed|adaptive|race`;
- `--relaxation-portfolio-probe-seconds <seconds>`;
- `--relaxation-portfolio-max-variants <N>`;
- `--frontier-pre-split-critical true --frontier-critical-max-depth <N>`;
- `--frontier-scheduling-mode default|v12-fast-close|adaptive-best-bound`;
- `--frontier-relaxation-parallel true --frontier-relaxation-workers <N>`.

The `mip-light` compact-flow relaxation is V20-safe but not currently a
universal default: it improves high-imbalance rows and one tight-T row, while
LP remains better on moderate rows in the current stress suite.

Experimental paper-candidate adaptive portfolio:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core-adaptive `
  --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 `
  --time-limit 300 --frontier-intervals 3 `
  --out results\paper_candidate_relaxation_round\raw\v12_m2_adaptive_300s.json
```

`paper-bpc-core-adaptive` keeps native HGA-TGBC as the paper-reproducible UB
source and keeps archive scanning disabled. It enables the adaptive relaxation
portfolio as an auditable candidate configuration. Current V20 evidence is
mixed, so canonical `paper-bpc-core` remains the paper-facing default unless a
future selector beats the best fixed LP/mip-light variants consistently.

Focused V20 interval-closure diagnostics:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\v20_interval_closure_harness.py `
  --input results\relaxation_closure_round\raw\high_imbalance_seed3202_miplight_1200s.intervals.csv `
  --instance reference\hard_stress\V20_M3\high_imbalance_seed3202.txt `
  --exe build\ExactEBRP.exe --output-dir results\v20_certificate_round `
  --target-ids 13,18 --time-limit 120 --relax-seconds 60 `
  --portfolio-mode exhaustive --variant-mode exhaustive --compact-flow mip-light --execute
```

Focused interval rows are diagnostic unless their coverage is safely merged
into the full frontier ledger. The V20 certificate round did not obtain a V20
global certificate; see `results\v20_certificate_round\final_report.md`.

Exact interval cutoff oracle:

```powershell
build\ExactEBRP.exe --method interval-cutoff-oracle `
  --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt `
  --lambda 0.15 --T 3600 `
  --interval-exact-cutoff-oracle compact-mip `
  --interval-exact-cutoff-gamma-L 0.554166666667 `
  --interval-exact-cutoff-gamma-U 0.573958333333 `
  --interval-exact-cutoff-UB 1.74931345205 `
  --interval-exact-cutoff-time-limit 3600 `
  --interval-exact-cutoff-export-lp results\v20_exact_certificate_round\cplex\interval.lp `
  --interval-exact-cutoff-result results\v20_exact_certificate_round\cplex\interval.sol
```

Oracle rows are interval-local evidence only. A proven infeasible oracle row can
support a certificate only after `scripts\merge_interval_oracle_results.py`
confirms exact full-frontier leaf coverage.

V20 replication candidate preset:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-exact-v20-certificate `
  --paper-run-sealed true `
  --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt `
  --lambda 0.15 --T 3600 --time-limit 3600 `
  --out results\sealed_paper_pipeline_round\raw\high_imbalance_seed3202.json
```

`paper-exact-v20-certificate` keeps native HGA-TGBC as a verifier-gated UB-only
source, disables archive scanning, uses the fixed mip-light V20 relaxation
portfolio with compact-flow connectivity, and automatically attempts exact
interval cutoff MIP closure for unresolved final leaves. `--paper-run-sealed
true` rejects archive scanning, external incumbents, focus-only certificates,
and stale resume/import evidence for paper-candidate rows. BPC fallback remains
off by default unless explicitly requested and exact pricing closes. The same
sealed command template is used for V12/V20 rows; only input, output, and time
budget change.

## Exact-Phase UB Tracing

Paper-core runs can write a verifier-gated incumbent event log:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core `
  --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 `
  --time-limit 300 --ub-event-log results\exact_primal_stress_round\ub_events\v12_m2.ub_events.csv `
  --out results\exact_primal_stress_round\raw\v12_m2.json
```

The `paper-bpc-core` preset keeps incumbents as UB-only evidence. It now traces
route-pool incumbent recombination and a deterministic local re-decode repair
pass. Disable the latter with `--exact-phase-local-redecode-repair false`.

## Paper Core Scope

The paper-facing exact algorithm is GF-RL-BPC: `--method gcap-frontier`
with `--algorithm-preset paper-bpc-core`. This preset uses elementary
route-load columns and exact-label pricing only. It explicitly disables
compact fallback certificates, hybrid/ng-DSSR pricing, two-track relaxed RMP,
large-instance diagnostics, focus-only runs, imported focus bounds, frontier
resume, and iterative-closure shortcuts.

The default paper-core upper bound is generated by a deterministic,
verifier-gated primal heuristic (`--primal-heuristic hga-tgbc`). Compact/CPLEX,
imported incumbents, route-pool incumbents, HGA-style route exports, and archive
incumbents may be used only as benchmark rows or verified upper-bound sources.
They must not contribute a BPC lower bound or BPC certificate. Use the audit
script before reporting any BPC result:

```powershell
python scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\certificate_audit.csv --fail-on-error
```

The solver also guards JSON output: an original-problem run with
`status=optimal` is downgraded before writing if the full certificate audit
does not prove `certified_original_problem=true`.

## New Optimization Options

- `--column-dominance true|false`: enable exact-safe route-load projection dominance.
- `--column-dominance-mode exact|pareto|off`: use exact projection equivalence when path-independent, or Pareto filtering when path-dependent coefficients matter.
- `--projection-bound true|false`: enable the inventory-ratio interval projection lower bound.
- `--penalty-domain-tightening true|false`: tighten final-inventory domains using incumbent objective and interval floor.
- `--movement-domain-tightening true|false`: tighten final-inventory domains using station reachability from route-duration, handling-time, station, and truck-capacity necessary conditions.
- `--movement-bound-audit true|false`: compute interval relaxation bounds with and without movement-domain tightening and record/use the stronger valid bound.
- `--frontier-best-bound-scheduling true|false`: process frontier intervals by deterministic valid lower-bound priority instead of raw interval order.
- `--frontier-relaxation-cache true|false`: reuse exact-key interval relaxation bounds across retry passes.
- `--frontier-split-before-tree true|false`: for adaptive frontier runs, defer
  initial branch-price trees on broad splittable intervals until after the
  interval is split and child relaxations are attempted. This is a scheduling
  option only; it does not change certificate requirements.
- `--support-duration-pruning true|false`: prune exact pricing labels whose station support contains a subset proven route-duration infeasible.
- `--support-duration-max-subset-size N`: maximum station subset size used for support-duration pruning precomputation.
- `--pricing-completion-lb-pruning true|false`: prune an exact-label pricing label only when a valid reduced-cost lower bound proves no completion can improve the current best priced column. This is certificate-safe but remains an explicit tuning option rather than the default paper-core setting.
- `--route-mask-support-duration-pruning true|false`: apply the same exact-safe support-duration infeasibility test to complete route-mask relaxation masks.
- `--frontier-focused-min-lb-retry true|false`: spend retry time on the unresolved frontier interval with the smallest valid lower bound.
- `--frontier-focused-intensification true|false`: reserve time to rerun stronger relaxations on the current minimum-LB unresolved interval.
- `--frontier-focused-reserve-fraction x`: fraction of the time limit reserved for focused intensification.
- `--frontier-adaptive-split true|false`: split the current minimum-LB unresolved Gini interval into exactly covering child intervals.
- `--frontier-adaptive-max-depth N`: maximum adaptive split depth for a frontier leaf interval. The `paper-bpc-core` and `paper-exact-portfolio` presets default this to 8 unless explicitly overridden, because depth-8 certificate-neutral child relaxations gave the best current V12 M1/M2 lower-bound progress before expensive BPC tree pricing.
- `--route-mask-operation-budget-cuts true|false`: add mask-specific pickup-operation budget rows to the route-mask relaxation using depot-cycle lower bounds.
- In `paper-bpc-core`, operation-budget route-mask rows are still enabled, but
  the frontier relaxation now uses a certificate-safe relaxation portfolio: if
  the operation-budget MIP does not fathom an interval within budget, the solver
  also tries the same vehicle-indexed inventory/route/Gini relaxation with
  operation-budget rows disabled and keeps the stronger valid lower bound. This
  prevents a harder strengthening MIP from regressing the final frontier ledger.
- `--route-pool-incumbent true|false`: collect verified BPC-generated route-load columns and solve a true-objective restricted route-column incumbent master for upper bounds only.
- `--route-pool-max-columns-per-vehicle N`: cap stored route-pool columns per vehicle after projection dominance.
- `--pickup-drop-compat-flow true|false`: strengthen the inventory/route/Gini relaxation with pickup-to-drop compatibility flow variables when pairs can be safely screened by route-duration lower bounds.
- `--pickup-drop-transfer-cap-flow true|false`: add safe quantity upper bounds to pickup-drop transfer variables from travel/handling lower bounds and capacities.
- `--primal-heuristic none|greedy|hga-tgbc|best-of-all`: generate a verifier-gated route-plan upper bound. `paper-bpc-core` defaults to deterministic seeded native HGA-TGBC; this replaces arbitrary result-directory archive scanning as the paper-core default UB source. The native path preserves the migrated TGBC decoder, route repair, route-inheritance crossover, ordered-separator crossover, mutation, guided education, compaction, and decode-cache components, and accepts only verifier-passed complete route plans.
- `--primal-heuristic-seconds <seconds> --primal-heuristic-seed <int> --primal-heuristic-runs <int>`: control the reproducible primal heuristic budget and seed.
- `--heuristic-candidates-csv <path>`: write every verifier-checked primal heuristic candidate with objective components, route counts, operation totals, route durations, runtime, and accepted-as-best status. This is useful for auditing HGA/TGBC-style incumbent quality without giving any lower-bound credit to the heuristic.
- `--bpc-incumbent auto|best-of-all`: run a bounded verified incumbent portfolio and select the best true-objective route plan as an upper bound.
- `--incumbent-archive-auto true|false --incumbent-archive-dir <dir>`: explicitly scan prior route-bearing results for verified upper-bound route plans. This is a diagnostic UB source only; `paper-bpc-core` does not enable it by default and archive evidence never contributes to a lower bound.
- `--progress-log <path> --progress-interval-seconds <seconds>`: write frontier progress checkpoints for convergence reporting.
- `--method certificate-basis-test`: runs C++ guard fixtures that construct
  unsafe original-BPC `SolveResult` objects and verify that JSON output is
  downgraded unless the full certificate conditions hold. It also includes a
  valid relaxation-only frontier certificate fixture.
- `--support-feasibility-oracle true|false`: reserved switch for exact small-support infeasibility checking; default is false and heuristic support cuts are not generated.
- `--incumbent-json <path> --incumbent-format exact_result --incumbent-source-name <name>`: import a verified incumbent route solution as an upper-bound/cutoff source only.
- `--incumbent-format auto|exact_result|route_json|csv`: parse incumbent files as ExactEBRP result JSON, route JSON, or CSV with vehicle/order/station/pickup/drop columns.
- `--hga-incumbent <path> --hga-incumbent-format auto|route_json|csv|legacy`: import HGA/TGBC-style route outputs when a compatible route-bearing file is available. Legacy objective-only files are rejected rather than fabricated into routes.
- `--external-incumbent <path> --external-incumbent-format auto|route_json|csv|legacy_text`: import any external heuristic route plan through the same independent verifier. Verified imports are upper bounds only.
- `--export-incumbent <path>`: export the current best route plan in the route JSON schema used by `--external-incumbent`.
- `--large-instance-mode auto|off|force`: enable large-instance guards. In `auto`, all-subset route-mask enumeration is disabled for large V unless a certifying replacement is available.
- `--pricing-engine exact-label|ng-dssr|hybrid --ng-size <N> --dssr-max-rounds <N> --dssr-time-limit <seconds>`: choose exact label pricing or the hybrid ng-route/DSSR pricing diagnostic. Relaxed pricing does not certify closure unless exact DSSR/final verification completes.
- `--cg-dual-stabilization none|smooth|box --cg-dual-smoothing-alpha <a> --cg-dual-box-radius <r>`: use stabilized duals for column discovery only; final closure still requires true-dual pricing.

Example large-instance diagnostic:

```powershell
build\ExactEBRP.exe --method pricing --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --time-limit 60 --large-instance-mode auto --pricing-engine hybrid --ng-size 12 --dssr-time-limit 60 --cg-dual-stabilization smooth --out results\optimization_update_round12\raw\V100_pricing_hybrid_60s.json
```

Generate deterministic engineering benchmarks when historical V8/V10/V20/V50/V100 source files are unavailable:

```powershell
python scripts\generate_reference_instances.py
```

If Python is unavailable, the checked-in `reference\generated\manifest.csv` identifies the generated engineering benchmark files already used by the round-twelve diagnostics.
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

Round-thirteen production hybrid-pricing examples:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --ng-size 8 --ng-neighborhood-mode dual-aware --dssr-max-rounds 5 --dssr-expand-per-round 3 --dssr-time-limit 20 --dssr-final-exact true --cg-dual-stabilization smooth --frontier-intervals 8 --frontier-adaptive-split true --frontier-focused-intensification true --progress-log results\optimization_update_round13\raw\progress_v12_m2_full_hybrid_300s.csv --out results\optimization_update_round13\raw\v12_m2_full_hybrid_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514 --frontier-closure-mode exact-cg --pricing-engine hybrid --ng-size 8 --ng-neighborhood-mode nearest --dssr-final-exact true --out results\optimization_update_round13\raw\v12_m2_focus_hybrid_300s.json
```

Large-instance diagnostic examples:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\generated\regen_V20_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --large-instance-mode auto --large-lb-mode movement-projection --pricing-engine hybrid --ng-size 12 --ng-neighborhood-mode hybrid --dssr-max-rounds 5 --cg-dual-stabilization smooth --out results\optimization_update_round13\raw\v20_hybrid_300s.json

build\ExactEBRP.exe --method pricing --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --time-limit 300 --large-instance-mode auto --pricing-engine hybrid --ng-size 12 --ng-neighborhood-mode hybrid --dssr-final-exact false --out results\optimization_update_round13\raw\v100_hybrid_pricing_300s.json

build\ExactEBRP.exe --method large-lb-test --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --large-lb-mode movement-projection --out results\optimization_update_round13\raw\v100_large_lb_test.json
```

External/HGA incumbent conversion and verification:

```powershell
python scripts\convert_hga_incumbent.py --input hga_routes.csv --format csv --output results\converted_hga_incumbent.json

build\ExactEBRP.exe --method incumbent-import-test --input reference\generated\regen_V50_M3_average.txt --lambda 0.15 --T 3600 --external-incumbent results\converted_hga_incumbent.json --external-incumbent-format route_json --out results\optimization_update_round13\raw\v50_external_incumbent.json
```

Hybrid/ng-DSSR and stabilized duals are column-discovery tools unless DSSR
exactness or true-dual final pricing verification completes. V50/V100 rows are
diagnostics unless the full certificate protocol closes.

Round-fourteen two-track relaxed route-load examples:

```powershell
build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --pricing-engine hybrid --column-tracks two-track --relaxed-columns-in-rmp true --relaxed-columns-max-per-pricing 8 --rmp-column-space two-track --dssr-close-relaxed-pricing true --dssr-final-exact true --progress-log results\optimization_update_round14\raw\progress_v12_m2_full_twotrack_300s.csv --out results\optimization_update_round14\raw\v12_m2_full_twotrack_300s.json

build\ExactEBRP.exe --method gcap-frontier --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-focus-only true --frontier-focus-range 0.489218,0.512514 --pricing-engine hybrid --column-tracks two-track --relaxed-columns-in-rmp true --rmp-column-space two-track --dssr-close-relaxed-pricing true --out results\optimization_update_round14\raw\v12_m2_focus_twotrack_300s.json

build\ExactEBRP.exe --method large-relaxed-rmp-test --input reference\generated\regen_V100_M5_average.txt --lambda 0.15 --T 3600 --large-instance-mode force --large-relaxed-rmp true --large-lb-mode movement-projection --pricing-engine hybrid --column-tracks two-track --relaxed-columns-in-rmp true --rmp-column-space two-track --out results\optimization_update_round14\raw\v100_relaxed_rmp_300s.json

build\ExactEBRP.exe --method relaxed-column-incumbent-safety-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --column-tracks two-track --relaxed-columns-in-rmp true --out results\optimization_update_round14\raw\v4_relaxed-column-incumbent-safety-test.json
```

Relaxed columns are lower-bound-only. They are excluded from route-pool
incumbents and exported route plans, and a relaxed RMP can support a
certificate only after ng-relaxed pricing closes for the chosen relaxation.
### Projection-Safe Relaxed-RMP CG

Round 15 adds a lower-bound-only relaxed column path for hybrid/ng-DSSR BPC.
Projection-safe non-elementary relaxed columns can be enabled with:

```bash
build/ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt \
  --lambda 0.15 --T 3600 --pricing-engine hybrid \
  --column-tracks two-track --rmp-column-space two-track \
  --relaxed-columns-in-rmp true --allow-non-elementary-relaxed-columns true \
  --relaxed-projection-strict true --relaxed-rmp-cg true \
  --frontier-relaxed-rmp-cg true --ng-relaxed-closure true
```

Large generated diagnostics can use the relaxed-RMP CG path without all-subset
route-mask enumeration:

```bash
build/ExactEBRP.exe --method large-relaxed-rmp-cg-test \
  --input reference/generated/regen_V50_M3_average.txt --lambda 0.15 --T 3600 \
  --pricing-engine hybrid --large-instance-mode force \
  --large-relaxed-rmp-cg true --large-relaxed-rmp-time 300 \
  --large-relaxed-rmp-column-budget 256 --ng-relaxed-closure true
```

Relaxed columns are lower-bound-only.  They are blocked from incumbent
reconstruction, route-pool incumbent masters, and exported route plans unless
they are explicitly elementary feasible columns.

### Paper Algorithm Presets

Round 16 defines reproducible presets for paper-facing runs:

```bash
build/ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt \
  --lambda 0.15 --T 3600 --time-limit 300 \
  --algorithm-preset paper-bpc-core \
  --primal-heuristic hga-tgbc --primal-heuristic-seed 20260626 \
  --progress-log results/optimization_update_round16/progress/v12_m2_core.csv \
  --out results/optimization_update_round16/raw/v12_m2_core.json

build/ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt \
  --lambda 0.15 --T 3600 --time-limit 300 \
  --algorithm-preset paper-exact-portfolio \
  --out results/optimization_update_round16/raw/v12_m2_portfolio_bpc.json

build/ExactEBRP.exe --method gcap-frontier --input reference/regen_candidate_V12_M2_average.txt \
  --lambda 0.15 --T 3600 --time-limit 300 \
  --algorithm-preset paper-bpc-experimental \
  --out results/optimization_update_round16/raw/v12_m2_experimental.json

build/ExactEBRP.exe --method large-relaxed-rmp-cg-test \
  --input reference/generated/regen_V100_M5_average.txt --lambda 0.15 --T 3600 \
  --algorithm-preset diagnostic-large --out results/optimization_update_round16/raw/v100_diag.json
```

`--production-preset` is accepted as an alias for `--algorithm-preset`.
`paper-bpc-core` is the main exact BPC configuration. `paper-exact-portfolio`
adds compact fallback evidence as a companion exact module. `paper-bpc-experimental`
enables hybrid/ng-DSSR and two-track relaxed-RMP features and remains
experimental unless relaxed pricing closes. `diagnostic-large` is for large
generated instances and is noncertifying unless the full certificate protocol
closes.

For paper tables, do not use `--incumbent-archive-auto true`; archive scanning
is retained only as a diagnostic UB source.
