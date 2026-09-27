# Unchanged DS-X, newly validated

The complete method is inherited from
[Round71 algorithm.md](../unified_exact_round71/algorithm.md), frozen with
source3867214f480d0a4fef4d77f03404f9fd89fb8b42 and the identical qualified
executable. Round72 introduces no C++ or parameter change.

|Arm|Actual preset/path|Role|
|---|---|---|
|P-GRB|plain-baseline, method gurobi|Original compact model/native defaults; no added startup/cuts/bounds|
|DS|research-round70-vds-descent|24 finite fully decoded intra-route descents before VD-S proof|
|DS-X|research-round71-vds-interroute-descent|Same method with uniform limited cross-route tail relocation|
|K1-R|research-round65-k1-h with existing reliability repairs|Necessary D7 protection reference, conditional long comparison|

DS/DS-X use seed20260626 and first strict decoded-fitness gain greater than
1e-12. Every unsuccessful pass checks its complete generated neighborhood.
The proxy orders candidates only. A separately verified route/operation witness
supplies UB, followed by the unchanged one-hot Gini-product formulation and
full-frontier AM proof. Compatible native MIP Starts are fully mapped and
checked. AM retains one initial interval, midpoint splits, threshold0.08,
depth8 and width1e-4. None of these choices uses internal seconds or Work.

The cross-route neighborhood moves only eligible first tail supply/demand
stations to service anchors. Its tail is defined by travel-plus-return T;
the full decoder checks handling and load prefixes. It omits many other
relocations/exchanges. Finite descent is not a global heuristic-optimality
or speed guarantee. All work is paid; only the whole-run deadline can end a
non-certified complete run. The diagnostic prefix is not an algorithm input.

Mathematical scope is frozen in [campaign/mathematics.md](campaign/mathematics.md).
Physical UB, valid global LB/coverage and numerical certificate checks remain
separate. No new-theory or rational-certificate claim is made. The experimental
long-run gate selects research work only; it is absent from the solver.
