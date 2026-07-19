# moderate4301 root fixation and conflict result

The canonical equal-capacity vehicle relabeling fixes 1,812 unambiguous
semantic variables and leaves connectivity, order, bit, product, and other
nonunique auxiliaries free. CPLEX solves this partial-fix root LP to feasibility
and optimality in approximately 0.02 seconds at objective
0.019278051143257303. The deterministic complete extension has zero unsupported
columns, zero bound/integrality failures, zero row violations at 1e-9, and
maximum scaled residual 4.2211046439599917e-17.

Fixing the retained vehicle labels without quotienting equal-capacity vehicle
symmetry is infeasible first at row `c11035`, the valid visit-count ordering
symmetry breaker (`sum z_0 - sum z_1 >= 0`). This is not an original-model
contradiction: all three vehicles have capacity 30, and canonical relabeling
preserves the route solution and satisfies the row.
