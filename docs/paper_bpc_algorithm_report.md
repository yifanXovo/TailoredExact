# Paper BPC Algorithm Report

Date: 2026-06-14.

## Scope

The recommended exact algorithm is now a tailored exact portfolio for the original EBRP objective

```text
minimize G + lambda * P
```

where `G = H/(V*S)`, `H=sum_{i<j}|r_i-r_j|`, `S=sum_i r_i`, and `P=sum_i w_i |r_i-1|`. Current experiments use `lambda=0.15`, `T=3600`, pickup time `60`, and drop time `60`.

The portfolio has two exact modules:

- `original_bpc`: pure full Gini-frontier route-load BPC (`gcap-frontier`).
- `original_compact`: strengthened compact branch-and-cut fallback.

Plain CPLEX with `--plain-baseline` is the benchmark. Diagnostics such as pricing, master, fixed-cap, cuts, and restricted pools are not original-problem certificates unless wrapped by a complete exact certificate.

## Algorithm

`gcap-frontier` covers at least `G in [0, incumbent_objective]`. For each interval `[gamma_L,gamma_U]`, it solves or bounds a route-load branch-price tree:

- Gini cap: `G <= gamma_U iff H <= V * gamma_U * S`.
- Interval floor: `G >= gamma_L`, hence objective lower bound `>= gamma_L`.
- Columns are complete elementary vehicle routes with integer pickup/drop operations.
- Node closure requires exact route-load pricing unless the interval is bound-fathomed by a valid lower bound.
- Ryan-Foster/co-route branching, subset-row cuts, operation-time conservation, final-inventory pickup/route/Gini bounds, complete `V<=12` route-mask duration/load relaxations, and station-operation cuts are active where valid.

Pure-BPC incumbent generation includes greedy construction, randomized greedy starts, exact load-decoded local search with relocate/resize/swap moves, and a restricted verified route-column pool incumbent master. These mechanisms provide upper bounds only.

The station-operation relaxation rows are documented in `docs/station_operation_cut_proof.md`:

```text
p_i + d_i <= U_i v_i
p_i + d_i >= v_i
U_i = max(min(Y_i^initial,Qmax), min(C_i-Y_i^initial,Qmax)).
```

## Certificate Rules

A BPC result is certified only if `status=optimal`, `gap=0`, `lower_bound=upper_bound=objective`, `verifier_passed=true`, `unresolved_intervals=0`, `invalid_bound_intervals=0`, and the full frontier ledger closes. Compact fallback certificates require the same objective equality, closed MIP gap, and verifier pass, but they are not BPC.

`wall_time_seconds` is elapsed wall time. Aggregate worker timings may exceed wall time under parallel BPC.

## Optimization Update: 2026-06-20

Implemented exactness-preserving BPC optimizations:

- Closed route-load column projection dominance in `ColumnPool`. Exact mode compresses columns with the same vehicle, station mask, and signed operation vector when the active master has no path-dependent objective term. Pareto mode is available for path-dependent objectives.
- Filtered multi-column pricing insertion. When `--gcap-pricing-columns N` returns multiple negative columns, candidates are dominance-filtered before entering the RMP. Early negative pricing stops still only add columns; they cannot close a node.
- Inventory-ratio interval projection lower bound. Valid final-inventory intervals imply lower bounds on `P`, `H`, `G`, and `G+lambda P`; interval floors are included.
- Incumbent penalty-budget domain tightening. In an interval with floor `gamma_L`, only inventory domains that can satisfy `gamma_L + lambda P <= UB` are retained for incumbent-improvement proofs.
- BPC-owned route-column incumbent pools are also dominance-compressed before the restricted incumbent search.

CLI controls:

```text
--column-dominance true|false
--column-dominance-mode exact|pareto|off
--projection-bound true|false
--penalty-domain-tightening true|false
--gcap-pricing-columns <N>
--frontier-column-cache true|false
```

The frontier column cache flag is currently logged but not enabled; cache reuse remains a documented TODO until a separate stability pass verifies no certificate issues.

Proofs are in `docs/optimization_proofs.md`. Short smoke and ablation outputs are in `results/optimization_update/`.

## Target Benchmark Table

Detailed machine-readable rows are in `docs/portfolio_benchmark_table.csv`.

| Instance | Method | Scope | Status | UB/objective | LB | Gap | Time (s) | Certified? |
|---|---|---|---|---:|---:|---:|---:|---|
| V10 M2 average | pure BPC | original_bpc | optimal | 0.463263009179 | 0.463263009179 | 0 | 589.0030 | yes |
| V10 M2 average | strengthened compact | original_compact | not certified | 0.463263009179 | 0.456115849720 | 0.0154279 | 300.1681 | no |
| V10 M2 average | plain CPLEX | plain_cplex | not certified | 0.463263009179 | 0.451894669070 | 0.0245397 | 1200.1490 | no |
| V10 M1 average | pure BPC | original_bpc | optimal | 0.492625123580 | 0.492625123580 | 0 | 641.0844 | yes |
| V10 M1 average | strengthened compact | original_compact | optimal | 0.492625123580 | 0.492625123580 | 0 | 166.3436 | yes, not BPC |
| V10 M1 average | plain CPLEX | plain_cplex | optimal | 0.492625123580 | 0.492625123580 | 0 | 63.3175 | yes |
| V10 M2 low | pure BPC | original_bpc | not closed | 0.831494993816 | 0.820406010310 | 0.0133362 | 1200.6103 | no |
| V10 M2 low | strengthened compact | original_compact | optimal | 0.824301313135 | 0.824301313135 | 0 | 938.1948 | yes, not BPC |
| V10 M2 low | plain CPLEX | plain_cplex | not certified | 0.824301313135 | 0.793050728170 | 0.0379116 | 300.0874 | no |
| V12 M1 average | pure BPC | original_bpc | optimal | 0.690938574743 | 0.690938574743 | 0 | 5280.7002 | yes |
| V12 M1 average | strengthened compact | original_compact | optimal | 0.690938574743 | 0.690938574743 | 0 | 123.3197 | yes, not BPC |
| V12 M1 average | plain CPLEX | plain_cplex | optimal | 0.690938574743 | 0.690938574743 | 0 | 9.2284 | yes |
| V12 M2 average | pure BPC | original_bpc | not closed | 0.404618571401 | 0.350523627890 | 0.1336937 | 1200.5870 | no |
| V12 M2 average | strengthened compact | original_compact | not certified | 0.366168793171 | 0.258189227130 | 0.2948901 | 300.2094 | no |
| V12 M2 average | plain CPLEX | plain_cplex | not certified | 0.365626842595 | 0.304969452260 | 0.1658997 | 300.2167 | no |

## Portfolio Outcomes

| Instance | Portfolio certificate | Status | Objective | LB | Gap | Portfolio runtime (s) |
|---|---|---|---:|---:|---:|---:|
| V10 M2 average | pure_bpc | optimal | 0.463263009179 | 0.463263009179 | 0 | 589.0030 |
| V10 M1 average | pure_bpc | optimal | 0.492625123580 | 0.492625123580 | 0 | 641.0844 |
| V10 M2 low | compact_fallback | optimal | 0.824301313135 | 0.824301313135 | 0 | 2138.8051 |
| V12 M1 average | pure_bpc | optimal | 0.690938574743 | 0.690938574743 | 0 | 5280.7002 |
| V12 M2 average | none | not certified | 0.366168793171 | 0.350523627890 | 0.0427266 | 1500.7963 |

The portfolio certifies four of the five target instances. V12 M2 remains open and must not be reported as optimal.

Correct comparison wording:

- V10 M2 average: BPC certified in `589.00s`; plain CPLEX did not certify within `1200.15s`, final gap `0.0245397`.
- V10 M2 low: portfolio certified by compact fallback in `2138.81s`; plain CPLEX did not certify within `300.09s`, final gap `0.0379116`.
- For V10 M1 and V12 M1, plain CPLEX is faster than BPC; do not claim a BPC speedup.

## Certificate Audits

- `docs/v10_m1_bpc_certificate_audit.md`
- `docs/v12_m1_bpc_certificate_audit.md`
- `docs/portfolio_certificate_audit.md`

The V12 M1 BPC audit notes that one retry tree was incomplete after finding the improved incumbent. The final certificate is not based on that restricted tree; it is based on the full frontier ledger becoming bound-certified with `unresolved_intervals=0`, `invalid_bound_intervals=0`, top-level `open_nodes=0`, and `gap=0`.

## Hard-Case Diagnosis

V10 M2 low remains open for pure BPC because the high-Gini interval lower bounds do not reach the best incumbent. The strengthened compact fallback closes it in `938.19s`, so the portfolio is robust on this instance even though BPC is not.

V12 M1 was previously a BPC near miss. The deeper 7200s run found the compact-optimum incumbent during interval retry and then bound-fathomed the remaining frontier, certifying pure BPC in `5280.70s`.

V12 M2 remains the only open target. The current best portfolio incumbent comes from compact B&C (`0.366168793171`) while the best valid portfolio lower bound comes from BPC (`0.350523627890`), leaving a valid portfolio gap of about `0.0427266`. Strong BPC-owned incumbents helped but did not close the lower-bound gap.

## Recommended Paper Direction

The paper should present a tailored exact portfolio, not pure BPC alone:

1. Run full Gini-frontier route-load BPC as the main decomposition-based method.
2. If BPC stalls, run strengthened compact branch-and-cut as an exact fallback.
3. Report module scopes separately.
4. Report portfolio optimality only when one module proves `gap=0` and the verifier passes.

Pure BPC is still valuable: it certifies V10 M2 average, V10 M1 average, and V12 M1 average. The compact fallback is necessary for robustness because it certifies V10 M2 low while pure BPC does not.

## Second Optimization Pass: Safe Pricing Closure, Movement-Domain Tightening, And Frontier Lower-Bound Scheduling

This pass adds certificate-preserving improvements to the BPC/frontier implementation:

- Incomplete frontier runs now report a valid top-level lower bound from the interval ledger rather than defaulting to zero.
- Duplicate or dominance-filtered negative pricing projections no longer close a node; they leave the node unresolved unless exact pricing proves no missing negative projection exists.
- Dominance statistics now separate pricing enumeration, dominance input/kept/removed counts, existing-projection removals, and RMP insertions.
- Movement-reachable inventory domains intersect station final-inventory bounds before projection and interval relaxations.
- Initial frontier intervals can be scheduled by deterministic best-bound priority, and interval relaxations can be reused through exact-key caching.

Round-two smoke and ablation outputs are in `results/optimization_update_round2/`. On the local inputs available for this pass, V4 smoke remains certified by BPC. V12 M1/M2 60s stress rows remain noncertified, but their top-level lower bounds now reflect valid interval-ledger progress instead of zero where a valid interval bound exists.

## Third Optimization Pass: Range Coverage, Movement Audit, Support Pruning

This pass adds additional certificate-safety and exactness-preserving runtime tools:

- Frontier coverage is checked against `min(incumbent_objective,(V-1)/V)`. A run with an explicit Gini cap below that range is labeled capped/partial diagnostic rather than original optimal.
- Movement-bound audit can compute interval relaxations with and without movement-domain tightening and use the stronger valid lower bound.
- Support-duration pricing pruning removes labels whose station support contains a subset proven impossible by metric-closure route-duration plus minimum handling time.
- The relaxation cache no longer keys on time budget; larger-budget hits are recomputed and logged as partial hits.
- BPC-owned incumbent pools now reject malformed route-load candidates with missing operation vectors. This fixed a captured Windows access violation in V12 M1 `--bpc-incumbent pricing/portfolio` repro runs.

Round-three outputs are in `results/optimization_update_round3/`.

| Instance | Variant | Status | UB | LB | Gap | Time (s) | Certified? |
|---|---|---|---:|---:|---:|---:|---|
| V4 smoke | off | optimal | 0 | 0 | 0 | 0.0004 | yes |
| V4 smoke | improved_full | optimal | 0 | 0 | 0 | 0.0005 | yes |
| V12 M1 average | off | not closed | 0.379830913219 | 0.253220608813 | 0.333333333333 | 28.53 | no |
| V12 M1 average | improved_full | not closed | 0.379830913219 | 0.253246606270 | 0.333264888517 | 28.59 | no |
| V12 M2 average | off | not closed | 0.779342269192 | 0.471977495770 | 0.394389969045 | 23.44 | no |
| V12 M2 average | improved_full | not closed | 0.779342269192 | 0.473381644940 | 0.392588258519 | 23.68 | no |

The local checkout contains runnable V4 and V12 text instances only. V8/V10 source text files were not present, so round-three ablations could not rerun those cases. No new original-problem certificate was obtained in this short pass beyond the V4 smoke certificate. The V12 average rows remain lower-bound progress only.

The captured address error is documented in `results/optimization_update_round3/notes_incumbent_failures.txt`; gdb traces are stored under `results/optimization_update_round3/logs/`. Post-fix repros are `raw/repro_v12_m1_pricing_after_fix.json` and `raw/repro_v12_m1_portfolio_after_fix.json`.

## Fourth Optimization Pass: Stronger Support-Duration Cuts, Route-Mask Pruning, Strong Incumbents, And Focused Frontier Retry

This pass tightened the exact-safe support-duration rule from one operation to
`ceil(|S|/2)` pickups for a station support `S`, applied the same rule to the
complete route-mask relaxation, added verified route JSON/CSV and compact-seed
incumbent paths, and exposed focused retry on the current minimum-LB frontier
interval. The support-feasibility oracle switch is present but remains disabled
by default; no heuristic support cuts are generated.

Local runnable source files for this pass were `testdata/examples/gcap_smoke_V4_M1.txt`,
`reference/regen_candidate_V12_M1_average.txt`, and
`reference/regen_candidate_V12_M2_average.txt`. V8/V10 source `.txt` files were
not present in the checkout; only historical logs/results were found, so those
cases were not rerun in round four.

| Instance | Variant | Status | UB | LB | Gap | Time (s) | Certified? | Incumbent source |
|---|---|---|---:|---:|---:|---:|---|---|
| V4 smoke | baseline_round3 | optimal | 0 | 0 | 0 | 1.51 | yes | empty route |
| V4 smoke | improved_full | optimal | 0 | 0 | 0 | 0.00 | yes | BPC-owned strong |
| V12 M1 average | baseline_round3 | not closed | 0.493696053863 | 0.239988434930 | 0.513894362630 | 56.16 | no | empty route |
| V12 M1 average | improved_full | not closed | 0.366157179488 | 0.276689024590 | 0.244343576775 | 49.97 | no | compact CPLEX seed |
| V12 M1 average | improved_full_long | not closed | 0.368331870826 | 0.277477740570 | 0.246663776480 | 90.70 | no | compact CPLEX seed |
| V12 M2 average | baseline_round3 | not closed | 1.008223209850 | 0.354202757800 | 0.648686169552 | 49.94 | no | empty route |
| V12 M2 average | improved_full | not closed | 0.759438494406 | 0.589597623560 | 0.223640060515 | 50.46 | no | BPC-owned portfolio |
| V12 M2 average | improved_full_long | not closed | 0.759438494406 | 0.589597623560 | 0.223640060515 | 78.28 | no | BPC-owned portfolio |

Best verified seeds on the local regenerated V12 inputs:

- V12 M1 average: compact-CPLEX seed, UB `0.366157179488`. This is a verified
  upper bound only and makes the run seeded/hybrid, not pure BPC performance.
- V12 M2 average: BPC-owned portfolio/strong seed, UB `0.759438494406`.

The real V4/V12 instances in this local pass generated zero support-duration
cuts and removed zero route masks. The required synthetic diagnostics are stored
in `smoke_support-pruning-test.json` and `smoke_route-mask-support-test.json`;
they show cases where the old one-operation rule cuts nothing but the
`ceil(|S|/2)` rule cuts infeasible supports. Therefore the mechanism is covered,
but it did not explain the V12 bottleneck on these regenerated cases.

All round-four smoke, incumbent, and ablation commands exited with code `0`; no
captured stdout/stderr log contained address/access-violation, segmentation,
`bad_alloc`, or out-of-memory signatures. Raw outputs and summaries are in
`results/optimization_update_round4/`.

## Fifth Optimization Pass: Focused Retry Execution, Route-Column Pool Incumbents, And Pickup-Drop Compatibility Relaxation

This pass fixes the focused-retry execution path so `--frontier-focused-min-lb-retry true`
spends remaining time on the unresolved interval that determines the current
global lower bound. It also adds a frontier route-column pool and a
true-objective restricted incumbent master. The pool master is verifier-gated
and supplies only upper bounds. Finally, the inventory/route/Gini relaxation can
include pickup-drop compatibility flow constraints; station pairs are removed
only when directed route-duration lower bounds prove that a pickup at `i` cannot
feed a drop at `j`.

Local runnable inputs remained `testdata/examples/gcap_smoke_V4_M1.txt`,
`reference/regen_candidate_V12_M1_average.txt`, and
`reference/regen_candidate_V12_M2_average.txt`. V8/V10 source `.txt` files were
not present in this checkout. CPLEX plain benchmarks were skipped in this pass;
compact/CPLEX-style seeds are used only as labeled upper-bound sources where
requested.

| Instance | Variant | Status | UB | LB | Gap | Focused attempts | Route-pool UB? | Incompatible pairs | Time (s) | Certified? |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---|
| V4 smoke | gcap-frontier | optimal | 0 | 0 | 0 | 1 | yes | 0 | 2.95 | yes |
| V12 M1 average | round4_improved_baseline | not closed | 0.382683045935 | 0.258804234390 | 0.323711261476 | 0 | no | 0 | 57.09 | no |
| V12 M1 average | focused_retry_only | not closed | 0.382683045935 | 0.258804234390 | 0.323711261476 | 1 | no | 0 | 71.09 | no |
| V12 M1 average | improved_full | not closed | 0.382683045935 | 0.258804234390 | 0.323711261476 | 0 | yes | 0 | 72.62 | no |
| V12 M1 average | improved_full_long | not closed | 0.382683045935 | 0.258804234390 | 0.323711261476 | 1 | yes | 0 | 124.80 | no |
| V12 M2 average | round4_improved_baseline | not closed | 0.759438494406 | 0.587614408090 | 0.226251483934 | 0 | no | 0 | 51.22 | no |
| V12 M2 average | focused_retry_only | not closed | 0.759438494406 | 0.587614408090 | 0.226251483934 | 1 | no | 0 | 60.57 | no |
| V12 M2 average | improved_full | not closed | 0.759438494406 | 0.587614408090 | 0.226251483934 | 1 | yes | 0 | 66.83 | no |
| V12 M2 average | improved_full_long | not closed | 0.759438494406 | 0.581677222300 | 0.234069346518 | 1 | yes | 0 | 111.08 | no |

The compatibility test was conservative on both V12 regenerated instances:
every pickup/drop pair remained compatible, so the new flow constraints added
auditable structure but did not improve the lower bounds. Focused retry now
executes in unresolved V12 rows, but the retry passes did not make valid
lower-bound progress before the time caps. The route-pool incumbent master found
verified restricted-pool incumbents in route-pool-enabled rows, but those
incumbents matched or trailed the existing seeds and are reported only as upper
bounds.

Best V12 incumbent audit rows in this pass:

- V12 M1 average: BPC-owned `local`, `pool`, `portfolio`, and `strong` modes all
  reached UB `0.369698924539`.
- V12 M2 average: BPC-owned `strong` and `portfolio` modes reached UB
  `0.759438494406`.

No new original-problem certificate was obtained in round five. V4 smoke remains
certified; V12 M1 and V12 M2 remain noncertified with positive gaps. Raw outputs
and summaries are in `results/optimization_update_round5/`. All round-five
commands exited with code `0`, and the captured logs did not contain
address/access-violation, segmentation, `bad_alloc`, or out-of-memory
signatures.

## Sixth Optimization Pass: Auto Incumbent Portfolio, Full Route-Pool Column Harvesting, Focused Relaxation Intensification, Transfer-Cap Flow, And Long-Run Convergence Tests

This pass adds `--bpc-incumbent auto` / `best-of-all`, exports BPC tree columns
into the global route-pool incumbent master, reserves time for focused
relaxation intensification on the current minimum-LB interval, adds
quantity-aware pickup-drop transfer caps, and writes progress-log checkpoints.
All mechanisms preserve the certificate protocol: auto incumbents and route-pool
masters are upper-bound mechanisms only, transfer caps and intensified
relaxations are lower-bound strengthenings only, and no positive-gap row is
reported as optimal.

Local runnable inputs were still limited to the V4 smoke file and regenerated
V12 average files. V8/V10 source `.txt` inputs were not present in this checkout.
Plain CPLEX benchmarks were skipped for this pass; compact/CPLEX-style seeds are
recorded only as incumbent candidates when they return verifier-accepted routes.

| Instance | Variant | Status | UB | LB | Gap | Time (s) | Best incumbent source | Route-pool raw cols | Focused intensification passes | Capacity-limited pairs | Certified? |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| V12 M1 average | round5_baseline | not closed | 0.368581603155 | 0.278083249730 | 0.245531390200 | 66.50 | BPC-owned portfolio | 1169 | 0 | 0 | no |
| V12 M1 average | improved_full | not closed | 0.368581603155 | 0.281762943209 | 0.235548001319 | 68.30 | BPC-owned portfolio | 8 | 1 | 90 | no |
| V12 M1 average | improved_full_300s | not closed | 0.367765009974 | 0.281531929781 | 0.234478750980 | 304.42 | compact tailored seed | 3345 | 2 | 135 | no |
| V12 M2 average | round5_baseline | not closed | 0.735318539854 | 0.583020101640 | 0.207118996679 | 69.03 | BPC-owned portfolio | 4024 | 0 | 0 | no |
| V12 M2 average | improved_full | not closed | 0.745474506024 | 0.583173497560 | 0.217715035394 | 60.28 | BPC-owned portfolio | 17 | 0 | 70 | no |
| V12 M2 average | improved_full_300s | not closed | 0.719065249476 | 0.585987841514 | 0.185070003118 | 292.15 | BPC-owned portfolio | 5743 | 2 | 140 | no |

Auto incumbent selection behaved as intended on the local V12 audit: V12 M1
auto selected a BPC-owned portfolio incumbent in the 45s audit row, and the
300s production run selected a verifier-accepted compact tailored seed when it
was better than the BPC-owned candidates. V12 M2 auto selected the BPC-owned
portfolio/strong incumbent rather than the weaker compact-CPLEX candidate.

Route-pool harvesting is now effective once interval trees have time to run.
The 300s V12 rows exported thousands of BPC columns into the pool
(`3345` raw for V12 M1, `5743` raw for V12 M2). Some 60s improved rows exported
few columns because the short cap was spent in incumbent generation and
relaxation before substantial tree column production.

Focused intensification executed and consumed time in the improved V12 rows.
The valid lower bounds were kept by taking the maximum of old and intensified
relaxation bounds; no intensified pass closed a frontier. Transfer-cap flow
found many capacity-limited compatible pairs on V12, but it did not close the
remaining gaps by itself.

No new original-problem certificate was obtained in round six. The V4 smoke
frontier remains certified with objective `0`; V12 M1 and V12 M2 remain
noncertified with positive gaps. Raw JSON, logs, progress traces, and summaries
are stored in `results/optimization_update_round6/`. All round-six commands
exited with code `0`, and captured logs contained no address/access-violation,
segmentation, `bad_alloc`, or out-of-memory signatures.

## Seventh Optimization Pass: Adaptive Frontier Splitting, Route-Mask Operation-Budget Cuts, And Long-Run Convergence

This pass adds three certificate-preserving mechanisms to the frontier code:
periodic progress logging, adaptive splitting of the current global-min-LB
frontier interval, and mask-specific operation-budget rows in the route-mask
relaxation. Adaptive splitting replaces a parent Gini interval by exactly
covering child intervals and keeps the global lower bound as the minimum over
active leaves. Operation-budget cuts use a non-overestimating depot-cycle lower
bound and the operation identity
`operation_time = (pickup_time + drop_time) * total_pickup` to limit pickup
quantity on each route mask. Neither feature is a standalone certificate; all
frontier closure requirements still apply.

Local runnable inputs were again limited to the V4 smoke file and regenerated
V12 average files. V8/V10 source `.txt` inputs were not present in this
checkout. Plain CPLEX benchmarks were skipped; no speedup claims are made.

| Instance | Variant | Status | UB | LB | Gap | Time (s) | Incumbent source | Adaptive children | Op-budget cuts | Focused passes | Certified? |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| V12 M1 average | round6_baseline 60s | not closed | 0.368581603155 | 0.278083249730 | 0.245531390200 | 65.12 | BPC-owned portfolio | 0 | 0 | 0 | no |
| V12 M1 average | improved_full 60s | not closed | 0.368581603155 | 0.278078671850 | 0.245543810462 | 65.22 | BPC-owned portfolio | 0 | 2 | 0 | no |
| V12 M1 average | improved_full 300s | not closed | 0.366563817616 | 0.279082208580 | 0.238653148053 | 300.99 | compact tailored seed | 2 | 4 | 0 | no |
| V12 M2 average | round6_baseline 60s | not closed | 0.719065249476 | 0.583173497560 | 0.188983895433 | 65.65 | BPC-owned portfolio | 0 | 0 | 0 | no |
| V12 M2 average | improved_full 60s | not closed | 0.719065249476 | 0.583686779230 | 0.188270077500 | 65.87 | BPC-owned portfolio | 0 | 2 | 0 | no |
| V12 M2 average | improved_full 300s | not closed | 0.719065249476 | 0.595725069580 | 0.171528494787 | 310.74 | BPC-owned portfolio | 4 | 6 | 0 | no |

The V4 smoke `gcap-frontier` row remains certified with objective `0`, gap `0`,
and `certified_original_problem=true`. The V12 rows remain noncertified because
they have positive gaps and unresolved intervals. The operation-budget cuts
improved the V12 M2 lower bound in both 60s and 300s rows. On V12 M1, the short
operation-budget rows did not improve the solved time-limited relaxation bound;
the 300s row improved mainly through a better incumbent and adaptive child
processing. The progress traces now contain initial, after-seed, interval,
adaptive-split, route-pool, and final checkpoints; see
`results/optimization_update_round7/progress_trace_v12_m1_300s.csv` and
`results/optimization_update_round7/progress_trace_v12_m2_300s.csv`.

The prepared 1200s reproduction commands are recorded in
`results/optimization_update_round7/commands.md`, but were not run locally in
this pass because the required smoke and V12 60s/300s suite consumed about 31
minutes of wall time. Raw JSON, logs, summaries, and progress traces are stored
in `results/optimization_update_round7/`. All executed commands exited with
code `0`; captured logs contained no address/access-violation, segmentation,
`bad_alloc`, out-of-memory, or STATUS_ACCESS_VIOLATION signatures.
