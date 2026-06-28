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

## Eighth Optimization Pass: Vehicle-Indexed Route-Mask Relaxation, Focus-Only Interval Diagnostics, And Benchmark Restoration

This pass adds vehicle-indexed station service and operation variables to the
inventory/route-mask/Gini relaxation, plus vehicle-indexed pickup-drop transfer
flows linked to route masks. It also adds focus-only interval diagnostics and a
deterministic generator for missing V8/V10 engineering benchmark inputs. These
features strengthen valid lower bounds or improve diagnostics only; they do not
change the certificate protocol.

The vehicle-indexed operation relaxation links `y_{k,i}`, `p_{k,i}`, and
`d_{k,i}` to each vehicle's route-mask variables, station disjointness,
vehicle pickup/drop balance, depot-return capacity, and mask-specific operation
budgets. The vehicle-indexed transfer flow decomposes pickups and drops by
vehicle and station pair, with safe duration/capacity upper bounds. Focus-only
interval runs report `diagnostic_interval_only` and are not original-problem
certificates.

| Instance | Variant | Status | UB | LB | Gap | Time (s) | Best incumbent source | Transfer cap-limited pairs | Certified? |
|---|---|---|---:|---:|---:|---:|---|---:|---|
| V12 M1 average | round7_baseline 60s | not closed | 0.368581603155 | 0.276436202366 | 0.250000000000 | 70.30 | BPC-owned portfolio | 0 | no |
| V12 M1 average | improved_full 60s | not closed | 0.368581603155 | 0.276436202366 | 0.250000000000 | 70.21 | BPC-owned portfolio | 90 | no |
| V12 M1 average | improved_full 300s | not closed | 0.368581603155 | 0.284563809518 | 0.227948961416 | 305.53 | BPC-owned portfolio | 180 | no |
| V12 M2 average | round7_baseline 60s | not closed | 0.745474506024 | 0.585987841514 | 0.213939797031 | 62.63 | BPC-owned portfolio | 0 | no |
| V12 M2 average | improved_full 60s | not closed | 0.745474506024 | 0.585074010670 | 0.215165634851 | 63.42 | BPC-owned portfolio | 70 | no |
| V12 M2 average | improved_full 300s | not closed | 0.719065249476 | 0.689651961258 | 0.040904894569 | 295.71 | BPC-owned portfolio | 490 | no |
| V12 M2 average | improved_full 1200s | not closed | 0.719065249476 | 0.689651961258 | 0.040904894569 | 1119.94 | BPC-owned portfolio | 560 | no |

The V12 M2 1200s production row was run and remained noncertified. It matched
the 300s lower bound and incumbent, indicating that the remaining gap was not
closed by additional branch-price time under this configuration. The V12 M1
1200s row was not run locally; the V12 M2 serious row was prioritized because
its 300s gap was still decreasing relative to the round-seven 60s baseline.

Focus-only diagnostics closed the selected minimum-LB interval for both V12
instances but only within diagnostic scope. V12 M1 focus-only selected interval
`0` over `[0,0.184291]` and ended with interval LB `0.368581603155`; V12 M2
focus-only selected interval `0` over `[0,0.372737]` and ended with interval LB
`0.745474506024`. These runs clarify that individual intervals can be closed
when isolated, but they do not close the complete frontier.

Historical V8/V10 `.txt` inputs were not found in this checkout, so deterministic
parser-compatible engineering benchmarks were generated under
`reference/generated/` with manifest `reference/generated/manifest.csv`.
Generated V10 M2 average and generated V10 M2 low both certified within the 60s
improved-full runs, but they are not claimed to be historical paper targets.
Generated V8 M2 average and generated V10 M1 average remained positive-gap
diagnostics. Raw JSON, logs, progress traces, summaries, and the generator
manifest are stored in `results/optimization_update_round8/`.

## Ninth Optimization Pass: Inventory Branching, Operation-Mode Branching, And Focus-Interval Closure

This pass adds final-inventory branching, operation-mode branching, focus-range
selection for active frontier leaves, and import of compatible focus-interval
lower bounds into a full frontier ledger. These changes target the unresolved
adaptive leaves observed after round eight, especially V12 M2
`[0.465922,0.512514]` and V12 M1 `[0.230364,0.276436]`. Focus-only runs remain
diagnostic interval runs; imported interval bounds improve the full frontier
ledger only when the covered range is compatible and the full ledger is still
reported honestly.

| Instance | Variant | Status | UB | LB | Gap | Time (s) | Focus range | Inventory branch nodes | Imported bounds | Certified? |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---|
| V12 M2 average | focus_auto_300s | not closed | 0.719065249476 | 0.689652394993 | 0.040904291376 | 296.50 | [0.465922,0.512514] | 8 | 0 | no |
| V12 M1 average | focus_auto_300s | not closed | 0.369698924539 | 0.330637007941 | 0.105658723910 | 295.34 | [0.230364,0.276436] | 14 | 0 | no |
| V12 M2 average | full_import_300s | not closed | 0.719065249476 | 0.712948394993 | 0.008506675142 | 315.11 | imported focus bound | 0 | 1 | no |
| V12 M1 average | full_improved_300s | not closed | 0.369698924539 | 0.282149235152 | 0.236813481393 | 315.87 | full frontier | 10 | 0 | no |

The V12 M2 focus run substantially tightened the critical interval lower bound
from `0.496993274667` to `0.689652394993`, but the interval did not close and
retained open nodes. Importing that compatible focus result into a full frontier
run split the active ledger and raised the full run lower bound to
`0.712948394993`, leaving one unresolved interval and a noncertified
`0.008506675142` gap. A corrected `--frontier-focus-from-result` diagnostic
then selected the unresolved imported-ledger leaf `[0.489218,0.512514]` and
confirmed the same interval lower bound within a short diagnostic budget. The
V12 M1 focus run also strengthened its selected
interval but did not close the full frontier; the full 300s row remained weaker
than the isolated focus diagnostic.

Branching diagnostics on the V12 M2 critical interval were run for Ryan-Foster,
inventory-only, and bounded `strong` selection modes at 60s. All returned the
same interval lower bound and remained noncertified. Inventory branching created
nodes in the longer focus runs, while operation-mode branching was available but
did not become the selected branch type in these V12 focus rows. The current
`strong` mode is a bounded scoring selector rather than full child-LP strong
branching, so it is treated as a search heuristic.

The V4 smoke `gcap-frontier` row remains certified with objective `0`. The
generated V8/V10 engineering benchmarks were rerun for 60s with the new
branching-enabled configuration; all four runs completed without process errors
but remained positive-gap diagnostics in this budget. They are not historical
paper targets.

No new original-problem certificate was obtained in this pass. The main
improvement is a safer path to target, tighten, and import difficult leaf
intervals without relabeling interval diagnostics as full BPC certificates. Raw
JSON, logs, progress traces, and CSV summaries are stored in
`results/optimization_update_round9/`. Plain CPLEX benchmarks were skipped, so
no CPLEX speedup claims are made.

## Tenth Optimization Pass: Exact CG Continuation, Pricing Closure Audit, And V12 Focus-Bound Imports

This pass fixes pricing-closure reporting and adds interval state export/resume
metadata plus an exact-CG continuation mode for unresolved focus intervals.
Pricing closure is now reported false whenever exact pricing is incomplete,
negative reduced cost remains, or duplicate-negative projection blockage is
unresolved. Focus/resume/import runs remain diagnostic unless the complete
frontier ledger closes.

| Instance | Variant | Status | UB | LB | Gap | Pricing status | Notes |
|---|---|---|---:|---:|---:|---|---|
| V4 smoke | gcap-frontier | optimal | 0 | 0 | 0 | duplicate_negative_projection | certified by zero nonnegative objective, not by pricing closure |
| V12 M2 average | exact_cg_focus_300s | not closed | 0.719065249476 | 0.712948394993 | 0.008506675142 | pricing_time_limit | focus interval `[0.489218,0.512514]`; state exported |
| V12 M2 average | resume_exact_cg_300s | not closed | 0.719065249476 | 0.712948394993 | 0.008506675142 | pricing_time_limit | compatible state loaded; open nodes rebuilt, not serialized |
| V12 M2 average | exact_cg_focus_smooth_60s | not closed | 0.719065249476 | 0.712948394993 | 0.008506675142 | pricing_time_limit | smoothing requested but true-dual pricing used for safety |
| V12 M2 average | full_import_focus_300s | not closed | 0.719065249476 | 0.657495783410 | 0.085624310327 | negative_columns_remaining | imported focus bound accepted; other active leaves still open |
| V12 M1 average | full_import_focus_300s | not closed | 0.375405784113 | 0.330637000000 | 0.119254380214 | pricing_time_limit | round-nine focus bound accepted; other intervals control closure |

The V12 M2 focus interval reproduced the previous near-closed bound but did not
achieve exact pricing closure. The final reduced cost reported by the focus run
was numerically zero, but pricing timed out before exact completion, so the run
remains noncertified. The full V12 M2 import run accepted the focus evidence but
still found remaining negative reduced cost in another interval. This validates
the new reporting rule: lower-bound progress is preserved without converting an
incomplete pricing run into a certificate.

State export currently records compatible interval metadata, incumbent scalar
data, lower bounds, and generated-column counts. It does not serialize live open
branch-price nodes, so resumed runs rebuild the exact tree. This is safe but
does not yet deliver the desired warm continuation speedup.

Raw JSON, logs, progress traces, and CSV summaries are stored in
`results/optimization_update_round10/`. Plain CPLEX benchmarks were skipped in
this pass, so no CPLEX speedup claims are made.

## Eleventh Optimization Pass: Iterative Closure, Open-Node Resume, And Final Pricing Verification

Round eleven adds explicit interval certificate-basis auditing and a full-result
certificate-basis summary. Frontier intervals now report whether they are
closed by a pricing-closed BPC tree, fathomed by a valid
inventory/route/Gini relaxation, skipped by gamma floor or incumbent cutoff,
imported from a compatible focus interval, diagnostic-only, unresolved, or
invalid. This resolves the ambiguity where V4 smoke could be certified even
though pricing closure fields were non-closed: every V4 interval is skipped by a
non-pricing gamma-floor/nonnegative objective basis, so pricing closure is not
required for that certificate.

The new iterative closure loop selects the current minimum-LB unresolved leaf,
refreshes its relaxation, runs a focused exact-CG/tree continuation pass,
checkpoints the pricing verifier, and updates the full ledger. The loop is
certificate-neutral and still reports positive-gap rows as noncertified.

| Instance | Variant | Status | UB | LB | Gap | Iterative rounds | Target intervals | Certified? |
|---|---|---|---:|---:|---:|---:|---|---|
| V4 smoke | gcap-frontier | optimal | 0 | 0 | 0 | 0 | gamma-floor skips | yes |
| V12 M2 average | iterative_reserved_300s | not closed | 0.719065249476 | 0.689651961258 | 0.040904894569 | 2 | `[0.465922,0.489218]`; `[0.489218,0.512514]` | no |
| V12 M1 average | multifocus_300s | not closed | 0.368581603155 | 0.344666733450 | 0.064883514261 | 0 | imported historical focus bound | no |
| V12 M1 average | iterative_lite_300s | not closed | 0.369698924539 | 0.330637007941 | 0.105658723910 | 2 | `[0.230364,0.276436]`; `[0.276436,0.369699]` | no |
| V12 M2 average | resume_60s | not closed | 0.719065249476 | 0.697218726816 | 0.030378174501 | n/a | loaded partial state metadata | no |

The V12 M2 iterative run executed two rounds but did not improve the controlling
interval lower bounds. The pricing verifier wrote checkpoints but did not
complete exact true-dual pricing, so pricing closure remains false. The V12 M1
multi-focus import accepted one compatible focus bound and improved the active
full lower bound, but unresolved leaves still control the certificate.

Open-node resume is currently partial. It loads compatible interval metadata,
column counts, and open-node counts, and reports
`open_node_state_resume_exact=false` because live node-local RMP queues are not
yet serialized. This is a warm restart, not exact tree continuation.

No new original-problem certificate was obtained in this pass. Raw JSON, logs,
progress traces, and CSV summaries are stored in
`results/optimization_update_round11/`. Plain CPLEX benchmarks were skipped, so
no CPLEX speedup claims are made.

## Twelfth Optimization Pass: Scalable Pricing, Large-Instance Safety, And Heuristic Incumbent Bridge

Round twelve adds the first large-instance-safe route-column data path. Route
columns and dominance keys now carry a `StationSet`, using a compact backend
for small V and a dynamic vector backend beyond 63 stations. Large-instance
mode disables all-subset route-mask enumeration when it would be unsafe or
infeasible and reports the disabled feature instead of producing a certificate.

The pricing diagnostic now supports `exact-label`, `ng-dssr`, and `hybrid`
engines. The ng-DSSR implementation is used as a scalable column-discovery
engine and inserts only verified elementary route-load columns. It is exact
only when final exact verification completes. Smooth/box dual stabilization is
used only for candidate discovery; reduced costs and closure checks remain
true-dual.

External/HGA-style incumbents can be imported from route JSON or CSV and must
pass the independent verifier before they update an upper bound. The
round-twelve smoke test verified a synthetic route JSON import and rejected a
malformed route.

| Instance | Variant | Status | UB | LB | Gap | Pricing engine | Certified? |
|---|---|---:|---:|---:|---:|---|---|
| V12 M2 average | frontier hybrid 300s | not closed | 0.719065249476 | 0.689651961258 | 0.040904894569 | hybrid flag; frontier exact-label internals | no |
| V12 M1 average | frontier hybrid 300s | not closed | 0.368581603155 | 0.330636509913 | 0.102948961415 | hybrid flag; frontier exact-label internals | no |
| V12 M2 average | pricing exact-label 60s | pricing diagnostic | n/a | n/a | n/a | exact-label | no |
| V12 M2 average | pricing ng-DSSR 60s | pricing diagnostic | n/a | n/a | n/a | ng-DSSR with exact final check | no |
| V12 M1 average | pricing hybrid smooth 60s | pricing diagnostic | n/a | n/a | n/a | hybrid/smooth | no |

| Scale | Variant | Status | Station-set backend | Disabled exact features | Certificate scope |
|---|---|---|---|---|---|
| V20 | hybrid pricing 60s | time_limit / DSSR incomplete | uint64 | none | diagnostic |
| V50 | hybrid pricing 60s | time_limit / DSSR incomplete | uint64 | all-subset route-mask relaxation | diagnostic |
| V70 | large-instance guard | diagnostic complete | dynamic | all-subset route-mask relaxation | diagnostic |
| V100 | hybrid pricing 60s | time_limit / DSSR incomplete | dynamic | all-subset route-mask relaxation | diagnostic |

No new original-problem certificate was obtained in round twelve. The useful
algorithmic change is scalability safety: V70/V100 parse, route-column set
handling, verification, and ng-DSSR pricing diagnostics run without mask
overflow or memory/address failures, while remaining clearly noncertified.
Raw JSON, logs, progress traces, and CSV summaries are stored in
`results/optimization_update_round12/`. Plain CPLEX was skipped.

## Thirteenth Optimization Pass: Production Hybrid Pricing And Scalable BPC Integration

Round thirteen wires the hybrid/ng-DSSR pricing options through the BPC
column-generation, tree, frontier, focused-closure, and iterative-closure
entry points. Explicit `--pricing-engine hybrid` requests now use the hybrid
engine even on V12; small-instance rows still require exact final verification
before node closure. Returned hybrid columns are evaluated under true duals
before insertion, and incomplete DSSR rows remain noncertified.

| Instance | Variant | Status | UB | LB | Gap | Engine used | DSSR exact? | Certified? |
|---|---|---:|---:|---:|---:|---|---|---|
| V4 smoke | frontier exact-label | optimal | 0 | 0 | 0 | exact-label | n/a | yes |
| V4 smoke | frontier hybrid | optimal | 0 | 0 | 0 | hybrid | yes | yes |
| V12 M2 average | focus exact-label 300s | not closed | 0.780792889928 | 0.712948394993 | 0.086891793983 | exact-label | n/a | no |
| V12 M2 average | focus hybrid 300s | not closed | 0.780792889928 | 0.712948394993 | 0.086891793983 | hybrid | no | no |
| V12 M2 average | focus hybrid smooth 300s | not closed | 0.780792889928 | 0.712948394993 | 0.086891793983 | hybrid/smooth | no | no |
| V12 M2 average | full exact-label 300s | not closed | 0.780792889928 | 0.684222130220 | 0.123682939425 | exact-label | n/a | no |
| V12 M2 average | full hybrid 300s | not closed | 0.780792889928 | 0.684222130220 | 0.123682939425 | hybrid/smooth | no | no |
| V12 M1 average | full exact-label 300s | not closed | 0.386764365884 | 0.338980588720 | 0.123547517245 | exact-label | n/a | no |
| V12 M1 average | full hybrid 300s | not closed | 0.386764365884 | 0.334782317080 | 0.134402373613 | hybrid/smooth | no | no |

Hybrid pricing now reaches the BPC path: the V12 M2 focus rows used hybrid
pricing with no fallback and returned elementary negative columns quickly, but
DSSR did not prove closure, so the exact certificate remains open. Smooth
stabilization affected column discovery counters but did not change the final
lower bound in the 300s focus test.

| Scale | Variant | Status | UB | LB | Gap | Pricing engine | Scope |
|---|---|---:|---:|---:|---:|---|---|
| V20 | gcap-frontier hybrid 300s | not closed | 1.13623075045 | 0.368133269885 | 0.676004834634 | hybrid/smooth | original BPC incomplete |
| V50 | pricing hybrid 300s | time_limit | diagnostic | diagnostic | n/a | hybrid/smooth | pricing diagnostic |
| V100 | pricing hybrid 300s | time_limit | diagnostic | diagnostic | n/a | hybrid/smooth | pricing diagnostic |
| V100 | large-lb movement projection | diagnostic complete | 6.62899864046 | 0 | 1 | n/a | global lower-bound diagnostic |

The V50/V100 generated rows use dynamic/guarded large-instance mode where
needed and avoid all-subset route-mask certification. They parse and run
without mask overflow, `bad_alloc`, access violation, or segmentation-fault
signatures in the captured logs, but remain scalability diagnostics because
DSSR is incomplete.

External incumbent workflow was exercised by exporting a verified V4 route
plan and re-importing it through the independent verifier. A malformed V50
route JSON was rejected with no incumbent update.

No new original-problem certificate was obtained beyond the existing V4 smoke
certificate in this pass. Raw JSON, logs, progress traces, and CSV summaries
are stored in `results/optimization_update_round13/`. Plain CPLEX was skipped.

## Fourteenth Optimization Pass: Two-Track Relaxed Route-Load BPC

Round fourteen introduces a two-track route-load column architecture. The
elementary track remains the only source for feasible incumbents, route-pool
masters, and exported route plans. The relaxed-ng track is lower-bound-only
and may enter relaxed RMP diagnostics. Dominance keys separate the two tracks,
and the route-pool incumbent master rejects relaxed columns at insertion and
selection.

The current implementation is intentionally conservative: relaxed lower-bound
columns are created only from verified elementary projections. Non-elementary
relaxed routes are still rejected until projection feasibility and station
capacity semantics are fully certified. Therefore the new path is certificate
safe, but the relaxed-RMP bound is mostly diagnostic unless ng-relaxed pricing
closure is proven.

| Instance | Variant | Status | UB | LB | Gap | Relaxed columns in LB RMP | Relaxed certificate? | Certified? |
|---|---|---:|---:|---:|---:|---:|---|---|
| V4 smoke | exact-label frontier | optimal | 0 | 0 | 0 | 0 | n/a | yes |
| V4 smoke | two-track hybrid frontier | optimal | 0 | 0 | 0 | 0 | false | yes |
| V12 M2 average | focus exact-label 300s | not closed | 0.780792889928 | 0.712948394993 | 0.086891793983 | 0 | false | no |
| V12 M2 average | focus two-track 300s | not closed | 0.780792889928 | 0.712948394993 | 0.086891793983 | 0 | false | no |
| V12 M2 average | full exact-label 300s | not closed | 0.780792889928 | 0.684003547210 | 0.123963889477 | 0 | false | no |
| V12 M2 average | full two-track 300s | not closed | 0.780792889928 | 0.710571053706 | 0.089939723334 | 0 | false | no |
| V12 M1 average | full exact-label 300s | not closed | 0.386764365884 | 0.337454471060 | 0.127492337626 | 0 | false | no |
| V12 M1 average | full two-track 300s | not closed | 0.386764365884 | 0.337666891430 | 0.126943152007 | 0 | false | no |

| Scale | Variant | Status | UB | LB | Scope | Notes |
|---|---|---:|---:|---:|---|---|
| V20 generated | two-track frontier 300s | not closed | 1.13623075045 | 0.372692167178 | incomplete BPC | no certificate |
| V50 generated | relaxed-RMP diagnostic 300s | diagnostic complete | 3.25947584043 | 0 | diagnostic | movement-projection LB rejected when it exceeded verified UB |
| V100 generated | relaxed-RMP diagnostic 300s | diagnostic complete | 6.62899864046 | 0 | diagnostic | movement-projection LB rejected when it exceeded verified UB |

The smoke diagnostics confirmed that a synthetic relaxed column is excluded
from route-pool incumbent construction and from route export. No access
violation, segmentation fault, `bad_alloc`, out-of-memory, ASan, or fatal
exception signature was found in the round-fourteen logs. No new
original-problem certificate was obtained beyond V4 smoke. Plain CPLEX was
skipped. Raw artifacts are stored in `results/optimization_update_round14/`.
## Fifteenth Optimization Pass: Projection-Safe Non-Elementary Relaxed Columns and Relaxed-RMP CG

This pass moves the two-track implementation beyond metadata by validating
non-elementary ng-relaxed route-load projections and allowing safe relaxed
columns into the lower-bound RMP.  The elementary incumbent path remains
separate: relaxed columns are lower-bound-only and are blocked from route
exports, route-pool incumbents, and candidate reconstruction.

| instance/run | method | status | LB | UB | gap | non-elementary relaxed inserted | certificate note |
|---|---|---|---:|---:|---:|---:|---|
| V4 smoke | exact frontier | optimal | 0 | 0 | 0 | 38 | certified |
| V4 smoke | two-track relaxed-RMP CG | optimal | 0 | 0 | 0 | 38 | certified |
| V12 M2 focus | exact-label | not closed | 0.712948 | 0.780793 | 0.086892 | 0 | noncertified |
| V12 M2 focus | two-track relaxed-RMP CG | not closed | 0.712948 | 0.780793 | 0.086892 | 2 | noncertified |
| V12 M2 full | exact-label | not closed | 0.702420 | 0.780793 | 0.100377 | 0 | noncertified |
| V12 M2 full | two-track relaxed-RMP CG | not closed | 0.681925 | 0.780793 | 0.126625 | 2 | noncertified |
| V12 M1 full | exact-label | not closed | 0.325981 | 0.386764 | 0.157159 | 0 | noncertified |
| V12 M1 full | two-track relaxed-RMP CG | not closed | 0.325981 | 0.386764 | 0.157159 | 8 | noncertified |
| V20 generated | two-track relaxed-RMP CG | not closed | 0.359196 | 1.136231 | 0.683871 | 16 | noncertified |
| V50 generated | large relaxed-RMP CG | diagnostic | 0 | 3.259476 | 1.0 | 0 | diagnostic |
| V100 generated | large relaxed-RMP CG | diagnostic | 0 | 6.628999 | 1.0 | 0 | diagnostic |

The new relaxed path is active on V4, V12, and V20, but ng-relaxed pricing does
not close on the larger rows within the tested limits.  Those relaxed-RMP values
are therefore reported as diagnostics unless another valid bound supports the
ledger.  No CPLEX comparison was run in this pass.

## Round 16: Paper Algorithm Consolidation and Verified Ablation

Round sixteen consolidates the algorithm into named presets and makes active
configuration reporting a single-source artifact. The paper-facing presets are:
`paper-bpc-core`, `paper-exact-portfolio`, `paper-bpc-experimental`, and
`diagnostic-large`. Production results now include instance scope/hash,
incumbent archive accounting, BPC/compact/portfolio module fields, option audit
status, and result-integrity audit status.

| Instance | Preset | Status | UB | LB | Gap | Certified |
|---|---|---|---:|---:|---:|---|
| V12 M1 average | paper-bpc-core | not closed | 0.368581603155 | 0.336357248340 | 0.087428006550 | no |
| V12 M2 average | paper-bpc-core | not closed | 0.719065249476 | 0.698710208326 | 0.028307641296 | no |
| V12 M1 average | paper-bpc-experimental | not closed | 0.368581603155 | 0.344296397770 | 0.065888273252 | no |
| V12 M2 average | paper-bpc-experimental | not closed | 0.719065249476 | 0.698710208326 | 0.028307641296 | no |
| V8 M2 generated | paper-bpc-core | not closed | 0.160763515679 | 0.160089160387 | 0.004194703562 | no |
| V10 M2 generated | paper-bpc-core | not closed | 0.253798619218 | 0.199276278129 | 0.214825207705 | no |
| V20 M2 generated | paper-bpc-core | not closed | 0.693289533282 | 0.376378229256 | 0.457112488813 | no |
| V50 generated | diagnostic-large | diagnostic | 3.259475840430 | 0 | 1.0 | no |
| V100 generated | diagnostic-large | diagnostic | 6.628998640460 | 0 | 1.0 | no |

The controlled V12 M2 ablation used a shorter 60 second companion suite because
the complete requested 300 second by six-instance matrix was not affordable in
this local run. The archive/auto incumbent and vehicle-indexed relaxation stage
were the clearest practical improvements in that companion suite. Two-track
experimental rows did not produce a certificate-valid relaxed-RMP lower-bound
improvement, so two-track remains an appendix/experimental module by default.

The result-integrity audit over the new raw JSON files reported no failures.
No new original-problem certificate was obtained beyond the existing V4 smoke
certificate. Compact fallback companion rows were run for V12 M1/M2 but remained
time-limited and noncertified; plain CPLEX benchmark comparisons were skipped.

## Paper-Core Follow-Up: Deeper Certificate-Neutral Frontier Splitting

After narrowing the paper-facing algorithm to GF-RL-BPC
(`gcap-frontier`/`paper-bpc-core`), the main plateau was traced to broad
frontier intervals reaching branch-price trees before child relaxation bounds
were fully exploited. The paper presets now default adaptive split depth to 8
unless the command line overrides it. This is a
scheduling/ledger granularity change only: replaced parent intervals are
ignored, child intervals exactly cover the same Gini range, and original-problem
certification still requires all active children to be empty, validly
bound-fathomed, or closed by exact BPC pricing.

| Instance | Row | Status | UB | LB | Gap | Certified |
|---|---|---|---:|---:|---:|---|
| V4 smoke | paper-core depth 5 | optimal | 0 | 0 | 0 | yes |
| V12 M1 average | depth 3 300s | not closed | 0.357200583208 | 0.331296710948 | 0.072519120847 | no |
| V12 M1 average | depth 5 300s | not closed | 0.357200583208 | 0.340282088370 | 0.047364129942 | no |
| V12 M1 average | depth 5 1200s | not closed | 0.357200583208 | 0.340282088370 | 0.047364129942 | no |
| V12 M1 average | depth 6 300s | not closed | 0.357200583208 | 0.341121462223 | 0.045014262969 | no |
| V12 M1 average | depth 6 1200s | not closed | 0.357200583208 | 0.344881668930 | 0.034487385681 | no |
| V12 M1 average | depth 7 300s | not closed | 0.357200583208 | 0.344613240900 | 0.035238862701 | no |
| V12 M1 average | depth 8 300s | not closed | 0.357200583208 | 0.344613240900 | 0.035238862701 | no |
| V12 M1 average | depth 9 300s | not closed | 0.357200583208 | 0.344613240900 | 0.035238862701 | no |
| V12 M2 average | depth 3 300s | not closed | 0.719065249476 | 0.696966843140 | 0.030732129459 | no |
| V12 M2 average | depth 5 300s | not closed | 0.719065249476 | 0.706200471341 | 0.017890974630 | no |
| V12 M2 average | depth 5 1200s | not closed | 0.719065249476 | 0.710439004053 | 0.011996471 | no |
| V12 M2 average | depth 6 300s | not closed | 0.719065249476 | 0.713690734357 | 0.007474307962 | no |
| V12 M2 average | depth 7 300s | not closed | 0.719065249476 | 0.715075764785 | 0.005548153933 | no |
| V12 M2 average | depth 8 300s | not closed | 0.719065249476 | 0.716948330538 | 0.002943987267 | no |
| V12 M2 average | depth 9 300s | not closed | 0.719065249476 | 0.715075764785 | 0.005548153933 | no |

The V12 rows remain noncertified, but the lower-bound improvements are valid
inventory/route/Gini relaxation evidence in the full frontier ledger. The
certificate audit over `results/paper_bpc_core/raw` reported zero failures.
The V12 M1 1200s depth-6 row improves the valid lower bound beyond the 300s
depth-6 row, but it still does not certify the original problem. The first 300s
are dominated by child relaxation and focused splitting; the remaining budget is
dominated by exact-label pricing/tree closure on
`[0.223250364505,0.230692043322]`, which leaves one BPC node open at timeout.
Depth 7 recovers nearly the same V12 M1 lower bound in 300s without entering
expensive pricing, and it further improves V12 M2 to a 0.55% valid gap in 300s.
Depth 8 is neutral on V12 M1 but improves V12 M2 again to a 0.29% valid gap in
300s, still with three unresolved active intervals and no original-problem
certificate.
Depth 9 was tested explicitly but rejected as a default: it does not improve
V12 M1 and is worse than depth 8 on V12 M2 within 300s.

The follow-up V12 M1 scheduling diagnostic tested whether the default should
start tree work earlier. Disabling focused intensification at depth 8 leaves
the 300s bound unchanged, and forcing a shallower depth-6 ledger with no
focused intensification starts tree pricing but lowers the 300s LB to
`0.341121462223`. The latter row now records per-pricing-call trace objects
before time-limit returns. A pricing timer bug was fixed in this path so the
pricer receives the actual pricing-call start timestamp when its budget is a
remaining per-call budget. After the fix, the controlling time-limited pricing
call enumerates real states instead of immediately timing out. A subsequent
exact label-dominance bucket compaction removes stale inactive label indices
without changing the dominance rule. The refreshed depth-6 diagnostic enumerates
about `3.51M` route states and `171.5M` operation states, records `1,239,056`
bucket compactions and `17,581,023` compacted entries, and still returns with
negative reduced cost remaining. This supports keeping depth 8 as the default
and moving the next optimization effort to pricing-state reduction or stronger
valid relaxation on the depth-8 active children.

The follow-up label-dominance trace audit did not change the algorithmic
certificate path, but it makes the pricing plateau easier to explain. V12 M1
300s records `330135991` label-dominance comparisons and `186012791` exact
label prunes while preserving the same noncertified LB/gap. A naive
cross-pickup dominance experiment was rejected because the extra comparisons
made pricing slower; it is not part of the paper-core preset.

The next bound-time cleanup added a continuous LP cutoff precheck before the
integer V<=12 route-mask MIP used in the inventory/route/Gini relaxation. The
precheck is certificate-safe because it only exits early when the continuous
relaxation of the same cutoff model proves infeasibility or reaches the
incumbent cutoff; otherwise the existing integer MIP still runs. V4 remains
certified at objective 0. In 60s V12 diagnostics, the precheck fathoms the
first low-Gini interval for both M1 (`[0,0.119067]`) and M2
(`[0,0.239688]`) before the integer route-mask MIP. These rows are still
noncertified (`M1 LB=0.242572114996`, `M2 LB=0.461969904320`) and are recorded
only as evidence that easy cutoff-fathomed intervals can be skipped more
cheaply. The depth-8 300s V12 plateau remains controlled by later active
children and still needs stronger valid relaxation or exact pricing closure.

The precheck is now gated to low/high Gini ranges. An ungated V12 M2 300s
diagnostic was rejected because it only reached `LB=0.715075764785`, below the
current depth-8 best. The gated row restores the best V12 M2 300s valid lower
bound `0.716948330538`, while V12 M1 300s remains at
`0.344613240900`. A required-closure pickup lower bound was also added to the
exact-label pricer for Ryan-Foster require-together branches. It is a safe
partial-label feasibility bound, but current V12 diagnostics still show
time-limited pricing with negative reduced cost remaining; it is not sufficient
by itself to close the plateau.
## Round Next: Vehicle-Indexed Relaxation Certificate Path

The custom `v12_m2_ablation_plus_vehicle_relaxation_1200s` certificate was
reproduced under `results/paper_core_round_next/` and audited as a valid
relaxation-only frontier certificate. The key finding is that route-mask
operation-budget cuts are valid but can make the interval relaxation MIP harder
within the time budget. The paper-core solver now keeps those rows enabled but
adds a certificate-safe no-operation-budget fallback relaxation on the same
interval when the configured operation-budget relaxation does not fathom it.

Round-next regenerated engineering results:

| instance | preset | time limit | status | objective | LB | UB | runtime | certified |
|---|---|---:|---|---:|---:|---:|---:|---|
| V4 smoke | paper-bpc-core | 30s | optimal | 0 | 0 | 0 | 11.3841401 | yes |
| V12 M1 average | paper-bpc-core | 300s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 265.220702 | yes |
| V12 M1 average | paper-bpc-core | 1200s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 257.5489498 | yes |
| V12 M2 average | paper-bpc-core | 300s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 217.7839095 | yes |
| V12 M2 average | paper-bpc-core | 1200s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 215.7528562 | yes |

The V12 certificates are full improving-Gini-range frontier certificates where
all final intervals are bound-fathomed by valid inventory/route/Gini relaxation
lower bounds. Compact CPLEX rows in the same result directory are benchmark
only.

## Heuristic UB And Generated Variant Round

The paper-core default UB source was changed from arbitrary archive scanning to
a reproducible verifier-gated primal heuristic. Archive scanning remains
available only as an explicit diagnostic UB source.

Key current regenerated V12 rows with the new paper heuristic default:

| instance | row | status | UB | LB | gap | certified |
|---|---|---|---:|---:|---:|---|
| V12 M1 average | paper-core heuristic 300s | not closed | 0.364375057616 | 0.354350322125 | 0.027512134218 | no |
| V12 M2 average | paper-core heuristic 300s | not closed | 0.756165366387 | 0.688739371450 | 0.089168319437 | no |

This is the expected consequence of removing the stronger archive incumbent
from the paper-core default. The exact lower-bound certificate mechanism is
unchanged; the frontier simply has a weaker incumbent cutoff.

The generated variant round created twelve deterministic capacity/inventory
variants under `reference/generated_variants/` and ran ten 60s paper-core rows.
Five of the ten tested variants certified within 60s, including all three V10
M2 variants, one V8 M2 variant, and one V12 M2 variant. All optimal claims in
`results/heuristic_relaxation_dataset_round/` and
`results/generated_variant_round/` pass `audit_bpc_certificate.py
--fail-on-error`.
## Round 18: Primal UB Improvement And Focused Certificate Check

This round strengthened the paper-reproducible primal heuristic with
candidate-level auditing, HGA-style route sequence operators, and a
verifier-gated operation-portfolio bridge. The improved heuristic is stronger
on regenerated V12 M2 than the previous paper heuristic but remains weaker than
diagnostic archive incumbents. Focused paper-core 300s rows for regenerated
V12 M1/M2 remain noncertified under the reproducible heuristic UB; V12 M2 still
certifies under a diagnostic archive UB, confirming that archive evidence is
not part of paper-core but remains a useful UB-quality threshold diagnostic.

Raw results and audit output are in `results/primal_ub_improvement_round/`.

## Exact Primal Stress Round

This round tested whether paper-core can make progress when the initial native
HGA-TGBC UB is not already enough to make relaxation-fathoming easy.

Key findings:

- Regenerated V12 M2 certifies with native HGA-TGBC UB `0.718504070755`; raw
  result: `results/exact_primal_stress_round/raw/v12_m2_core_300s.json`.
- A weak greedy-start V12 M2 row begins at UB `0.789342396801`; local re-decode
  repair improves UB to `0.718504070755`, after which the full frontier closes.
- Regenerated V12 M1 remains noncertified at 300s with UB `0.357200583208`,
  LB `0.332675660948`, gap `0.0686586848205`.
- Six hard V20/M3 stress rows remain noncertified at 300s. UB did not improve
  after the native HGA-TGBC incumbent; relaxation lower-bound time dominates.

The next targeted work should strengthen certificate-safe interval relaxations
for V12 M1 and V20/M3 rather than broaden primal search.

## Relaxation-Bound Targeted Round

This round strengthened lower-bound relaxations and added controlled BPC
fallback scheduling while keeping native HGA-TGBC incumbents as UB-only
evidence.

| instance | row | status | LB | UB | gap |
|---|---|---:|---:|---:|---:|
| V12 M2 regenerated | original paper-core 300s command | optimal | 0.718504070755 | 0.718504070755 | 0 |
| V12 M1 regenerated | paper-core 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 |
| V12 M1 regenerated | paper-core 1200s | optimal | 0.357200583208 | 0.357200583208 | 0 |
| V20/M3 high_imbalance_seed3202 | 300s | not closed | 1.57423364041 | 1.74931345205 | 0.100084871258 |
| V20/M3 high_imbalance_seed3202 | 1200s | not closed | 1.60644024991 | 1.74931345205 | 0.081673871528 |

All optimal rows in `results/relaxation_bound_round/raw` pass
`scripts/audit_bpc_certificate.py --fail-on-error`. V20/M3 rows are labelled
`hard_generated_v20_m3` and remain noncertified.

## Relaxation Closure Round

This round targeted lower-bound closure after native HGA-TGBC made primal UB
quality nonbinding on regenerated V12 M1/M2. New paper-core options add
multi-station V20 cover-cut separation, station residual objective-cutoff domain
cuts, optional compact-flow relaxation (`off|lp|mip-light`), frontier
pre-split controls, and explicit relaxation worker aliases.

| instance | row | status | LB | UB | gap |
|---|---|---:|---:|---:|---:|
| V4 smoke | 30s | optimal | 0 | 0 | 0 |
| V12 M2 regenerated | paper-core 300s | optimal | 0.718504070755 | 0.718504070755 | 0 |
| V12 M1 regenerated | paper-core 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 |
| V12 M1 regenerated | paper-core 600s | optimal | 0.357200583208 | 0.357200583208 | 0 |
| V20/M3 high_imbalance_seed3202 | `mip-light` 300s | not closed | 1.65415045452 | 1.74931345205 | 0.0544001976401 |
| V20/M3 high_imbalance_seed3202 | `mip-light` 1200s | not closed | 1.69375051373 | 1.74931345205 | 0.0317627113992 |

The `mip-light` compact-flow relaxation reduces three of six V20/M3 300s gaps
materially. Multi-station cover cuts are valid but inactive on the current
stress suite. BPC fallback remains diagnostic because it does not improve bounds
after the relaxation changes and can hurt V12 M1 by displacing relaxation time.

Raw results and audit output are in `results/relaxation_closure_round/`.

## Paper-Candidate Relaxation Portfolio Round

This round added an auditable adaptive relaxation portfolio candidate:

```text
--algorithm-preset paper-bpc-core-adaptive
--relaxation-portfolio-mode fixed|adaptive|race
```

It also added proof-safe optional strengthening flags for compact-flow
connectivity, service-operation minimum handling, and penalty movement lower
bounds.  Transfer-subset capacity cuts are wired as a disabled future option;
no such cuts are active in the current results.

The V12 regression results are safe:

| instance | row | status | LB | UB | gap | runtime |
|---|---|---:|---:|---:|---:|---:|
| V4 smoke | adaptive 30s | optimal | 0 | 0 | 0 | 0.751s |
| V12 M2 regenerated | adaptive 300s | optimal | 0.718504070755 | 0.718504070755 | 0 | 204.997s |
| V12 M1 regenerated | current 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 301.673s |
| V12 M1 regenerated | adaptive 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 310.083s |
| V12 M1 regenerated | adaptive 600s | optimal | 0.357200583208 | 0.357200583208 | 0 | 473.765s |

The V20/M3 selector evidence is mixed and does not justify changing the
paper-core default.  The adaptive rows preserve metadata
`instance_scope=hard_generated_v20_m3`, but most 300s gaps are worse than the
best previous fixed LP/mip-light rows.  Only `moderate_seed3302` shows a very
small improvement over the previous best gap (`0.33021736845` to
`0.329231102492`).  Therefore the round conclusion is conservative:

- `paper-bpc-core` remains the canonical paper-facing command;
- `paper-bpc-core-adaptive` is an experimental paper-candidate preset;
- BPC fallback remains diagnostic/off by default;
- the next useful target is a better per-interval budget/variant selector, not
  broad benchmark testing.

Raw results, certificate audit, and summaries are in
`results/paper_candidate_relaxation_round/`.

## V20 Certificate Round

This round targeted a true V20/M3 certificate, prioritizing
`high_imbalance_seed3202`.  It added:

- `--relaxation-portfolio-mode exhaustive`;
- cutoff-feasibility certificate metadata;
- a conservative focused interval-closure harness;
- result fields that prevent focus-only rows from being merged into the full
  frontier ledger without an explicit coverage audit.

The priority row did not certify.  The full 300s exhaustive attempt ended with
LB `1.61719766358`, UB `1.74931345205`, gap `0.0755243654678`, worse than the
previous mip-light 1200s gap `0.0317627113992`.  Focused attempts on intervals
13 and 18 were also weaker than the inherited full-ledger bounds and are marked
diagnostic-only.

V12 stability remained intact:

- V4 smoke certified with objective `0`;
- regenerated V12 M2 certified with objective `0.718504070755`;
- regenerated V12 M1 certified in the 600s adaptive row with objective
  `0.357200583208`.

Conclusion: a paper-candidate V20 preset is not justified yet.  The next target
is either a true standalone cutoff-feasibility MIP for the controlling interval
or a focused harness that safely carries parent ledger bounds into exact
coverage merges.

Raw results and audit output are in `results/v20_certificate_round/`.

## V20 Exact Certificate Round

The next round added a standalone compact fixed-interval cutoff oracle and a
safe ledger-merge script, then reran the priority V20/M3 instance
`high_imbalance_seed3202`.

The reproduced full-frontier mip-light run certified the instance without
needing focused interval merge:

| instance | row | status | LB | UB | gap | runtime |
|---|---|---:|---:|---:|---:|---:|
| high_imbalance_seed3202 | full-frontier mip-light | optimal | 1.74931345205 | 1.74931345205 | 0 | 409.831s |

The certificate is relaxation-only full frontier: all final leaves are
bound-fathomed by valid inventory/route/Gini lower bounds reaching the verified
native HGA-TGBC incumbent.  No route-mask all-subset enumeration is used as
certifying evidence and no BPC tree pricing closure is required because no BPC
tree interval contributes the certificate.

Diagnostic interval-cutoff oracle rows were run against older unresolved leaves
and timed out; the merge audit correctly leaves that older ledger incomplete.
This confirms that focused timeout evidence is not promoted to a full
certificate.  Raw results are in `results/v20_exact_certificate_round/`.
