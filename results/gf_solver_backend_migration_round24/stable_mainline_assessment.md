# Stable-mainline assessment

Corrected CPLEX S0/F0 remains the sole stable paper mainline. Round 24 does not provide licensed Gurobi performance evidence and therefore cannot support a backend migration, a longer production matrix, or a change to stable defaults.

The source audit confirms that S0-SAFE remains presolve off with Reduce 0 and Linear 0, parent-copy estimates, full inherited rows, deferred child-local rows, one thread, one environment/problem/model read/`CPXmipopt`, exact-zero gaps, F0, and P1/P2/F3 off. The new unsafe presolve-on switch defaults false, requires a separate research-mode flag, visibly marks the native configuration invalid, and forces `strict_certified_original_problem=false` even if native status is 101. No instance/path/name/seed dispatch was added.

Round 24 establishes useful implementation feasibility: one canonical LP source feeds both plain adapters; the solver-neutral external controller passes exhaustive structural tests; CPLEX consumes a static F0 interval model with valid monotone bounds; Gurobi retained-leaf and complete-start mechanisms are implemented behind fail-closed gates. It does not establish runtime feasibility because the installed Gurobi 13.0.2 environment has no usable license.

Decision: no promotion and no long migration round. The single next experiment is a licensed rerun of Stage 0 followed, only if every gate passes, by the preregistered 120-second V12_M2 fresh/cold/warm Stage 1B gate. This is a capability qualification, not a mainline migration.
