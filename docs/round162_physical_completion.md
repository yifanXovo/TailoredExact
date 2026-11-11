# Physical completion of the old shared-Gini products

Round162 keeps the original M-B/VD-P objective and penalty, and asks whether
the two inventory endpoints implicit in its shared G products can belong
to one common, bounded physical continuous subsystem. OLD+STOCK is the
direct baseline. This is a study of conditional physical consistency;
the endpoint hull, RLT operation and dual aggregation are established tools.
The [actual goal](../results/unified_exact_round162/goal.md) specifies the
evidence gates and finite experiments. The optional C++ executable and
its CMake switch are default off. Stable GI-TBC/B, E+ and the bare CLI
preserve their existing defaults.

## The declared physical polyhedron

Read the unpresolved native OLD+STOCK matrix. Register every column by its
exact writer grammar. The physical coordinates are arc x, visit/owner z,
service mode, pickup p, drop d, load, order, connectivity flow, final
inventory Y and inventory state selectors. All their original finite
bounds are included. An original row belongs to Q exactly when its entire
nonzero support is in these coordinates. Thus

\[
 Q=\{X:AX\le b,\ EX=f,\ \ell\le X\le u\}.
\]

The original G, state_g, zprod, r, e, h, r_min, r_max and W_SP coordinates
are auxiliary coordinates outside X. Their rows, types, objective and
bounds remain in the outer model. In particular e has finite original
bounds: excluding it defines this study's object. No penalty mechanism
is changed. Q is this specified subsystem, rather than the exact
projection obtained by eliminating all objective auxiliaries or an
integer fleet hull. Unknown columns are rejected instead of ignored.

The physical rows cover route/depot degrees, nonzero one-way ownership,
empty departure, load propagation and loaded return, complete travel and
handling time, connectivity, inventory balance and selector--Y/service
links. Inventory-only consequences of the current common interval/cutoff
can be present because they already occur in this same original matrix.
There is no endpoint-specific propagation. The two copies use identical
loaded A, b, E, f and boxes.

With B the sum of station initial inventories, empty departure and final
return loads R_k give sum Y=B-sum R_k, 0<=R_k<=Q_k. Therefore
max(0,B-sum Q)<=sum Y<=B. The depot inventory is excluded. The original
writer stores the B-sum Q lower row; nonnegative Y supplies the max with
zero when needed. Cumulative pickups can exceed capacity, while every
prefix load remains bounded. Complete handling is

\[
 t_p\sum_i p_{ki}+t_d\sum_i d_{ki}+t_dR_k
 =(t_p+t_d)\sum_i p_{ki}.
\]

This explains the original writer's pickup coefficient in its complete
vehicle-duration row, including unloading at the depot.

## Endpoint hull and integer preservation

For L<=G<=U, consider V=GX. If L<U, introduce nonnegative lambda_L and
lambda_U summing to one, with G=L lambda_L+U lambda_U. Introduce scaled
copies xi^L and xi^U, and require

\[
 X=\xi^L+\xi^U,\qquad
 A\xi^e\le b\lambda_e,\quad E\xi^e=f\lambda_e,\quad
 \ell\lambda_e\le\xi^e\le u\lambda_e.
\]

Only the coordinates whose moments are already in OLD need product links:

\[
 state\_g_{iy}=L\xi^L_{state_{iy}}+U\xi^U_{state_{iy}},\qquad
 zprod_i=L\xi^L_{Y_i}+U\xi^U_{Y_i}.
\]

Here zprod is GY, not GY divided by the target. Every new column is
continuous with objective zero. Original types are relaxed for capacity
LPs and retain their original types in MIPs.

Necessity follows by choosing xi^e=lambda_e X for a graph point and
taking convex combinations. Conversely, when both weights are positive,
X^e=xi^e/lambda_e belongs to Q. The extended point is the convex
combination of (X^L,L,LX^L) and (X^U,U,UX^U). If a weight is zero, the
finite perspective bounds force its entire xi vector to zero. This
establishes endpoint closure without dividing by zero. Equivalently, for
L<G<U, the conceptual moments give

\[
 X^U=(V-LX)/(G-L),\qquad X^L=(UX-V)/(U-G).
\]

Thus the complete extension is conv{(X,G,V):X in Q, L<=G<=U, V=GX},
projected onto the old moment coordinates when the other V are omitted.
For L=U, directly impose each existing product equal to L times its
physical coordinate and introduce no endpoint weights/copies.

The endpoints are continuous points in Q and can contain fractional
routes, owners and selectors. They are not integer fleets and their true
Ginis need not equal L or U. G is the original epigraph variable. Every
original integer solution, including one with a nonminimal epigraph,
extends with the same X at both endpoints. The attached model therefore
preserves all original integer solutions and the original optimum.
Neither positive total inventory nor positive G is needed.

The original coefficients are copied, without forming L*A or U*A.
New endpoint boxes are min(0,ell)<=xi^e<=max(0,u); perspective rows tighten
these boxes with lambda. New rows with exceptionally small coefficients
receive a positive power-of-two scale. Native write/readback must retain
every old column/row and every new coefficient exactly. An initial tiny
failure exposed rounding by GRBwrite's human-readable LP serializer;
the final implementation writes all loaded binary64 values with 17
significant digits and checks exact readback. Failure evidence is retained.

## STOCK containment and a sufficient no-increment condition

Let s=sum Y and z=sum zprod. Lifting the two total-stock bounds at the
high endpoint yields Bminus(G-L)<=z-Ls<=B(G-L). Lifting them at the low
endpoint yields Bminus(U-G)<=Us-z<=B(U-G). These are the four STOCK
inequalities before its outward RHS rounding. If Bminus=0 is supplied by
nonnegative Y, its perspective bound has the same implication. Therefore
full Q implies the qualified STOCK rows. STOCK remains explicitly in both
arms for a fair direct comparison.

If an optimal S point satisfies state_g=G*state at every supported state,
the original links also give zprod=GY. Taking xi^e=lambda_e X completes
it without changing the original objective, so full Q has no LP increment
in that scope. The original complete VD-P forces this consistency at
G=L or G=U. In particular G=L=0 satisfies this condition. This explains
why conditional continuous physical completion cannot remove every
zero-G integer-objective/Jensen gap from R133. A positive G and nonzero
product residual are opportunities to test, rather than a proof of gain.

The condition is sufficient, not necessary. An S optimum may fail fixed
completion and still be replaced by a different F optimum with the same
original objective. Round162 observes precisely this distinction on RX35.
No claim extends a root no-increment observation to all subintervals,
instances or integer searches.

## One objective-specific projected row

Split F's rows into baseline rows and new extension rows. An optimal LP
dual in exact arithmetic aggregates the latter, together with the new
variables' box contributions, into one valid inequality on the original
variables. Adding that inequality to the same baseline preserves the
source objective optimum. The statement concerns this objective and
scope; it is neither a full projection description nor an integer hull.

The implementation uses the actual loaded row sense. A minimization
dual is nonpositive for <=, nonnegative for >=, and unrestricted for =;
wrong-sign numerical components are clipped to zero. Normalize every
used row to <= with nonnegative weight. Let the exact aggregate be
a_x*x+a_y*y<=beta. Setting all new coefficients to zero is valid after
adding max_box(-a_y*y) to the RHS. Rounding the original coefficients to
c_x adds max_box((c_x-a_x)*x). Outward interval arithmetic encloses these
supports, including explicitly removed tiny coefficients. Independent
offline rational arithmetic checks the final direction and slack using
the actual binary64 matrix and multipliers. Physical original terms are
kept; the old RN-name-only projector is not used.

For NB35, free S/F/C values are .382633909653361,
.382821159444977 and .382796814406686. The one row keeps about 87.0% of
the observed full-Q increment. Its 5,348 terms include original arcs,
connectivity, visits, quantities, load/order, Y, selectors, G and zprod.
The eliminated-column box support is about 2.0305184692e-5. No new column
is present in C. Exact independent dual-box readback still gives an
original-J increment of at least .000162904753285 over the saved S point.
This is finite retained information, not yet evidence of complete
algorithm value.

## Source evidence and the role of complete time

The two 35-station parents are fixed, identity-complete offline own-H/R83
inlets inherited from R160/R161. Their reuse is development input, not
a fresh full algorithm. All original variables freely reoptimize in S
and F. Both saved S optima fail the fixed-point completion diagnostic.
RX35 nevertheless reaches .193136114218839 in both free models. NB35
has the positive increment reported above. Actual primal/dual registries,
LP/MPS, scope, residuals, statuses, Work/iterations and outer fees are saved.
Numerical closure is reported at the inherited tolerance, not as exact
algebraic equality of computed floating-point optima.

There is one semantic ablation: omit only the two endpoint copies of
each original complete vehicle-duration row, retaining those rows in
the original outer model and retaining every other endpoint condition.
The C++ code recognizes this family by its entire exact writer expression,
not a row-name heuristic. On NB35 this relaxed extension returns
.382633909653361, the S value. Thus, conditional on all the other Q
information, the lifted complete travel/handling budgets are necessary
for this observed increment. This does not establish that any one time
row alone suffices or that time is the only physical interaction. No
row-family combination scan is performed.

## Finite algorithm experiment

The predeclared primary-positive branch uses RX35 and NB35, S versus C,
one 900s outer clock per arm, 4,096-node development capacity and
Seed0/Threads1/MIPFocus0. C rebuilds and solves a fresh full-Q source,
projects once, releases the temporary source, and uses the remaining
same deadline for Native search. S has no source to pay. Both use the
same original parent, Start, complete root scope and STOCK. Source lower
is diagnostic; it does not enter the formal proof ledger as a new scalar
floor. These calls are whole-native development experiments, not the
full GI method or P-GRB. The completed search decision and conditional
full panel are recorded in the final research report.

## Frozen complete-method integration

The complete research family is `--round162-physical-completion off|stock|on`.
The default is off. The stock and on modes both use the same R138 four rows
at every applicable LP/MIP; on adds one once-initial-root full-Q source.
It requires the existing GI-TBC ms2 controller and the unchanged, self-paid
E+ RN16384 proof-only inventory helper. The R160 neighborhood, RN replacement,
old RN source and asymmetric STOCK placement are disabled. All inputs use
this same recipe. No instance-name, scale or elapsed-time rule chooses a
different mechanism.

The initial complete OLD+STOCK root is copied into a disposable source model.
The backend captures its actual primal, row duals, status, finalization and
quality evidence. Only a terminal optimal source with the inherited evidence
qualification can produce a PC row. After compression the backend is released;
only one original-variable row and its scope remain. Its lower is saved as a
diagnostic and never enters the formal proof ledger as an extra scalar floor.
The formal proof continues to combine the existing qualified interval cover,
actual LP/MIP bounds and the independently paid E+ helper. No source primal is
installed as a Start or incumbent.

Each later model receives the row only within the same input and covered
cutoff/G interval, selector support and coefficient boxes. A selector missing
from a narrower legal support is exactly zero; no missing physical term is
dropped. Each installed model receives a new file hash and row signature, so
an old backend model cannot survive under the old cache identity. Actual Native
readback checks one registered PC row, original columns only, and unlimited
NodeLimit. The development 4096-node capacity is not inherited.

The old helper's placement reader needed a narrow compatibility adapter:
actual row/column comparisons prove that a temporary source contains the
unchanged baseline, and that a formal PC model differs by exactly the audited
PC row. These identities are used only to check that the helper adds zero
Native floor rows. Raw model hashes, journal observations and the formal proof
collector are never rewritten. The stock control has the same proof-only
helper and no physical source.

Short complete PC/Stock qualification runs use fresh H and helper and are
explicitly excluded from performance evidence. The first PC post-reader
rejected an inherited STOCK metadata assumption; correcting that pure reader
and re-reading the sealed run required no repeat solve. A separate C++ scope
test verifies a covered child with the full original integer Start and rejects
a one-ULP larger cutoff, using saved source evidence and zero Optimize calls.
The incomplete engineering build v1 is invalidated before any scientific
launch; every qualified complete call uses the stable v2 PE and exact retained
source bytes. Complete results and their production/verification costs are
reported separately from these interface checks.

## Attribution and limits

The mathematical tools follow Balas (1985),
[Disjunctive Programming and a Hierarchy of Relaxations for Discrete
Optimization Problems](https://doi.org/10.1137/0606047), Sherali and Adams
(1990), [A Hierarchy of Relaxations between the Continuous and Convex Hull
Representations for Zero-One Programming Problems](https://doi.org/10.1137/0403036),
and Sherali, Adams and Driscoll (1998), [Exploiting Special Structures in
Constructing a Hierarchy of Relaxations for 0-1 Mixed Integer
Problems](https://doi.org/10.1287/opre.46.3.396). Their publisher abstracts
were checked. R62 already applied Gini-RLT to finite physical conflicts;
R138 already established shared-factor endpoint convexification for
selected resource blocks; R143--145 already studied objective-specific
one-row compression. The new question is the particular common full-Q
completion condition beyond STOCK and its measured cost/value in this BRP.
The history table records the remaining boundaries. The limited roles
and one Seed cannot support a claim of stable superiority to P-GRB.
