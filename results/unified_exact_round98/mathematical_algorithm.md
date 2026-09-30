# Shared inventory state and service reconstruction

This preliminary proof is frozen before performance selection. Original physics,
VD-P upper epigraph G, true-G embedding, cutoff complement, full leaf coverage,
AM targets/finite control, numerical contract and distance restrictions are
inherited from R96/R97 mathematical_algorithm.md. The new local algebra needs
no distance assumption; this does not extend the whole ENS/F0 validated scope.
Code target[i] is mathematical D_i; d_k_i is operation delivery; mode_k_i is m.
state_i_y and state_g_i_y are s/q, zprod_i is Z=GY at integer states.

## Actual baseline and history

R0 contains binary z/m/s, integer p/d/Y/load, ∑k z<=1, quantity visit bounds,
mode perspective bounds, p+d>=z, inventory balance, route/load/time/flow and
the existing VD-P Y/G/Z block. Thus integer solutions already imply A/B.
Existing visit/inventory envelopes do not reconstruct expected movement and
visit from the same s. R55 proves isolated Y/G/Z hull and VD-J ratio/minimum
penalty reconstruction; R62 studies threshold service coupling and conflict
projections with a continuously completable service-only dictionary. Neither
is this joint all-state P/D/v block. R66 shows why exact row elimination and
implied integrality need full-run evidence despite equal LP projection.

## A/B and local hull

The original physics remains Y_i=b_i+sum_k(d_ki-p_ki), r_i=Y_i/target_i,
S=sum r_i, H=sum_(i<j)abs(r_i-r_j), true Gini=H/(V*S) for S>0 with
the inherited zero-S convention. F=true Gini+lambda*sum_i weights_i*abs(r_i-1).
Each station has at most one nonzero single-direction service. Vehicle k
departs with load0, every route prefix has load in[0,Q_k], and the return load
may be positive. Quantity/time convention remains
travel+(pickup_time+drop_time)*sum pickup<=T. These local equations neither
bound total pickup by Q_k nor conserve total station inventory. Mathematical
T is separate from the experiment's whole-process cutoff.

For nonnegative quantities, balance gives D-P=∑(y-b)s. A gives
P+D=∑|b-y|s. Adding/subtracting yields exactly
P=∑(b-y)+s and D=∑(y-b)+s. B gives v=∑(y!=b)s.
When b is absent no fake state is created and v=1. A singleton b fixes no
service; another singleton fixes one integer nonzero operation. Empty domains
retain the existing infeasible-domain contract.

At an integer physical point choose its unique inventory selector and q=Gs.
All new rows hold. Conversely integer selectors choose y; the original
quantity/route constraints and A/B recover the same physical service.
The isolated joint (Y,G,Z,P,D,v) hull follows standard disjunctive convexification:
for each s_y>0 use G_y=q_y/s_y in[l,u]; s_y=0 forces q_y=0. Every feasible
extension is the convex combination of the corresponding state segments;
every such convex combination is an extension. This excludes vehicles/routes,
other stations sharing G and their global correlation. No BRP ideality claim.
The b10/states8,12 example demonstrates a local common-coordinate distinction,
not feasibility in the complete existing LP.

## Exact direction projection and implied operation integrality

The only mathematical mode usages in the active writer are m<=z,
p<=a*m and d<=c*(z-m), with ACTUAL a=min(b,Q_k),c=min(C-b,Q_k).
Positive a/c admit a continuous m iff p/a<=z-d/c. R2 emits
c*p+a*d<=a*c*z with double multiplication, preserving p<=a*z,d<=c*z.
If a=0, p=0 and the delivery visit bound remain; choose m=0. If c=0,
d=0 and pickup visit bound remain. Both zero choose m=0. No divide-by-zero
or degenerate product can discard the remaining bound. No tighter domain
coefficient is substituted under a claim of pure elimination.

With integer s/z, A/balance give integer P/D and one nonzero direction.
B/∑z<=1 and nonnegative quantity visit bounds force all but the unique selected
vehicle's quantities to zero. Thus that vehicle's p/d equal the determined
integers, including heterogeneous Q and initial/absent/singleton states.
Its old binary m can be recovered as1 iff pickup>0, otherwise0. Routes,
prefix capacities, empty departure and loaded return remain unchanged.
Y/load types remain integer. Native continuous p/d must still pass their
PHYSICAL integrality check, finite/bounds and the independent Evaluator.

All-continuous R1 and R2 project equally on common columns by the above
continuous m recovery, including zero cases. A differing optimal raw LP
value outside the numerical contract is a qualification failure, not evidence
of new strengthening. Native presolve/cuts/branching/time may differ.

Counterexamples: C alone allows z1,p=d=.5; integral mean Y10 with
s8=s12=.5 is not a unique state; relaxed z with two z=.5,p=.5 at y9
does not imply integer operations. Removing any other m usage would need its
own projection proof. Eligible vehicle-state pairs do not prove route existence.

## Production mapping and certificate scope

Start construction loops actual model columns: removed mode keys in its
temporary dictionary do not create submitted columns. Integer witnesses map
unchanged to state/q and route/load; full actual-row checks remain required.
R98 decoder checks ALL p/d, including unvisited columns, against inherited
1e-5 integer tolerance before int conversion. Old paths are untouched.
Complete ordered LP SHA/row_signature binds new rows/types/columns; native
reuse is artifact/epoch scoped. Cutoff changes rebuild the state domain through
the existing epoch invalidation. No matrix or old column order is reused across
identities. New LP bounds may alter AM outcomes; full runs include that effect.

At a legal original witness the final integer inventory chooses s=1, its q=G,
all other s/q=0, actual route p/d/z/load unchanged. For a restricted leaf use
the inherited legal true-G epigraph embedding inside its certified domain.
At a new integer selection, A/balance force the appropriate one-direction
quantity and B selects exactly one vehicle unless y=b. Old m is1 for pickup
and0 for delivery/unvisited; if both direction caps vanish choose0. This
constructs an old original feasible witness and identical original objective.
It does not require preservation of irrelevant old auxiliary assignments.

The new constraints preserve every legal original embedding in each valid
cutoff/interval, and remove no physical witness from the union coverage. The
inherited cutoff complement therefore remains valid. A LP/MIP leaf bound
still requires the original numerical acceptance, actual interval identity,
cutoff witness and complete current G-domain cover before global promotion.
In particular G is an epigraph variable at arbitrary leaf points; the hull
proof never replaces epigraph feasibility by G=true Gini. Unfinished optional
LP points, fractional decoded operations, unclosed coverage and restricted
fixed-route optima never become whole-original certificates.

## Literature and novelty limits

Joint finite-state convexification uses standard Balas disjunctive programming
(1979), https://www.sciencedirect.com/science/article/pii/S016750600870342X .
Projection by interval existence is ordinary continuous elimination. Implied
integrality is established presolve theory; see the original research paper
https://arxiv.org/abs/2504.07209 . Gurobi presolve also transforms representations:
https://support.gurobi.com/hc/en-us/articles/360024738352-How-does-presolve-work .
The research contribution can only be this project's actual joint linkage,
exact production simplification and measured full-solve effects. None of these
standard principles, a local hull or a smaller generated model is sufficient
by itself for an originality or performance claim.
