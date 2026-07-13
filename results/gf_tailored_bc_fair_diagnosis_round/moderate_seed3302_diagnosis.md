# moderate seed3302 Diagnosis

## Fresh Matched Evidence

- Fresh matched budget used for diagnosis: **300 s**. The maximum requested budget was **1800 s**; 4 paper-candidate row(s) at that maximum were engineering/finalization blocked.
- Best reported Tailored selection: `tailored_full_static_baseline` with gap **0.875** versus plain CPLEX **0.463439315391**.
- Matched Tailored tie set: `tailored_cheap_cuts`, `tailored_full_static_baseline`, `tailored_route_cutset_callback`, `tailored_static_no_callback`.
- Bottleneck parent leaf: `6` over G=[0.0244545258186, 0.0366817887279], leaf gap **0.17118168073**.
- Classification: `engineering_finalization_failure;callback_overhead;plain_solver_stronger_root_bound;low_gini_denominator_weakness;root_bound_weakness`.
- Memory/hardware: no package row was used after a memory/resource stop; all matched rows use one CPLEX thread and serial process isolation.
- UB provenance: Tailored rows use only same-run verifier-gated incumbents. Plain CPLEX uses its own benchmark incumbent, and no plain or diagnostic bound enters a Tailored ledger.

| Variant | Status | LB | UB | Gap | Runtime (s) | Blocked |
| --- | --- | --- | --- | --- | --- | --- |
| plain_cplex | not_certified | 0.11450097091 | 0.213397988698 | 0.463439315391 | 301.612 | False |
| tailored_callback_telemetry_only | gcap_frontier_not_closed | 0.0244545258186 | 0.195636206549 | 0.875 | 297.681 | False |
| tailored_cheap_cuts | gcap_frontier_not_closed | 0.0244545258186 | 0.195636206549 | 0.875 | 297.692 | False |
| tailored_full_static_baseline | gcap_frontier_not_closed | 0.0244545258186 | 0.195636206549 | 0.875 | 291.674 | False |
| tailored_route_cutset_callback | gcap_frontier_not_closed | 0.0244545258186 | 0.195636206549 | 0.875 | 297.687 | False |
| tailored_static_no_callback | gcap_frontier_not_closed | 0.0244545258186 | 0.195636206549 | 0.875 | 291.779 | False |

## Isolated Worst Leaf (900 s)

| Variant | Status | Best bound | Cutoff | Runtime (s) | Nodes |
| --- | --- | --- | --- | --- | --- |
| plain_fixed_interval_mip | interval_unresolved_timeout | 0.14117883864 | 0.195636206549 | 900.1292096 | 14924 |
| tailored_cheap_leaf | interval_unresolved_timeout | 0.139647699628 | 0.195636206549 | 630.3470463 | 3726 |
| tailored_route_leaf | interval_unresolved_timeout | 0.139427352533 | 0.195636206549 | 600.6433267 | 6572 |
| tailored_static_leaf_no_callback | interval_unresolved_timeout | 0.14052838974 | 0.195636206549 | 600.2398725 | 8248 |

## Causal Answers

1. Cheap cuts do not avoid the regression: cheap, static, full-static, and route profiles all finish at gap 0.875 in the valid 300 s comparison.
2. At 900 s on the selected leaf, plain reaches 0.14117883864, while the best Tailored bound is 0.14052838974. This directly implicates root/search strength on that leaf, not callback overhead alone.
3. The route profile added 50 cuts without a full-row gap gain. The data do not distinguish a useful cheap/full activation rule.
4. Four 1800 s paper-candidate rows were finalization blocked, but the valid 300 s and isolated comparisons already show a genuine Tailored bound deficit.
5. No generic policy is implemented because no cross-control early metric supports one.

## Evidence Boundary

Fresh evidence summary: 4 paper-candidate row(s) at 1800s ended through wrapper/resource finalization | route callback added cuts without a better final gap | plain gap 0.463439 beats best tailored gap 0.875 at 300s | worst open leaf 6 G=[0.0244545258186,0.0366817887279] gap=0.1711816807304 | plain fixed-interval bound beats every isolated tailored leaf variant.

All statements use fresh package-local rows. Isolated leaf runs and telemetry-only rows are diagnostic and are never merged into a paper certificate.
