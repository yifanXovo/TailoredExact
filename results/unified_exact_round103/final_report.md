# Round103: certified resource-hull separation and complete-solve evaluation

**Completed: certified diagnosis, one production branch, development/protection,
two frozen confirmation roles and two 3600s groups. Do not promote the candidate;
ENS-C remains the protected default.** The inherited hull has useful F2
convexification space and real C2/F5 separation, but point separation does
not guarantee objective or complete-solve benefit. The unchanged candidate
has mixed contemporary results, including material confirmation regressions.

## Baseline and measured identity

This branch stacks on R102 / PR164, delivery
`0b5640f0de5a29abf6545962dd776a2fab198f90`, rather than main. The supplied
measured R102 source `2b65d483ecacd6084782922cff8c8252be9d3a63` and PE SHA
`f1c071135b6dd7cc84d92a71efec17aec33187747ad1829d53a1058576871c1d`
were verified. R103 production source is frozen at
`317579b974336233472acd6db80f9f5a4478c880`, with measured PE SHA
`836b2ee3f7e373c8be0a1f2bdf5b6e06ac67a95ea7ef65374972288acdc862ea`.
Later reporting/packaging commits do not identify a newly measured executable.
`production_freeze.json` binds all C++/header/include sources, build and helper
identities, the actual Gurobi13.0.2 DLL, and the unchanged rules.

P-GRB is the principal benchmark, using its original compact model and
quantity types without external Start or new rows. ENS-C is the direct
reference and advantage-protection target. M-B, R101 and R102-J remain
unpromoted. The original startup,24+1 closure, VD-P/F0, AM0.08, mathematical
target, quantity types, objective mapping, cutoff complement and complete
interval coverage are retained. Native parameters remain Threads1, Seed0,
PresolveAuto, zero relative/absolute MIP gap and the original tolerances.
Only the disposable diagnostic LPs use tighter numerical tolerances.

## What the same necessary domain can and cannot explain

The inherited domain contains all stations, skip/integer one-direction
service, original single-station operation caps, final D<=P, and the safe
maximum singleton closed-trip bound plus cP<=T. It deliberately permits
intermediate D>P and cumulative P>Q. The actual conservative binary64
predicate, including outward resource boundaries, is identical in support
and plan validation. Zero-weight stations and external supply/receiving
stations remain present. This domain is necessary; it does not establish a
route, prefix loads, joint travel or cross-vehicle integer correlation.

Eight actual complete raw/first-native points cover C2,F5,F2,N2. The former
C2/F5 finite-family zero hits do not imply hull membership: complete-domain
certified pricing separates their saved points. F2 supplies the positive
control. At N2's first native point, one vehicle is OUTSIDE and two have
explicit within-tolerance INSIDE combinations. The F2 native point is
INSIDE/OUTSIDE. `capability_table.md` retains every status and stop reason.

Same-scope capability measurements are:

| Model | L0 | finite LJ | full-domain result | Interpretation |
|---|---:|---:|---:|---|
| R98-C2 |0.16123605049876005|0.16123605049876005|0.16123605049876005|Optimal outer LP, all explicit members within1e-8|
| F5 |0.24416944802555995|0.24416944802753696|outer LB0.244169448027537; finite-column upper witness0.24416944802753704|Original closure UNKNOWN; numerical full-matrix upper witness, no exact rational equality|
| F2 |0.528625649465355|0.5286753357380306|0.638005040404497|Optimal outer LP, all explicit members within1e-8|

C2 closure uses133 valid rows,79 outer LP/1566 restricted-master LP/1471
DP calls and77.2147s; F2 closure uses827 valid rows,456 outer LP/3188 restricted-master
LP/3105 DP calls and134.6018 observed outer seconds. These are diagnostic
costs. Production does not import these historical points, plans or rows.
Within1e-8 membership is not strict rational equality at the floating point.
The LP objectives are qualified Gurobi numerical optima with exact valid
dyadic rows, not rational optimality proofs. F5's original terminal evidence
retains a1.284648919e-8 residual and UNKNOWN. Its tiny signed upper-minus-
outer values are preserved, including the enhanced bracket's negative
2.498e-15 numerical inversion, and are never clamped into equality.

This separates two conclusions: R102's finite directions substantially
missed some points; nevertheless, C2/F5 can remix to the same objective.
F2 has substantial remaining convexification space. The available results
therefore do not justify declaring the entire inherited hull weak.

## One domain enhancement and one production branch

The unique-access Lagrangian boundary is proved in
`mathematical_algorithm.md`: membership in each vehicle hull plus the
existing sum(z)<=1 linking rows prevents this nonnegative multiplier
combination from separating the point. This concerns that particular
combination, not all stronger cross-car integer hulls or finite-search
benefits. No multiplier grid was opened.

The only domain enhancement investigated is a three-anchor mask. A safe
closed-tour lower bound through the selected anchors is combined by max
with the inherited singleton bound. Directed shortest-path closure,
conservative additions and enumeration of up to six orders prove global
necessity. Anchors are chosen from the current combination's actual travel
resource deficits by a fixed rule, not a historical optimal route. Large
combination mass is excluded, but original points are reclassified so
remixing is allowed. One C2 vehicle remixes INSIDE. Enhanced C2 still closes
at the unchanged objective; enhanced F5 has the same numerical bracket and
honest incomplete classification. Additional cost has no useful objective
gain, so anchors are rejected for production.

F2's positive capability selects one unified production branch: one
self-paid standard LP before each new qualified canonical MIP, followed
by physically normalized hull distance/pricing and at most one reliably
violated global support row per car. Finite-column distance is a full
distance upper bound and cannot certify OUTSIDE. An explicit verified
combination can certify INSIDE within the declared tolerance. OUTSIDE
requires complete-domain safe support upper bounds for the actual dyadic
weights and positive enclosed violation. Duplicate columns, incomplete
LPs, resource limits and insufficient precision return UNKNOWN; contract,
mapping, API, proof or persistence failures propagate durably.

The DP returns a full attaining plan through bounded traceback, with
independent legal-plan/profit checks. Dyadic precision is derived from the
physical widths and tolerance; the submitted direction is repriced. Exact
power-of-two row rescaling preserves RHS and coefficients. The admission
threshold is greater than ten original FeasibilityTol in the submitted
scale; no coefficients are silently discarded. This one-pass rule is
neither full-hull closure nor tree separation. It has no callback Optimize,
PreCrush, internal time/Work switch, historical direction import or B&B
restart. Only the existing whole-algorithm global deadline applies.

Inserted rows preserve the old LP's original variable order, types,
bounds, objective and every original row. Actual readback verifies both
old and added data before canonical SHA/row signature/cache identities
change. Start is then validated against every row of that new canonical
model. Reused canonical preparation is bound to exact source/input/scope/
interval/objective identities and its paid artifact SHA; preparation cost
is included in native-event clocks and whole-process costs.

## Qualification and independent review limits

Independent small-domain enumeration passes1728 signed base and552 anchor
supports plus boundary fixtures, including external supply, zero-weight
stations, c=0, intermediate D>P and cumulative P>Q. Seven injected-master
fixtures cover finite-distance misclassification, signed support,
duplicates, zero-width/zero-domain coordinates, incomplete LP and contract
failure. Actual F2 SHADOW/SUBMIT120s qualification proves row readback,
canonical identity, all9271 Start rows and acceptance; those short runs
are not complete performance comparisons. SUBMIT generated two rows,
19 auxiliary Optimize/18 DP calls and0.408s preparation. SHADOW generated
the same selected rows without submission and paid0.266s preparation.

Two actual preparation persistence collisions force durable failure;
the inherited evidence reader rejects both streams, with zero MIP
Optimize. Their six required LP calls,19 auxiliary LP calls and18 DP
calls are billed. These tests concern the exercised failures, not total
storage loss or every possible native fault.

An independent reviewer proves the dual/sign/scale and Lagrangian boundary,
recomputes two actual production supports with a different level-DP
recurrence (40 level computations), checks254 legal plans and six actual
model reads, and verifies exact dyadic RHS/scaling and exact rational
combination residuals. It does not rerun native B&B, independently price
all827 F2 capacity rows, or prove full-matrix rational feasibility. The
paid review exits1 at its final overstrict assertion requiring begin
records in the old C2 log, after successful mathematical checks. Its raw
failure,6.0273s fee and separate scoped conclusion remain preserved.

Historical Python upper-display conversion could round half an ULP down;
INSIDE decisions compared the exact Fraction residual and remain valid.
The future writer now emits strict outward floats plus the exact rational
residual. Historical files are retained. Old reason strings saying
exact_dyadic for normalized combinations should read exact_rational.
C++ interval certificates are unaffected. Hashes establish provenance;
they do not substitute for actual plans, points, matrices or proofs.

## Complete comparisons and final decision

All22 complete development/protection/confirmation/long arms and the two
separate short qualification arms returned normally and passed the original
physical/numerical audit. The table shows complete endpoints; exact common
covered-time comparisons are in `reports_final01/checkpoint_pairs.csv`.
Native global deadlines reserve drain time, so the observed approximately
1797/3597s endpoints remain below the corresponding1800/3600s caps.
Admission, preparation and the auxiliary optimizations are included in
whole time. Postexit audit seconds are additionally charged to the round,
but do not identify a hidden engine certification instant.

| Role | Cap (s) | Arm | Observed whole time (s) | U | L | Signed U-L | Certificate |
|---|---:|---|---:|---:|---:|---:|---|
| F2 | 1200 | H-SUBMIT | 634.859 | 0.865943520323 | 0.865943520323 | 7.77156117238e-16 | yes |
| F2 | 1200 | ENS-C | 575.672 | 0.865943520323 | 0.865943520323 | 3.33066907388e-16 | yes |
| F2 | 1200 | P-GRB | 1197.438 | 0.865943520323 | 0.762875839590 | 0.103067680733 | unproved |
| F2 | 1200 | J-SUBMIT | 523.297 | 0.865943520323 | 0.865943519614 | 7.08994196685e-10 | yes |
| R98-C2 | 1800 | P-GRB | 1797.375 | 0.198302848584 | 0.186627086958 | 0.0116757616261 | unproved |
| R98-C2 | 1800 | H-SUBMIT | 1797.390 | 0.223638761698 | 0.189571204210 | 0.0340675574884 | unproved |
| R98-C2 | 1800 | ENS-C | 1797.328 | 0.216793065272 | 0.189691616686 | 0.0271014485858 | unproved |
| R99-N2 | 1800 | ENS-C | 1797.375 | 0.199516075095 | 0.162506550499 | 0.037009524596 | unproved |
| R99-N2 | 1800 | P-GRB | 1797.344 | 0.177364361443 | 0.164821519585 | 0.0125428418583 | unproved |
| R99-N2 | 1800 | H-SUBMIT | 1797.390 | 0.181966056075 | 0.162459570301 | 0.0195064857733 | unproved |
| R98-C3 | 1800 | ENS-C | 1797.391 | 0.328346625730 | 0.193275489144 | 0.135071136586 | unproved |
| R98-C3 | 1800 | H-SUBMIT | 1797.360 | 0.340892100088 | 0.193278281424 | 0.147613818664 | unproved |
| R98-C3 | 1800 | P-GRB | 1797.360 | 0.542416624215 | 0.185483592994 | 0.35693303122 | unproved |
| R103-H1 | 900 | P-GRB | 897.375 | 0.496654432818 | 0.259149670797 | 0.237504762022 | unproved |
| R103-H1 | 900 | ENS-C | 897.313 | 0.439725784412 | 0.304742507576 | 0.134983276836 | unproved |
| R103-H1 | 900 | H-SUBMIT | 897.359 | 0.415562741138 | 0.303799371421 | 0.111763369718 | unproved |
| R103-H2 | 3600 | H-SUBMIT | 3597.454 | 0.592672383150 | 0.425699668632 | 0.166972714518 | unproved |
| R103-H2 | 3600 | P-GRB | 3597.375 | 0.660708680596 | 0.401725272641 | 0.258983407955 | unproved |
| R103-H2 | 3600 | ENS-C | 3597.437 | 0.553413736999 | 0.434037226744 | 0.119376510256 | unproved |
| F5 | 3600 | ENS-C | 3597.469 | 0.329323694641 | 0.281453806344 | 0.0478698882966 | unproved |
| F5 | 3600 | P-GRB | 3597.391 | 0.434235836764 | 0.268250596924 | 0.16598523984 | unproved |
| F5 | 3600 | H-SUBMIT | 3597.390 | 0.320716625245 | 0.281452122248 | 0.0392645029966 | unproved |

F2 H preserves certification against censored P, without an invented exact
speed ratio. H is59.187s/10.28% slower than ENS and111.562s/21.32% slower
than contemporary J. Both are material under the frozen30s AND10% rule;
neither is severe under120s AND25%. At600s ENS/J already certify while H
still has gap0.0113929. One run per arm provides these observed comparisons,
not statistical stability. A one-sided certificate permits only observed
time bounds; all other complete groups are doubly unproved and eventual
certification-time ordering remains unknown.

At1797s N2 materially improves ENS on U/gap while losing to P. C2 loses
both references at the late budget; its earlier600s ENS improvement is
also retained. C3 materially improves P but regresses against ENS on U;
its9.29% larger endpoint gap is below the frozen10% gap materiality gate.
All signed differences, missing values and uncovered checkpoints are kept.

The unchanged candidate entered the already frozen groups through immutable
`stage_decision.json`, using13 completed development/protection arms and
two qualification arms. This was experimental admission, not adoption.
V30/H1 (seed103050301, three_rings, Q18/24/30) and V50/H2
(seed103050502, bent_grid, Q16/22/28/34) were drawn once before any
confirmation search. Both have T7200,60+60 handling, lambda0.15, positive
weights and an explicit nonzero stock shortage. They use established broad
research families but their exact bytes/seeds had no earlier data. All
three conditional groups were completed; none was cancelled or redrawn.

At the common897s checkpoint H1 improves ENS by U -0.024163043274 and
gap -0.023219907118, and also improves P. At3597s H2 improves P but
regresses against ENS by U +0.039258646151 and gap +0.047540035470.
The latter differs slightly from the endpoint gap difference because ENS
has a final bound publication after3597s; no interpolation is used.
At3597s F5 improves both references; versus ENS its U/gap differences
are -0.008607069396/-0.008605385300. F5 has an earlier897s ENS regression,
U/gap +0.026937973017/+0.026938104475, before the late improvement.
These changes are material under the frozen U rule (absolute0.001 AND1%)
and gap rule (absolute0.001 AND10%).

The final recommendation in `final_decision.json` is **not_promote**.
Actual N2/H1/F5 budget gains preserve research value, while F2 certification
cost and C2/C3/H2 regressions do not justify replacing ENS-C. No severe
certification-time regression is observed, but that absence alone is not
adoption evidence. Do not infer universal hull weakness or pure-cut
causality: the pass changes canonical data and native trajectories, and
short SHADOW qualification does not isolate full-solve causal effects.
Stop this round without another domain, mode, threshold fit or redraw.

## Paid mechanism cost and final verification

Each complete H arm pays one fresh preparation; the terminal MIP reuses
that exact paid canonical preparation. No historical rows are imported.

| Role | Actual submitted rows | Auxiliary LP Optimize | DP | Preparation (s) |
|---|---:|---:|---:|---:|
| F2 |2|19|18|0.3495576|
| C2 |3|251|250|6.0104123|
| N2 |3|307|306|5.9823009|
| C3 |4|286|285|14.6750060|
| H1 |3|244|243|6.3296596|
| H2 |4|295|294|16.3544833|
| F5 |3|1169|1168|46.8810978|

`small_hull03` passes32 actual full-enumeration primal/dual/classification
cases,81 LP/33 DP calls, on a same-source export-only VD-P model. Failed
small_hull01/02 are preserved and charged: an exclusive-ledger writer error,
then an unqualified original compact matrix. Neither reached Optimize.
`final_evidence_development02` reprices12 production supports, reads9 actual
models and checks1835 signed physical row/witness pairs. Its failed first
attempt rejected a preloaded second DLL before model reads or Optimize;
the reader import order was corrected without changing production.

The final `final_evidence01` batch independently of the original run repeats
the production oracle on10 additional directions, reads6 actual models,
and checks1928 physical row/witness pairs across H1/H2/F5. It verifies exact
old variable/type/bound/objective/row preservation and exact new dyadic data,
full standard-LP point residuals, complete-domain supports and combinations.
Both execution-team evidence readers use zero Optimize and no native B&B;
repeated production pricing is not an independent alternative recurrence.
The paid `reports_final01` reader verifies all24 complete report trajectories,
coverage, scope, clocks and missing values without recovery overlays.

The final independent metadata reader passes25805 checks, zero errors/missing
fields and26 warnings, covering all24 arms and782 paid-associated call logs.
It uses no Gurobi import, Optimize, DP, model read or native B&B. Its scoped
conclusion is `review/round103_final_review02.json`. The earlier metadata
review and mathematical review, including the latter's preserved final
format failure, remain part of the evidence.

Final fees are **72 charged starts/44907.45178329994 outer seconds**, below
the72/80000 limits. Native Optimize102, auxiliary Optimize19675 and DP18624
are separately reconciled in `fees_final01/fees.csv` and
`fee_reconciliation.json`; nested elapsed time is not added twice.
The complete DP total includes the contemporaneous J's52 inherited R102
calls, independently checked from two successful callback summaries;
`reports_final01/whole_run_costs.csv` only contains the new-hull DP subset.
The first fee snapshot and review omitted that subset, are preserved, and
the final supplemental review verifies the correction without another
solve. No missing BEGIN is invented. Failed reader/setup attempts and
conservative physical-child/preflight allowances are charged. Intentional
root-persistence faults also remain; builds, unit fixtures, receipt
reconciliation and byte packaging are separate engineering.

`compact_evidence03/manifest.json` maps exact-byte compressed points,
plans, proofs, original/canonical LPs, Start rows/values, all production
rows and full first points, physical witnesses, fee/failed-attempt records
and independent review to their SHA-bound sources. Large local iterations
are indexed, not all duplicated or independently re-proved. Executables,
DLLs, licenses and unrelated user changes are excluded. See `reproduce.md`
for the build, exclusive-label run/reader workflow and unpacking limitations.
No required experimental group remains pending. This is a stacked draft
research delivery; no merge, default promotion or deployment is authorized.
