# Prospective construction hypothesis; not a new opened experiment

This note is prepared while the unchanged Round72 D7 long campaign runs.
It responds to Round71's already exposed route-quality deficit. It neither
changes the current candidate nor declares a new resource budget. Decide
whether to pursue it only after the complete long evidence. No efficiency,
global heuristic optimality or theoretical novelty is claimed here.

The alternative is direct construction with jointly chosen station insertions
and integer service quantities. Start from an independently verified route
set and inventories, using empty routes only when the original no-service
solution is legal. Consider new, unvisited stations only. Evaluate the exact
original F after each tentative inventory change; do not substitute total
dissatisfaction or a fixed-target loading theorem for the normalized Gini
objective. All original hard constraints still require final physical replay.

## Feasible motifs under the current common handling convention

Let a verified vehicle route have duration Dk, capacity Qk and original leg
loads Lh. Inventory bounds [ell_i,u_i] mean the actual legal station bounds
from the original model, not guessed target-based limits. Denote pickup plus
drop handling time per picked bike by c. In this project, depot unloading of
the return load is included, so duration is travel+c*total_pickup.

Insert a new pickup station i before a new drop station j on the same route,
with quantity q at each. The inventory change is Yi-=q, Yj+=q and return
load is unchanged. If a and b are their original insertion-leg indices,
a<=b, the affected loads increase by q from the pickup to the drop. A safe
integer range is

q <= min(Yi-ell_i, u_j-Yj, Qk-max(Lh for h in [a,b]),
         floor((T-Dk-delta_travel)/c)).

For c=0, omit the quotient and require Dk+delta_travel<=T. Reject negative
or empty ranges. When both insertions use one leg, delta_travel must be
computed for the ordered path predecessor->i->j->successor; two independent
one-node insertion deltas would be wrong. For distinct original legs, the
two travel replacement deltas add. Existing operations remain unchanged.

Also allow a single new pickup, increasing return load: its capacity margin
is Qk-max suffix load, inventory reduction is bounded by Yi-ell_i, and added
handling is c*q. A single new drop is bounded by the minimum suffix load and
u_j-Yj. Its total pickup is unchanged, so its added handling is zero under
this depot-unloading convention: unloading is moved from depot to station.
Its travel insertion and every load prefix still need checking. These motifs
preserve unique station service and permit loaded returns. They never bound
a vehicle's cumulative pickups by Qk.

## Finite selection and a useful computational reduction

For every feasible positive integer q, compute the actual reduction in F.
Among positive-duration insertions, reduction per added physical duration is
a possible construction score; this duration is the mathematical route
resource, not CPU seconds or Work. Handle nonpositive added duration as an
explicit priority class, with deterministic ties, avoiding division by zero.
Accept only an actual original-objective improvement. Each accepted motif
adds at least one previously unvisited station, giving at most n accepted
construction steps. This is a complexity property, not a renamed runtime slice.

For a fixed station pair and quantity, objective change does not depend on
insertion positions. Enumerate placements, compute each one's qmax and travel
delta, and store the best delta/positions for each qmax. Suffix minima over
qmax then give the least-duration feasible placement for each q. This avoids
re-evaluating the same inventory objective at every placement. Precomputed
range maxima of original leg loads support constant-time capacity checks.
Updating S, H and the weighted deviation after one/two inventory changes
requires only the affected ratios and their pairs with other stations.

The reduction applies only to this local score and unchanged existing service
quantities; it is not a dominance theorem for the full BRP. Retain independent
route reconstruction and the original numerical verifier before publishing UB.
A selected constructor would still feed the complete existing exact proof.

## Conditions before any implementation can be admitted

First check the actual parser/model inventory domains and shared objective/
depot-unloading implementation. A new isolated preset would need tests for
same-leg pair insertion, suffix capacity, cumulative pickups above capacity,
loaded return, zero handling, legal empty start and S=0 semantics. Exhaustive
tiny motif enumeration should check the placement/quantity reduction against
direct enumeration. Full original-input comparisons must then establish route
quality and total certification/gap benefit. Construction may still be too
myopic or expensive. No new build, solver run, candidate switch or confirmation
claim is authorized merely by this note.
