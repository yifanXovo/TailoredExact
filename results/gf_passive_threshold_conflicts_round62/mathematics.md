# Mathematical contracts and scope

## Passive upper bound and final termination

The parsed objective remains `F=G+lambda*P` with the original S=0 convention,
weights and physical routing semantics. Both terms are nonnegative. A complete
F0 model covering `0<=G<=min(U_control,(n-1)/n)` and containing the canonical
non-strict row `F<=U_control` covers every improving solution `F<U_control`.
An independently verified control witness therefore converts its native bound
B into the original-problem bound `min(U_control,B)` even without native
SolCount. Gaps, native statuses and original-problem certificates are separate.

For K1, the immutable launch snapshot contains every live leaf, including open,
terminal-ready, closed and empty leaves. Replaced ancestors are excluded only
after the inherited atomic coverage contract validates their children. Each
leaf contributes its valid bound; the currently solved *whole leaf* contributes
the maximum of that bound and its MIP global bound. Empty leaves contribute
U_control. The outer minimum is capped by U_control to include omitted
nonimproving solutions. Roots, parent-child coverage, actual interval coverage,
model identity, cutoff, epoch and bound/witness consistency are checked.
Unknown/open leaves retain their structural G floor; an active leaf alone can
never close the original problem while another leaf has a lower bound.

For a verified archive, U_usable=min(U_control,U_archive). At the same legal
logical state its gap is no larger than the control gap. This does not predict
wall-clock speedups: PREFIX, verification and observation consume process time.
OBSERVE changes no search input or organization. CERT may call GRBterminate
only when the *full snapshot* closes the existing absolute certificate tolerance.
At the outer boundary the same full-ledger criterion can stop before a native
call. It never closes individual leaves, changes incumbent_epoch, cutoff,
propagated domains, branch scores, native starts/hints or continuation targets.
OUTER retains the Round61 post-native archive merge; SUBMIT additionally maps
and submits candidates. Neither is called passive.

After return, the live final ledger, finalized native bound and independently
recomputed best witness must pass coverage, lifecycle, numerical and consistency
gates again. A tentative callback stop without final validation is un-certified.
Native INTERRUPTED stays in native logs/lifecycle; logical closure relative to
U_usable does not rewrite the control leaf statuses. The result serializer has
an explicit passive-certificate gate. Archive evidence write failure does not
erase a verified in-memory witness; persistence is a separate evidence property.

The implementation uses the documented [MIP callback bound](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html)
and [GRBterminate API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/solving.html),
then reads final status and attributes after synchronous optimize returns.

## Service events and directed travel lower bounds

One nonzero unidirectional service per station implies total pickup P_i and
drop D_i cannot both be positive, and a served station belongs to one vehicle.
Thus P_i>=q iff Y_i<=b_i-q and D_i>=q iff Y_i>=b_i+q for integer q>0.
These equivalences would fail under repeated visits or split service; those
changes are not made here. Q_k is vehicle capacity, not the event threshold q.

Floyd-Warshall on nonnegative directed arc costs gives shortest-path lower
bounds. A route visiting distinct i,j has a travel prefix, middle segment and
suffix, hence travel is at least the smaller of
`dbar(0,i)+dbar(i,j)+dbar(j,0)` and the reverse visiting order. Intermediate
stations, including potential suppliers, cannot lower this bound. Actual routes
are evaluated with original arcs, never the shortest-path replacement.

Empty departure and nonnegative load at return imply total pickup >= total
drop on each vehicle. For two required events the total pickup is therefore
at least `max(required pickups,required drops)`. Add c times that value to
the travel lower bound, where c is parsed pickup_time+drop_time. This remains
valid with extra supply, delivery and visited stations and with loaded return.
Total pickup is *not* bounded by Q_k; only every load prefix is so bounded.

An event's eligible vehicle set is conservatively filtered only by q<=Q_k and
the single-station time lower bound. A pair is incompatible if no eligible
vehicle is common, or every common vehicle violates the time lower bound by
more than `1e-5*max(1,T)`. The parser currently supplies common T and handling,
and potentially heterogeneous Q; no heterogeneous T support is claimed.

A distinct-station clique requires distinct vehicles for all simultaneously
true events. Thus sum(z_e)<=|union eligible vehicles|. Each generated clique
has strictly more events than this union. Reducing thresholds enlarges event
regions and may enlarge eligibility; every reduction recomputes the proof.
All rows use global physical domains L=max(0,b-max Q), U=min(cap,b+max Q).
No node bound, cutoff or Gini leaf is a proof premise, so rows can be regenerated
unchanged throughout K1. Proof JSON stores domains, events, eligible vehicles,
all edges, margin and final coefficients; run manifests bind input bytes.

## Representations and continuous completion

Scalar event definitions use the two exact integer iff rows from the task.
Constant events are fixed first; shared events reuse one binary and nested
thresholds have monotonicity rows. All definition rows are ordinary required
model rows, never optional user cuts. Sparse events are declared in the LP
before native model reading; callback variable creation is not used.

For a low event Y<=theta, at a frozen fractional Y the legal scalar interval is
`max(0,(theta+1-Y)/(theta+1-L)) <= z <= min(1,(U-Y)/(U-theta))`.
For a high event, it is
`max(0,(Y-theta+1)/(U-theta+1)) <= z <= min(1,(Y-L)/(theta-L))`.
The minimal completion respects nesting automatically on a common domain.
Therefore a clique separates that point only if the sum of legal minima
exceeds its RHS; selecting convenient event values is not a separation proof.

The service alternative adds `P>=q*z, P<=(q-1)+(Pmax-q+1)*z` for pickup
events, or the analogous drop rows, plus `z<=sum visits`. Single service makes
these integer-equivalent to the scalar event. Their event minima are stronger
than the scalar minima, but under the existing F0 perspective service hull,
service-only still admits a continuous completion for every old LP point;
the stronger restriction arises when coupled to clique rows. Both service-only and service+
conflicts use the same dictionary. Candidate mapping computes every r62lo/hi
variable from independently verified final inventories and still checks all
native rows. Formal B ablations leave candidate generation off.

The box projection sum(low (Y-L)/(theta+1-L)) +
sum(high (U-Y)/(U-theta+1)) >= 1 is valid: at least one event is false,
its term is >=1, and every other term is nonnegative. Denominators are checked
after constant simplification. This does not describe the full forbidden
integer orthant and is not guaranteed to cut an LP point. Its intended role
is a cheap no-new-binary reference. Integer validity, LP strengthening, native
adoption and net search gains must be measured separately.

### Exact LP projection for the automatically retained cliques

For an event let t_e be its nonnegative box-projection term. Its minimal
legal scalar completion is `z_e=max(0,1-t_e)`. This minimum also respects
all same-station/direction nesting rows. For a clique with k events and RHS
k-1, continuous completion exists exactly when

`sum max(0,1-t_e) <= k-1`, equivalently `sum min(1,t_e) >= 1`.

Because all t_e are nonnegative, the latter is equivalent to `sum t_e>=1`:
if any term is at least 1 both hold; otherwise the two sums coincide. Thus
the plain box row is the **exact projection onto original variables** of
the scalar event definitions plus this one clique's LP relaxation. Taking
the same componentwise minimum satisfies all upper-count clique rows at once,
so the equivalence extends to the shared dictionary with multiple such rows.
EVENTS-only projects to the full original box and cannot by itself improve
the original-objective plain LP bound. Service links and product lifting have
additional variables in their premises and are outside this equivalence.

The automatic DFS stops as soon as a conflict appears. Its preceding prefix
of k-1 events was not deficient, and adding an event cannot reduce the vehicle
union. Therefore the first deficient set has union size exactly k-1. Threshold
weakening only enlarges eligibility, and each accepted weakening must retain
the conflict, so this equality is preserved. Every generated object is checked
for this property. The argument does **not** apply to an arbitrary manually
supplied clique with a larger deficiency, where the single reference box row
can be weaker than the scalar formulation's LP projection.

Binary event variables still represent the full logical forbidden orthant
at integer solutions; the box row alone need not exclude every integer point
in that orthant. Equal projected LPs do not imply identical MIP presolve,
branching, cuts, nodes or time. This explains why the representation-cost
control and the native comparisons remain necessary.

## Alternative projections

### Stronger projection onto existing service variables

Let A_i=min(max_k Q_k,b_i) and B_i=min(max_k Q_k,capacity_i-b_i).
For pickup use t_e=(A_i-P_i)/(A_i-q+1); for drop use
t_e=(B_i-Drop_i)/(B_i-q+1). The row sum_e t_e>=1 is globally
integer-valid: at least one event is false, its term is at least one,
and all other terms are nonnegative by the single-visit service caps.
An impossible event makes the row redundant; nonpositive denominators are
rejected. No new variables, native parameters or local-domain premises enter.

Since L_i=b_i-A_i and U_i=b_i+B_i, inventory balance gives
box_t_pickup = service_t_pickup + Drop_i/(A_i-q+1), and
box_t_drop = service_t_drop + P_i/(B_i-q+1).
Thus each service-projection row dominates its box row on the old F0 LP.
Dominance need not be strict after all other F0 constraints are imposed.

For positive A_i,B_i, the existing visit/mode perspective bounds imply
P_i/A_i+Drop_i/B_i<=sum_k visit_ki<=1. Zero-cap cases follow by removing
the corresponding zero quantity. The legal service-event minimum is
max(0,(P_i-q+1)/(A_i-q+1)) or its drop counterpart. It exceeds the
scalar minimum, satisfies service upper limits and visit bounds, and respects
nesting. To check scalar upper compatibility, maximize opposite service using
the perspective bound: the scalar upper is at least P_i/A_i, whereas the
service minimum is at most P_i/A_i (the drop argument is symmetric).
Therefore, for the deficiency-one generated cliques, the same clipped-sum
argument proves service projection is exactly the LP projection of the
service-linked dictionary plus clique rows **conditional on this F0 hull**.
This is not a claim for arbitrary routing formulations lacking that hull.

The v3 containment experiment independently checks the old F0 region against
every box row and solves the original objective once with service projection.
It separates algebraic dominance, actual feasible-region strengthening,
objective-bound improvement and measured MIP effects.

### Product lifting

For a valid row aY>=b in a complete canonical interval [l,u], the rows
`aW-l*aY-b*G >= -b*l` and `u*aY-aW+b*G >= b*u` are valid, since they
are respectively (G-l)*(aY-b)>=0 and (u-G)*(aY-b)>=0, with W_i=G*Y_i.
The existing bit-product model's zprod_i has exactly this integer semantics.
No new variable is needed. The original box projection is retained. Unlike
the underlying physical clique, these lifted coefficients are interval-scoped;
each whole-submodel build regenerates them with its actual l,u and records
both endpoints. A row proved using a narrower G interval cannot be reused
on a wider interval. This is a standard product lifting, not a novelty claim.

## Threshold decision oracle

The existing time oracle retains all stations, original arcs, load prefixes and
single service, while releasing original-T-derived bounds and arc deletions.
Threshold rows replace exact inventory fixation where requested. A cheap
clique can classify the original T without an optimizer; forced-native mode is
an explicitly charged cost comparison. Otherwise a native threshold-decision
callback stops tentatively at a bound above T+margin or incumbent Tstar<=T.
Only the finalized valid time bound or independently verified route determines
classification. Crossing intervals remain unknown. No required-time bound is
ever an original F lower bound or an original objective certificate.

## Relation to previously tested families

Round 61 fixed four inventories and encoded a bit no-good. Here an event fixes
only a service *lower bound*, and all other stations remain available. For the
user-specified D4 regression, the four forbidden-coordinate box has
`20*30*25*14=210000` integer combinations, compared with one four-coordinate
combination for the old exact no-good (both leave the remaining stations free).
This is a statement about the logical forbidden region; the cheap projection
does not cut every forbidden integer combination. Neither counts feasible
routings nor proves any LP bound gain.

The existing pair/triple support-duration covers depend chiefly on visit
support and minimal service. Threshold conflicts instead use specified service
amounts, direction and vehicle eligibility, then exclude a joint inventory
orthant. They do not replace those existing rows. Round 54 inventory-route
closure used directed net-inventory/load-flow inequalities and many closure
optimizations; this round has no closure optimizer and no such cut family.
Round 55 VD-P/VD-J expanded full inventory values and perspective states;
this round shares only a small selected threshold dictionary, or adds no
variables in projection/RLT modes. These differences identify mechanisms,
not a claim that one dominates the historical formulations.

Historical reports remain the authority for their own negative results:
[Round 53](../gf_k1_f0_callback_isolation_round53/final_report.md),
[Round 54](../gf_k1_am_sf_inventory_route_round54/final_report.md),
[Round 55](../gf_k1_am_sf_station_state_chain_round55/final_report.md), and
[Round 61](../gf_transfer_block_native_time_round61/final_report.md).
Their times are not used as same-build paired measurements in Round 62.

More specifically, Round 53 identified mixed callback regressions while
supporting F0's removal of the exhaustive historical subset-duration block;
we retain that F0 and do not reintroduce the removed block. Round 55 reported
inactive pair/triple covers in its 162 diagnostics, but removing them still
lost certificates or materially regressed cases. Their inactivity is not
permission to remove them here. Its stronger MC4/VD-J relaxations and mixed
full-K1 VD-P result also warn against using an LP-bound gain or fixed-domain
gain as a substitute for complete-algorithm protection. The old pre-fix epoch
cache trajectories are not timing controls in this round.
