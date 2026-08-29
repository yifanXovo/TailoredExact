# K1-AM-SF algorithm

K1-AM-SF means **K1 Adaptive-Mass with Sparse Fixed-Interval Formulation**.
The canonical CLI preset is `paper-k1-am-sf`.

## Outer controller

1. Obtain and independently verify a same-run incumbent.
2. Form one complete initial interval for every Gini value that could improve
   that incumbent (`K0=1`).
3. Solve the interval with the F0-CLEAN backend and retain only scope-valid
   bounds, infeasibility conclusions, or verified original solutions.
4. When refinement is required, split at the exact midpoint. The adaptive-mass
   score and frozen threshold `tau=0.08` decide refinement; the native-target,
   exact-parent closure, and child-infeasibility behavior are unchanged from
   Round 53.
5. Maintain exact coverage. A monotone global lower bound is the minimum valid
   bound over the final covered leaves.
6. Issue an original-problem certificate only when coverage, lifecycle,
   lower-bound, and independent incumbent-verification checks all pass.

## Inner backend

F0-CLEAN is the historical Round 50 v0 fixed-interval model with the exhaustive
V<=12 subset-duration block omitted and all other audited active static
families retained. Gurobi uses `Presolve=Auto`, `Seed=0`, `Threads=1`,
`MIPGap=0`, and `MIPGapAbs=0`; branching and PreCrush are left at native
defaults. The MIPNODE user-cut callback and tailored dynamic cuts are off.

## Identity and exclusions

The aliases `k1-am-f0` and `paper-k1-am-f0` canonicalize to this exact outer
configuration. The inner alias
`interval-mip-core-no-exhaustive-subset-duration` canonicalizes to F0-CLEAN.
The six Round 54 semantic sentinels agree on deterministic command settings,
controller actions, interval endpoints, backend policy, objectives, bounds,
and certificate class. Fixed-interval model files are byte-identical whenever
the bounded sentinel reached model construction; the V20/V50 checks remained
in the deterministic heuristic phase and therefore produced no model file.

Gamma-veto, AMF, reduced-cost rescue, fixed-rho, PMM/FPMM, non-midpoint split
points, AMC for K1, custom branching, symmetry, exhaustive Big-M, and Round
52/53 callback research are not part of K1-AM-SF.
