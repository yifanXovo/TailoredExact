# Native sources, qualification and consumer contract

Status: finite D1 implementation/failure-disposition qualification independently PASS; all D3 runs complete. Final science and delivery review pending. The old rejected
call remains REJECTED. This note does not declare native reliability repaired.
The independently reviewed design is in `review/design_review.md`; actual
candidate/plan hashes and finite execution outcomes supersede provisional
builds only after a recorded freeze and admission.

## Four inherited facts and their scope

1. R132 D24, X-35-U/Seed1/S2, call4 has model SHA256
   `a630251059be795777416ea1d63e6d8881c17baf1b75ccba776b5004a7294bc1`.
   Its own sequence21 fleet has exact integer inventory Y=D, hence G=P=F=0.
   It belongs to G in [0,0.16038610038610038] and F at most that cutoff.
   Sequence17/18/19 bounds 2.2155204177669103e-7,
   2.3794866331140976e-7 and 2.889725344877011e-7 each violate the inherited
   1e-7 contract. This is an own-source counterexample, not a transferred P
   certificate. The historical position remains UNEVALUABLE; it is not an
   eighteenth formal S2 certificate or a Win.
2. The three numbers appear under names `active_leaf_valid_lower_bound` and
   `valid_global_lower_bound` in the old exported trace at approximately
   110.1104132,116.4877274,128.204897 seconds. The writer replayed callback
   events after Optimize returned. The actual outer scheduler merged final
   outcome.native_bound=0, with only parent LP, two child LP probes and one
   terminal MIP; split=0, no target phase, no target ledger entries. The
   terminal tree event has L=U=0. Therefore trace contamination is established;
   actual erroneous outer pruning is not. Native internal pruning and a
   counterfactual search remain unknown.
3. The producer's old evidenceParameterReadback required seed==0. X15B
   D15/D16 supplies same-model/same-cover P/S2 controls: readback differs only
   by Seed, yet Seed1 loses journal eligibility and receives a misleading
   scope reason. Its separate offline actual-Seed check qualifies those
   sources. `historical_impact.md/.json` preserve this distinction and exact
   evidence hashes; the bug is not a reason to invalidate all old Seed1 data.
4. C03 SC-B20-S/Seed0 is actually GEOM despite the launch method label S2R.
   Native status is OPTIMAL with Obj=Bound approximately 0.3153886972242;
   physical U=0.31538912105343897 leaves about 4.238292032e-7. The complete
   old production workflow took about707.443s, not a1200s timeout. A positive
   physical gap alone is qualified-open when source/physical/other contracts
   hold; it does not alone establish source contradiction or UNEVALUABLE.

## Mathematical contract and numerical claims

For physical feasible set X, region I_l and legal cutoff c, use
X_l(c)={x in X:G_true(x) in I_l,F(x)<=c}. An exact native relaxation must
contain every such point's legal extension and underestimate F there. A
qualified bound b on that restricted set yields the unconditional regional
floor min(b,c), because the objective-cutoff complement has F>=c. Infeasibility
of the restricted model yields floor c, not infinity for the original region.
Take maxima only of independent valid floors for the same region and minima
across a complete regional cover. A missing child, discarded interval or
cutoff complement cannot be recovered by numerical clipping.

A verified same-input witness refutes a raw restricted claim only after
membership in that call's F/G domain is confirmed. Model SHA or the cutoff
used to generate the witness is not its membership criterion. New source
checks do not expand the physical witness domain by1e-7; that tolerance is
used for the objective discrepancy, not to admit an out-of-domain witness.
The source's raw claim is checked before any min(b,c). None of min(L,U),
negative-gap clamping, deleting bad observations or subtracting an observed
constant is a source repair.

The exact algorithm, ideal coefficients, loaded binary64 matrix, commercial
numerical bound, independent physical witness and finite engineering
qualification are separate objects. The project's1e-7 numerical contract is
not derived from Gurobi's feasibility/optimality/integrality tolerances.
MIPGap=0 is not exact arithmetic. No tolerance has been relaxed in this round.
Finite qualification does not prove every future commercial native bound.

## D24 complete actual-model extension

`review/directed_old_evidence_check.py` reconstructs the own zero fleet and
checks all22,996 actual LP rows,9,391 columns and601 equalities with Fraction
arithmetic on the serialized binary64 coefficients. The naive mathematical tight
completion has three ratio-equality residuals, maximum1/2^54. It is therefore
incorrect to call that naive vector exactly feasible for the rounded matrix.

Using each actual ratio coefficient, adjusted r/e/h and legal epigraph slack
g=2^-40 gives a complete exact feasible extension. Its model objective is
295153098392673137459/324518553658426726783156020576256,
approximately9.095107e-13. This complete matrix counterexample is also far
below all three native bounds, beyond the original1e-7 check. Tiny coefficient
rounding cannot account for the observed bound gap. The exact loaded model
objective is not asserted to equal the physical zero exactly. The native
bound layer is implicated; the commercial internal mechanism remains UNKNOWN.
A fresh read of this same LP with the bound original DLL was compared against
the serialization (269,462 comparisons): only three RHS positive/negative
zero bit differences occur. Thus the rational model and the exact extension
proof transfer to that fresh loaded matrix. This does not reconstruct the
historical presolve, retained cuts, basis or MIP tree.

The independent reviewer accepts C-R1 NOT_NEEDED on this evidence. Its unused
2400s allowance is not converted to a numerical parameter search. C-R2 and one
prospectively fixed C-R3 model replay were completed under the recorded plans.
C-R2 reproduced native OPTIMAL with physical gap about4.238292e-7 in709.219s.
The initial C-R3 interpreter failed before Env/Optimize; its0.156s and logs
are retained. An explicit runtime-only repair used the existing Gurobi Python
environment and the same model/DLL, cold start and parameter policy. Its one
Optimize returned TIME_LIMIT in1169.336s outer time. Eight saved vectors were
checked; the final physical objective agrees with native incumbent to rounding.
An intermediate g has slack, so native g cannot simply be equated to G_true.
The replay did not reproduce the original gap; the original point was not
saved and the internal cause remains UNKNOWN. A physical-readout helper fix
preserves its first output and binds the repaired comparison to the identical
point hashes; it starts no additional Optimize. These are diagnostic evidence,
never a replacement for an old or new performance position.

## Implementation design and actual consumers

The declaration of the numerical policy is fixed: Threads1, requested Seed
and Presolve, registered MIPFocus/Cuts, MIPGap=MIPGapAbs0,
FeasibilityTol1e-6,IntFeasTol1e-5,OptimalityTol1e-6. Read errors, unsupported
requests and mismatched individual parameters have distinct reasons. The
expected values are not copied from readback. Model identity and model/domain
mapping failures remain separate from parameter, cover, witness and native
quality failures. Settings preserve actual and expected values.

NativeEvidenceJournal now also maintains same-run source qualification in
memory when receipt output is disabled. Local qualification is independent
of global-cover completeness. It remembers both peak bound claims and
INFEASIBLE claims for each original frozen call scope; every later same-run
physical witness is checked against all of them. Semantic source rejection
leaves raw observation recording enabled. An evidence-I/O failure and a
semantic source rejection are separate states; both prevent proof use.

| Consumer | Qualified input and effect | Rejection disposition |
|---|---|---|
| Native callback bound target/NEXT | Same local predicate, then unconditional regional min(b,c) | No target termination from unqualified raw values; safety rejection terminates explicitly without proof |
| LP return and child probes | Actual model/parameters, completed LP status and local qualification; probes need not already be live global-cover pieces | No bound or infeasibility promotion from unqualified return |
| Target/terminal return | Raw quality and status preserved; final own witness and raw final bound checked before qualified derived values | No optimal/infeasible close from rejected source |
| C6 target close | Same physical-gap predicate as terminal decision | Native OPTIMAL with physical U-L>1e-7 remains open; no fabricated timeout |
| Scheduler merge/close and child cover | Only qualified unconditional floors; original cover transactions remain | Late rejection abandons the dependent control state |
| Final certificate | Source and physical gates plus complete cover and ordinary lifecycle | Full-domain analytic floor0 and verified own U; strict native certificate false |
| Trace | Raw callbacks retain their clocks in journal/progress; qualified retrospective rows use availability after native return | A rejected call supplies no qualified callback replay; source revocation is explicit |
| Future offline reader | Immutable bytes/sequence/clock, requested/actual policy, physical/model/Start/return/source/cover semantics | Rejected source differs from ordinary qualified-open; performance eligibility remains explicit |

On late rejection, the implementation records the abandoned leaves and
replaces the controller with one open region [0,(n-1)/n], analytic floor0 and
the best verified own U. No old monotone maximum, contraction or closure is
retained. This is a new proof epoch and complete unresolved domain, not a
claim that resetting an outer bound repairs native internal pruning. If an
own-zero physical proof exists, it remains independently recognizable;
the rejected native tree does not regain qualification.

The original S2 full framework remains operational for normal sources.
Instance names, Seed identities, model-SHA lists, machine speed and elapsed
seconds do not select safety behavior. H, pair/triple support, leaf ranking,
resource semantics, baseline policy and repository ENS-C default are unchanged.
Two model emitters formerly inserted artificial 0<=-1 when a penalty-floor
test was within1e-9 of cutoff. This can exclude a legal inclusive boundary
point. Both shortcuts are removed, preserving the actual penalty-floor rows.
The exact dyadic positive-lambda boundary fixture checks all27 rows/bounds
and shows the old empty row fails. This is a model behavior repair and triggers
D3 if the candidate is adopted; it does not explain the feasible D24 matrix or
the already shortcut-free S2R/GEOM anomaly. R105/R107 disabled modes receive
only signature compatibility for their pre-existing fixed parameter policy;
they are not reopened as research architectures.

## Version, tests and remaining admission

The candidate is separately built; it is not frozen E3. Scope/Request/Outcome
ABI equivalence was actually compiled against pinned old and new headers
(`qualification/ABI.json`), after review identified and removed a proposed
embedded Scope field. Settings metadata uses the inherited JSON carrier.
The initial compile failure and a zero-cutoff test expectation failure are
retained in fees; necessary repairs do not hide their costs.

The bounded tests cover supported Seed0/1/42 and the declared upper Seed,
wrong readback, fixed-policy mismatch, local-without-global cover, same-domain
zero contradiction, F/G-outside witnesses, late bound and infeasibility
revocation across calls, loaded return/S=0, abandonment of a dependent closed
state, GEOM-type qualified-open, target disposition and a normal positive
optimal close. Journal lifecycle/receipt/quality/revocation fault checks now
pass, with the initial missing-metadata import failure retained. Only5832bytes
of pinned R94 metadata were staged for pure inherited reader imports.
Independent frozen source/matrix admission is recorded for D1; D3 execution remains gated. No fixture is a natural
performance instance.

D1 fixes14 full exposed regression positions/15600s and at most2400s build/
small checks, total18000s. D3 is triggered if this behavior-changing version
is adopted as the manuscript implementation:8 full arms/7200s, with complete
same-environment original/fixed S2 pairs. D results cannot silently replace
R132 timing or support performance claims for paths not actually exercised.
All 14 D1 positions are sealed; managed outputs qualify implementation/failure disposition 14/14 and native/source 13/14, with 8certificates/5qualified-open/1natural source-rejected safe-open. D3 outputs are complete (eight qualified certificates, four time-close pairs); independent D3 completion passes; pre-release science/artifact and delivery review remain PENDING.

## Post-seal accepted-H reconstruction repair

D1 execution has independent admission (`review/D1_admission.json`); the bounded positive native unit also passes with exact own U=L=1.5=oracle 3/2, actual 3 LP+1 MIP OPTIMAL and complete H/Start/return/seal evidence. The unit is excluded from the 14-position qualification/performance sample. Actual tree-call native statuses must come from journal native_quality or optimize ledger: generic endpoint.native_status can inherit result.gurobi_status=0 and is not the per-call status source.

The first D1 X-35-U/Seed0 arm seals normal four-call production and ownzero. Its first frozen postverifier fails because it assumes accepted H equals the exchange-descent final fleet. Actual reused main only updates routes on Fnew<Fold-1e-10. Two neutral and zero strict improvements leave its initial fleet accepted, matching the journal. The real defect is post-seal reconstruction, not H/native production.

Explicit adapter `scripts/round133_postverify_repair.py` SHA 8feae1d544d92fba843f4836f0c685c2cf38151f20386cd2538396ac34af6640 and amendment 7501459291ac9a7a2945f0ce022f52a72d09822df21cec7eb014889f0a8e4f6b preserve all original helper, matrix, PE/native-argv and seal identities. 41 controlled fixtures pass; independent repair/first-effective-receipt review permitted continuation under the same amended wrapper; all 14 D1 positions subsequently sealed. Cold P no-H/null and PS original numerical Start auditing remain. The adapter operates only after producer seal, with a unique effective receipt/four-output SHA gate; original failure/fees remain and no Native retry occurs.

The repaired first endpoint is source/native/model/physical/lifecycle qualified with own-zero U=L=0. Tproduce/Tcert remain 120.17624272953253 seconds, Tverify 1743.5059913999867 and Ttotal 1863.6822341295192 retain actual disposition delay. Later K15 methods and both D3 versions use the same management wrapper; imports/admission wall are paid, never subtracted. The first qualification wrapper differs; this is not a fresh cross-version comparison. No whole-D or final implementation PASS follows. See `review/D1_postverify_continuation_admission.json`; D3 execution and finite completion qualification pass; pre-release science and delivery remain pending.

## Complete fixed D1 observations

Managed reports/D1 arms/pairs now contain all 14 sealed positions and all 8 planned comparisons, without missing positions: 8 certificates, 5 qualified-open results and 1 natural source-rejected safe-open. Implementation/failure-disposition qualification is 14/14; native/source qualification is 13/14. X35U Seed1 ownzero remains analytically independent while certificate/native/performance flags are false and Tcert null; the actual rejected source triggers full-domain OPEN and does not regain proof credit. The commercial internal reason remains UNKNOWN. Seed0 is a normal clean source-qualified ownzero certificate.

K15 S2 certifies at both Seeds while P and paid PS remain open; GEOM is a certificate-direction Lose to S2R at both Seeds, with Seed0's physical gap 4.238292e-7 kept open and Seed1 slower. UCB20B has positive certificates in 4.117/4.011 seconds and 11 native calls each; independent D1 review confirms three splits, nine LP(one root/eight child), one child-target interrupt/requeue with cache reuse and one terminal MIP per Seed. Actual NEXT remains zero. Normal proof functionality and genuine source-failure handling are therefore both observed, without declaring all native sources reliable. D3 runs are complete; independent final-science review and publication/PDF/restoration remain pending. R132's historical 17/24 plus separate ownzero is not relabelled.

## Complete actual paths and adopted-version bridge

All 14 fixed D1 positions are sealed and independently pass finite implementation/failure-disposition qualification: 14/14 implementation, 13/14 native/source, eight certificates, five qualified-open and one naturally source-rejected safe-open. The set is exposed regression evidence, not holdout. X-35-U Seed1 reproduces the same three raw bad bounds; sequence 27 is its own zero witness, 28 records rejection and 31 the API return. Native MIP is INTERRUPTED; the dependent controller is replaced by an OPEN full domain [0,34/35], with own U=L=0 but certificate/native/performance false and T_cert null. The independent physical zero remains. Rejected raw values are absent from the qualified trace. This demonstrates correct source rejection and complete-domain preservation, not repair of the native internal search, whose cause remains UNKNOWN.

Normal positive proof functionality remains: K-15-S S2 certifies at both Seeds while cold P and paid PS remain open; the four corresponding S2 comparisons are one-sided certificate Wins and the two PS/P comparisons are both-open. GEOM loses to S2R at both Seeds; Seed0 is native OPTIMAL with physical gap 4.238292032e-7 and remains qualified-open, while Seed1 certifies in 781.293 seconds versus 681.174. These are known qualification controls, not a new performance population.

UC-B20-B at each Seed has three actual atomic splits, nine LP calls (one root and eight child), one CHILD_BOUND_TARGET_MIP interrupted after reaching its target and requeued, cached-child reuse, and one terminal OPTIMAL MIP: 11 Optimize calls. Positive certificates take 4.117/4.011 seconds. Natural NEXT calls are zero throughout D1; NEXT coverage is static and controlled D2 semantics only, with no natural NEXT performance claim. Actual native statuses come from per-call journal quality/optimize ledgers, never the generic legacy endpoint.native_status=0.

All eight fixed D3 arms and four complete known-role/Seed pairs finish with source/model/implementation qualification and certificates on both sides. Candidate versus original E3 gives two strict Win and two Lose; every difference is TIME_CLOSE under the unchanged materiality convention. Signed candidate-minus-original T_cert is +0.002491188934072852, -0.30825315485708416, +1.2644485813798383 and -2.450773081742227 seconds in the table order. Both sides have identical corresponding qualified endpoints; their separate actual production/verification/total clocks are retained. Independent D3 review accepts all eight arms and four pairs. Each old/new pair has the same four actual canonical model SHA values, complete own-H semantic SHA and accepted-H fleet SHA. All 32 actual model-contract marker checks are empty, and a separate scan of six unique actual canonical LPs finds no known artificial 0<=-1 row. The conservative legacy UNEVALUABLE branch was not triggered; no marker case was promoted back into eligibility. Consequently D3 does not exercise a domain where removal of that row changes the model. The bridge bounds timing claims to the two reached known-role domains; performance in changed-marker, natural NEXT or other untested domains is not established. Exact dyadic D2 tests supply the removed row's correctness check, not changed-domain performance evidence.

Each arm actually executes three LP calls and one terminal MIP, with no target or NEXT call; these known mostly-root paths do not validate broader split/target/NEXT performance stability. Both versions pay their own complete H/Start/physical/source/return costs, under the same amended management wrapper and declared resource/cap policy. Original and candidate verifiers can have different actual costs; none is subtracted. Four Seed pairs on two previously seen inputs are not four independent new problems, and this bounded bridge does not support a global speed claim or retroactively relabel R132 timings as candidate measurements.

Actual finite compute total 11824.854547899857/39600 seconds; D3 outer cost 3508.809842899791 seconds. All formal compute receipts are closed. Postverification/prose/PDF/delivery remain separately metered, without adding nested native Runtime/Work.
