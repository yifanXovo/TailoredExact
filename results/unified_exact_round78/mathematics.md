# Balanced contiguous blocks: scope and finite descent

Write a served operation as s=p-d and a route's post-service prefix load as
L_j=sum_{i<=j}s_i, with L_0=0. For a contiguous block (a,b], L_a=L_b is exactly
zero net block load. Its deletion preserves every source prefix outside the
block. At a target leg carrying load l, block feasibility requires
0<=l+min_{a<=j<=b}(L_j-L_a) and
l+max_{a<=j<=b}(L_j-L_a)<=Q_target. The target's later prefixes and both return
loads remain unchanged. A relative negative prefix may need positive entry
load. Balance alone never implies feasibility on an empty vehicle.

Each station and its same nonzero one-way integer operation is transferred
once, preserving single visit, station stock and the entire final inventory Y.
Thus original coupled Gini/deviation F is exactly unchanged, including the
original S=0 convention. No constraint or objective is weakened. Both source
and target travel are recomputed in route order. Handling uses original
c_pick*pickup+c_drop*station_drop+c_drop*return_load; balance preserves each
return load. Source deletion is checked even without triangle inequality.
Physical feasibility uses the unchanged original1e-7 route threshold.

The neighborhood includes all balanced contiguous source intervals, every
other vehicle and every target leg, preserving order within the transferred
block. It excludes noncontiguous blocks, reversed blocks and within-vehicle
reorderings; exhaustion is only for this declared neighborhood. A scan has
at most O(V^3+MV^2) placements across bounded routes; the implementation
recomputes O(V)-length travel for a placement and sorts an M-length duration
tuple. No candidate-count limit stands in for exhaustion. Insertion and quantity
proposal criteria are the inherited R76 rules, not a minimum-F union oracle.

At a fixed Y, accept a balanced move only if the finite vector of all route
durations sorted descending strictly decreases in exact lexicographic order.
Choose the minimum feasible vector, then deterministic source/interval/target/
leg index order. This is a bottleneck-time proxy, not a theorem about future
search speed. No epsilon lex comparator may skip an earlier tiny increase.
Strict R76 steps decrease recomputed original F by more than1e-12; their
prediction agreement remains1e-10. Neutral steps require exact integer-Y and
computed-F equality, and full verified duration-tuple agreement.

The combined state key (computed F, sorted duration vector) strictly decreases
at every accepted step. With bounded integer inventories, finite route orders,
assignments and operations, this precludes cycles without an arbitrary pass
cap. This is a termination argument for the implemented finite descent, not
global BRP optimality, a runtime bound, new theory or a rational certificate.
The sole whole-run deadline ends the algorithm, retaining its last verified
witness. No internal time/Work allocation or instance-history switch is added.

Exactness still comes from unchanged complete VD-S coverage/native proof. The
heuristic only supplies a verified incumbent/Start. The inherited R68 native
path invokes normalizeRound61Routes: used routes are assigned to lower vehicle
indices only within equal-Q classes and verified again. Unequal-Q routes are
never relabeled. This existing mapping preserves Y and actual feasibility;
neutral search itself keeps original vehicle identities and deterministic ties.
The unchanged outer1e-10 handoff threshold may retain the prior witness for
neutral-only or smaller improvements. Actual handoff and Start must be audited.

Generic block relocation and quantity improvement are established local search
ideas; primary BRP literature and model differences are in R74 literature_notes.
The present increment is this full original-objective, prefix/time-checked,
finite plateau-crossing composition and its measured effects. Correctness,
design rationale and complete-method performance remain separate claims.
