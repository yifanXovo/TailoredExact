# Prospective confirmation design notes — not an admitted allocation

Written while the original R85 D3 P arm is active. Only E7/S12's six valid
endpoints have been seen in this stage. No new input has been generated and
no confirmation solve is allocated. R85 must finish and be published first;
the resource review and an exact committed generation recipe precede any later
generation/solve. These notes are retained even if later losses require a
different research direction.

The next validation should test the frozen ENS-C method on fresh outcomes
across target structures, including nonzero medium/large proof difficulty.
Reusing only the familiar three-cluster generator and two close geographic
draws would leave a narrow scope. A useful finite design would combine:

- One small CitiBike surplus role to check the repaired startup/certificate
  behavior, using a prospective geographic draw and120s common cap.
- One V20 synthetic high-imbalance role at300s with a spatial recipe distinct
  from the old three-cluster generator.
- Four common3600s medium/large roles: V30 synthetic corridor, V30 regional
  CitiBike, V50 synthetic perturbed grid, and V50 compact long-T CitiBike.

This would be18 complete P/ENS/K1 arms, maximum44460 process seconds; it is
an upper-bound proposal, not permission already allocated to the driver.
Dimensions, capacity/fleet, original mathematical T, stock/target rules,
source namespace, seed derivation and exact formulas must all be fixed before
generation. Do not inspect generated difficulty or outcomes to resize, filter,
reseed, shorten/extend or replace roles. A source-format failure can be repaired
with the failed bytes retained; it does not authorize performance selection.

Prefer deriving each data seed from the already-frozen candidate source ID,
a single version string and the canonical structural-role description. Keep
the eventual R85 results/publication commit as branch provenance, without
using measured outcomes or publication timing as a seed-selection input.

For the new synthetic recipes, use serialized Euclidean coordinates and the
project's original parser conventions, with strictly positive targets/weights,
legal stocks/capacities and both local pickup/delivery opportunities. An
analytically enforced aggregate shortage can guarantee a nonzero optimum
without solving or selecting the instance: empty departure and nonnegative
terminal load imply sum(Y)<=sum(b)<sum(D), while positive penalty weights
make F=0 require Y=D. This guarantees nonzero objective, not proof difficulty
or a useful native proof bound at a particular runtime. Full-model difficulty must
be observed and reported, including unexpected easy certification.

For those strictly positive-weight shortage roles, an input-only diagnostic
can also state the elementary lower bound
F >= lambda * min_i(weight_i / D_i) * (sum(D)-sum(b)) > 0.
It follows from the penalty term, the triangle inequality and nonnegative
return loads. This is a structural nonzero certificate, not a performance
selection rule, a strict rational solver certificate, or an imported bound
for the frozen algorithm. No new optimizer call is needed to establish it.
All sums and minima here are over service stations; the depot's sentinel
inventory/target fields do not enter the original objective.

Keep at least the V50 long-T shortage role to challenge the behavior implicated
by R82 U6; do not quietly replace it with only short-T or zero-objective roles.
Record overlap with all old CitiBike selections and R82 generated selections.
Fresh station draws from the same443-station source are related geography,
not independent cities. Synthetic grid/corridor tests broaden geometric shape,
not empirical-city representativeness.

The existing practical effect rules and complete-cost/physical-bound contract
remain fixed. No post-hoc mean can hide a consequential P regression or loss
of most of a meaningful K1/P advantage. If a consequential loss appears,
retain it and diagnose/revise the method; those confirmation inputs then become
development data. Avoid inventing an automatic K1-only rejection threshold or
claiming all future instances will improve.

Before eventual overall acceptance, combine the actual protected defects,
medium/large evidence, finite repeats and this separate unadapted check in a
single scope table. Unsolved, unavailable-UB, mixed-U/L, negative and certificate
loss rows remain explicit. No fixed number of positive samples alone satisfies
the overall user goal.

## Concrete recipe proposal while D6 P is still active

The following dimensions make the structural proposal reviewable before any
new input exists. They remain conditional on R85 closure and fresh resource
admission. A later stage must commit executable generation rules and their
hashes before generating any row; these notes do not start that stage.

|Role|Geometry / inventory|V|M|Q|Mathematical T|Whole cap|
|---|---|---:|---:|---:|---:|---:|
|F1|CitiBike regional / surplus|12|2|20|3600|120|
|F2|Synthetic alternating rings / high local imbalance, aggregate shortage|20|2|30|3600|300|
|F3|Synthetic two-lane corridor / aggregate shortage|30|3|20|5400|3600|
|F4|CitiBike regional / shortage|30|3|20|5400|3600|
|F5|Synthetic perturbed rectangular grid / aggregate shortage|50|4|30|7200|3600|
|F6|CitiBike compact / shortage, long route horizon|50|4|30|18000|3600|

All roles keep lambda0.15, pickup/drop60 and the unchanged original distance
and inventory semantics. The candidate and native settings remain R83's.
The eighteen-run maximum stays44460s. F1 is retained even if it is zero/easy;
the other roles target nonzero behavior without requiring any observed runtime.

Use a deterministic field hash derived from source4496078f25c0cdad1cf7a5c39835fd23121e8978,
one version namespace and the canonical role JSON. Field-specific suffixes
separate coordinates, station ordering, targets, transfers and weights.
No publication timestamp, measured objective or outcome enters this material.
The executable recipe must define exact byte encoding and integer conversions.

Proposed synthetic coordinates are in meters before translation, serialized
to three decimals. F2 uses twenty angular positions on alternating700/1000m
rings with angle perturbation at most0.04 radians and radial perturbation at
most50m. F3 uses fifteen x positions150m apart on two lanes y=-175/+175m,
with each coordinate perturbed at most40m. F5 uses a10-by5 grid at220m spacing,
with each coordinate perturbed at most40m. The depot is the serialized point
centroid, and the original parser supplies Euclidean travel seconds at1.5m/s.
The fixed shapes broaden the old three-cluster recipe; they do not represent
measured cities or guarantee difficult routing.

For each even-sized synthetic role, hash-order stations and pair consecutive
indices. In each pair set donor inventory D_i+a and receiver inventory
D_j-a-delta. Proposed inclusive integer ranges are F2: D20..28,a8..12,
delta3..6; F3: D16..26,a4..9,delta2..5; F5: D14..24,a3..8,delta2..5.
Station capacity is D plus the role's maximum a plus an integer4..12.
Thus every donor and receiver remains legal without repair/rejection, both
local imbalance signs occur, and total shortage is exactly sum(delta)>0.
Weights are independent hash-derived values in[0.25,1] rounded to six
decimals; use the existing synthetic minimum-ratio formula for serialization.
These are generated artificial profiles, not observed demand.

The receiver's minimum stock is at least2,2,1 for F2/F3/F5, respectively;
the donor has at least4 units of capacity slack. Positive serialized weights
are at least1/4, and shortage is at least30,30,50. With lambda3/20 and maximum
targets28,26,24, the elementary penalty bound above yields, for every input
from the proposed recipe, F>=9/224,9/208,5/64 respectively. This is a
recipe-level mathematical nonzero guarantee, computed without generated
coordinates or optimizer calls. It does not establish native proof difficulty
and is not injected as a bound into either candidate or benchmark.

CitiBike selection and inventory construction reuse the hash-bound original
generator under a new fixed namespace. Keep source coordinates/capacities,
its nearest-V or farthest-first-in-nearest-2V geography, controlled stock
profile, artificial centroid and explicit source-station overlap report.
The same underlying443-station source remains a limitation.

If a later implementation reveals a formula/format ambiguity, resolve it
before generation and record the change. An outcome may motivate a future
algorithm revision, but never replacement, reseeding or rescaling of these
already generated roles.

## Prospective evidence-tool limit found before generation

Read-only preparation found that `round73_native_evidence.audit` currently
requires at least one committed physical witness. All19 completed R85 runs
have witnesses and passed that reader; this finding does not invalidate or
alter them. The frozen R85 driver/reader remains unchanged.

For future unseen roles, the user contract also permits a legitimate cutoff
with no finite U. `GurobiBaseline.cpp` reads SolCount and only extracts routes
when it is positive; `Result.cpp` serializes native U/gap as null when their
verified availability flags are false. The later confirmation tooling should
therefore retain a valid no-UB P endpoint as unavailable U/gap with only its
qualified original-model L, instead of assuming a witness or treating missing
primal progress as an implementation failure. This needs a separate narrow
reader/summary adaptation, with original model/settings/receipt checks kept
and no synthetic route, gap, certificate or inherited UB supplied to the run.
No such outcome has been observed or selected in the prospective data.

A generator preparation copy exists locally at
`build/round86_preparation/round86_generate.py` (SHA256
`d7e249b8276ab87cf366b1f5bcfaf481f01d6749b1b1220946203c5ae7be4042`).
Only AST parsing was executed (0.0033779s); no generator import/execution,
new data or Optimize call. Its guard prevents generation from the preparation
directory. Install, review and freeze it in the eventual stage only after
R85 publication and resource admission; the source and exact executable
recipe still require that committed freeze.
