# Round 36 frozen causal protocol

Round 36 is an incumbent–decomposition causal mechanism study. It does not
promote a new mainline. The validated default C6-HGA-FULL path, four-interval
count, `rho=0.01`, complete LP treatment, deterministic scheduling, target and
requeue rules, lazy child lookahead, midpoint refinement, exact closure, and
strict original-problem certification remain frozen.

The four diagnostic arms are:

- **HH:** HGA proof incumbent, HGA anchor, proof normalization;
- **SS:** SIMPLE proof incumbent, SIMPLE anchor, proof normalization;
- **BW-P:** minimum verified startup incumbent for proof, maximum verified
  startup incumbent for the anchor grid, proof normalization;
- **BW-A:** the same best proof and wide anchor, anchor normalization.

Only a verified proof incumbent may control objective cutoffs, pruning, global
upper bounds, penalty closure, or certification. The launch-frozen anchor may
control initial grid geometry and, in BW-A only, split-gain normalization. An
experimental configuration with `U_anchor < U_proof` is rejected. `K=4` and
`rho=0.01` are fixed; there is no instance-dependent dispatch or rho sweep.

The 14-row Stage B panel is generated solely from committed Round 35 evidence
by `scripts/freeze_round36.py`. The script refuses to overwrite the frozen
manifest. The selection contains both V12 rows, every weaker-SIMPLE/slower
row, scenario-balanced weaker-SIMPLE/faster representatives, long V50
regressions, M coverage, and neutral/tie controls. No Round 36 outcome is an
input to selection.

Correctness, baseline-equivalence, unsafe-anchor rejection, coverage,
normalization, lifecycle, and zero-false-certificate gates must pass before
Stage B. V12/V20 rows use a nominal 1,800-second process cap and selected V50
rows use 3,600 seconds, with Gurobi Seed 0, one thread, and current strict
certificate semantics. A global deadline preserves unresolved coverage and a
valid noncertificate; there are no per-leaf or per-action time slices.

Broader Stage C validation is permitted only after a positive, predeclared
mechanism signal. No candidate is promoted automatically.
