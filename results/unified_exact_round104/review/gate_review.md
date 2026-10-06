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

## Original-ENS observation gate addendum

Inspected `diagnostics/native_points02/summary.json`, its saved per-point
records and `scripts/round104_native_points.py` after the three execution-team
180s `native02` observations completed. The reader binds each complete point
to the actual terminal native call's journal BEGIN, original source SHA,
interval, cutoff and original native settings. It checks every model column
and the full original matrix. This reviewer did not independently read models,
recompute activities or run native search. These 180s runs are observations;
they are not complete algorithm performance comparisons or independent
replications. The 12 complete points have original-matrix maximum residuals
at most `3.545897603318693e-11`.

| Role / observed point | Point objective | ALL reliable rows | ACTIVE reliable rows | GROUPED reliable rows |
|---|---:|---:|---:|---:|
| F2 first root, sequence 1 | 0.6071799602644684 | 304 | 16 | 1 |
| F2 latest observable root, sequence 16 | 0.7685866257357956 | 9 | 0 | 0 |
| F2 positive node count 1 | 0.7730102300546992 | 5 | 2 | 0 |
| F2 positive node count 10 | 0.7759151363566111 | 29 | 2 | 0 |
| F2 positive node count 100 | 0.8116094016256583 | 9 | 1 | 0 |
| C2 first root, sequence 1 | 0.16123605049876003 | 0 | 0 | 0 |
| C2 latest observable root, sequence 12 | 0.18875094776129178 | 0 | 0 | 0 |
| C2 positive node count 1 | 0.18874524284515182 | 0 | 0 | 0 |
| C2 positive node count 10 | 0.18923586131527187 | 0 | 0 | 0 |
| C2 positive node count 100 | 0.19052636623931793 | 0 | 0 | 0 |
| F5 first root, sequence 1 | 0.24420882282482045 | 0 | 0 | 0 |
| F5 latest observable root, sequence 4 | 0.28141416661991164 | 0 | 0 | 0 |

Reliable means exact signed binary-rational activity above ten original
FeasibilityTol in the submitted row scale. F2/C2 SHA exactly match their
raw pool scopes. F5 uses the different actual terminal SHA
`6493bd9b60e94124f4d43bbd55d0a20a5650e65867a114db78d1386815ac9f19`.
Its historical pool can be tested for row satisfaction because the resource
rows are global under the identical necessary contract, but its raw objective
certificate and old `LH` do not become same-scope terminal evidence. Re-solve
the finite pool on this actual F5 source before using its zero ACTIVE result
as a terminal-scope selection conclusion. No F5 positive-node point was
available within the observation window.

F2's latest root point objective exceeds historical raw `LH`, yet nine ALL
rows still separate it. This directly prevents an inference that higher
native objective proves implication of the necessary domain. The saved point
objective must also not be relabeled the native global LB. No claim is made
that sequence 16 is the solver's internally final cut closure.

The real observations support the theorem's information-loss warning:
GROUPED's two rows preserve the raw numerical objective but miss all later
F2 sampled nodes, while ACTIVE still separates them. ACTIVE's maximum signed
violations at node counts 1/10/100 are respectively
`0.05664459749194488`, `0.0034287695477375753`,
`0.020242711877392832`. ALL also contains nine separating rows at the latest
observable root which ACTIVE discarded. Neither root certificate compression
nor zero violation at one point proves preservation of later proof progress.

C2's 133-row pool has no positive signed activity at any of its five saved
points; its maximum signed margins are negative, not merely under threshold.
F5's 82-row pool likewise has negative maximum signed margins at both saved
roots. These are strong finite-pool negative controls. They do not constitute
full necessary-hull membership proofs, or show that newly repriced supports
could never interact with native cuts. The zero compressed sets are tied to
the returned old-objective dual support, not a general feasibility-domain
redundancy theorem.

**Recommendation: do not expand to long confirmation, and do not yet claim a
complete C-type stop.** There is observed F2 positive-node information in
ACTIVE; therefore the evidence is stronger than merely an old raw objective
phenomenon and leaves the requested B/D practical-cost question unresolved.
After the actual-F5-scope pool qualification, perform one bounded complete
F2 cost control with a unified fresh generator, ACTIVE submission and faithful
SHADOW, retaining contemporary unchanged ENS and P benchmarks. The window
should cover the inherited roughly 575s ENS certification scale, rather than
another short observation (a preregistered 1200--1800s window is appropriate).
Every arm must start fresh; ACTIVE/SHADOW must pay all generation, objective
LP, compression, Start and MIP costs. Do not use free historical 827-row
replay time as an algorithm result. The unchanged official SHADOW bounds and
cutoff must not consume its diagnostic improved LP bound.

The evidence favors ACTIVE for this finite control. GROUPED currently loses
all observed F2 positive-node separation and does not need its own complete
performance matrix. This choice follows the present verified objective and
structural evidence, not an instance dispatch rule. A completed control can
justify explicit stopping if its net effect cannot offset generation cost
and the actual medium-large scopes still have no useful proof information.
Then cancel unstarted long confirmations and close the **objective-certified
root preprocessing scheme** with its finite-domain/observational limits.
If the control is worthwhile, medium-large opportunity must still be shown
before large frozen confirmation; F2 success alone does not satisfy that
gate. Do not reopen anchor families, parameter thresholds or arbitrary pools
to rescue this scheme.

This addendum is still the first mathematical/information gate review, not
the separate delivery-stage independent numerical aggregation/RHS recompute.

## Actual-F5 scope and production-control source addendum

Read `diagnostics/pool_F5_native01` and its actual terminal source plan. On
SHA `6493bd9b60e94124f4d43bbd55d0a20a5650e65867a114db78d1386815ac9f19`,
RAW/ALL/ACTIVE/GROUPED are numerically 0.24420882282482045 with all 82 new
Pi zero and zero compressed rows. ALL primal-minus-dual is
`3.469446951953614e-15`; the empty model's is
`2.7755575615628914e-16`. PASS remains separately signed at
0.24420882282465986, with primal-minus-dual `4.652758539558377e-9`.
This closes the finite-pool actual-F5-scope issue; historical full-domain
UNKNOWN is unchanged.

Statically read the new `src/Round104GurobiObjective.inc`, the changed
paid-bank optional argument in `ServiceResourceHull.cpp`/header, the new
backend API, isolated mode/default checks, `PaperExternalGiniTree.cpp`
preparation/Start ordering, and the updated standalone interval primitive.
No build, solver or test was executed by this reviewer.

The new generator uses the current canonical source, self-paid standard and
outer LPs, and valid complete-support rows. Its bank is empty for every new
canonical preparation, contains only this call's paid oracle plans, validates
seeds under the current contract, and leaves the inherited no-bank behavior
intact. DP begin records precede actual supports, and Optimize begin records
precede auxiliary optimization. A changed objective/row model is adopted only
after exact old typed matrix/objective/bounds and added-row readback, and its
SHA/signature replace the request before the existing all-row Start check.
SHADOW does not submit rows, change request/cutoff or consume the diagnostic
LP lower bound. The new mode is default off and isolated from R101/102/103.
These are sound source-level prerequisites; actual accepted Start, cache,
readback and numerical qualification remain execution evidence obligations.

The generator does not call an unchanged objective a closure. Every fresh
accepted direction eliminates the current point by a qualified signed margin;
duplicate/no-admissible directions stop UNKNOWN, and the finite dyadic
direction set plus the global deadline avoids an unsupported unlimited-LP
claim. Selection keeps all strictly negative pool Pi, records small wrong-sign
repair, and solves the selected LP anew. It labels this as numerical ACTIVE,
not exact optimal-dual support. UNKNOWN fallback retains the valid ALL pool
and its separate identity rather than pretending compression succeeded.

**Fix before the complete control:** at the inspected source snapshot, the
vehicle loop condition included `remaining()>0`, while `all_inside` started
true. Deadline exhaustion after checking only INSIDE vehicles could skip the
remaining vehicles and incorrectly emit `all_members_within_tolerance`.
Require a completed-vehicle count equal to the fleet size, and label partial
deadline coverage UNKNOWN. Likewise initialize the actual standard-LP value
before a loop that deadline may prevent entering; do not emit zero as its
value. On an incomplete last outer LP, distinguish the last qualified
optimal value from the current unsolved pool value, preserving null/UNKNOWN
where necessary. These issues affect certificate/status accuracy even though
the already proved resource rows themselves remain valid.

For the new complete control, save the compressed LP full vector and the
pool/compressed primal/dual solver residuals, and put Runtime on each
auxiliary return. The observed objective difference threshold alone does not
establish a complete numerical qualification, and production stage cost must
be reviewable. Full Pi/RC plus points allow the final independent reader to
reconstruct more of the certificate. The inspected artifact row prefix was
still `r103_hull_`; rename it to the current round to avoid misleading row
provenance. These findings were sent to the execution agent before its
campaign admission.

The standalone interval implementation now has subnormal behavior detection,
rejects infinity sentinels in changed-coordinate compensation, and explicitly
sets tiny native-unsupported coefficients to zero with the same signed
endpoint compensation. This addresses the earlier two arithmetic findings.
The saved `qualify01` tiny-coefficient readback failure must remain in the
failed-attempt ledger. Production ACTIVE copies source coefficients without
this conversion, so its final exact readback remains essential.

The single finite complete-control recommendation stands, conditional on the
above deadline/status and evidence fixes plus actual qualification. It does
not admit any long-window confirmation or default promotion.
