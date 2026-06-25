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

The audit over `results/paper_bpc_core/raw` at that stage covered fourteen
solver JSON rows with zero failures.

## Compatibility-Flow Relaxation Ordering

The inventory/route/Gini relaxation can evaluate both a pickup/drop
compatibility-flow model and a no-compatibility model, then keep the larger
valid lower bound. This is certificate-safe because either relaxation produces
a valid lower bound; the compatibility-flow rows are strengthening rows, not a
certificate shortcut.

The ordering now solves the no-compatibility model first. If that easier model
already cutoff-fathoms the interval, the compatibility model is skipped. This
does not weaken certification: a bound-fathomed interval still has a valid
non-pricing lower bound at the incumbent cutoff, and no BPC pricing closure is
claimed.

Validation rows:

- V4 paper-core smoke remains certified at objective 0.
- V12 M1 300s remains noncertified with unchanged LB/gap.
- V12 M2 300s improves from `LB=0.577560696100`, gap `0.196789586869`
  to `LB=0.692627421486`, gap `0.036766938758`. The formerly controlling
  split child `[0.359532624738,0.479376832984]` is now bound-fathomed by
  the no-compatibility relaxation before the solver runs out of time.

## Split-Before-Tree Frontier Scheduling

The V12 M2 1200s row exposed a scheduling failure: the solver spent most of the
budget running a branch-price tree on a broad high-Gini parent interval before
adaptive splitting. When the split finally occurred, one active child retained
only the inherited parent lower bound, so the final global lower bound regressed
to `0.469117173935` despite a better 300s relaxation-bound row already being
available. The row remains audit-safe and noncertified, but it is a poor use of
paper-core time.

`--frontier-split-before-tree true` now defers the initial branch-price tree for
eligible broad intervals and lets adaptive child intervals receive relaxation
bounds first. This is certificate-neutral because the parent interval is not
counted after replacement and the children exactly cover the same range.

Validation rows:

- V4 paper-core smoke with split-before-tree remains certified at objective 0.
- V12 M2 split-before-tree 300s remains noncertified but improves the valid
  lower bound to `LB=0.696966843140`, gap `0.0307321294594`, with two
  unresolved high-Gini leaves.
- The non-split 1200s diagnostic remains noncertified with `LB=0.469117173935`
  and documents the scheduling regression.

The full audit over `results/paper_bpc_core/raw` now covers twenty solver JSON
rows with zero failures.

## V12 M1 1200s Paper-Core Row

The required V12 M1 1200s paper-core row was run after enabling
split-before-tree scheduling. It remains noncertified:

- UB `0.357200583208`, LB `0.332675660948`, gap `0.0686586848205`.
- `unresolved_intervals=2`, `open_nodes=2`, `invalid_bound_intervals=0`.
- The lower-bound source is `focused_child_inventory_route_gini_relaxation`.
- Runtime is dominated by exact-label pricing:
  `pricing_time_seconds=896.6435636`, `master_time_seconds=79.5333302`,
  `bound_time_seconds=211.0970326`.

The audit accepts the row only as a noncertified result. This row supplies the
current strongest V12 M1 paper-core lower bound and confirms that the remaining
plateau is pricing/tree closure in the high-Gini children, not a false optimal
certificate.

The completion-LB pruning diagnostics were rerun after split-before-tree
scheduling on V12 M1 and V12 M2. Both rows remain noncertified and audit-safe;
neither changes the certificate-relevant lower bound versus the matching
split-before-tree baseline. This supports keeping completion-LB pruning as an
explicit diagnostic/tuning option rather than a paper-core default.

The full audit over `results/paper_bpc_core/raw` now covers twenty-four solver
JSON rows with zero failures.

The V12 M2 split-before-tree 1200s row was added after that diagnostic. It is
also audit-safe and noncertified: `LB=0.703291904615`,
`UB=0.719065249476`, gap `0.0219359020237`,
`unresolved_intervals=1`, `open_nodes=1`, and
`certified_original_problem=false`. The audit accepts the valid lower bound but
does not allow original-problem optimality because the final active interval is
not closed.

The full audit over `results/paper_bpc_core/raw` now covers twenty-five solver
JSON rows with zero failures.

The adaptive split-depth paper-core change was then validated. The paper
presets now default `frontier_adaptive_max_depth` to 5 unless the command line
sets another value. This is certificate-neutral: split children exactly cover
their parent and still require normal interval completion or valid
bound-fathoming. V4 remains certified at objective 0. V12 M1 300s improves to
`LB=0.340282088370`, gap `0.0473641299419`; V12 M2 300s improves to
`LB=0.706200471341`, gap `0.0178909746296`. Both V12 rows remain
noncertified because active child intervals are unresolved.

The full audit over `results/paper_bpc_core/raw` now covers thirty-one solver
JSON rows with zero failures.

The V12 M2 depth-5 1200s row was added next. It remains noncertified but raises
the valid lower bound to `0.710439004053` with gap `0.0119964710145`.
`unresolved_intervals=2`, `open_nodes=2`, and `certified_original_problem=false`
are correctly preserved, so no original-problem certificate is claimed.

The full audit over `results/paper_bpc_core/raw` now covers thirty-two solver
JSON rows with zero failures.

The V12 M1 depth-5 1200s row was added after that. It remains audit-safe and
noncertified: `LB=0.340282088370`, `UB=0.357200583208`, gap
`0.0473641299419`, `unresolved_intervals=3`, `open_nodes=29`, and
`certified_original_problem=false`. The audit accepts the row only as valid
lower-bound progress evidence, not as an original-problem certificate.

The full audit over `results/paper_bpc_core/raw` now covers thirty-three
solver JSON rows with zero failures.

The label-dominance trace audit added two more paper-core rows: V4 smoke and
V12 M1 300s. V4 remains certified at objective 0. V12 M1 remains correctly
noncertified with positive gap and unresolved intervals. The new dominance
counters are diagnostic trace fields only; they do not affect certificate
classification. The full audit over `results/paper_bpc_core/raw` now covers
thirty-five solver JSON rows with zero failures.

The depth-6 default validation rows were then added. V4 smoke remains
certified at objective 0. V12 M1 300s and V12 M2 300s remain correctly
noncertified with positive gaps and unresolved intervals. The V12 M1 depth-6
1200s row is also correctly classified as noncertified:
`LB=0.344881668930`, `UB=0.357200583208`, gap `0.0344873856805`,
`unresolved_intervals=3`, `open_nodes=4`, and
`certified_original_problem=false`. The full audit over
`results/paper_bpc_core/raw` now covers thirty-nine solver JSON rows with zero
failures.

The depth-7 default validation rows were added next. V4 smoke remains certified
at objective 0. V12 M1 300s reaches `LB=0.344613240900`,
`UB=0.357200583208`, gap `0.035238862701`, and V12 M2 300s reaches
`LB=0.715075764785`, `UB=0.719065249476`, gap `0.00554815393275`.
Both V12 rows remain correctly noncertified because they have positive gaps and
`unresolved_intervals=3`. The full audit over `results/paper_bpc_core/raw` now
covers forty-two solver JSON rows with zero failures.

The depth-8 default validation rows were then added. V4 smoke remains certified
at objective 0. V12 M1 300s remains audit-safe and noncertified with
`LB=0.344613240900`, `UB=0.357200583208`, gap `0.035238862701`,
and `unresolved_intervals=3`. V12 M2 300s improves to
`LB=0.716948330538`, `UB=0.719065249476`, gap `0.00294398726726`,
but remains correctly noncertified because the frontier still has three
unresolved active leaves. The full audit over `results/paper_bpc_core/raw` now
covers forty-five solver JSON rows with zero failures.

The explicit depth-9 diagnostics were then added as rejected scheduling
evidence. Both rows remain correctly noncertified: V12 M1 is unchanged from
depth 8, and V12 M2 is weaker than the depth-8 default within the same 300s
budget. The full audit over `results/paper_bpc_core/raw` now covers forty-seven
solver JSON rows with zero failures.

The trace completeness audit was extended after a V12 M1 depth-6/no-focused
diagnostic exposed that aggregate BPC pricing calls could be present while the
paper-core trace lacked per-call JSON objects. The CG path now writes pricing
trace objects before time-limit returns, including event, vehicle, exact
completion, best reduced cost, state counts, dominance counters, and unfinished
state count. The same audit found and fixed a pricing timer bug: per-call
remaining budgets were being paired with the older CG/node start timestamp,
which could cause immediate timeouts before state enumeration. A one-interval
V12 M1 trace validation row confirms the `pricing_calls` array is populated for
a started BPC tree and that time-limited pricing now reports nonzero route and
operation states. The depth-6 no-focused diagnostic records a real time-limited
pricing call with negative reduced cost remaining, so the node remains
unresolved. A follow-up exact-pricing optimization compacts inactive label
indices inside dominance buckets. This is certificate-neutral because it
removes only references to labels already marked inactive by the unchanged exact
dominance rule. The refreshed V12 M1 depth-6 diagnostic records `1,239,056`
bucket compactions, `17,581,023` compacted entries, and the same noncertified
lower bound/gap. The full audit over `results/paper_bpc_core/raw` now covers
fifty-three solver JSON rows with zero failures.

The audit script self-test includes intentionally invalid cases for incomplete
pricing, duplicate negative-column blockage, partial frontier coverage,
route-mask certifying with enumeration disabled, and original optimality without
`certified_original_problem=true`.

The continuous LP cutoff-precheck rows added another V4 smoke row and V12
M1/M2 60s diagnostics. The V4 row remains certified at objective 0. The V12
rows remain correctly noncertified with positive gaps and unresolved intervals.
The precheck can mark an interval as cutoff-fathomed only when the continuous
relaxation of the same inventory/route/Gini cutoff model is infeasible or has a
lower bound at the incumbent cutoff; otherwise it falls back to the existing
integer route-mask MIP. The full audit over `results/paper_bpc_core/raw` now
covers fifty-six solver JSON rows with zero failures.

The gated-precheck and required-closure-pricing rows extend the audit to
sixty-three solver JSON rows with zero failures. The additional V4 rows remain
certified at objective 0. The V12 M1/M2 rows remain correctly noncertified with
positive gaps and unresolved intervals, including the rejected ungated V12 M2
300s diagnostic and the accepted gated V12 M2 300s row.

The short-budget compatibility-flow skip and archive-incumbent scheduling rows
extend the audit to seventy-six solver JSON rows with zero failures. V4
paper-core remains certified at objective 0. The new V12 rows are correctly
noncertified: V12 M1 archive-skip 300s has
`LB=0.344881668930`, `UB=0.357200583208`, gap `0.0344873856805`, and
`unresolved_intervals=4`; V12 M2 archive-skip 300s has
`LB=0.717435865864`, `UB=0.719065249476`, gap `0.00226597462971`, and
`unresolved_intervals=3`. In both cases the archive incumbent is used only as a
verified upper-bound cutoff and does not contribute to lower-bound evidence or
certificate closure.

Two later scheduling probes extend the audit to seventy-eight solver JSON rows
with zero failures. Both are deliberately noncertified. The V12 M1 300s
adaptive-focus-reserve probe (`--frontier-retry-reserve 75`) regresses to
`LB=0.340282088370`, gap `0.0473641299419`, and
`unresolved_intervals=3`; the V12 M2 300s focused-relaxation probe
(`--frontier-focused-relax-seconds 2.5`) regresses to
`LB=0.715075764785`, gap `0.00554815393275`, and
`unresolved_intervals=3`. These rows confirm that the certificate guard still
keeps positive-gap scheduling experiments non-optimal, and they are rejected as
default paper-core configuration changes.

The V12 M2 archive-incumbent 1200s long-run row extends the audit to
seventy-nine solver JSON rows with zero failures. It is correctly
noncertified: `LB=0.717435865864`, `UB=0.719065249476`, gap
`0.00226597462971`, `unresolved_intervals=4`, `invalid_bound_intervals=0`,
and `open_nodes=30`. The row keeps the verified archive incumbent as an
upper-bound cutoff only and reports no original-problem certificate.

## Remaining Audit Work

- Add C++ unit-style fixtures that create unsafe `SolveResult` objects and
  verify the JSON guard directly.
- Extend pricing internals further with unfinished-state frontier counts.
  Current pricing-call traces include vehicle, engine, dual summary, generated
  columns, route/operation states, support pruning totals, dominance-bucket
  compaction totals, best reduced cost, completion status, and elapsed time.
- Run the required 300s/1200s V12 paper-core matrix after the first safety pass.
