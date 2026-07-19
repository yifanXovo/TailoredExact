# Correctness proof for the Round 23 callback correction

1. Presolve is an internal CPLEX transformation, not a constraint of the EBRP.
   Turning it off leaves the loaded root LP/MIP feasible region and objective
   unchanged.
2. The global tree still branches on the closed disjunction
   `[L,s] union [s,U]`; exact parent-child coverage and endpoint tests remain
   mandatory.
3. Root rows, child-local rows, bound changes, cutoff equality, canonical
   inheritance, candidate validation, and deferred-row reoptimization are
   byte-identical in mechanism-off mode apart from new auditing fields.
4. `Preprocessing.Presolve=0`, `Preprocessing.Reduce=0`, and
   `Preprocessing.Linear=0` are set and read back before callback registration
   and optimization. Any setter/getter/value mismatch returns without solving,
   so no evidence can be certified under an unknown configuration.
5. Status 103 is interpreted relative to `native_model_scope`. Original,
   improving-range, cutoff, fixed-Gini-child, and strict-improvement scopes are
   distinct classes.
6. If an independently verified feasible route is known to satisfy the native
   model, status 103 is contradictory. The feasibility-consistency gate rejects
   the certificate and records the contradiction; it does not alter the native
   status or invent a lower bound.
7. Corrected S0 and S1 both retain the moderate4301 search through the native
   deadline, return status 108 with valid native bounds, and pass lifecycle,
   callback, coverage, verifier, and feasibility-consistency gates.
8. CPLEX may tighten a node's local `G` bounds after valid cuts. Every row
   inherited for `[L,U]` remains valid on a nested interval `[L',U']` when
   `L' >= L` and `U' <= U`. The callback now accepts this contraction and
   stores the intersection, but aborts on any expansion, inverted interval, or
   nonfinite endpoint. Unit tests cover equality, contraction, both expansion
   directions, inversion, and nonfinite data. A live V12_M2 smoke confirms the
   root contraction `0.718504... -> 0.687434...` proceeds to 214 children with
   no callback or estimate failure.

Therefore the change removes an unsafe solver transformation from all
continuous custom-branch solves and makes every residual inconsistency
fail-closed. No invalid heuristic can become a UB: same-run verification still
precedes cutoff construction, and verifier failure prevents the tree solve.
