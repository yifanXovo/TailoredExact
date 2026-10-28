# Independent interim review of the offline Round137 pipeline

Reviewer: `/root/independent_review`, 2026-10-27 (Asia/Shanghai). Scope:
small saved source files for `round137_analyze`, `decision`, `documents`,
`plots`, `portable_check`, `release` and RESUME, with the directly relevant
R133/R134/R135 helpers. This is a source review of moving offline prototypes,
not final scientific/PDF/public-recovery acceptance. While the serial native
queue is active, this reviewer did not parse large raw journals, run an
optimizer, compile, export PDF, archive, restore or load a native library.
Only this review file was written; implementations and the frozen measured
helper graph were not changed by the reviewer.

## Concrete findings and minimum corrections

1. **Relative gap at zero U (initial defect; structurally corrected during
   review).** The initial analyzer used `(U-L)/max(abs(U),1e-12)` and would
   report a zero percentage for an exact-zero case. The accepted
   `round108_decisions.relative` instead returns null with reason
   `original_zero_objective_tolerance` at abs(U)<=1e-12 and preserves signed
   gaps otherwise. Latest source calls that accepted helper and checks agreement
   with the stored endpoint. This addresses the scientific-definition mismatch;
   actual derived-output validation remains after execution.

2. **Logical AM decisions were missing (initial defect; structurally corrected
   during review).** `adaptive_mass_decision_ledger.csv` is written only when
   neither child LP is infeasible (`PaperExternalGiniTree.cpp`, around 7720).
   It therefore cannot alone substantiate all logical/terminal exposure claims.
   The latest analyzer joins `c6_split_decision_ledger.csv` and the finite-score
   ledger by unique decision_sequence, checks consistency, separates logical
   one/both-infeasible, finite gate, finite no-strict-improvement terminal and
   other actions, and leaves logical score/margin null. This is the correct
   direction. The documents' score maximum now filters actual finite gates.
   Runtime-check the real joined ledgers after the queue is idle; do not infer
   threshold sensitivity from a logical split or terminal decision.

3. **Closed-root input/progress admissions (initial recovery blocker;
   structurally corrected during review).** The first prototype allowed only
   the current round tree and omitted the R135 checker's exact per-launch input
   and native-progress admissions. Six known inputs live outside that tree,
   and progress can live under results/gurobi_work. Latest source adds the
   declared per-launch files without admitting whole historical trees. Validate
   this in the planned local pure replay before the one real public recovery.

4. **Copied historical appendix points to the wrong current files (open at
   inspection).** In copied Appendix B.1, the R135 candidate/first-stage/
   conditional-stage links remain relative `candidate_manifest.json`,
   `C_matrix_frozen.json`, `D_matrix_frozen.json`; the latter two do not describe
   Round137, and the first would falsely identify Round137 metadata as R135.
   Pin those historical links to the actual R135 commit and add the actual
   current matrix/config/source identity as the new entry. The formulation
   proofs may be retained while updating their version/reproduction gateway;
   an `exact_appendices_retained` receipt must describe the actual final edits.

5. **Stale prose/figure references (open at inspection).** The retained body
   says a state-penalty projection comparison is in Section 6, whereas new
   Section 6 is the mechanism/AM section. Point to the correct historical
   supplement or retained discussion. Present-tense main-method references
   still say S2 in support/startup/pseudocode; use GI-TBC with S2 confined to
   its stated historical identity. The appended R135 supplement references
   `figures/count_bound_scope.png`, but the new prepare routine copies no
   historical figures. Either copy that exact existing source asset or pin
   the old reference to its historical location. Check other relative links
   in the inherited supplement before calling it independently readable.

6. **Strict positivity needs its positive-weighted-objective premise (open at
   inspection).** General model prose permits lambda>=0, while the newly
   inserted shortage statement concludes F>=lambda*a*s>0 without stating
   lambda>0 (equivalently rho>0). Add that premise explicitly in the maintained
   body and mathematical note. B2 rho=1 and B3 rho=.5/1/2 satisfy it; the actual
   registered experiments and preflight proof are unaffected.

7. **Actual depth/width limits are not yet fully analyzed.** `AM_max_depth`
   currently measures the largest parent depth among logged decisions. It is
   not the largest reached leaf depth and does not establish whether depth8 or
   width1e-4 prevented a split. Use saved leaf/event evidence to report reached
   geometry and any directly exposed limit-trigger reason. If a trigger is not
   recorded, say unknown rather than converting a configured value or missing
   decision into an observed trigger. This needs only existing saved data.

8. **Root comparisons need an explicit matched-scope eligibility field.** The
   latest analyzer requires a complete optional root-point record, which avoids
   treating partial optional CSV output as a real root. Before using its
   numerical differences as group attribution, compare full and variant own-H
   semantic/fleet identity, initial G interval, objective/weight and cutoff.
   Publish a matched-scope flag/reason; show unmatched root observations as
   descriptive. Reoptimizing auxiliaries is appropriate; fixing them to the
   full solution is not. No extra root solve is required.

9. **Add finite public binding assertions.** The prototype should check that
   the capsule's helper hashes equal frozen matrix.helpers, that the matrix's
   candidate/plan/input SHA fields equal restored bytes, and that each restored
   identity's launch equals the corresponding frozen launch. The package writer
   already checks many of these locally; the public checker should also bind
   its replay bytes to the declared execution identities. These are small
   existing-metadata assertions, not a new numerical qualification framework.

## What the current design gets right

The aggregation retains all registered positions and separate B1/B2/B3,
Seed0/Seed1 and mechanism/AM denominators. It counts only performance-eligible
certificates, carries U and L separately with signed gaps, keeps null open
certificate times, and conditions geometric speed ratios on both-certified
pairs. The inherited pair function uses the declared max(10s,10% of faster
certificate time) materiality rule; it does not convert a cap into a solve
time. Source-reduced observations remain distinguishable from ordinary open
results. The retained raw-versus-qualified certificate fields are useful.

The new paper sources preserve the actual physical problem, own paid H,
same-problem HGA-TGBC lineage, historical source versions/denominators and
synthetic operational-data boundary. Fixed lambda and fixed rho are separated;
resource inclusion is not misrepresented as runtime monotonicity. The proposed
resource figure labels U/L as finite endpoints and uses filled U markers only
for eligible certificates. Mechanism prose correctly treats deletion effects
as conditional, and distinguishes ideal LP inclusion from full-search cost.

The closed-root factory adaptation is narrow in source: it runs the exact
published Round137 wrapper's actual control/AP/A-B adapter setup, returns its
configured R135 verifier once, then applies the established R133 clock/path/
derived-write transport. It does not substitute a second verifier or weaken
physical/model/H/Start/source-return-cover predicates. Native process/DLL/network
entry points remain blocked by the engine. This source assessment is not a
claim that the new wrapper has already passed its local/public replay.

The release design preserves current raw in place, packs explicit physical
inputs, keeps failures/fees/costs, uses fixed current-source bytes and does not
repeat historical whole-campaign recoveries. Completion guards prevent planned
120 positions from being assembled as measured completion. RESUME accurately
distinguishes the healthy queue, resolved first-P pure-reader error and work
that is still pending.

## Final integration conditions

The decision/document templates still require evidence-driven interpretation
once all runs finish. Actual B2/B3 relative-method changes, Seed changes,
material reversals, AM gate exposure and each mechanism's supported conclusion
must be stated with concrete witnesses. A table followed by generic caveats is
not yet the requested answer to each scientific question. The mechanism table
should connect mathematical role, actual comparison, supported conclusion and
boundary. Keep the main text readable without requiring the reader to discover
the principal conclusion in a separate stage report.

After native work is idle: runtime-validate the pure analysis/assembly, inspect
the real derived values, validate the planned closed-root replay locally, then
perform actual PDF export and every-page visual review. None of the findings
above requires rerunning a healthy native arm, expanding the experiment matrix
or modifying the measured source/helper graph. The ongoing serial queue can
continue; final scientific/delivery acceptance remains pending actual results.


## Formal-paper structure review, 28 October 2026 (partial)

The independent reviewer inspected only the authoring/decision sources and small existing mechanism notes while position 94 remained live. The reviewer found that the original four-column definition table did not yet meet F3 and recommended a six-row five-column synthesis covering complete H, outer control, A/B, C_R, C_G and AM. The reviewer also recommended distinct Seed0 and limited Seed1 AM/mechanism blocks, with C1 8 additional/12 views, C2 16/20, and actual Seed1 shared defaults. The authoring source now prepares these changes and imports the evidence-bound research priorities into the main discussion. It has not been assembled or exported. All120/idle guards remain.

The review explicitly leaves 94-96, all Seed1 outcomes, actual root-domain/objective/cutoff matches, model/LP/MIP/Work/node attribution, depth/width audit and PDF layout pending. This is a scoped structural review, not final integrated acceptance. Main-process follow-up corrected the H row to compare P/PS, since PS/GI-TBC shares the defined own-H startup and does not isolate H.

## Limited Seed1 interim reviews

### 28 October 2026: first K15 main triplet only

Disposition: **PASS for `Seed1_K15_triplet_checkpoint.json` and the six
matching observations**, not complete D2 or final integration. Selected
actual Seed0 positions1/2/3 and Seed1 positions97/98/99 by declared role,
method and Seed. Read only the6174-byte checkpoint, small sealed endpoint/
result files (554334 bytes combined) and frozen launch metadata while100
was active. No audit, LP, live100, full analyzer, native, PDF or archive was
used. Only this review was appended.

All checkpoint endpoint hashes and compared fields match. Native results
report successful Gurobi Seed set/get return codes and actual effective
Seed0/1 matching each declared launch. All six retain the same input/PE,
lambda=.15, physical T3600 and cap600. T/cap are taken from the frozen
launch and checked against actual result fields; a missing compact-PS
endpoint T_seconds is not changed or interpreted as a different horizon.
Cold P has no applicable H fields, so its nulls are not failed H runs.
Within each Seed, PS/GI-TBC have independently complete own H with equal,
nonempty valid semantic/fleet hashes. Matching H does not transfer a Start.

All six own U=.5922648822560825. Only GI-TBC has its own qualified
certificate at each Seed:

| Seed | GI-TBC T_cert seconds | P final L | PS final L |
| --- | ---: | ---: | ---: |
| 0 | 112.76930311694741 | .5276627721386670 | .5205834419787349 |
| 1 | 115.44408525200560 | .5291148420406868 | .5322797793258769 |

The GI certificate-time difference is2.6747821350581944s, below the
declared max(10s,10% of faster time)=11.276930311694741s threshold. This is
an observed nonmaterial difference on one preselected role, not statistical
evidence of a runtime distribution or general Seed insensitivity.

The compact final-L ordering changes from P>PS at Seed0 to PS>P at Seed1.
This is a finite capped dual-endpoint direction change. All four compact
runs remain own open with null T_cert despite matching the GI feasible U;
they inherit neither a certificate nor a certificate time.

The original Seed0 observations remain in B1; the three actual new Seed1
positions are D2-main. No adverse first result is replaced, no two-Seed
pool is substituted for the main Seed0 denominator, and common Seed does
not imply common native random trajectories for different models. The
remaining three preselected main roles plus limited AM/mechanism repeats,
all120 analysis, root/cost integration, public recovery and PDF/final review
remain pending.

Checkpoint SHA:
`3540d9b13d6d272925d1a8bb80eb4b5805908c1c06cfb79eff0245649c66e4fb`.

### 28 October 2026: second UC main triplet only

Disposition: **PASS for `Seed1_UC_triplet_checkpoint.json` and its six
matching sealed observations**. Selected baseline7/8/9 and new100/101/102
by actual role/method/Seed (new PS100, GI101, P102). Read only the6494-byte
checkpoint, small endpoint/result files (554375 bytes combined) and frozen
launch metadata while103 was active. No audit, LP, live103, native, full
analyzer, PDF or archive was used. Only this review was appended.

Checkpoint endpoint fields/hashes match the sources. All six UC observations
are performance-eligible and have their own qualified certificate at the same
U=.5773330699702928, with T_cert=T_produce. Input/PE, lambda=.15, physical
T7200, Q/handling and cap1200 match. Actual result Seed requested/effective
values and successful set/get return codes agree with the declared Seed0/1;
physical horizon and nominal cap also agree with result readback. Within
each Seed, independently complete PS/GI own H semantic/fleet hashes match
and are nonempty. Cold P's absent H remains not applicable.

| Method | Seed0 T_cert s | Seed1 T_cert s | Absolute difference s | Declared threshold s | Material difference |
| --- | ---: | ---: | ---: | ---: | --- |
| P | 315.40275652264245 | 314.51318851392716 | .889568008715287 | 31.451318851392717 | No |
| PS | 236.09050685004330 | 125.39078612066805 | 110.69972072937526 | 12.539078612066806 | Yes |
| GI-TBC | 4.148974274052307 | 4.099896670319140 | .049077603733167 | 10 | No |

Applied the same max(10s,10% of faster certificate time) rule throughout.
GI-TBC is substantively faster than each compact method in both observed
Seeds on this role. However, PS's complete cost changes materially between
these two observations. The stable all-certified pattern therefore does
not establish stability of every method's wall time. This is descriptive
finite evidence under the predeclared threshold, not a statistical
significance claim, an estimated runtime distribution or a general Seed
robustness conclusion.

The actual Seed0 observations remain in the main B1 panel; the new triplet
remains D2-main. No first result is replaced or pooled into a new main
denominator. Two of four preselected main roles have now been reviewed in
this limited sequence; remaining main configurations, AM/mechanism repeats,
root/cost interpretation, all120 and public/PDF/final integration are still
pending.

Checkpoint SHA:
`838377d975a6429f685f704a6fe1b5b4db34be5a9a0aa056e62edebae4cd3768`.

### 28 October 2026: third R-B20 main triplet only

Disposition: **PASS for `Seed1_RB20_triplet_checkpoint.json`, its six
matching observations and the inspected new document/decision paragraphs**.
Selected actual Seed0 positions37/38/39 and new104P/105PS/103GI by declared
method. Read only the6910-byte checkpoint, small sealed endpoint/result
files (557367 bytes combined), frozen launch metadata and the corresponding
short authoring excerpts while106 was active. No audit, LP, live106, native,
full analysis, PDF or archive was used. Only this review was appended.

Checkpoint fields and endpoint hashes agree with their sources. All six
observations are performance-eligible. Input/PE, physical T3300, cap1200,
lambda=.07423904974016332 (rho1 on this input), Q=[30,30] and pickup/drop60
match. Actual result horizons/caps and Gurobi requested/effective Seed0/1
with successful set/get return codes match the frozen launches. Independently
complete PS/GI own H has equal nonempty semantic/fleet hashes within each
Seed; cold P remains not applicable for H.

| Method | Seed0 U / L | Seed1 U / L | Own certificate pattern |
| --- | --- | --- | --- |
| P | .5400846274202015 / .3581581080473884 | .4932244667705688 / .3546256862300782 | open / open |
| PS | .48663902305130596 / .3653241651989888 | .4807354359737054 / .36748229915779834 | open / open |
| GI-TBC | .4807354359737054 / .4807354229937215 | .4807354359737054 / .4807354342564066 | own C / own C |

GI-TBC's own certificate costs are784.1434840508737/656.7340374183841s.
The absolute difference127.40944663248956s exceeds the declared threshold
65.67340374183841s. This is a material descriptive shift on this finite
matched role, not statistical significance or an estimated Seed runtime
distribution. Stable certification pattern does not imply stable clocks.

Seed1 PS matches GI-TBC's feasible U but keeps its own L=.36748229915779834
and open/null-T_cert status; the GI proof/time is not transferred. Relative
to its own Seed0 result, P improves U but weakens L, so neither cross-Seed
endpoint dominates. PS improves both finite endpoints relative to its own
Seed0 result but still does not certify. These observations do not replace
the first runs or select a favorable Seed.

The new manuscript and stage-report paragraphs accurately preserve the
GI material shift, PS same-U/open distinction and P opposed endpoint change.
No scientific correction was found in this limited scope. Original Seed0
rows remain B2 and the actual new triplet remains D2-main. Three of four
preselected main roles have been reviewed; K35, limited AM/mechanism repeats,
full root/cost/120 scientific integration, entry/public execution and PDF
acceptance remain pending.

Checkpoint SHA:
`a1bd779b1453220c805bbe5eed85e45d0c938bf3795ae0252c6fe10e2e6906f6`.

### 28 October 2026: fourth K35 main triplet and selected-role counts

Disposition: **PASS for the K35 checkpoint and complete four-role main-Seed
endpoint denominator**, not AM/mechanism or final integration. Selected actual
Seed0 P15/PS13/GI14 and Seed1 P106/PS107/GI108 by declared method. Read only
the6855-byte checkpoint, those six endpoint/result files (563294 bytes),
launch metadata and50471 additional bytes of small main endpoints to cover
the other selected roles. No audit, LP, live109, native, full analyzer,
Git or PDF was used. Only this review was appended.

All checkpoint fields and endpoint SHAs match. Every K35 observation is
performance-eligible and own open, with null T_cert. Input/PE, lambda=.15,
physical T10800, cap2400, Q=[20,25,30] and pickup/drop60 agree. Actual result
Gurobi requested/effective Seeds and successful set/get return codes match
Seed0/1; actual horizon/cap and declared command parameters also match.
Within each Seed, independently complete own PS/GI H has identical nonempty
valid semantic/fleet hashes; cold P has no applicable H.

| Method | Seed0 U / L | Seed1 U / L |
| --- | --- | --- |
| P | .6647466018182986 / .33555561820120866 | .7588515976478332 / .33057445547198877 |
| PS | .7674566047247167 / .33192176731164724 | .7126478011151949 / .33509461987030625 |
| GI-TBC | .6928543586313136 / .565765681464995 | .6683582547445452 / .5547798643285181 |

Checked all stated directions with1e-7 tolerance. At Seed0, P/GI have
opposed endpoints: P has lower U, GI higher L. At Seed1, GI has lower U
and higher L than either compact control. P dominates PS in the two finite
endpoints at Seed0; PS dominates P at Seed1. GI's own Seed1 U improves
over its Seed0 U while its L weakens, so GI's cross-Seed endpoints are also
opposed. These are finite endpoint observations; all six remain open and
support no certificate-time ordering, general Seed ranking or best-Seed
replacement. A smaller gap alone does not change that distinction.

The separate small-endpoint census selects exactly24 observations: twelve
actual D2-main positions97-108 and their twelve matching B1/B2 Seed0
observations, across K15, UC, R-B20-S-T1 and K35. Unique role/Seed/method
keys are complete, with no AM or mechanism variant included. Each Seed has:

| Method | Own eligible certificates / selected roles |
| --- | ---: |
| P | 1/4 |
| PS | 1/4 |
| GI-TBC | 3/4 |

Thus the preselected four-role certificate pattern agrees between Seeds,
while the previously reviewed material time shifts and current endpoint
reversals remain. The main Seed0 panels keep their original denominators;
these repeated roles are not new independent inputs or an estimated runtime
distribution. All first observations and their own proof identities remain.

No issue was found in this limited main-Seed scope. Actual109-120 AM/mechanism
repeats, full root/model/cost/120 analysis, entry/public execution and final
scientific/PDF integration remain pending.

Checkpoint SHA:
`4590f5c5898beeb247b28fb4154d3e71595701f381620f1d3164e566ded958a0`.

## Entry-promotion preparation, 28 October 2026 (static only)

Disposition: **statically feasible within the zero-native boundary; actual
entry/release acceptance remains pending**. Read only the new
`round137_entry.py`, `round137_release.py` and small
`infra/entry_promotion_preparation.json`. Independently parsed the helper,
release and generated thin-wrapper ASTs. Did not import/call promote or
verify, execute CLI checks, inspect PE/DLL bytes, perform Git/source scans,
or touch the healthy native queue. Only this review was appended.

Promotion calls analysis_preflight before mutations, then requires the
complete120 summary and retain-default decision (.08/AP off/pair-only).
It checks the legacy config against the candidate's original config SHA,
preserves its bytes, prepares current candidate/matrix-SHA authority and
retains the historical argv provenance separately. Defaults are the actual
28 S2 launches from B1/B2/B3/D2-main. The prepared launcher edits change the
CONFIG pointer and human-facing labels; the verifier becomes a thin call to
the new helper. The new source remains outside the frozen experiment graph.

The planned verification invokes28 real Python CLI expansions without
--run, checks normalized full vectors plus declared numerical parameters,
input hashes and source/config identities, rejects six unsuitable requests,
and checks frozen source/helper hashes. PE/DLL checks are intended byte-hash
reads through the retained launcher, with no vendor load or native solve.
These are post-study entry/identity checks, not new performance samples or
a reproduction of native timings. AST and prior normalized-vector metadata
checks alone do not establish that the actual28/6 execution succeeds.

The release source capsule now includes the new helper, both entry scripts
and both configs. Two small coverage improvements were recommended before
publication acceptance:

1. Before the verifier claims preserved historical16-vector provenance,
   explicitly compare historical_argv_provenance with the pinned legacy
   config's authority. The inspected code verifies the legacy file SHA but
   does not separately validate the stored historical authority object.
2. Before the immutable source capsule/manifest is produced, require a
   successful promotion receipt and actual CLI verification receipt bound
   to the current profile/launcher/verifier bytes. The inspected release
   idle gate checks study completion but does not itself prove the entry
   has already been promoted and validated. Preparation metadata is not
   that execution receipt.

The actual driver OS/root-session exit, all120 completion, promotion,
28 default CLI checks, six refusals, actual binary/source byte checks,
documentation synchronization and final integrated/PDF review are still
required. No current entry pointer/config mutation or actual asset validation
was performed by this review.

Reviewed source SHAs:

- Entry helper: `122d9ab4c10409b2b873a9b259a6bc79fb530400de1a802c9214150eb4614ddb`.
- Release: `8fc11745862bbd36ba43bbcc4120a6fcf6dcd6061133600928f1afd594109e54`.
- Preparation receipt: `93b00a1c88ff37f32376facadfbd85d209de001392fb96901b14dfdcb0971b9c`.

## Entry receipt-binding follow-up, 28 October 2026 (static only)

Disposition: **PASS for the inspected static binding design; no runtime
entry or final integration acceptance**. Read only the current
round137_entry/release sources and the entry-binding branch of the portable
checker while the queue was reported healthy at105. Parsed these source
ASTs and the generated thin-wrapper AST without importing or calling them.
No CLI, asset-byte read, native, full analysis, archive or Git scan was run.
Only this review was appended.

Both prior recommendations are implemented. The verifier now requires the
stored historical_argv_provenance object to equal the immutable legacy
config authority, in addition to checking the legacy file's candidate-bound
SHA. The pure public checker independently repeats both the authority-object
equality and the old-config SHA binding. Promotion still delegates to the
all120 preflight, complete summary and actual retain-default decision before
changing the profile/pointer. Legacy bytes have pre/post SHA gates. These
are inspected future assertions, not a claim that promotion has occurred.

The actual entry-check receipt now records current launcher, thin verifier,
new helper and profile/legacy-config hashes, plus matrix, candidate and
promotion-receipt hashes. Verification also checks the promoted file hashes
against the promotion receipt. The source-capsule function requires that
successful28-vector receipt and zero-native counters before one-shot packing,
then binds its exact entry/config bytes and promotion receipt. The manifest
checks publication-receipt and bundle hashes and rejects entry/config/docs
changes after source capture.

The portable source-publication branch binds the recovered receipt/promotion,
entry scripts/configs, candidate and matrix to the same bytes; it checks the
historical authority and legacy SHA. This branch reads receipt/source/config
data and registers PE/DLL attestations as never opened. It does not invoke
the asset-reading CLI verifier or obtain new performance evidence.

No additional local blocking logic error was found in this restricted
receipt-binding source review. Its conclusion depends on later successful
execution of the real28 default CLI expansions and six refusal checks; AST
success and hash-binding design do not substitute for those executions.
Actual all120/OS/root-session closure, promotion, binary/source checks,
publication/recovery, scientific integration and PDF review remain pending.

Reviewed source SHAs:

- Entry helper: `820d45b3426d424fc30e82f03dd3b1287dfbcc8a260b8c3e20fe93914e80a292`.
- Release: `62ead3b5b77a54962ccf50b112c09c685b7d5cdd49da4906bf308300e9f624c2`.
- Portable checker: `aeaa89cb335072468da5f2f81b2e7c9111b8162d023fa2a9ee5ee5fdff6853ab`.

## Manuscript table compaction, 28 October 2026 (source/editorial only)

Disposition: **no blocking local source error found; small caption/legend
improvements recommended**. Read only round137_documents.py and its small
compaction receipt. Reviewed source SHA
`29f705a74e61bce7bbee62297149b51d3137d9359245194e03c88a8b255e045d`,
matching the receipt. Parsed the AST and inspected literal caption/header
and F3-row structure; no assemble, analyzer, PDF, result table or raw
evidence was evaluated. Only this review was appended.

The initialized detail string is retained through the final supplement
write. Complete breadth endpoints, eight GI resource operating points,
eighteen weight observations, twelve Seed1 main positions, six Seed1 AM
views and twenty/ten Seed0/Seed1 mechanism views remain in the supplement.
The all-arms table also retains every position, input/Seed/method, eligible
certificate/open/UEV state, U/L and production/verification/total clocks.
Full-precision JSON/CSV authorities and the actual stage report remain
referenced/copied. No ineligible or adverse row is filtered out by the new
detail placement.

The weight table groups by physical configuration and actual rho and
displays all three methods with explicit own C/open/UEV cells. It iterates
the grouped float keys rather than indexing a nominal integer rho1, so the
known floating representation of rho1 does not itself create a lookup error.
An explicit six-groups/all-three-methods assertion would make the intended
compression cardinality clearer. The four-role root table uses observed
initial-LP fields with n/a for absent points; it does not substitute final L,
and retains the separate matched-domain/objective/cutoff/H qualification.
Actual root values and matches are not scientifically revalidated here.

All eleven main_table header-prefix keys match the caption dictionary.
Together with the single Seed0 AM caption branch they give the intended
local Table1-12 order; detail tables do not increment that counter. The
six-row F3 synthesis has exactly five cells per row and no embedded literal
pipe that would break its Markdown table. No blocking variable, loop or
string-combination error was found in the inspected assembly source.

The main text keeps the core opposite findings: paid-start reversals,
K15 C_R deletion advantage, lack of full-over-root advantage on the selected
hard roles, K35 deletion U/L opposition, finite weight/component dominance
and the UC Seed1 PS time shift. Complete lists move to the supplement;
the scientific qualifications do not disappear with them.

Two small editorial improvements were sent to the implementer:

1. Add Seed0 explicitly to the initial-LP, K15-cost and K35-endpoint captions
   so these tables do not require preceding prose to identify the Seed.
2. Put the C/open/UEV and null-time legend before detail, rather than after
   all detailed tables, and remove or demote detail's second level-one
   heading beneath the supplement title.

This is local source/editorial acceptance only. Materialized all120 values,
new full-analysis schema compatibility, root/cost/Seed1 scientific synthesis,
inherited-prefix table numbering and actual PDF layout remain subject to
the later runtime and final integrated review.

## Pending release/reading-record preparation, 28 October 2026

Disposition: **PASS for the revised unapplied TEMP drafts' preparation
consistency**, not actual delivery/integration acceptance. Read only the
three named pending Markdown drafts and necessary small candidate/config/
matrix metadata. Edited only those authorized TEMP drafts for English
spacing, wording and the concrete corrections below. Formal docs/source,
entry/config pointers, native queue and measured evidence were not changed.
No CLI, PE/DLL read, Git scan, full raw, native, recovery or PDF was used.

The substantive corrections were:

- UC-B20-B's example cap is1200, matching its registered n20 launch, rather
  than600. Its input path, physical T7200, lambda=.15 and Seed0 also match.
- Promotion, actual CLI checks, Draft-PR existence/readback and public
  recovery are prospective/receipt-governed. The drafts no longer imply a
  promoted active pointer, an existing new PR or a passed new recovery.
  Applying the documents does not require public recovery first; their
  recovery language is conditional, avoiding a source-publication cycle.
- The frozen Round137 production PE is distinguished from whichever entry
  pointer is active before promotion. Registered-campaign supervision is
  identified separately from a standalone command expansion.
- Prefix capacity is described as the load along a route; deliveries can
  permit cumulative pickups above Q. Loaded-return unloading, depot
  exclusion and distinct physical T/computing cap remain explicit. Integer
  target storage and the experimental D<=C convention do not add a new
  physical target-capacity constraint or advertise fractional-target parsing.
- Historical R132/R134 denominators are explicit and versioned; broad
  Seed0 and finite repeated observations remain separate. AM wording refers
  to observed coarse actions, not identical complete native trajectories.

The candidate source779713ad, production PE d6fd9e66 and DLL9b5fccef agree
with the drafts' full hashes and paths. The unchanged legacy config SHA
f3f20396 matches the candidate. Matrix metadata confirms120 positions,
16 input identities,20 physical configurations,24 objective configurations,
28 default S2 vectors and planned caps174600s. These are metadata identity/
design checks, not revalidation of native runs or an all120 completion claim.

Verified accepted-main base b2b940c1 remains distinct from the unmerged
Round137 Draft-PR plan and production source779713ad. No new Git/PR state
was queried. The three outstanding author-confirmed categories remain
HGA-TGBC bibliography/authorship/status, this paper's author order/affiliations,
and old CITI443 capture/selection provenance; no names or status were invented.
Fixed-commit anonymous HTTPS/pure replay forbids Optimize, compilation, Git
fallback and vendor loading. Failed transfer resumes in its owned root;
passed current or accepted R135 recovery is not repeated. No such recovery
was executed here.

After-edit TEMP hashes:

- Release guide: `1eab3c4cbe3043902c282321f3011e80e4e8ec5da03ad5862b18b161f3f9e4a3`.
- Reading packet: `18037a0aff6c340f393a510fc93aa639cd150537b759d76d092c5775988648fb`.
- Mainline record: `8d91b554c17734e8e9428c1f781a5235b92257b458f04a61df9dbc1e96dac770`.

Actual120 closure, entry/CLI/PDF/public checks, PR readback and final scientific
integration remain pending. All three files remain explicitly DRAFT ONLY.
