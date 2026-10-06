# Round104 independent gate review

Reviewer: a separate read-only agent, commissioned by the execution agent under
the user's explicit two-review request. Review date: 2026-10-06 (Asia/Shanghai).
This first review permits the finite-pool expression prototype and the bounded
original-ENS observations. **Expansion to complete candidate campaigns is
pending actual same-scope diagnostic evidence.** No native performance result
or production candidate is approved by this static conclusion.

## Scope and methods

Read the user's Round104 request; Round104 `mathematical_algorithm.md`,
`protocol.json`, `baseline.json`, setup and receipt scripts; Round103
`final_report.md`, `capability_table.md`, `mathematical_algorithm.md`,
`independent_review.md`, `reproduce.md`, `RESUME.md`, production freeze and
complete-pair/cost CSVs. Inspected the actual finite-pool loop and point-source
mapping in `scripts/round103_capacity.py`, `round103_points.py`,
`round103_hull.py`, the R102 support/native-point readers, and production
`src/Round103GurobiHull.inc`, `ServiceResourceHull.cpp`,
`ServiceResourceCuts.cpp`, and their contracts. Read real F2/C2/F5 capacity
plans and the F2 production contract/summary. Targeted source searches found
no matching objective-dual resource-pool compression in these implementations.
This is a bounded source review, not a proof that no historical experiment
anywhere used LP duality.

The reviewer executed only text/source reads and searches and wrote this review.
No Gurobi import or model read, Optimize, DP/support computation, build, native
search or performance run was performed. No production source was changed.
The reviewer has not independently repriced all historical rows, proved full
rational LP optimality, replicated native runs, or audited all historical raw
metadata. The inherited measured source/PE are reported identities, distinct
from this mathematical review and from the later delivery head.

## Mathematical gate

The stated exact theorem is correct under its stated feasible, bounded,
attained optimal primal/dual assumptions. For a minimization LP, a new
`<=` row has Gurobi `Pi <= 0`; the nonnegative Lagrangian multiplier is
`lambda = -Pi`. This sign convention applies to the mapped new rows only.
Equalities have unrestricted dual multipliers; old `>=` rows use the opposite
Gurobi sign. Taking absolute values of every Pi would not be a valid argument.

For completeness, retain the exact old certificate, including all old row,
free equality and variable-bound terms and the objective constant `c0`.
Its new-row Lagrangian contribution is
`sum(lambda_j * (a_j^T x - b_j)) = abar^T x - bbar`.
Assigning multiplier one to the aggregate gives exactly the same Lagrangian
and dual lower value `LC`, so every aggregate-feasible point has objective at
least `LC`. The full-pool optimal point satisfies the aggregate and gives
objective `LC`, proving the reverse inequality. Old constraints and bounds
must remain present. The proof therefore includes the objective constant and
bound/equality contributions even when these supply most of the certificate.

Keeping just the exact nonzero new dual support has the same argument.
Partitioning that support into groups and assigning multiplier one to each
aggregate also preserves the certificate. If all new multipliers are zero,
the retained old certificate already proves `LC`; omit the zero aggregate.
Degeneracy permits several different supports and does not make the support
unique or establish that it is smallest. An arbitrarily truncated small
multiplier is not an exact zero. Float Pi can choose a valid nonnegative
combination, but it is not automatically an exact optimal dual certificate.

The branch-weakening counterexample is correct. A fully explicit MIP version
avoids the loose phrase "unrelated binary variable": let `x,y >= 0`,
`z in {0,1}`, retain old row `x >= 2z`, minimize `x+y`, and compare the valid
pool `x >= 1, y >= 1` against `x+y >= 2`. Both root LP values are 2. In the
descendant `z=1`, the full pool has value 3 and the aggregate has value 2.
The aggregate can therefore lose later bounds while preserving the root
objective. A single aggregate algebraically resembling the objective in this
example is an illustration; production must aggregate the actual resource
rows rather than insert `F >= LC`.

The numerical RHS compensation is correct. If exact aggregate coefficients
are `abar`, submitted binary64 coefficients are `ahat`, and old globally
valid bounds are `LB <= x <= UB`, define `delta_i = ahat_i - abar_i`. Then
`delta^T x <= sum(max(delta_i*LB_i, delta_i*UB_i))`. Any outward represented
`bhat` at least `bbar` plus that exact sum preserves validity. This handles
negative coefficients, negative bounds and coefficient deletion. It requires
finite valid endpoints wherever `delta_i != 0`, and exact or outward-enclosed
products/sums; an infinite Gurobi bound sentinel is not a finite mathematical
endpoint. Exact unchanged coordinates need no correction. If a parser drops
an emitted coefficient, use the *actual readback* coefficient in this formula
or reject the row. Overflow, unsupported bounds, or nonfinite values require
an explicit failure/UNKNOWN, not an uncertified RHS.

Safe compensation can weaken the exact certificate. Reoptimizing the emitted
model and preserving the signed objective difference is therefore mandatory.
Record primal row/bound residuals and dual stationarity/sign/complementarity
or a correctly reconstructed dual objective/gap with old bounds and `c0`.
Residuals qualify a numerical optimum; they do not manufacture a rational
optimality theorem. Wrong-sign/nonfinite new Pi must be recorded and cannot
silently retain an "exact preservation" label. A repaired nonnegative
selection remains only a candidate until its actual LP is solved.

Repricing the aggregate direction on the complete necessary domain can lower
its RHS relative to weighted RHS addition. It is valid strengthening, and
can improve a finite-pool objective, not equivalent compression. No valid
support can raise an *exactly solved* full-hull minimization optimum above
that full-hull optimum. R103 within-tolerance closure and F5 UNKNOWN do not
establish those exact premises. The score/dimension/traceback limits in the
actual support implementation must remain honest UNKNOWN; an attaining plan
by itself establishes only a support lower bound.

## Inherited information and scope findings

The inherited facts support a distinct compression question, not another
anchor/direction sweep. F2's raw numerical bound 0.528625649465355 rises to
0.638005040404497 under its 827-row, 456-outer-LP necessary-domain diagnostic.
The production H pass submitted two rows, not that closure. C2 closes within
the declared tolerance at 0.16123605049876005; F5 retains UNKNOWN and narrow
numerical upper/lower evidence near 0.244169448027537. Neither can be described
as strict equality. Three-anchor masks gave no meaningful objective benefit.

The actual F2 raw capacity source is SHA
`a37e2165fb900bb0d26d9158b89ade883202049456b7d1c6180f361070638091`;
the inspected paid production H contract has the same source SHA and the
scope `complete_original_compact_milp_intersected_with_static_gini_interval`.
This permits a qualified F2 `Lpass` from its two *actual* H rows on that
source; it does not permit replacing `Lpass` by R102's `LJ`. Corresponding
C2/F5 scope/source matching still needs the new diagnostic's recorded audit.
Raw C2 uses SHA
`41aacb59acd6bbb72cc56c9840a2ea0e47e0aad47a45304ad981bbd139a049bc`;
raw F5 uses SHA
`813d3f1b8e0cb890daf11432695dd01474b0acd383ae43581b21b707281472b7`.
Interval, cutoff, objective sense/constant and full typed matrix remain part
of scope in addition to the physical resource contract.

**Important historical qualification:** `round103_points.py` maps its
`kind='native'` points to Round102 **J-SUBMIT** arms. The inspected
`diagnostics/F2_native01/plan.json` explicitly names
`round102/protection01/raw/02_F2_J-SUBMIT/...round102.point.json`.
The other mappings are likewise J-SUBMIT. These full vectors are genuine
points from those modified runs; they are not original ENS observations.
The R103 capability table's "first native" classifications must not be
reused as evidence that original ENS still offers the same opportunity.

The production implementation obtains the standard raw LP once, classifies
each vehicle and emits its first reliable separation row. Its distance-master
dual is not the old objective LP's dual for a generated resource pool. The
R104 target changes what proof information is selected and retained and is
therefore not an exact repeat of R103, provided the actual objective pool and
native opportunity are tested. Mere compression of historical bytes or a
new switch without these tests would not establish the requested increment.

R103's negative results remain material: F2 H certifies in 634.859s versus
ENS 575.672s and contemporary J 523.297s; C2 is worse than both references at
the late budget; C3 and H2 regress against ENS, whereas N2/H1/F5 have budget
benefits. Most arms are jointly unproved, so their eventual certification
ordering is unknown. Existing gains do not establish broad certification
advantage. ENS-C remains the protected default.

## Evidence required before expansion

1. Use one legitimate SHA-bound finite pool per selected raw scope. Record
   `L0`, actual-H-row `Lpass`, `LC`, historical `LH` with its tolerance or
   UNKNOWN qualification, row map, signs, nonzero Pi support, coefficient
   scales and generation identity. Re-solve ALL, ACTIVE and GROUPED on the
   exact same old matrix/objective; record the actual signed differences,
   dimensions, sparsity and full primal/dual qualifications. F2 and at least
   one C2/F5 zero-objective role are required. Historical generation cost is
   shared only in this expression diagnostic, never free algorithm timing.
2. Observe original ENS's first qualified root, available later root and
   necessary positive-node full vectors under the actual source identity.
   Save the full column residuals, interval/cutoff and scope. Evaluate actual
   pool and compressed rows with reliable signed activities. Label the last
   observable root exactly so; do not assert it is the solver's final internal
   cut closure. Point objective, node LP value and global LB are distinct.
3. A reliable OUTSIDE point can justify one finite opportunity control; it
   does not prove useful objective or complete-solve gain. If the native
   point is reliably separated only by zero-dual/nonselected rows, that is
   evidence that root objective compression discarded information relevant
   after native processing. Compare ACTIVE/GROUPED on the same generated
   pool before opening another family or fitting thresholds.
4. For an expandable candidate, show meaningful new information at original
   native stages beyond F2's historical raw effect and a feasible unified
   self-paid generator. Keep C2's P disadvantage and F5/H2's medium-large
   role in development. A faithful complete SHADOW and P/ENS/candidate costs
   must precede any adoption conclusion; native paths after submission differ.
   Only then freeze two unused roles and the authorized common long windows.
5. A native LB above historical `LH` is only a numerical ordering. It does
   not show that native cuts imply the necessary hull or exclude synergy.
   Conversely, raw root preservation is not evidence of native gain.

An explicit stop is justified if qualified compression preserves the actual
finite-pool proof but the observed original-ENS root/later/node points offer
no reliable useful submitted information on the decisive medium-large roles,
or one informative control shows that paying the generator overwhelms the
available increment. If point separation survives but its practical relevance
is unresolved, execute one bounded informative control rather than either
declaring success or expanding to a mandatory large matrix. A short no-gain
test alone does not satisfy this stop. Any stop remains limited to the
single-vehicle necessary-resource scheme and does not negate stronger route
or cross-vehicle integer structure.

## Current disposition

Exact mathematical prototype: passes this scoped static review. Numerical
implementation, real-pool target preservation, original-ENS information
increment and complete end-to-end cost: **not yet reviewed**. The protocol's
P benchmark, ENS protection, honest numerical status, whole-algorithm deadline
and cost limits are consistent with the request. The source identity/default
rules inspected here do not authorize unqualified production reuse or any
automatic stacking. Add the actual diagnostic-gate conclusion to this file
once those artifacts are available, with its inspected paths and limits.

## Finite-pool evidence addendum (same review, before native gate)

Read execution-team artifacts `diagnostics/pool_F2_02`, `pool_C2_02`,
`pool_F5_01`, their plans, ALL/ACTIVE/GROUPED/FLEET records, saved dual support
and the actual `scripts/round104_pool.py`. This is inspection of saved real
LP results, not an independent Optimize or full-matrix numerical recompute.
The SHA-bound pool reader verifies original and compressed historical pool
bytes; it does not newly establish the support maximum of every old row.

| Role | RAW | Actual H rows replayed on RAW | ALL | ACTIVE | GROUPED | Pool / active / grouped rows |
|---|---:|---:|---:|---:|---:|---|
| F2 | 0.528625649465355 | 0.528625649464638 | 0.6380050404075234 | 0.6380050404058131 | 0.6380050403233034 | 827 / 30 / 2 |
| C2 | 0.16123605049876005 | 0.16123605049876008 | 0.16123605049876008 | 0.16123605049876005 | 0.16123605049876005 | 133 / 0 / 0 |
| F5 | 0.24416944802555995 | 0.24416944802753737 | 0.24416944802753754 | 0.24416944802555995 | 0.24416944802555995 | 82 / 0 / 0 |

F2 ALL/ACTIVE/GROUPED have 13015/319/69 nonzeros. Its fleet diagnostic has
one row, 69 nonzeros and value 0.6380050388956274. Signed differences from
ALL are ACTIVE `-1.7102985694350537e-12`, GROUPED
`-8.42199643358299e-11`, FLEET `-1.5118959417748101e-9`. The real pool has
substantial objective information beyond the actual two H rows, and few
resource rows retain it to the observed numerical precision. That establishes
the requested real-pool compression phenomenon, without an exact rational
claim or a claim of native value.

An important qualification is present in the raw saved Pi: F2 ALL has 12
positive new-row Pi values, largest `1.2971981631657845e-10`. The Python
diagnostic checks an explicit small sign-residual envelope and uses
`max(0,-Pi)`. Its 30-row ACTIVE includes eight strictly positive multipliers
smaller than `1e-8`, so it did not prune small correctly signed multipliers.
Nevertheless this is **a numerically repaired nonnegative selection** followed
by reoptimization, not the exact optimal-dual-support theorem. The signed
wrong-sign values must remain disclosed. The C++ `resourceMultiplier` instead
rejects every positive Pi; these behaviors must not be conflated under a
single qualification label.

The recorded F2 ALL primal residual is `3.4155434036620136e-10`, stationarity
residual `4.812377616067433e-12`, and primal-minus-dual value
`9.528568267747062e-9`. GROUPED has primal residual
`3.497202527569243e-14`, stationarity `1.263797294369684e-12`, and
primal-minus-dual `2.4101410756038888e-8`; FLEET's latter is
`1.1455956272499179e-7`. These certificate residuals are larger than the
small observed compression objective differences and must accompany them.
ACTIVE's primal-minus-dual difference is `2.4550250721233624e-11`.
These are adequate numerical evidence of large retained F2 objective gain;
they do not make all reported digits a certified exact lower bound.

C2/F5 have zero new Pi in the selected ALL solution. Their compressed models
correctly emit zero rows. C2 GROUPED-minus-ALL is
`-2.7755575615628914e-17`; F5's is `-1.97758476261356e-12`.
F5 RAW and the empty compressed models have primal-minus-dual difference
`1.0160027882899492e-7`, while F5 ALL has
`9.262035582935368e-14`. The tiny signed objective shift cannot establish
strict full-hull equality or override historical UNKNOWN. Zero new Pi
concerns this returned old-objective certificate, not whether all pool rows
are redundant as feasible-set constraints or useless in descendants.

F2 and C2 H production source SHA match their raw source SHA. F5's actual
H rows originate from production canonical SHA
`6493bd9b60e94124f4d43bbd55d0a20a5650e65867a114db78d1386815ac9f19`, whereas
the raw diagnostic source SHA is
`813d3f1b8e0cb890daf11432695dd01474b0acd383ae43581b21b707281472b7`.
The script checks identical all-station necessary resource contracts and
replays the actual globally valid H rows on the unchanged raw model. This
is a qualified transferable-row `Lpass` diagnostic, not the objective
attained in H's original production LP scope; state both identities.

Also read the standalone C++ primitive `include/ObjectiveResourceCompression.hpp`
and `src/ObjectiveResourceCompression.cpp`. Nonnegative grouping, scope
rejection, signed interval coefficient/RHS accumulation and endpoint
compensation are sound under their arithmetic/bound assumptions. These
interval aggregates are a different numerical representation from the
Python exact-Fraction, power-of-two-scaled diagnostics; their emitted rows
still require their own actual readback and qualification.

Two engineering requirements were sent to the execution agent before using
this primitive: detect subnormal/flush-to-zero behavior as the inherited
support code does, since IEEE type metadata and nearest-rounding mode alone
do not ensure gradual underflow; and require globally valid finite
mathematical bound endpoints rather than treating Gurobi's finite numeric
infinity sentinel as a valid bound. The current standalone signature makes
the supplied global-bound contract the caller's responsibility. No production
integration, compiled numerical result or test was independently checked here.

Disposition after real-pool inspection: the mathematical and finite-pool
compression gates have useful qualified evidence. **Native information and
complete-campaign expansion remain pending original-ENS observations.**
