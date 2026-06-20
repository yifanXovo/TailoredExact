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
