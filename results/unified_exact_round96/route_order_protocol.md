# R96 second hypothesis: order-induced physical slack

Frozen before the free-order diagnostic or order-prototype execution. F5's final
fixed-owner, fixed-order, full-quantity MILP was certified at its original F,
while the separately verified P witness is better. This identifies a structural
barrier for that F5 witness, without identifying which structural restriction is
responsible. D7 and U6 remain unclassified after their quantity time limits.

One additional independent diagnostic allows every permutation of the originally
served nodes on its original vehicle, optional deletion and all inventory/sign
changes. It adds no new station and does not change ownership. Directed path
degrees, MTZ ranks and conditional arc-load equalities replace the ordered DAG.
The original full-range Gini/product rows and objective remain unchanged. All
returned routes and model vectors must pass independent physical and row audits.
The restricted bound is never a global bound. Cap: one 300 s F5-final process.
Qualification: 750 inventory/permutation mappings, then one native micro (30 s).
No run is retried to obtain a more favorable endpoint.

The production-shaped prototype is different from this timed diagnostic MIP:
after the unchanged R83 closure, enumerate every triple of cuts in one vehicle's
served sequence. Between cuts are two nonempty adjacent blocks A,B; enumerate
both block orders and both orientations of each block. Preserve the outer prefix
and suffix, station quantities and ownership. Choose the feasible proposal with
the smallest sorted descending vector of full vehicle durations, using fixed
enumeration order for ties. Require exact strict lexicographic decrease and
unchanged inventory/objective. Then repeat the original R83 closure. Stop only
on exhaustion, objective zero, verification failure or the common whole-process
deadline; no internal k-second allowance, credit or timed fallback.

This includes two-block transpositions and reversals within a route. R78 moves
balanced blocks only to a different vehicle; R83 exchanges equal-net blocks
between different vehicles without reversal. The new neighborhood changes order
and can free travel time or alter feasible load prefixes that quantity-only
moves and those intervehicle proposals cannot reach.

Finite termination: each strict R83 step lowers F. Each neutral R83/order step
preserves inventory and lowers the same duration tuple. The finite physical
integer-inventory, assignment and permutation state space therefore has no
cycle. This proves only termination/exhaustion of these declared proposals.

Development: one legal micro must demonstrate a complete two-station stop and
an order-enabled original-F improvement. Then exactly six existing D7/U6/F5
snapshots, each with two tasks: original R83 closure and the new closure starting
from that same R83 endpoint. External guard 120 s per process; no restarts or
alternative seeds. All six negatives and costs remain in the report. Native
optimizer calls for the C++ prototype: zero. This costs at most nine additional
charged processes (native micro + F5 diagnostic + C++ micro + six real cases),
and reserves formal paired/long-window runs within the 72-start ceiling.

Integration is conditional on real quality/cost evidence, followed by a frozen
default-off hook and matched end-to-end comparison. A negative finite revision
is retained and stopped rather than inserted into all startup candidates.
