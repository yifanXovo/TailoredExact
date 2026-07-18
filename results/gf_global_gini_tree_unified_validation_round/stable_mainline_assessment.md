# Round 22 stable-mainline assessment

## Decision

The single stable paper mainline remains **S0/F0 `round20-current`**. S1/F3 `normalized-start-coupled` remains an exact, optional research variant and is not promoted. No instance-dependent selector or formulation portfolio is authorized.

This is the direct outcome of the qualitative rule frozen in `evaluation_protocol.md` before production. F3 could replace F0 only with broad non-regression across the complete existing and held-out evidence plus a meaningful overall advantage. The evidence is mixed and the broad-non-regression gate fails.

## Evidence against promotion

At 900 seconds on the eight existing instances, S1 improved 3 and regressed 5 relative to S0. At 1,800 seconds it again improved 3 and regressed 5. On the preregistered existing 3,600-second case, S1 regressed: S0 reached a status-101 engineering-exact certificate in 3,285.8834974 seconds, whereas S1 ended at status 108 with a 0.005840593926718977 verified-UB gap. Across existing-suite horizon comparisons, the count is therefore 6 improvements and 11 regressions.

On the six held-out instances at 900 seconds, S1 improved 2, regressed 3, and had 1 unavailable comparison because neither side supplied the required comparable bound. On the preregistered held-out 3,600-second case, S1 improved the final native lower bound from 2.750535975594117 to 2.766628577081043, reducing the common-UB gap from 0.012058296883191072 to 0.006278131758414157. Across held-out horizon comparisons, the count is 3 improvements, 3 regressions, and 1 unavailable.

S0 and S1 had equal strict-certificate counts at each complete existing fixed matrix: 2 each at 900 seconds and 2 each at 1,800 seconds. Neither certified a held-out row at 900 seconds. The conditional 3,600-second stage added one strict certificate for S0 and none for S1. Across all 81 official rows, the strict counts are S0 5, S1 4, and plain 2.

Dense normalized bound-progress AUC is also mixed. S1 wins 3 of 8 existing comparisons at 900 seconds, 4 of 8 at 1,800 seconds, 2 of 6 held-out comparisons at 900 seconds, and the selected held-out 3,600-second comparison. S0 wins the complementary 14 of the 24 production-horizon AUC comparisons; S1 wins 10. Mean S1-minus-S0 AUC is +0.0006179 at existing 900 seconds, +0.0014260 at existing 1,800 seconds, -0.0050715 at held-out 900 seconds, -0.0047473 on the selected existing 3,600-second case, and +0.0041488 on the selected held-out case.

The common-fresh checkpoint analysis records 47 leader changes. The two 3,600-second cases summarize the mixed behavior: S1 first overtakes S0 in the existing case in `(2, 10]` seconds, but S0 retakes the lead in `(15, 20]` seconds and ultimately certifies; S1 overtakes in the held-out case in `(2, 15]` seconds and retains the better final bound. Every interval, rather than an interpolated crossing time, is retained in `flow_overtake_intervals.csv`.

No S1-specific certificate, model, lifecycle, verifier, or instrumentation validity failure occurred. The rejection is empirical stability, not correctness: existing regressions exceed improvements, held-out regressions do not fall below improvements, there are far more than one material regression, and the complete certificate count is lower for S1.

## Stable production settings

The stable algorithm is one persistent global Gini tree with F0 `round20-current` connectivity flow, parent-copy child estimates, the full inherited row pack, deferred child rows, native MIP start disabled, one environment/problem/model read/`CPXmipopt`, one thread, presolve enabled, traditional search, native best-bound node selection, default CPLEX cuts/probing/heuristics, exact-zero relative and absolute MIP-gap requests and readbacks, and dense progress enabled. These settings apply uniformly to every instance.

## Next common experiment

The strongest shared convergence signal is Gini-sibling starvation, not a need for an instance-specific flow dispatcher. Across production Tailored runs, 443 observed sibling first-process delays exceeded 300 seconds, 66 exceeded 900 seconds, and the maximum was 2,940.0933434 seconds. The next experiment should therefore introduce and preregister one formulation-independent, starvation-resistant Gini-sibling scheduling rule, apply it identically to F0 and F3, and evaluate it with the same dense trajectory and certificate gates. Basis reuse and additional formulation strengthening should remain secondary until this common scheduling mechanism is isolated.
