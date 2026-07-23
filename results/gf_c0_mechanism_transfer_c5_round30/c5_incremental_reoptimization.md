# C5 incremental reoptimization and state claims

C5 retains the same Gurobi model object from a leaf's complete LP relaxation
to its parent partial-target or terminal MIP. The integer variable domains are
restored and audited before MIP optimization. This eliminates an additional
model read for that same leaf.

C5 does **not** transfer a parent LP basis to child LPs. Child models have
their own canonical artifacts and model objects. No VBasis/CBasis mapping is
enabled, and basis reuse is reported as unavailable.

C5 does **not** claim native tree continuation after callback termination.
Keeping a `GRBmodel*` is object reuse, not evidence that presolve state, root
cuts, or branch-and-bound nodes survive a later `GRBoptimize`. Native logs are
audited for affirmative evidence; otherwise the classification remains
ambiguous or fresh restart.

The exactness argument depends only on the independently valid bound and
unchanged leaf coverage, never on retained native state. Thus a complete
restart may harm performance but cannot invalidate the proof.
