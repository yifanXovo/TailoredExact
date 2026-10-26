
# Round 50 research contract

Round 50 first audits and optimizes the uniform fixed-interval MIP backend, freezes one backend, and only then integrates that backend into unchanged K1-AM. The K1 controller remains `K0=1`, exact midpoint refinement, adaptive-mass gate, and `tau=0.07915`. AMF-v1, reduced-cost rescue, gamma-veto, root-processing rescue, fixed-rho fallback, and AMC are inactive.

Every official solve uses Gurobi Presolve Auto, Seed 0, Threads 1, zero relative and absolute MIP gaps, the complete minimization objective, the same verified cutoff, certificate tolerance `1e-7`, and an honest external process cap no greater than 1800 seconds. The feasible set, valid bounds, interval coverage, monotone bounds, exact termination, and original-problem certificate are invariant.

At most four one-family development iterations are permitted. Confirmation freezes all algorithmic choices. The conditional LP tail-repair stage may open only after a backend freeze, K1 qualification, and a newly recomputed severe split error. No instance, size, panel, runtime, Work, nodes, memory, machine, historical-winner, or known-optimum dispatch is permitted.
