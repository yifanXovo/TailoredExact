# Independent agent mathematical and model review

Reviewer: the separate `math_review` agent requested under Round168 H.1.
This is an independent agent review, not human peer review. No Optimize,
model mutation or source edit was performed by this reviewer. The only
additional computation is saved, solver-free independent offline readback
in `fraction_tiny_readback.py` and `fraction_tiny_readback.json`.

Status: **PASS. Model, six tiny qualifications, all11 final positions,
interval propagation, numerical qualification and the final research
interpretation have been independently read back.**

## Actual material examined

- `src/round168_route_family.cpp`, including pool loading, all three
  branches of `Built`, mapping/decoding, actual-matrix audit, independent
  enumeration, callback stop, finalized bound gate and propagation.
- `route_family_theory.md`, `research_design.md`, the frozen target/family
  manifests and actual tiny enumeration/membership records.
- All six tiny `result.json`, saved actual scope LPs and mapping checks.
- The available C35 Seed0 order/owner `result.json` and the three saved
  substantive LPs (including the currently running eligible scope).
- The unchanged original physical duration tolerance and the original
  evaluator objective/loaded-return conventions inherited by the tool.

## Completeness and physical correspondence

The compiler represents complete declared families, not a bounded block
neighborhood. For every station in old E it retains every stock0..C;
outside E it retains exactly b. A separate readback of the actual saved
C35 LP variable names confirms these full supports for all three scopes,
G in[0,1], no cutoff row and the sole old-E omission18. The exact target
is therefore not being tested inside an old child interval or contracted
stock box.

The shared s/q block couples every vehicle through the full Gini
numerator and denominator and the original weighted penalty. At integer
s, q=G*s. Epigraph slack can increase the model objective but cannot
produce a physically better objective than the decoded fleet. Every
physical family fleet has an equal-objective extension. At S=0, the
pair row permits G=0 with all h=0; no normalization by zero is used.
Thus family minima coincide, although arbitrary slack epigraph points
need not have model objective equal to true physical F.

For order, the complete forward DAG contains every skip arc. One source
arc, one sink arc and station degree equal to optional nonzero visit
give exactly the retained subsequence. Prefix sums over original order
are precisely the true loads after zero-operation deletion. Owner and
eligible use all allowed station arcs, degree constraints, a valid rank
cycle exclusion with M=m+1, and single-commodity arc loads. Source loads
are zero and station load balance is pickup minus drop. Degree and rank
exclude disconnected station cycles; an integer point yields one source
to sink path and legal prefixes. No terminal-load equality or total
pickup<=Q is imposed.

The service equations admit exactly one owner iff Y differs from b and
recover one-way integer quantities from binary stock and owner choices.
Continuous declarations of p/d do not create fractional integer-point
operations. Owner columns or reverse-order arcs are absent where their
use is structurally forbidden.

Every selected skip arc pays the actual distance between its retained
endpoints. The time row uses total pickup times(tp+td). Empty departure
gives R=P-D, so station handling plus return unloading is
tp*P+td*D+td*R=(tp+td)*P. The rule is valid for the actual uniform input
operation times and permits loaded return. Empty routes and empty E have
the source-sink bypass. Single-station service and direction flips are
covered without a special fixed-direction assumption.

## Independent tiny verification

The primary C++ oracle does not read model variables or generated rows.
It enumerates stock vectors, allowed owner assignments and every allowed
retained permutation, with independent direct physical arithmetic. The
six MIPs attain the corresponding enumerated optima; every recorded
matrix, bound, type and physical reverse-map residual is zero.

The reviewer separately recomputed these spaces using exact Fraction
arithmetic on the frozen binary64 objective coefficients and integer
distances/handling. It used direct station handling plus loaded-return
unloading, not the model's compact time row. Candidate and feasible counts
agree exactly:

| Tiny | Scope | All candidates | Feasible | Exact binary-coefficient optimum |
|---|---|---:|---:|---:|
| A | order |256|71|5404319552844595/36028797018963968|
| A | owner |2713|196|same|
| A | eligible |12661|742|same|
| B | order |256|63|0|
| B | owner |625|84|0|
| B | eligible |12661|545|0|

The first fraction rounds to0.15. The saved independent JSON binds the
frozen enumeration, parent fleets, six Native result files and readback
script by SHA256. This is independent offline recomputation, not a new
research model or an extra Optimize. It establishes only these finite
tiny spaces; substantive Native lower bounds remain numerical certificates.

The saved larger-scope order-release/owner-release witnesses are accepted
with actual row residual0. Both requested strict membership separations
exist, even though the optima happen to agree across scopes. The saved
B_zero fleet is an eligible cross-owner S=0 witness; its actual eligible
row embedding passes. Its rejection in the two smaller families is not
evidence that S=0 is physically impossible in those families.

## Bound policy and currently available exclusions

The full physical parent is retained as U in every query and its complete
Start is mapped and checked before Optimize. The implementation requests
zero relative/absolute gaps, fixes Threads1 and Seed0 and reads back the
inherited numerical defaults. An actual MIPSOL fleet is physically checked
before an early HIT request. A callback lower stop is tentative; final
classification still requires the finalized finite bound, accepted status,
unchanged model hash, consistency with physical U and all available
solution/Native quality residuals<=1e-7. Status11 is the expected normal
evidence interruption; it is not being mistaken for Native optimality.

Qualified L is reduced by1e-7 and rounded downward; the nonnegative
objective supplies zero if no finite qualified Native lower is retained.
This matches the declared engineering policy. It is not a rigorous
rational rounding-error certificate and must not be advertised as one.

C35 Seed0's currently available records support:

| Family | Raw bound | Safe L | True U | Verdict |
|---|---:|---:|---:|---|
| order |0.09702158444546395|0.09702148444546393|0.12956638965196043|EXCLUDED|
| owner |0.0933984307773885|0.09339833077738849|0.11512886899258191|EXCLUDED|

Both safe lowers exceed theta=0.09331944374779841. Actual final matrix
residuals are about5.75e-14 and5.31e-14; both physical reverse mappings
have residual0 and no decoding error. Hence all quantities, flips and
deletions at fixed old order are insufficient, and even arbitrary order
with old owners remains insufficient under this numerical policy. Neither
restricted lower is an original full-problem lower. The eligible result
must be read before claiming that owner release suffices or that activating
an outside station is necessary.

Propagation in the C++ driver follows the correct directions: supersets'
lower bounds strengthen subsets and subsets' physical witnesses strengthen
supersets. Raw fields remain separate. UNKNOWN in a smaller scope cannot
establish necessity of a larger structural change.

## Findings and dispositions

1. The first theory draft contained `*minimum*+is`. The parent corrected
   the prose; this reviewer read back the corrected sentence. No model
   or numerical evidence was affected.
2. Negative structural mapping records have residual=-1 because `map()`
   rejects the fleet at its structural membership gate before matrix-row
   mapping. They are not measured row violations. The parent has now
   explicitly documented this sentinel and the absent owner-column/
   reverse-order-arc reason. Positive larger-domain records really were
   checked against every actual row and have residual0. No additional
   Optimize is needed or justified for that clarification.
3. No unresolved mathematical or implementation defect affecting family
   completeness or the two available exclusions was found. The finite
   evidence is parent-specific and uses the frozen numerical policy;
   it does not establish algorithm acceleration, Native search causality
   or a general OR contribution.


## Final campaign and decision readback

All11 registered positions are present, with **8 EXCLUDED, 2 archive
HIT and 1 UNKNOWN**. The seven initially nonattaining order families
are all excluded. B35 Seed1 and X35 Seed0 are the two self-targeting
archive witnesses and consume no Optimize. The eighth exclusion is C35
Seed0 owner. These are saved parents on three physical inputs, not
eleven independent instances or a generalization percentage.

The final C35 eligible row is correctly conservative. Its actual raw
Native bound is0.033592546196099075, but ConstrVio and independently
recomputed matrix residual are both7.912396935427779e-7. This exceeds the
frozen1e-7 gate; `bound_qualified=false` and safe L=0 are therefore
required. Default solver feasibility tolerance1e-6 does not authorize
retroactively relaxing the declared research gate. The row remains a
limited, valid physical-feasible UNKNOWN, with the unqualified bound
retained as raw evidence. No API, missing-data or model-scope failure is
hidden as UNKNOWN. Its physical incumbent has F=0.12724407070237156; the
more accurate original-objective evaluation is used rather than its
slightly smaller model epigraph value0.1272440465118152.

Owner's legal fleet gives a stronger eligible upper by containment:
U_eligible=0.11512886899258191. Owner's lower is **not** propagated upward
to eligible. The final eligible interval[0,0.11512886899258191] straddles
theta=0.09331944374779841, so it is UNKNOWN. Raw fields and both propagation
sources remain visible. Every CSV/JSON row was cross-checked for L/U,
verdict, tau/theta, parent F and provenance. The interval formulas
[F_p-U,F_p-L] and[max(0,L-theta),max(0,U-theta)] hold for every recorded
row. All L<=U<=F_p relations pass. In particular, C35 order's obstacle
interval is[0.0037020406976655262,0.036246945904162026]; owner has a
strictly positive obstacle lower7.88870295900801e-5.

The research decision and author memo state the strongest warranted
conclusion: on C35 Seed0, any full fleet attaining the declared threshold
must change at least one retained old served owner **or** activate an
old-ineligible station. No result proves that old-eligible owner release
is sufficient, nor that station18 is necessary. The P witness's use of18
is a sufficient full-problem example, not an eligible-family exclusion.
There is no EXCLUDED/HIT cross-layer separation identifying a single
sufficient released structure. X35 Seeds1/2 demonstrate legal within-order
quantity improvement while still failing the target, so exclusions do
not mean that quantities never help.

Recommending **no new complete-method mechanism** and closing this
diagnostic expansion is supported by the evidence and historical boundary.
The useful order/owner exclusions are retained, while the one broadest
MIP does not discriminate between ownership release and outside-E
activation. No renamed R96 fixed-route oracle, enlarged R160 block,
complete-method gain, future pilot or automatic extra time/Seed/input
expansion is claimed. B remains default with C166/D167 off. The EJOR/TRE/OR
author interpretation stays within these scoped facts.

The15 actual Optimize records have distinct call IDs and exactly one
flushed begin/end pair each: six tiny and nine substantive. Their Runtime
sum436.8279995918274s and Work sum847.4033862839872 agree with the cost
report. The437.2573462s recorded call outer fees sit inside the
551.9747133255005s enclosing diagnostic window, below5400s; Native is a
nested cost and is not added twice. No new Optimize was used in this
final review.

No further mathematical/model or conclusion-direction correction is
required. The finite qualifications and limitations remain as stated.

Final reviewed byte identities:

- `route_family_results.json` SHA256 `c0168c6e22aec6f863fb3728b3a1d6b5655494988b8ed461f21bf08d8f9b2991`.
- `route_family_results.csv` SHA256 `da19fe66eb54f3c9f139ef7ba0308e8690e3254505ebcd20e2589406945fbe8f`.
- `research_decision.md` SHA256 `4d371fb7c42f0f3bdcc16919af1b1b93ef6018631e3ce3508f03a8648a3c6b95`.
- `author_decision_memo.md` SHA256 `97264ce7db744bb11ce4c341ed3b007966bd866c62f89420c190f11e2c16e497`.
- `cost_report.json` SHA256 `381c2be23abce2a6bcf1881ffe560564d22fe4955088543c213700b4ca80f682`.
- `route_family_theory.md` SHA256 `e4af508055bf7d581c5300b4f346aec75709672f8db5236991b7a0114deda7bc`.

The final readback wall window was measured from 2026-11-15T03:53:00Z to 2026-11-15T03:54:43.853975+00:00, **103.853975s**. The earlier model review was not separately clocked; its complete active duration is not invented. Both review periods belong to the shared scientific wall window and are not additive Native charges.
