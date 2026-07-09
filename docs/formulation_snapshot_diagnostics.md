# Formulation and Snapshot Diagnostics

This diagnostic round evaluates benchmark formulations and relaxation-vector extraction for `paper-gf-tailored-bc` without changing the paper-core algorithm.

The paper-facing algorithm remains the Gini-frontier decomposition with valid interval bounds and CPLEX-managed tailored fixed-interval branch-and-cut. Plain CPLEX, telemetry-only variants, exact-S alternative formulation audits, and LP snapshots are benchmark or diagnostic evidence only.

Implemented diagnostics:

- Current binary-expansion compact MILP metadata is emitted and labelled `tolerance_exact`.
- Exact denominator enumeration, exact denominator selector, and exact parametric cutoff are audited for complete S-domain coverage. They are exact only if every possible rational denominator value is included.
- A V4 direct-algebra toy verifies exact-S equivalence. V12/V20 route domains exceed the configured exact-S cap and are reported as `exact_but_too_large`.
- Exported fixed-interval LP files are relaxed and solved with command-line CPLEX to produce root LP primal values, reduced costs, and constraint slacks.
- Callback and telemetry relaxation vectors are explicitly marked unavailable until an audited callback-vector export path is implemented.

Dominant low-Gini K4 result:

- Plain fixed-interval MIP 14400s: LB `0.048398566621`, gap-to-cutoff `0.0007539860437`.
- Static tailored compact BC 14400s: integer optimal fixed-interval improving solution `0.0491015319884`, gap-to-old-cutoff `0.0000510206763`.

The 14400s tailored result is a fixed-interval subproblem result and a candidate incumbent improvement. It is not a full original-problem certificate until verified and merged through the normal frontier ledger.
