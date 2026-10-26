# Independent preimplementation reliability review

Reviewer: `/root/reliability_review`; primary implementer: `/root`.
Review baseline: `1ae14721e800d7c601adc1e7e42d5dfa89e48fbb` (PR 194).
Scope: targeted source/data reading and an independent all-row rational
completion check. No native module, Optimize, compilation, full campaign
restore, or performance rerun was used. This is an internal independent
review, not third-party replication.

## Decision

The proposed architecture is admissible **subject to implementation and
candidate review**: separate raw observation, local source qualification,
global coverage, and final certificate predicates; derive parameter
expectations from the declared method/numerical policy; revoke any source
contradicted by the same run's verified same-domain witness; prevent every
reachable consumer from using it. If prior controller dependencies cannot
be restored rigorously, abandon that controller state, preserve its audit
history, retain a verified feasible upper bound, and return an explicitly
full-domain open state with the independently justified floor zero. Normal
qualified sources must retain their existing ability to improve bounds
and close leaves. This is a failure path, not unconditional open behavior.

This decision is not candidate qualification, a declaration that numerical
root causes are repaired, or authorization to enter D before source/tests
are independently reviewed.

## Directly confirmed facts

1. `GurobiBaseline.cpp::evidenceParameterReadback` hard-codes `Seed==0`,
   even though the constructor separately checks requested/effective Seed.
   D_group15/16 X-15-B P and S2 have identical same-method model identities
   and the same non-Seed settings. The Seed0 MIP journal calls qualify;
   Seed1 MIP calls do not. The slice evaluator folds parameter conditions
   into its active-scope predicate and consequently reports
   `native_scope_not_matching_frozen_live_leaf` for this parameter failure.
   Existing `round127_evidence.expected` and Seed projection do separately
   compare requested/effective settings (currently declared Seeds 0–3).
   This producer bug alone does not invalidate every historical Seed1
   certificate.
2. In D24, call4's model is
   `a630251059be795777416ea1d63e6d8881c17baf1b75ccba776b5004a7294bc1`.
   The retained physical witness sequence21 belongs to
   `[0,0.16038610038610038]` and satisfies the same cutoff. The three
   sequence17/18/19 observations exceed its physical objective zero by
   more than `1e-7`. The original failure disposition remains REJECTED.
3. D24's exported `active_leaf_valid_lower_bound` and
   `valid_global_lower_bound` contain those three values. The actual
   Optimize ledger has parent LP, two child LPs, and terminal MIP only;
   the target ledger is empty. Tree events contain LP completion and
   terminal completion only; terminal L=U=0. Source inspection confirms
   callback events are replayed into the exported trace after solve
   returns, while scheduler merge uses the final native bound. Therefore
   this is demonstrated trace pollution; outer bad-bound pruning is not
   demonstrated. Native internal pruning and counterfactual search remain
   UNKNOWN.
4. C_group03's `02_SC-B20-S_S0_R1_S2R` launch has `expression=geom`.
   Its native terminal log returns OPTIMAL after 705.47 native seconds,
   with Obj/Bound approximately `0.3153886972242`; physical result U is
   `0.31538912105343886`, retained L `0.31538869722423574`. The gap is
   approximately `4.238292031e-7`. Its existing rejection is
   `global_bound_gap_not_closed`, with engineering failure reason `none`.
   This is qualified-open absent another source/physical failure. It is
   not a timeout and not a lower bound exceeding a feasible objective.

## Complete D24 rounded-matrix check and C decisions

`directed_old_evidence_check.py` reuses the old narrow, read-only
physical/seal checker and independently maps every column of the actual
call4 LP. All parsed numeric coefficients are first read as binary64 and
then represented as exact `Fraction`s. This is a statement about the
serialized binary64 matrix, not ideal rational problem coefficients or
the solver's invisible presolved/cut matrices.

The tight mathematical zero completion has objective zero but fails three
actual ratio equalities: c20928, c20948, c21020. Each absolute residual is
exactly `1/18014398509481984 = 2^-54`. Therefore physical domain membership
does not prove strict feasibility of that particular tight completion in
the rounded matrix.

There is nonetheless a complete **exactly feasible** rounded-matrix
extension of the same fleet. Set ratios using the actual ratio equations,
set the associated absolute deviations and pair differences, and use the
legal auxiliary epigraph value `G=2^-40` with matching state products.
This changes no model, input, parameter, or physical fleet. All 22,996
rows, 9,391 bounds/columns, variable types and 601 equalities pass exact
rational checks. Its actual objective is

`295153098392673137459/324518553658426726783156020576256`

(approximately `9.09510704596994e-13`). Its model objective is slightly
above the physical objective zero; do not claim an exact objective-
preserving rounded embedding. It is nevertheless far below each rejected
bound, even after the inherited `1e-7` comparison tolerance. Thus these
observed bound failures also have a serialized-matrix feasible-point
counterexample; the `2^-54` ratio residuals cannot explain away them.
The selected epigraph slack is a diagnostic feasible point, not a new
numerical threshold or a subtraction from a claimed bound.

The later preregistered C-R3 read-only load compares this serialized matrix
with a fresh initial model read by the original DLL, without Optimize or
Start. Its 269462 field comparisons differ only in the signs of three zero
RHS values (`c3016`, `c3018`, `c3019`). Thus the exact rational linear model
is identical, and the complete previously proved point transfers to that
fresh engine-loaded initial matrix. The raw binary64 fields are not all
bit-identical. This is not a snapshot of the historical retained model,
presolved matrix, cuts or native tree. See `d24_loaded_transfer_review.json`.

The completion is reproducible from the checker and saved fleet, and both
complete point maps have canonical SHA256 identities in
`directed_old_evidence_receipt.json`. No full duplicate vector is needed.
The full-domain cutoff is an inclusive `<=` row in this matrix; the
rounded-matrix feasible extension obeys it exactly. A native INFEASIBLE
claim for this call would contradict that extension; a physical boundary
witness in another call is not, by itself, proof of rounded-row extension.

**C-R1: no additional original-native reproduction is needed.** The sealed
physical witness, actual trace/ledger, rejected observations, and complete
rounded-matrix feasible counterexample suffice to localize the retained
failure to native bound/numerical treatment rather than a missing fleet
extension. Invisible native internal causes remain UNKNOWN. The unused
C-R1 budget cannot become a parameter grid.

**C-R2: existing evidence is insufficient for the requested native/physical
component comparison.** The old GEOM arm retains pre-LP and submitted
Start vectors, not its final native/MIPSOL full vector. A bounded,
preregistered new diagnostic acquiring g/e/service/route coordinates and
quality attributes is appropriate. It must retain its new diagnostic
identity and costs, and must not replace R132 time or qualification.

Two completed checker revisions consumed measured script outer times
1.3915364999556914 and 1.6453079000348225 seconds respectively. They are
non-native B/postverification, not D performance or new E enumeration.
The first was before adding the inherited physical/seal replay and point
identities; the final receipt reports the second run. Source reading time
is not exact CPU or an additive experimental charge.

## Required consumer changes and test implications

| Consumer | Existing reachable behavior | Required qualification/rejection result |
|---|---|---|
| MIP callback / target | Reads finite raw callback bound; journal failure does not gate target | One local-source predicate before target decisions; preserve raw progress; later contradiction revokes the whole call |
| LP return | Reads optimal ObjVal as bound; MIP journal preconditions deliberately exclude LP | Separate LP conditions; do not disable all LP bounds by reusing a MIP-only flag |
| Terminal / target return | Raw `native_bound_available`; native OPTIMAL/INFEASIBLE can close | Qualified bound and qualified status/source; physical gap beyond contract leaves domain open |
| Parent/child LP and lookahead | Native LP bounds merged/cached, cover built later | Apply local qualification before cache/merge and preserve precise scope/epoch; global cover is a separate proof |
| Scheduler merge / close | Sources have generic strings, old monotone maxima can survive later failures | Track/reject dependencies, or explicitly abandon prior controller and publish safe full-domain open fallback |
| Exported trace | Replays raw callback bounds under names containing `valid`; clamps global value at U | Keep raw values in raw fields; qualified fields cannot silently contain rejected raw observations; separate retrospective replay from control events |
| Certificate / final result | Uses controller flags and finite global bound | Rejected source cannot survive in LB, closed flags, coverage-derived certificate or certification time; preserve verified U |
| Offline reader / table | Independent Seed projection and source reconciliation; different historical performance predicate | Freeze new explicit predicates; preserve old data and the original R132 formal denominator/disposition |

Specific hazards to check in the candidate:

- Source contradiction and evidence-I/O failure must be distinct. Semantic
  revocation must not stop raw recording. Missing or corrupt evidence
  cannot be called a known same-domain contradiction.
- New witnesses must be checked against each source's frozen call domain,
  not merely the current cutoff/epoch. Different model or cutoff identity
  does not decide membership; verified G/F membership does. Domain-outside
  witnesses do not revoke unrelated sources. Boundary-uncertain numerical
  membership must not be presented as strict mathematical membership.
- Full-original and local cut-model qualification must not require a
  complete global cover. A finite local bound can be useful while cover
  remains incomplete; it cannot then issue a global certificate.
- The unconditional leaf bound is `min(b,c)` only after the restricted
  source is qualified, including the mathematical cutoff complement.
  This operation must never conceal a same-domain contradiction.
- Parameter expectations for fixed tolerances must come from a declared
  numerical policy, not from the observed readback itself. Preserve
  mismatch/read-error/model/scope/cover/source/quality/missing-evidence
  reason categories. Test a supported Seed beyond 0/1 and deliberate
  mismatch.
- On late source rejection, merely assigning result.L=0 while retaining
  closed/controller-valid/certificate flags is insufficient. A safe
  fallback must explicitly retain the full unresolved original domain.
- Test normal positive certificates, qualified-open returns, and safe
  rejection. Unconditionally disabling proof is not S2 qualification.
- Fixtures for NEXT/child/epoch/revocation semantics are not natural
  performance records; do not force splits to obtain them.

## D matrix and budget review

The fixed 14-arm arithmetic is correct: X35 2x2400=4800;
SC-B20-S S2R/GEOM 4x1200=4800; K-15-S P/PS/S2 6x600=3600;
UC-B20-B 2x1200=2400; full arms total 15,600 seconds. Build/tests have at
most 2400 additional seconds, so D1/D2 total 18,000. Conditional D3 is
8 full arms/7200 seconds (SC-C15-B 4x600 and SC-B20-S 4x1200). The whole
package ceiling is 39,600 seconds, including C7200, E1800 and repair5400.
Nested child/Runtime/Work costs must not be added to outer process wall
again. D requires serial single-thread native calls without simultaneous
compilation, heavy parsing, packing or PDF export.

The proposed online qualification and safe-rejection changes affect
production behavior and timing. If adopted as the manuscript implementation,
they trigger D3; it is not optional merely because the model rows stay the
same. D1's S2R/GEOM is not a substitute for D3's original/fixed S2.
Freeze identities, full argv, input identities, order, readout and caps
before seeing any candidate qualification result. Qualification inputs are
exposed regression inputs, not holdout. Do not extend caps, add Seeds, or
rerun ordinary open/Lose/slow observations.

Candidate freeze/source/test review, final metric reconstruction, E math
review and final delivery review remain pending. No D admission or final
PASS is implied by this preimplementation decision.
