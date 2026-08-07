# Round 33 frozen V10 convergence protocol

## Frozen arms

P-GRB is the complete compact original MILP in Gurobi 13.0.2 with one
thread, Seed 0, automatic presolve, zero relative/absolute MIP gaps, and no
HGA or decomposition. C6-FROZEN is the unchanged validated Round 31/32
nonblocking native-bound Gini interval decomposition with its fixed HGA,
four initial intervals, rho 0.01, lazy child lookahead, adaptive split
geometry, native targets, requeues, and exact-closure semantics.

## Instances and pre-result freeze

The 18 V10 instances and six repeats are frozen in their manifests before
any solver result. Seeds are SHA-256-derived from the starting commit,
`round33-v10-convergence`, M, Q, and scenario. Structural invalidity alone
permits the recorded counter-based deterministic replacement rule; solver
performance never permits replacement.

Every V10 and V12 canonical compact model is imported before official runs.
Its Gurobi fingerprint, model export hash, instance hash, executable hash,
and verifier contract are frozen. Each V10 fingerprint is then exercised by
a non-performance native-optimal certificate-promotion preflight. No
fingerprint is created from an official result.

## Timing and execution

Every row is an independent process with a 3,600-second process-entry cap,
a 15-second internal shutdown margin, and a 3690-second
external emergency watchdog. Rows stop naturally after strict
original-problem certification. The primary certificate time is
`final_process_wall_time_seconds`, covering process entry, parsing, HGA when
present, construction, scheduling, native solves, verification, and exact
finalization. Solver-only `runtime_seconds` is diagnostic only.

Runs are serial, one-thread, and checksum-resumable at row granularity.
Algorithmic solve-state resume is not claimed. Partial and invalid rows are
preserved with explicit reasons. Result JSON is parsed after child exit and
all required artifacts are hashed before an atomic completion marker.

## Comparison and traces

Stage 1 contains 18 V10 x two arms (36 rows). Stage 2 contains V12_M1 and
V12_M2 x two arms (four rows). Stage 3 independently repeats the six
predeclared V10 cells x two arms (12 rows). Certificate-time speedup is
P-GRB time divided by C6 time when both strictly certify. Timing ties use
max(0.05 seconds, 0.1% of the faster time). Shifted geometric means use a
one-second shift and only both-certified pairs.

AUC and gap thresholds use observed, left-continuous bound steps only. A
real final-result bound may be added at its recorded process-entry time; no
interpolation or post-final-event extension is allowed. Round 32 evidence
may appear only in explicitly historical derived tables and is never mixed
with Round 33 raw rows.
