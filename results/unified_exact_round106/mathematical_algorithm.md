# Round106 mathematical and implemented contract

This is a default-off continuation of R105 at delivery commit
8dc274eb34ee6d8a575f0b94b57ef04476efc0f1 (PR167). The underlying problem and
objective do not change. For positive S=sum(Y_i/D_i), G=sum(i<j)|r_i-r_j|/(nS)
and F=G+lambda sum omega_i|r_i-1|. The original evaluator uses G=0 when S=0;
the absolute shortage penalty remains. Targets are positive on this domain.

Each station receives at most one vehicle's single nonzero one-direction
integer service. Vehicles start empty, all load prefixes and return load lie
in [0,Q_k], and a loaded return is legal. Cumulative pickup may exceed Q_k.
Y_i=b_i+sum(d_ki-p_ki); sum Y=sum b-sum return_load. All original legal
inventory/total bounds remain. Duration is full closed travel plus
(c_pick+c_drop)*sum pickup, including depot unloading on return. Route length
is a feasibility constraint, not an additional objective.

## Assignment master and solution embedding

The original R105 global strengthened VD-P/F0 compact model is written with
gamma_L=0, gamma_U=min(1,U0) and a non-strict F<=U0 row (epsilon=0). U0 comes
only from this run's unchanged paid ENS startup and complete physical witness.
All original rows/bounds/objective remain. Only x arc binaries and load
integers become continuous. Y, state selectors, z, direction, p and d retain
their original integer declarations; order variables remain continuous. No
AM or new necessary-root processing is added. Every original solution with
F<=U0 embeds with its actual route arcs, load, order and exact inventory
objective; U0 itself embeds. Since there is such a feasible solution, no
better original optimum is outside this domain. Exported original.lp,
variables.csv, embedding.json and start.mst record the actual change.

## Conservative metric travel

The inherited strengthened-model metric domain is required. For each pair,
take the smaller of the two directed double arc values, round strictly
downward to integer milliseconds, and run integer Floyd closure. This closed
matrix is exactly symmetric/metric and every entry is <= its original
directed arc. Closure also avoids assuming rounded raw arcs still satisfy
triangle inequalities. Sums are range-checked; conversion back to seconds
and h=c_pick+c_drop use downward nextafter. Thus bounds are conservative for
the original model's route, even for nearly metric input accepted by the
inherited gate. The implementation uses T+1e-7 and a strict rejection margin
1e-5*max(1,T), in addition to reliable raw-row violation under the unchanged
native tolerances. No rounding changes the physical witness validation.

## A: dynamic MST support/handling row

For support S, a closed route visiting S induces a connected walk on depot
and S in the conservative metric. Its length is at least the minimum
spanning-tree weight L(S), computed by true Prim minimization. An arbitrary
tree or heuristic tour would not establish this lower bound.

The row is h_lower sum(S)p_ki + L(S)(sum(S)z_ki-|S|+1)<=T+1e-7.
If all S are assigned to k, closed travel>=L(S), and their handling is no
more than full handling, proving the row. If one is absent, integer z gives
the parenthesis<=0; the support's handling alone is <=full duration<=T.
No current obligation outside S or cutoff is used. The inequality need not
hold for the relaxed-route master and therefore uses lazy semantics.

The generator begins with the actual candidate's nonzero pickups and
deterministically deletes stations while reliable time impossibility
persists. It does not enumerate 2^V supports or branch on input size.
Where h, T and travel coincide, this proof transfers independently to
another vehicle regardless of Q. Its currently unviolated row stays in a
pool and is never blindly sent through GRBcblazy.

For actual C2 input SHA07d0964..., S={1,5,6,13,17,21}, pickups
(8,6,6,7,9,7), P=43. Independent unrounded MST=2387.254251416504s;
the produced conservative MST=2387.252s. With h=120,T=7200 this violates
by about347.252s. The source row contains six p and six z coefficients,
without the ordinary mode conflict's fourteen absence conditions. The
original complete legal startup remains in every generated row. The
subset-duration principle is inherited R51/R52; new work is candidate
extraction, sparse support, pooling and early integer-event use.

## B: one balanced-three-stop family

On every candidate and every car, deterministic quantity matching selects
triples of distinct nonzero services with both directions and P_S=D_S=P0.
All six closed orders are evaluated, with every integer load prefix and
full conservative duration. A single failed order or heuristic failure
cannot reject. L is the minimum travel over all six orders ignoring loads;
by metric shortcut this is a lower bound even when auxiliary stations are
visited. It is stronger here than the ordinary MST and is not imported
from an offline oracle or hardcoded station identifiers.

Only if all six orders fail and L+h_lower*(P0+1)>T+1e-7 plus strict margin
do we drop absence literals. An additional pickup costs at least one
integer unit. If additional services are only deliveries, empty departure,
nonnegative return and P_S=D_S still require an extra pickup. This is
impossible under the budget. Hence S's exact positive-group row needs only
its three ownership literals plus three exact inventory-state literals,
with RHS5.

The threshold lift requires the same three ownership literals and
Y_i<=b_i-q_i for pickups, Y_i>=b_i+abs(q_i) for drops. Each implies an
operation quantity at least its threshold. The budget bounds total pickup
by P0. All pickup thresholds must equal their prescribed amounts; total
delivery<=total pickup forces all delivery thresholds to equal, and all
outside service to vanish. We can then apply the complete six-order proof.
This is not a generic quantity-monotonicity claim or a Y-only no-good.

Actual F2 Q30,T3600,h120, services6:+9,7:-16,9:+7 give four prefix failures
and two unrounded feasible-prefix durations3629.3192304 and3795.7147314s.
Independent minimum unconstrained travel1661.135564s, produced lower1661.133s;
the seventeenth pickup unit is impossible. The threshold row is
z_k6+z_k7+z_k9+sum(y<=25)state_6y+sum(y>=21)state_7y+
sum(y<=24)state_9y<=5. Root-omitted states are fixed zero and removed from
the API row. Exact positive-group and threshold rows are generated
automatically. The ordinary F2 MST (~978.553s) cannot provide this budget.

Unbalanced P>D, h=0, non-strict budget equality, and incomplete order
proofs do not enter B. In the direct Euclidean square/helper counterexample
at T20,Q3,h2, the no-helper duration12+6sqrt(2)>20 but helper pickup1
permits0-A-H-B-C-0 with travel12, handling8 and return load1. The budget
equality L+h(P0+1)=20 cannot exclude it. The pure and independent checks
retain this boundary and original parser speed convention.

## One native master and precise event contract

One production master Optimize registers MIPSOL. A distinct inner model
environment uses the same DLL, serially, with Threads1, Seed0, PresolveAuto,
original feasibility/integrality tolerances and zero relative/absolute gap.
No Optimize is called recursively on the active master. Every inner
Optimize/IIS receives only the single process deadline's remaining time;
its callback can terminate on that same deadline. No per-car budget exists.

Every raw MIPSOL_SOL/OBJ/OBJBND is persisted and checked against all base
rows, bounds, integrality, unique service and Y/state/operation mapping.
Nonoptimal epigraph may exceed independent Ftrue; modelObj below Ftrue
beyond tolerance stops as ERROR. FULL and CORE disable A/B. STRUCT checks
own-run cache, uniformly scans all cars for A/B, and submits all currently
reliably violated proved rows before any new full oracle. Cross-car
unviolated rows stay pooled. GRBcblazy itself rejects a current solution;
API0 on an earlier event does not reject a repeated current candidate, so
violated known rows are re-submitted. There is no arbitrary repeat limit.

Without a rejection, unseen cars are checked in fixed order by the inherited
full optional-station physical MIP. A verified feasible route is sufficient.
Native status INFEASIBLE alone establishes INF; limit/no incumbent/ambiguous
status is UNKNOWN. CORE can propose semantic IIS groups, then must re-prove
the released template with all outside stations free. STRUCT fallback is
always FULL. A proved car can reject without waiting for other unknown
cars. UNKNOWN without any rejection interrupts safely; it is never cached
as INF. Numerical/API/evidence errors stop separately as ERROR.

Only all-car physical verification yields an own UB. Canonical mapping
audits every necessary column, base row and pooled proved row before
GRBcbsolution. Submission is only for improved physical UB or an unsubmitted
fleet. At MIPSOL GRB_INFINITY means deferred processing, not acceptance or
failure; attempted/API0/observed exact vector/final exact-vector acceptance
and external physical UB are separate evidence fields. Cache keys include
full operations and complete physical/numerical data; same Y with different
ownership is not a hit. All evidence is local to the current run/strategy.

Callback bounds are tentative until the post-return original numerical
and parameter gates. Final native bound is not admitted with an unresolved
candidate; only previously valid global bounds survive that interrupt.
Errors discard this run's new LB, retaining paid physical UB. Native
INFEASIBLE in a domain containing legal Start or LB>UB triggers ERROR;
no clipping is used. Original certification requires trustworthy global
LB to close with own complete physical UB at the original tolerance.

Master native runtime includes callbacks. Reports retain it inclusively,
then partition into master exclusive, callback oracle/IIS/core-confirm,
arithmetic separation, audit/mapping and callback other. Nested times are
never added again to the paid outer process fee.

## Fixed-Y diagnostic and evidence layers

The exact historical repeated C2 Y is separately frozen with four source
solution SHAs and distinct assignments. R61 full-fleet template fixes Y,
retains all original integer assignment/service/order choices, sets
Tstar<=originalT and objective zero. Existence is equivalent to an original
fleet for that Y: any such fleet embeds by Tstar=max duration; conversely
a model solution gives a fleet whose each duration<=Tstar<=T. There is no
Gini/cutoff or expanded physical-time optimization. One cap1200 including
reserve30 is frozen, no retry after UNKNOWN. Its witness, LB or conclusions
never enter a formal arm.

Pure arithmetic, scripted C-API contracts on audited actual vectors,
historical retained-model native replay, newly generated native fixture
events and complete production performance are distinct evidence layers.
The independent review uses its own Decimal/physical mathematics and
restored raw evidence without production A/B functions. Same-engine
qualification is not an independent-engine performance reproduction.

Official interface checks: [callback C API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html),
[callback codes](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html),
[solving C API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/solving.html),
[separate-model callback threading](https://support.gurobi.com/hc/en-us/community/posts/19512820944529-Number-of-threads-used-when-solving-a-model-within-a-callback).
