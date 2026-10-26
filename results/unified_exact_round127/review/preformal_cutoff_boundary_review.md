# Round127 cutoff-boundary mathematical review

This is a focused review by a separate collaborating executor. It uses the current and frozen source plus the inherited R126 mathematical specification. It ran no build, native Optimize, or performance experiment. The implementing executor is separately producing zero-Optimize V2/T60 matrix and mapped-witness evidence; this document does not claim to have executed that export.

## Finding and disposition

The frozen numerical penalty-closure row can exclude a physical solution whose objective equals the nominal non-strict own cutoff. At exact equality its analytic premise still proves that no strictly better solution exists. Thus this boundary does **not** by itself contradict the frozen method's documented numerical cutoff-complement certificate policy. It **does** contradict Round127 MD's stronger stated requirement that every physical solution with F <= U0 embeds in its root and that the own equal-U0 Start is legal in that root.

**MD qualification must be blocked under the requested unchanged row pack.** Keep any S12 MD smoke as a functional qualification observation, not as a formal D ablation. Do not remove or change the inherited closure row, alter R, replace MD with another mode, or reinterpret this boundary as evidence that D has no value. Continue unaffected E0 confirmation, the bounded cold-P training, and separately qualified E1 P/PT/MB/MR/MG/MS2 arms; mark the D comparison and integrated core ablation incomplete.

## Exact source condition

`src/IntervalRowFactory.cpp`, the `penalty_lower_bound_closure` block, retains

    P >= penalty_lower

and, when the incumbent row is active, emits the impossible row

    0 <= -1

if

    gamma_L + lambda * penalty_lower >= cutoff_value - 1e-9.

Here the active controller uses `incumbent_epsilon=0`, so `cutoff_value=U0` at the initial root. The fallback writer contains the same condition in `src/CplexBaseline.cpp` near the `penalty_lower_bound_closure` block. This closure is outside C_R and C_G and is retained in MB, MD, MR, MG, and MS2.

The actual row is deliberately called `interval_no_improver_domain_closure`. The inherited R126 `model_appendix.md` A.5.6 already states that the ideal strict test is gamma_L + lambda*penalty_lower > c, while the implementation uses >= c - 1e-9; equality is not strict infeasibility of the non-strict cutoff set. A.7 and the manuscript's numerical qualification discussion retain this limitation. This is an existing contract boundary, not a newly introduced Round127 row.

## Deterministic artificial boundary

Take two service stations and one vehicle:

| Quantity | Value |
|---|---|
| n, m | 2, 1 |
| Initial stocks b1, b2 | 0, 0 |
| Targets D1, D2 | 1, 1 |
| Station capacities C1, C2 | 1, 1 |
| Vehicle capacity Q | 1 |
| Weights w1, w2 | 1, 1 |
| lambda | 0.15 |
| Pickup and drop time | 60 seconds each |
| Physical horizon T | 60 seconds |
| Travel | Any admitted metric with each depot round trip below T; zero travel also suffices |

All vehicles depart empty and no station contains stock to pick up. Unique nonzero one-way service and inventory/prefix balance prohibit a delivery without a source. Every physical solution therefore has the empty service fleet and Y=(0,0). Its ratios are zero, S=0, and the retained zero-denominator convention gives

    G_true = 0,  P = 2,  F = U0 = 0.30.

The same conclusion holds with a strictly positive Euclidean travel metric. For example, use depot (0,0), station 1 (1,0), and station 2 (0,1), interpreted in the normal travel units. Every depot round trip is 2, so the handling reach bound is

    floor((60 - 2) / 120 + 1e-9) = 0.

The factory's budget-then-reachability domains consequently give y_lower=y_upper=0 at both stations. Hence e_lower=1 at each station and penalty_lower=2. The full related root is

    I0 = [0, min(U0, (n-1)/n)] = [0, 0.30],
    F_model <= U0.

At its lower endpoint gamma_L=0,

    gamma_L + lambda * penalty_lower = 0 + 0.15*2 = U0.

The closure condition is true and writes `0 <= -1`. The own empty fleet has F=U0 and G_true=0, so it meets the stated interval and non-strict cutoff. Its tight physical completion satisfies the physical core, exact inventory/state/Gini representation, original objective row, and the other retained strengthening. It violates the impossible closure row by exactly 1. Its W_SP completion is S*P=0; there is no missing denominator operation or arbitrary W choice in this example.

This construction is a source-level proof of failed inclusive embedding and Start legality. It needs no solver infeasibility report. With the current MD controller, an actual root LP infeasibility on this matrix is correctly classified as the promised consistency fault rather than accepted as an MD certificate.

Empty initial stock alone is not enough to trigger the closure. The rectangular reachability calculation does not propagate the absence of total pickup supply into every y_upper. With a longer handling horizon it may retain positive upper inventories and a smaller penalty_lower. T=60 makes the trigger deterministic without relying on that extra propagation or changing the frozen algorithm.

## Why the inherited certificate meaning is different

In exact arithmetic let L0=gamma_L+lambda*penalty_lower, a valid physical regional objective floor under the admitted interval/domain premises.

- If L0 > c, the non-strict set F <= c is empty.
- If L0 = c, equal-c physical points may exist, but F < c is empty. The physical incumbent of value c and the independent regional floor c close improvement without needing a native proof that the inclusive cutoff model is feasible.
- Under the actual test L0 >= c - 1e-9, the directly justified floor is L0, not an exact rational floor c. Elevating closure to c is part of the inherited numerical certification policy, with its documented tolerance and absence of a global accumulated-error theorem. It cannot be presented as exact rational infeasibility.

The zero-Optimize equality witness therefore refutes the **inclusive-root representation statement**, not the assertion that no strictly smaller F exists in this particular example. A native INFEASIBLE status of the matrix containing `0 <= -1` is insufficient by itself to prove inclusive physical infeasibility. Its numerical no-improver use must retain the analytic closure premise, source identity, interval, cutoff, and existing tolerance qualification. The normal returned bound/physical-witness/signed-gap checks remain necessary.

R126 Lemma A3 states an ideal inclusive embedding assumption. The documented numerical closure exception must remain explicit when applying that lemma to actual frozen matrices. It must not be erased by calling the impossible row a harmless valid inequality for all F <= c.

## Scope of the blocker

MD has an additional Round127 proof/Start obligation that this example fails. Preserving the original closure and asserting that additional obligation cannot both be true for all required boundaries. The authorized response is the explicit mode-level block, not an unregistered algorithm repair or a narrower leaf substitution.

The same inherited closure is present in frozen MB and its MR/MG/MS2 deletion variants. Their pairwise deletion legality is unaffected: they retain identical domain construction and the same closure, MR removes only C_R, MG only C_G and its dedicated auxiliaries, and MS2 only triple support. This finding supplies no reason to block those modes solely for retaining the previously disclosed numerical closure policy. It also supplies no independent performance result for them. Their native/Start/returned-proof qualification must still pass on their actual paid runs, and any actual unqualified or contradictory returned claim must be handled under the inherited evidence rules.

Cold P and PT use the original compact model without this strengthened interval closure, so their model/parameter comparison and bounded training are unaffected. The E0 executable remains byte frozen and its historical numerical contract is preserved.

Conclusion: **existing documented numerical closure boundary; MD inclusive-root/own-U0-Start qualification blocked; no newly established blanket invalidity of the other frozen numerical modes.**
