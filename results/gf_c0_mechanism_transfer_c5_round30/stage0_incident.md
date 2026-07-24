# Pre-official Stage 0 audit incident

The first frozen Stage 0 execution completed all eight solver processes and
passed builds/tests, C0 parser totals, native target semantics, exactness, and
false-certificate gates. Its aggregate trace gate failed because the audit
harness required the exactly solved toy P-GRB row to contain at least two
native callback observations. The toy closed in one callback; no trajectory
was needed for its exhaustive exactness comparison.

This was an audit-scope defect, not a C5 solver, bound, coverage, lifecycle,
callback, or certificate defect. The four nontrivial external-arm
Moderate4301 traces and both nontrivial sentinel traces were complete.

Before any Stage 1 row, the harness was corrected so trace completeness is
required for the four nontrivial external rows and the nontrivial P-GRB/C5
sentinels. The toy remains an exactness-only gate. The original failed gate
and all original run artifacts are retained. New clean Release builds use
`cplex_only_r1` and `with_gurobi_r1`, and all Stage 0 processes are rerun under
`stage0r1_*`.

No C5 source, algorithm state, target, `rho`, geometry, callback semantics, or
official command policy changed.
