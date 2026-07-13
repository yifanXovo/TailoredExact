# moderate seed3301 Diagnosis

## Fresh Matched Evidence

- Fresh matched budget used for diagnosis: **300 s**. The maximum requested budget was **1800 s**; 4 paper-candidate row(s) at that maximum were engineering/finalization blocked.
- Best reported Tailored selection: `tailored_static_no_callback` with gap **0.75** versus plain CPLEX **0.442849635501**.
- Matched Tailored tie set: `tailored_cheap_cuts`, `tailored_full_static_baseline`, `tailored_route_cutset_callback`, `tailored_static_no_callback`.
- Bottleneck parent leaf: `8` over G=[0.0122881381662, 0.0153601727077], leaf gap **0.0368644144985**.
- Classification: `engineering_finalization_failure;callback_overhead;plain_solver_stronger_root_bound;low_gini_denominator_weakness;root_bound_weakness;frontier_scheduling_problem`.
- Memory/hardware: no package row was used after a memory/resource stop; all matched rows use one CPLEX thread and serial process isolation.
- UB provenance: Tailored rows use only same-run verifier-gated incumbents. Plain CPLEX uses its own benchmark incumbent, and no plain or diagnostic bound enters a Tailored ledger.

| Variant | Status | LB | UB | Gap | Runtime (s) | Blocked |
| --- | --- | --- | --- | --- | --- | --- |
| plain_cplex | not_certified | 0.037866383531 | 0.067964387971 | 0.442849635501 | 301.578 | False |
| tailored_callback_telemetry_only | gcap_frontier_not_closed | 0.0122881381662 | 0.0491525526647 | 0.75 | 301.621 | False |
| tailored_cheap_cuts | gcap_frontier_not_closed | 0.0122881381662 | 0.0491525526647 | 0.75 | 301.658 | False |
| tailored_full_static_baseline | gcap_frontier_not_closed | 0.0122881381662 | 0.0491525526647 | 0.75 | 295.635 | False |
| tailored_route_cutset_callback | gcap_frontier_not_closed | 0.0122881381662 | 0.0491525526647 | 0.75 | 301.759 | False |
| tailored_static_no_callback | gcap_frontier_not_closed | 0.0122881381662 | 0.0491525526647 | 0.75 | 295.62 | False |

## Isolated Worst Leaf (900 s)

| Variant | Status | Best bound | Cutoff | Runtime (s) | Nodes |
| --- | --- | --- | --- | --- | --- |
| plain_fixed_interval_mip | interval_closed | 0.0491525526647 | 0.0491525526647 | 2.17644 | 65 |
| tailored_cheap_leaf | interval_closed | 0.0491525526647 | 0.0491525526647 | 30.0968736 | 39 |
| tailored_route_leaf | interval_closed | 0.0491525526647 | 0.0491525526647 | 30.3535221 | 57 |
| tailored_static_leaf_no_callback | interval_closed | 0.0491525526647 | 0.0491525526647 | 2.9502143 | 51 |

## Causal Answers

1. Full-frontier scheduling/finalization is the primary demonstrated failure: all paper variants tie at gap 0.75 in the valid 300 s comparison, yet the selected leaf closes in both plain and Tailored isolated runs by 900 s.
2. The fresh bottleneck is the low-Gini leaf shown above. Historical fixed-bucket artifacts are intentionally excluded, so this round neither imports nor relies on the earlier bucket.
3. Static/no-callback, cheap, full-static, and route profiles have the same full-row gap. The route profile made 3346 callbacks and added 50 route cuts without a gap gain; cheap cuts also did not help.
4. Plain CPLEX has the stronger full-model bound at the selected budget, but this is not a universal fixed-leaf advantage because the isolated leaf closes in both solvers.
5. Four 1800 s paper-candidate rows ended through wrapper/resource finalization, so those cells are inconclusive rather than evidence of algorithmic inferiority.

## Evidence Boundary

Fresh evidence summary: 4 paper-candidate row(s) at 1800s ended through wrapper/resource finalization | route callback added cuts without a better final gap | plain gap 0.44285 beats best tailored gap 0.75 at 300s | worst open leaf 8 G=[0.0122881381662,0.0153601727077] gap=0.036864414498499996 | isolated worst leaf closes in both solvers while full-frontier tailored loses.

All statements use fresh package-local rows. Isolated leaf runs and telemetry-only rows are diagnostic and are never merged into a paper certificate.
