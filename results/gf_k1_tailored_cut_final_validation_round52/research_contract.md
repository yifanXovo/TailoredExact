# Round 52 frozen research contract

Round 52 is a preregistered, bounded study on base commit
`c6d7109bf69f50bd459174e8f05242b478e57d85`. Its ordered objectives are:

1. Correct the K1-AM action mapping and root-telemetry semantics, audit plain-LP
   v0/M1 monotonicity, and decide whether tau 0.08 is decision-equivalent to
   historical tau 0.07915.
2. Freeze the K0=1 midpoint K1-AM outer interval controller.
3. Complete a solver-independent cut library and a genuine default-off Gurobi
   `GRBcbcut` user-cut adapter, initially for rank-2/rank-3 support-duration
   inequalities.
4. Execute at most three preregistered cut-management iterations, freeze one
   inner backend, and independently compare contemporaneous P-GRB with
   K1-AM-FINAL on frozen V12/V20/V50 validation and holdout panels.

All official optimization uses Presolve=Auto, Seed=0, Threads=1, MIPGap=0,
MIPGapAbs=0, the complete original minimization objective, the verified
incumbent contract, the strict-improver Gini range, certificate tolerance
1e-7, and honest total-process caps no greater than 1800 seconds. Known-optimum
and archive-winner injection, instance-specific parameterization, and
result-dependent instance selection are forbidden.

Every candidate must preserve the exact original feasible set, complete
interval coverage, valid and monotone global lower bounds, finite exact
termination, and strict original-problem certificates. Algorithmic actions may
depend only on current mathematical state (for example LP violation, exact
dominance, duplicate identity, infeasibility, closure, or canonical support),
never on identity, dimensions, benchmark role, historical winner, elapsed
time, Work, nodes, memory, or hardware.

Cut development is limited to three iterations, two candidates per iteration,
and one development-only revision per iteration. Each plan is hashed before
runs, changes one allowed design dimension, evaluates the complete frozen core,
and preserves failed evidence. No algorithm change is allowed after fixed-
interval confirmation or final validation opens. If the permitted candidates
fail, the outcome is a bounded systematic negative result and production v0 is
retained. Independent P-GRB validation and sealed holdout remain mandatory.
