# Quantity neighborhood and scope

Let s_i = p_i-d_i at a currently served station. Its legal signed station
domain is b_i-C_i <= s_i <= b_i, so Y_i=b_i-s_i remains in [0,C_i].
Zero is represented by deleting the stop; other values give one nonzero
unidirectional integer operation. No new visit, assignment change or exchange
of route order is part of this neighborhood. Empty routes may remain [0,0].

A single change has delta s_a=t. A pair has delta s_a=t, delta s_b=-t,
including both signs of t. Enumerate each unordered pair once and every
integer t in its station/load intersection. For every old route prefix,
let c be the sum of these operation coefficients along that prefix. It is
-1, 0 or 1. The new load is L+c*t. Thus c=1 implies -L<=t<=Q-L;
c=-1 implies L-Q<=t<=L. For c=0 the original feasible load is unchanged.
Intersect these inequalities over every affected prefix, including the final
return load. This covers same-vehicle order in either direction and separate
suffixes for a cross-vehicle pair. Capacity limits loads, not cumulative pickup.

For each candidate, replace operation amounts and compute the new pickup,
station-drop and return-unload totals. Evaluate the original duration as
travel+c_pick*pickups+c_drop*station_drops+c_drop*return_load. This equals
travel+(c_pick+c_drop)*pickups algebraically, but the implementation retains
the original evaluation order. When either changed operation becomes zero,
recompute that route's entire travel after omitting both zero stops. This
handles adjacency and asymmetric/nonmetric distances without triangle-inequality
assumptions. All unaffected visits, loads and route durations remain unchanged.

Inventory changes are Y_a-=t and, for pairs, Y_b+=t. The objective updater
recomputes both changed ratios and their pairs with every unchanged ratio,
the changed mutual pair, ratio sum S and weighted deviation P. It uses
long-double arithmetic and falls back to the original full formula near
S/H cancellation. It never clips a conflicting value. Integer enumeration
does not assume convexity, monotonicity or optimality of maximum quantity.

Choose minimum full F among feasible strict improvements, then deterministic
(station_a, station_b, delta) ties. The selected complete witness is rebuilt
and verified with the original verifier; agreement within1e-10 and improvement
above1e-12 are required. On rejection retain the previous physical witness,
mark verification_failed, and stop the refinement; such an experiment fails
mechanism acceptance. No rejected witness enters the UB or native Start.

There are finitely many integer inventories and fixed template assignments.
Every accepted step strictly decreases deterministically recomputed original
F, so no inventory state can recur. Zero removal only shrinks the available
neighborhood. Exhaustion means no strict improving move in this declared
neighborhood at the heuristic tolerance; it is not BRP optimality. The global
deadline instead reports deadline termination and stops the whole run.

The inherited outer incumbent store still requires an improvement above1e-10.
If the refinement improves only between1e-12 and1e-10, the outer store may
retain its original valid witness. Both snapshots remain explicit; neither
the outer threshold nor the exact solver tolerance is modified.

The exact algorithm uses the same unrestricted original domain, full coverage,
VD-S interval MIP and independently checked Start. Quantity descent supplies
only a verified original upper bound. Existing strengthened presets still
require symmetric metric travel: the module's wider nonmetric tests do not
extend the inherited cuts' applicability. Numerical certificate scope is
unchanged; no strict rational certificate is added.

## Historical and literature distinction

R61 already implements repairRound61Block with full original-objective
two-inventory algebra. It selects up to24 ratio-ranked pairs, at most2048
quantity evaluations per round, up to16 rounds, and an internal safety-seconds
stop; its original fixed template allows removed nodes to reappear. It helped
BLOCK but gave no improvement to the short HGA PREFIX in its exposed four
roles. These facts are in R61 final_report.md section2 and its implementation.
That routine is not enabled by R75 and is not admitted as this goal's formal
time-independent method. Its negative PREFIX result limits expectations.

R75 applies to a different self-constructed JDS-X witness, enumerates all
declared pairs/quantities and singles, permits both operation directions and
cross-vehicle changes, and stops at neighborhood exhaustion. It restricts
reappearance after deletion. It is a structured extension/replacement, not
invention of inventory repair or an optimality theorem. The additional
long-double updater follows R61/R73 algebra without changing their code.
Read R74 literature_notes.md for the primary quantity-reallocation and routing
precedents; their separable objectives and route semantics differ from ours.
