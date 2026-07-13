# high imbalance seed3201 Diagnosis

## Fresh Matched Evidence

- Fresh matched budget used for diagnosis: **1800 s**. The maximum requested budget was **1800 s**; 0 paper-candidate row(s) at that maximum were engineering/finalization blocked.
- Best reported Tailored selection: `tailored_static_no_callback` with gap **0.287015734552** versus plain CPLEX **0.157449413757**.
- Matched Tailored tie set: `tailored_cheap_cuts`, `tailored_full_static_baseline`, `tailored_route_cutset_callback`, `tailored_static_no_callback`.
- Bottleneck parent leaf: `15` over G=[0.48984375, 0.5046875], leaf gap **0.70129516194**.
- Classification: `callback_overhead;plain_solver_stronger_root_bound;root_bound_weakness;frontier_scheduling_problem`.
- Memory/hardware: no package row was used after a memory/resource stop; all matched rows use one CPLEX thread and serial process isolation.
- UB provenance: Tailored rows use only same-run verifier-gated incumbents. Plain CPLEX uses its own benchmark incumbent, and no plain or diagnostic bound enters a Tailored ledger.

| Variant | Status | LB | UB | Gap | Runtime (s) | Blocked |
| --- | --- | --- | --- | --- | --- | --- |
| plain_cplex | not_certified | 2.0589350659 | 2.44369311412 | 0.157449413757 | 1800.891 | False |
| tailored_callback_telemetry_only | gcap_frontier_not_closed | 1.74210803 | 2.44340319194 | 0.287015734552 | 1794.648 | False |
| tailored_cheap_cuts | gcap_frontier_not_closed | 1.74210803 | 2.44340319194 | 0.287015734552 | 1794.88 | False |
| tailored_full_static_baseline | gcap_frontier_not_closed | 1.74210803 | 2.44340319194 | 0.287015734552 | 1790.934 | False |
| tailored_route_cutset_callback | gcap_frontier_not_closed | 1.74210803 | 2.44340319194 | 0.287015734552 | 1794.775 | False |
| tailored_static_no_callback | gcap_frontier_not_closed | 1.74210803 | 2.44340319194 | 0.287015734552 | 1788.986 | False |

## Isolated Worst Leaf (900 s)

| Variant | Status | Best bound | Cutoff | Runtime (s) | Nodes |
| --- | --- | --- | --- | --- | --- |
| plain_fixed_interval_mip | interval_unresolved_timeout | 2.1975143526 | 2.44340319194 | 900.1401466 | 47128 |
| tailored_cheap_leaf | interval_unresolved_timeout | 2.37379277855 | 2.44340319194 | 600.3416898 | 8486 |
| tailored_route_leaf | interval_unresolved_timeout | 2.38861621775 | 2.44340319194 | 600.4962463 | 22948 |
| tailored_static_leaf_no_callback | interval_unresolved_timeout | 2.3787544238 | 2.44340319194 | 600.1635209 | 15127 |

## Causal Answers

1. Plain CPLEX has the stronger full-row gap at 1800 s, and every Tailored profile has the same global gap. This rules out route cuts as the sole cause.
2. The isolated 900 s leaf reverses the result: plain reaches 2.1975143526, while `tailored_route_leaf` reaches 2.38861621775. The full frontier is therefore allocating time away from a leaf where Tailored is demonstrably stronger.
3. The route profile added 50 cuts but did not move the full-row gap relative to static/no-callback. Its isolated benefit does not transfer through the current scheduler.
4. No native exit, memory stop, or finalization blocker occurred in the comparable 1800 s rows.

## Evidence Boundary

Fresh evidence summary: route callback added cuts without a better final gap | plain gap 0.157449 beats best tailored gap 0.287016 at 1800s | worst open leaf 15 G=[0.48984375,0.5046875] gap=0.7012951619399999 | isolated tailored leaf beats plain while full-frontier tailored loses.

All statements use fresh package-local rows. Isolated leaf runs and telemetry-only rows are diagnostic and are never merged into a paper certificate.
