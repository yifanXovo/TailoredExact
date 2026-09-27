# Exact single-child contraction

If exactly one complete midpoint child LP is strictly infeasible, LP
infeasibility proves its MIP feasible set empty. The parent feasible set thus
equals the feasible sibling's set. AMC atomically replaces the parent by only
that sibling, records the eliminated half and strict status, preserves the
midpoint endpoint convention, inherits `max(B_p,B_feasible)`, and reuses the
already-built feasible model. Numerical, interrupted, ambiguous, or missing
statuses never contract. If both children are strictly infeasible, the parent
is closed through the exact infeasibility path.
