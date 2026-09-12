# Mathematical scope and frozen algorithms

The original evaluator remains unchanged: r_i=Y_i/D_i, S=sum r_i,
H=sum_{i<j}|r_i-r_j|, P=sum w_i|r_i-1|, F=H/(nS)+lambda P, with G=0 at S=0.
Real parsed targets, weights, lambda, capacities, travel and handling are used.
The current Instance supports heterogeneous Q but one common positive T and
common pickup/drop times; no heterogeneous time-limit claim is made.

## Transfer blocks

An append block first picks q at a and then drops q at b. Only unused stations
are considered. Its feasible q upper bound uses available inventory, receiver
space, Q_k-current_load and remaining handling time after the full route's
new travel. Starting from feasible routes, every old load prefix remains
unchanged; the new pickup load is <=Q_k and the new drop returns to the old
nonnegative load. Full travel+c*total_pickup <= T is checked before evaluation.
Single pickup/drop actions retain the original legal loaded-return option.
Pairwise conservation is never imposed on all routes.

For a,b changing by da,db, r'_a=r_a+da/D_a and r'_b=r_b+db/D_b.
S'=S+(r'_a-r_a)+(r'_b-r_b). H' removes and replaces the pairs incident to
a or b, counting pair (a,b) once. P' replaces only their two weighted terms.
This is exact O(n) arithmetic per quantity; no convexity or monotonicity is
assumed. Initial/full accepted-state evaluation is O(n^2). The exact zero
inventory sum identifies S=0 without subtraction cancellation. The tests
compare all 31x31 changed quantities in 400 random states with varied targets.

Ranking is heuristic: ratio contrast discounted by normalized added travel.
Every ordered feasible pair first selects its cheapest feasible vehicle; top
24 pairs and top 8 singles share a quantity-major round robin. At most 2048
quantity evaluations per round and 32 accepted rounds, with a 20s safety cap.
Shortlist truncation and incomplete quantity enumeration are heuristic. Neither
the shortlist nor choosing one vehicle is claimed locally or globally exact.
One scan costs O(M n^2 + n^2 log n); quantity work O(2048 n); at most 32 scans.
Only independently verified, strict final improvements replace the archive.
Thus BLOCK cannot worsen its empty-route input, but can miss useful blocks and
has no guarantee of making Gurobi faster. Tie-breaking uses IDs only after
structural keys; there is no ID-dependent policy or budget.

Revision 1 preserves each original route's station template and adjusts two
inventories together. Operations are rebuilt as (b-Y)^+ and (Y-b)^+, zero
services removed, and the full route is independently rechecked. This covers
direction changes without repeated visits. It preserves original feasibility
and strict objective improvement, but can miss order-changing improvements.
It uses at most 16 rounds of 24 pairs/2048 quantities and a 20s safety cap.
Additional full route verification can be O(n^2), separately measured.

## PREFIX and archive scope

PREFIX reuses the current HGA and decoder: population 24, decoder iterations
10, fixed seed 20260626, initialization plus 16 complete generations. The 30s
safety deadline is secondary. This is an empirical uniform configuration,
not an optimum stopping theorem. Observer OFF/ON use identical cached decoded
snapshots at extraction; neither consumes additional RNG or decoder work.
Publication failure leaves independently verified memory intact under the new
research flag; evidence persistence is a separate qualification.

Fixed F0 OFF/ARCHIVE/SUBMIT use the same original simple U0, full improving
Gini range and canonical rows (actual row is F<=U). ARCHIVE never changes the
native optimization. SUBMIT maps the same precomputed snapshot once, checks
current bounds/types/all linear rows and the current native incumbent. A
model-incompatible global archive does not update the model-applicable gate.
The final admission gate allows F equal to the current non-strict cutoff when
the native call has no incumbent or a strictly worse one. Global archive U is
not an incumbent of every later native model. Equality does not bypass Gini
membership, propagated bounds, any row, or per-call hash deduplication.
There is no HGA invocation in callbacks and no new LP-guided claim. The full
outer algorithm can merge the global archive after a native call, through the
existing verified-cutoff/coverage contract; this is separately measured.

Official [Gurobi callback documentation](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html)
was checked for this round: a successful return is an API operation, a finite
objective is immediate processing, and infinity outside MIPNODE is compatible
with delayed processing. Matching MIPSOL/final integer vectors and observed
incumbent changes are recorded separately; none proves unique causal origin.

## Inventory-time oracle

The oracle minimizes Tstar subject to all station inventories (or an explicit
subset), routes starting empty, at most one nonzero one-direction service per
station, vehicle assignment, arc degrees, ordering and load propagation. It
contains no Gini variables, F cutoff, original-T arc deletion, original-T
propagated domain, or inherited tailored rows. Released stations remain in
the model and can supply/deliver under their original capacities.
Inventory index 0 is the input's depot placeholder, excluded from objective,
station inventory conditions and available supply; vehicles still start with
zero load. Historical diagnostic vectors use 0 there, while parsed PREFIX
witnesses preserve the input placeholder. This does not provide depot bikes.

A simple route has at most n+1 arcs, each bounded by d_max. Because service is
single and unidirectional, total pickups across all vehicles cannot exceed
sum b_i. Thus B=(n+1)d_max+c sum b_i bounds every feasible route's duration,
independently of the original T. Tstar<=B does not remove a time-free feasible
routing. Load implications use 2Q_k: L_i-L_j-p_i+d_i lies in [-2Q_k,2Q_k].
Ordering uses n+1. Return-depot load is unrestricted; starting-depot load is 0.
An all-pairs shortest-path lower bound supplies a valid station-duration row,
even when input distances do not satisfy triangle inequalities.

LP objective/bound and integer ObjBound are lower bounds on required time,
never on F. A decoded route is checked independently with bound B and its
actual maximum duration is the upper bound. Original-T feasibility requires
that witness to meet original T. Strict time infeasibility needs a valid lower
bound > T + 1e-5 max(1,T). Intervals crossing T remain unknown. Model
infeasibility under B is time-independent infeasibility; numerical failure,
LP infeasibility, MIP infeasibility and unfinished runs remain distinct.

For the frozen Euclidean inputs, an additional solver-free necessary condition
uses pair travel lower bound d(0,i)+d(i,j)+d(j,0) and pickup lower bound
max(p_i+p_j,d_i+d_j). A clique of M+1 required services whose pair bounds all
exceed T is impossible with M vehicles, even when other stations can help.
This is conditional on those inventories, not a new F bound. See
`cheap_time_proof.md` for its metric assumption and the bounded search policy.

A proved impossible partial inventory pattern gives a logical no-good only
in its proven scope. Exact little-endian inventory bits give sum of mismatching
bits >=1. This excludes the pattern, not an arbitrary inventory hyperplane.
No cuts are submitted unless their scope, recorded-point violation and cost
support an additional frozen experiment. No theoretical novelty is claimed
for transfer moves, objective deltas, routing models or bit no-goods.
