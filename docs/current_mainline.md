# Current mainline

As of Round 55, the stable research and paper-facing algorithm is **K1-AM-SF**
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

The controller is now represented by first-class fields:
`initial_gini_interval_count=1`, `split_point_rule=midpoint`,
`split_score_rule=balanced-normalized-closure`, `split_threshold=0.08`,
maximum depth 8, minimum width `1e-4`, split factor 2, exact child
infeasibility, the existing native-target policy, and exact parent closure.
Historical K4/C6 values are compatibility adapters only. Eleven paired
semantic sentinels proved the canonical preset and its historical alias equal
in settings, actions, common model fingerprints, objectives, bounds, and
certificate class.

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
operation. VD-P completed the frozen fixed-interval confirmation and long
panels, then produced 14 versus 12 effective certificates in the 44-row K1
integration with shifted-Work GM 0.5691998368 and GI ratio 0.6090974548.
Nevertheless it severely regressed the frozen major witness, so the K1 gate
failed and the sealed V12/V20/V50 P-GRB panel remained unopened. No
universal-scale claim is made.

Round 55 found and repaired one semantic model-reuse defect: an incumbent
improvement did not always advance the artifact/LP cache epoch. The correction
prevents a stale cutoff from being reused. No false certificate was observed,
but pre-fix trajectory and performance evidence is not a valid comparator;
Round 55 therefore uses a contemporaneously requalified corrected baseline.
VD-P remains a useful default-off research candidate; VD-J, MC4, and SF-R1
were rejected at earlier gates. The stable split controller is retained
because the severe witness had no materially changed adaptive action. No
station-state or sparse variant replaces the paper preset.

## Round 56 status

Round 56 does not tune or replace the algorithm. The corrected first-class
K1-AM-SF controller, F0-CLEAN backend, branching, rows, certificate policy,
and Gurobi contract remain frozen. The round audits operational T throughout
the model and identity pipeline, then applies the same executable and settings
to a matched V=8 through V=50 paper-candidate screening panel.

`route_time_limit_seconds` is a mathematical per-vehicle limit;
`solver_process_cap_seconds` is execution metadata. The common proof horizon
is 3600 seconds, while nine predeclared V>=20/T=18000 rows may continue to a
7200-second final cap. Native route witnesses are retained exactly as returned,
independently verified from disk, and never post-optimized. Certified packages
are exact; capped verified incumbents are not. Round 56 remains screening
evidence because it has only one base landscape per V.

## Round 58 qualification

Round 58 does not change K1-AM-SF. It compares the same frozen
`paper-k1-am-sf` preset with plain P-GRB on 50 scenarios selected before
performance from the replicated 960-scenario `citibike443-regional-v1`
family. Every selected scenario receives both 3600-second screen arms. Longer
fresh attempts follow the frozen 10800/16200/21600-second gap rules, and six
hours is the absolute cap.

P-GRB is one complete original compact MILP with native Gurobi presolve, cuts,
heuristics, and branching, but no Gini decomposition, tailored rows or
callbacks, custom branching, HGA start, imported route, or archive-derived
bound. Both methods use the same executable, Gurobi version, one thread,
Seed=0, and automatic presolve. Comparisons of capped rows use qualified bounds
at common horizons; unequal final horizons are labeled. Native route witnesses
are archived without post-optimization and archive time is excluded from
algorithm time.
