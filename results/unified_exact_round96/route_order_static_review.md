# Route-order contrast: pre-execution review

Self-review from an adversarial perspective; not an independent agent review.
No test pass or real-instance benefit is claimed by this document.

## Diagnostic model

For each originally served node j, incoming and outgoing degree both equal
1-s[j,b[j]]. Start outdegree and copied-depot indegree are one. No arc enters
the start or leaves the copied depot. For each possible selected arc (a,b),
u[b]-u[a] >= 1-(N+1)(1-x[a,b]), with u[start]=0 and other ranks in [0,N].
Summing over a directed cycle contradicts its positive length. Degrees and
absence of cycles therefore give exactly one path through every active node.
Ranks may be continuous; their cycle exclusion does not require integrality.

On a selected arc ending at station b, load[b]-load[a]+Y[b]-initial[b]=0;
start load is zero and all subsequent loads lie in [0,Q]. The unconditional
expression ranges from -Q-initial[b] to Q+capacity[b]-initial[b], so symmetric
M=Q+max(initial[b],capacity[b]-initial[b]) is valid. For an arc into the depot
copy the change is zero and M=Q suffices. These constraints enforce each
prefix and permit a positive terminal load. They do not cap total pickups.

Travel is computed from selected arcs. Complete handling is
(pickup_time+drop_time)*sum((initial-Y)+), including return unloading.
Inactive stops vanish and signs are free. Unserved inventories stay initial.
The station product/Gini rows are inherited from the qualified full-quantity
diagnostic, with full G range. A 17-digit writer removes only exact zero.
The input witness maps to its original chain and exact integer inventory.
Qualification checks physical/model equivalence for all 750 micro mappings;
one native solve must match the exhaustive optimum before F5 is launched.

## Finite C++ proposal

The two nonempty blocks arise from all 0<=a<b<c<=n cuts. There are seven
nonidentity order/orientation choices per cut (some yield duplicate sequences
when blocks are singletons; duplicates are harmless and included in cost).
Prefix-load feasibility is scanned in int64. Inventories and total handling
are invariant. The original duration accumulation order is used and the final
chosen route is independently passed to the unchanged Evaluator. Its inventory,
F and duration potential must exactly equal the predicted neutral result.

No partial enumeration is committed on the common deadline. After a complete
neutral choice, the original R83/R76 closure runs. A route deleted by old
intervehicle moves is represented as an empty depot route for the stricter
starting-witness validator; no service or quantity is changed by normalization.
Trace snapshots retain all accepted neutral routes and subsequent closures.

The proposed micro has three stations at three corners of a unit square,
initial stock (4,0,0), targets (1,1,1), vehicle capacity 3, pickup/drop time .2,
and T=2+2*sqrt(2)+.8. The old route 0-1-2-3-0 with pickup2/drop1/drop1 has
F=19/60. Shortening to 0-1-3-2-0 releases enough travel time for one additional
pickup and depot unload, producing inventories (1,1,1) and F=0. The executable
must verify that the complete pair neighborhood and original R83 both stop at
the old witness before accepting this as a mechanism qualification.

## Admission and stopping

The formal LP-G executable and runner bindings are untouched. This prototype
has no production hook yet. After qualification, the six predeclared real
snapshots determine whether there is any incremental F gain and whether its
cost warrants an end-to-end test. The free-order MILP result is a separate
contrast and never supplies a production Start or bound. If its cap expires,
absence of improvement is unknown, not a certificate against order changes.
