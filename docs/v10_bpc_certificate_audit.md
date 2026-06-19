# V10 BPC Certificate Audit

Audited artifact:

- Result JSON: `results/paper_bpc_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`
- Captured stdout: `logs/paper_bpc_v10_m2_average_frontier_routemask_relax20_refine18_1200s.stdout.txt`
- Captured stderr: `logs/paper_bpc_v10_m2_average_frontier_routemask_relax20_refine18_1200s.stderr.txt`

No separate detailed `.log` file with the same stem was found. The detailed certificate ledger is embedded in the JSON `notes` array. The captured stdout contains the one-line run summary and stderr is empty.

## Scope

The artifact is a full Gini-frontier route-load BPC result:

- `method=gcap-frontier`
- `method_scope=original_bpc`
- `solves_original_objective=true`
- `is_bpc=true`
- `certificate_type=full_gini_frontier_route_load_bpc`

It is not the compact strengthened/tailored fallback, not plain CPLEX, and not a fixed-cap-only or restricted-pool diagnostic.

## Certificate Fields

The audited JSON reports:

- `status=optimal`
- `objective=0.463263009179`
- `lower_bound=0.463263009179`
- `upper_bound=0.463263009179`
- `raw_frontier_lower_bound_before_tolerance_normalization=0.463262931381`
- `certificate_tolerance=1e-7`
- `gap=0`
- `runtime_seconds=1006.3825323`
- `certified_original_problem=true`
- `verifier_passed=true`
- `unresolved_intervals=0`
- `invalid_bound_intervals=0`
- `pricing_closed_nodes=26`
- `open_nodes=0`
- `nodes=28`
- `columns=12615`
- `pricing_calls=76`
- `cuts_added=12`

The raw frontier lower bound is within the explicit `1e-7` certificate tolerance of the incumbent objective, after which the top-level lower and upper bounds are normalized to the verified objective.

## Frontier Coverage

The JSON notes include:

```text
frontier cover range=[0,0.463263], intervals=16, incumbent_objective=0.463263, incumbent_G=0.345161, full_objective_range=true
```

The final frontier summary is:

```text
frontier certification summary: closed_intervals=0, bound_certified_intervals=48, skipped_intervals=0, unresolved_intervals=0, invalid_bound_intervals=0, final_full_objective_range=true
```

This covers the required original-objective Gini range `[0, incumbent_objective]`. Every active interval is either bound-fathomed by a valid lower bound or closed by branch-price pricing closure; no unresolved or invalid-bound interval remains.

## Verifier

The independent verifier reports feasible routes, station-disjoint visits, load feasibility, station feasibility, duration feasibility, matching final inventories, and matching objective:

- `G=0.345161450961`
- `P=0.787343721456`
- `G + 0.15 P = 0.463263009179`

The reported routes are:

- vehicle 0: `0-6-9-8-7-0`
- vehicle 1: `0-5-3-1-0`

## Audit Decision

The artifact satisfies the project certificate protocol for the original problem. The V10 BPC certificate is accepted as real and complete, subject to the route-mask relaxation validity proof in `docs/route_mask_bound_proof.md`.

The CPLEX benchmark file is separate and remains non-certified when its gap is positive. The compact/tailored fallback certificate must not be reported as BPC success.
