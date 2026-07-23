# C5 solver-event contract

The only partial-solve stopping event is a mathematical dual-bound target.
The Gurobi callback is installed at `GRB_CB_MIP`, reads
`GRB_CB_MIP_OBJBND`, rejects nonfinite or Gurobi-infinity sentinels, and calls
`GRBterminate(model)` once the certified value plus `1e-7` reaches the frozen
target. An incumbent (`GRB_CB_MIP_OBJBST`) never satisfies the target.

After `GRBoptimize` returns, C5 requires a successful API return, verifies the
native status, reads finite `ObjBoundC`, and rechecks that the bound reaches
the target. A target-caused `GRB_INTERRUPTED` status is a state transition,
not exact closure and not a global interruption. Any other interrupted status
is treated as the overall deadline and leaves the leaf open.

All observed callback bounds are written with callback runtime and the active
leaf's inherited bound. The trace global bound is
`min(active certified bound, other relevant open-leaf minimum)`. No callback
sample is interpolated. Finalization uses the scheduler's valid bound.

The implementation deliberately makes no claim that callback termination
preserves Gurobi's native branch-and-bound tree, presolved model, root cuts,
or basis. Reoptimization is classified from affirmative native-log evidence;
absent such evidence it is `unavailable_or_ambiguous` or a fresh restart.

The native-root-only prototype is rejected: `GRB_CB_MIP` with zero processed
nodes can report valid root-phase bounds, but it does not prove that all root
cut rounds are complete. Root events remain telemetry, never a C5 stop rule.
