# Current mainline

As of Round 54, the stable research and paper-facing algorithm is **K1-AM-SF**
(K1 Adaptive-Mass with Sparse Fixed-Interval Formulation), selected with
`--algorithm-preset paper-k1-am-sf`.

The outer tailored Gini-interval branch-and-cut framework begins with one
complete interval covering every potentially improving Gini value. It refines
at midpoints, uses the adaptive-mass score with threshold `tau=0.08`, preserves
the existing native-target lifecycle and exact-parent/child closure rules, and
certifies only after exact interval coverage and original-solution verification
pass.

The inner backend is F0-CLEAN: the historical Round 50 fixed-interval v0 model
with only the exhaustive V<=12 subset-duration block removed. It is a sparse
tailored fixed-interval MILP solved by Gurobi's native branch-and-cut with one
thread, seed zero, automatic presolve, zero relative and absolute MIP gaps,
native branching, default PreCrush, and no MIPNODE user-cut callback.

Backward-compatible outer aliases are `k1-am-f0` and `paper-k1-am-f0`; the
historical inner-policy name is
`interval-mip-core-no-exhaustive-subset-duration`. The canonical preset is the
only recommended paper command.

Plain Gurobi and earlier CPLEX/route-load configurations are contextual
baselines. Inventory--route root closure, dynamic support-duration callbacks,
custom branching, symmetry, Gini-spread, required-movement, transfer-cutset,
and subset-inventory research families are default-off. Round 54's IR1 study
was negative at the frozen fixed-interval gate and did not change the mainline.

The evidence-backed support is exact V12 operation and bounded V20 sentinel
operation. V50 startup/configuration is supported, but the Round 54 sentinel
did not reach a fixed-interval solve within its bounded check, and the new
sealed V50 strengthening panel remained unopened. No universal-scale claim is
made.
