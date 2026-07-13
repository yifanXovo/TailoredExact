# tight T seed3102 Diagnosis

## Fresh Matched Evidence

- Fresh matched budget used for diagnosis: **900 s**. The maximum requested budget was **1800 s**; 4 paper-candidate row(s) at that maximum were engineering/finalization blocked.
- Best reported Tailored selection: `tailored_full_static_baseline` with gap **0.474370843117** versus plain CPLEX **0.213178413509**.
- Matched Tailored tie set: `tailored_cheap_cuts`, `tailored_full_static_baseline`, `tailored_route_cutset_callback`, `tailored_static_no_callback`.
- Bottleneck parent leaf: `14` over G=[0.140790102348, 0.14548310576], leaf gap **0.284956670095**.
- Classification: `engineering_finalization_failure;callback_overhead;plain_solver_stronger_root_bound;root_bound_weakness;frontier_scheduling_problem`.
- Memory/hardware: no package row was used after a memory/resource stop; all matched rows use one CPLEX thread and serial process isolation.
- UB provenance: Tailored rows use only same-run verifier-gated incumbents. Plain CPLEX uses its own benchmark incumbent, and no plain or diagnostic bound enters a Tailored ledger.

| Variant | Status | LB | UB | Gap | Runtime (s) | Blocked |
| --- | --- | --- | --- | --- | --- | --- |
| plain_cplex | not_certified | 0.47816961683 | 0.607723053154 | 0.213178413509 | 901.371 | False |
| tailored_callback_telemetry_only | gcap_frontier_not_closed | 0.31574776659 | 0.600704436685 | 0.474370843117 | 898.339 | False |
| tailored_cheap_cuts | gcap_frontier_not_closed | 0.31574776659 | 0.600704436685 | 0.474370843117 | 898.292 | False |
| tailored_full_static_baseline | gcap_frontier_not_closed | 0.31574776659 | 0.600704436685 | 0.474370843117 | 879.271 | False |
| tailored_route_cutset_callback | gcap_frontier_not_closed | 0.31574776659 | 0.600704436685 | 0.474370843117 | 897.837 | False |
| tailored_static_no_callback | gcap_frontier_not_closed | 0.31574776659 | 0.600704436685 | 0.474370843117 | 879.307 | False |

## Isolated Worst Leaf (900 s)

| Variant | Status | Best bound | Cutoff | Runtime (s) | Nodes |
| --- | --- | --- | --- | --- | --- |
| plain_fixed_interval_mip | interval_unresolved_timeout | 0.38558986743 | 0.600704436685 | 900.1202424 | 25644 |
| tailored_cheap_leaf | interval_closed | 0.600704436685 | 0.600704436685 | 150.1457064 | 2194 |
| tailored_route_leaf | interval_closed | 0.600704436685 | 0.600704436685 | 180.5183879 | 3342 |
| tailored_static_leaf_no_callback | interval_closed | 0.600704436685 | 0.600704436685 | 269.9541566 | 4963 |

## Causal Answers

1. The earlier native-exit symptom does not reproduce in the post-fix 300/900 s engineering checks; all fixed-interval variants finalized with valid artifacts.
2. A separate pre-matrix V12 M2 access violation exposed an adaptive-frontier vector-reference lifetime bug. Copying the parent bound source before child insertion fixed it, and all post-fix engineering checks pass.
3. At 900 s, the selected Tailored leaf closes at cutoff 0.600704436685, while plain remains open at 0.38558986743. The leaf subsolver is not the cause of the full-row loss.
4. The valid 900 s parent comparison favors plain because the frontier does not exploit that leaf-level Tailored advantage. Four 1800 s paper-candidate rows are finalization blocked and are explicitly inconclusive.
5. The route profile added 50 cuts without improving the matched full-row gap over static/no-callback.

## Evidence Boundary

Fresh evidence summary: 4 paper-candidate row(s) at 1800s ended through wrapper/resource finalization | route callback added cuts without a better final gap | plain gap 0.213178 beats best tailored gap 0.474371 at 900s | worst open leaf 14 G=[0.140790102348,0.14548310576] gap=0.284956670095 | isolated tailored leaf beats plain while full-frontier tailored loses.

All statements use fresh package-local rows. Isolated leaf runs and telemetry-only rows are diagnostic and are never merged into a paper certificate.
