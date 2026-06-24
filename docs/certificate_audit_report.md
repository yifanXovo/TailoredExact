# Certificate Audit Report

Date: 2026-06-25

## Implemented Guards

- Added `scripts/audit_bpc_certificate.py`.
- Added a JSON output guard in `src/Result.cpp`: if an original-problem method
  tries to emit `status=optimal` but the full certificate audit does not prove
  `certified_original_problem=true`, the emitted status is changed to
  `not_certified_incomplete_certificate`.
- The guard also downgrades derived `bpc_status`/`portfolio_status` fields when
  they would otherwise retain a stale `optimal` value.

## Paper-Core Scope Enforcement

`--algorithm-preset paper-bpc-core` now resolves to elementary-column,
exact-label GF-RL-BPC settings and disables:

- compact fallback certificates;
- hybrid/ng-DSSR;
- two-track relaxed RMP;
- large diagnostic modes;
- focus-only runs;
- imported focus bounds;
- frontier resume;
- iterative closure shortcuts.

## Validation Commands

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --progress-log results\paper_bpc_core\progress\v4_paper_core_smoke.csv --progress-interval-seconds 5 --out results\paper_bpc_core\raw\v4_paper_core_smoke.json
build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\paper_bpc_core\raw\option_consistency_paper_core.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\generated\regen_V8_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --frontier-relax-seconds 0.5 --frontier-focused-reserve-fraction 0 --frontier-focused-intensification false --progress-log results\paper_bpc_core\progress\v8_trace_tree_probe_60s.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v8_trace_tree_probe_60s.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_300s.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_300s.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s.json
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\audit\certificate_audit.csv
```

## Current Audit Evidence

`results/paper_bpc_core/audit/certificate_audit.csv` currently audits eight JSON
rows with zero failures:

- V4 paper-core smoke: certified original problem, objective 0.
- option-consistency diagnostic: not certified, as expected.
- V12 M1 Average 20s trace validation: not closed, not certified.
- V12 M1 Average 60s: not closed, not certified.
- V12 M1 Average 300s: not closed, not certified.
- V12 M2 Average 60s: not closed, not certified.
- V12 M2 Average 300s: not closed, not certified.
- V8 M2 generated 60s tree-trace probe: not closed, not certified; used only
  to validate node/pricing trace emission.

The audit script skips `*.trace.json` files whose top-level object contains
`trace_schema`; those files are diagnostic artifacts, not solver result JSON.

## Plateau Trace Artifacts

Every `paper-bpc-core` result with an output path now records:

- `bpc_trace_json`;
- `bpc_interval_trace_csv`.

The trace schema is `paper_bpc_core_plateau_trace_v1`. For normal frontier
runs it records the active interval ledger plus aggregate tree/pricing
counters. For branch-price trees that actually start, it also records
structured `branch_price_nodes` and `pricing_calls` arrays. For early
zero-objective certificates it records a minimal early-exit trace.

The V8 generated tree-trace probe validates this path with 53 node trace
objects and 100 pricing-call trace objects. V12 M1/M2 60s rows still report
`branch_price_node_trace_available=false` because their controlling leaves do
not reach a branch-price tree before the time/reserve stop.

The V12 300s rows do reach branch-price trees and expose the first actionable
plateau evidence:

- V12 M1 300s: UB 0.357200583208, LB 0.268414876140, gap 0.248559804329.
  The controlling interval is `4:[0.1786,0.238134]`, inherited from a split
  parent. The run has 5 node trace objects and 5 pricing-call trace objects;
  unresolved nodes report `pricing_did_not_close`.
- V12 M2 300s: UB 0.719065249476, LB 0.577560696100, gap 0.196789586869.
  The controlling interval is `4:[0.359533,0.479377]`, with an
  inventory/route/Gini relaxation lower bound. The run has 4 node trace
  objects and 14 pricing-call trace objects; unresolved nodes report
  `pricing_did_not_close`.

The interval CSV now records per-interval aggregate BPC counters when a tree
pass actually starts: `bpc_nodes`, `generated_columns`, `cuts`,
`pricing_calls`, `pricing_time_seconds`, `rmp_solve_time_seconds`, and
`relaxation_time_seconds`. If a relevant leaf has `open_nodes>0` but
`bpc_nodes=0`, the trace reason is
`tree_not_started_before_time_limit_or_reserve`; this distinguishes a queued
frontier leaf from a branch-price tree that has started and remains open.

## Completion Lower-Bound Pricing Pruning Diagnostic

Exact-label completion lower-bound pruning is implemented as an explicit tuning
option. It is a certificate-safe enumeration reduction: a label is skipped only
when a true-dual reduced-cost lower bound proves that no feasible completion
can improve the best priced column already found. The pruning does not certify
node closure; exact pricing still has to complete with no negative reduced-cost
column.

Validation rows with the pruning enabled explicitly:

- V4 paper-core smoke remains certified at objective 0.
- V12 M2 60s remains noncertified. It still does not start the controlling
  BPC tree before the time/reserve stop, so completion-LB pruning has no
  opportunity to affect the plateau in that short run.
- V8 generated tree-trace probe remains noncertified and audit-safe, but now
  records `completion_lb_pruned_labels=9559313` at aggregate result level and
  per-pricing-call completion-prune counters in the trace. This confirms the
  pruning is active on real branch-price pricing calls without changing
  certificate semantics.
- V12 M1 300s with pruning reaches the same LB/gap as the baseline while
  reducing captured operation states. V12 M2 300s with pruning is worse in the
  current controlled row because the controlling split leaf keeps only the
  inherited parent lower bound rather than the stronger relaxation bound seen
  in the baseline. Therefore the pruning remains disabled by default in
  `paper-bpc-core` until more robust evidence is available.

The full audit over `results/paper_bpc_core/raw` now covers fourteen solver JSON
rows with zero failures.

The audit script self-test includes intentionally invalid cases for incomplete
pricing, duplicate negative-column blockage, partial frontier coverage,
route-mask certifying with enumeration disabled, and original optimality without
`certified_original_problem=true`.

## Remaining Audit Work

- Add C++ unit-style fixtures that create unsafe `SolveResult` objects and
  verify the JSON guard directly.
- Extend pricing internals further with detailed dominance-bucket and
  unfinished-state frontier counts. Current pricing-call traces include vehicle,
  engine, dual summary, generated columns, route/operation states, support
  pruning totals, best reduced cost, completion status, and elapsed time.
- Run the required 300s/1200s V12 paper-core matrix after the first safety pass.
