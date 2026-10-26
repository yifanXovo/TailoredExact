# Round 51 frozen research contract

Round 51 starts from Round 50 commit `eccc795c0f5b2df5b57e24da31b56648150334b9`. It preserves all 23 frozen fixed-state identities, gamma intervals, verified cutoffs, objective, certificate tolerance, and panel roles.

The ordered mechanisms are causally separated:

1. M1 replaces only the `V<=12` exhaustive subset-duration conditional-row constant 100000 with the analytic row value `max(0,tsp[mask])` and fails closed for nonfinite or materially negative values.
2. S1 and S1-R1 are re-audited only on M1 with default branching.
3. A1 is developed only on M1 plus v0 cardinality symmetry. It reuses the required root LP evidence, probes at most four fractional primitive integer variables with two disposable child LPs each, gives positive priority to at most two variables, includes every probe in total Work/time, and never adapts after terminal MIP start.

No instance, panel, seed, V/M/Q, size, runtime, Work, node, memory, machine, historical-winner, or known-optimum dispatch is allowed. No MIP pilot, learned classifier, branching callback, controller change, or silent historical-mode change is allowed. Candidate selection uses only current root-LP primal values, original types/bounds, semantic families, and valid child-LP bounds/infeasibility.

Solver contract: Gurobi Presolve Auto, Seed 0, Threads 1, MIPGap 0, MIPGapAbs 0, complete minimization objective, identical verified cutoff, certificate tolerance 1e-7, honest process caps, and zero false certificates. Core is D1,D2,D3,D4,D5,D6,D9,D10,D11 at 120 seconds; development is D1-D14 at 300 seconds; confirmation is C1-C9 at 1200 seconds; predeclared long checks are at most 1800 seconds. Confirmation cannot select or revise a candidate.

The historical Round 50 backend remains explicit and reproducible. M1 is a candidate baseline, not an automatic production promotion. Symmetry/A1 interaction opens only if both independently pass. K1-AM integration opens only if a new fixed backend passes, and its K0=1, midpoint, adaptive-mass gate, tau=0.07915, controller, and certificates remain unchanged.
