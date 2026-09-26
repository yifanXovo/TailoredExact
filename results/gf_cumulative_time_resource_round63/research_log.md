# Round 63 research decisions

## Restoration and initial decision (before experiments)

PR #123 is OPEN/draft, base Round61, head and remote Round62 branch both
71e955acad596acba2a9e74e738173113116d9f7. Its measured implementation is
7936ed53951113297df07d2fb243954e2f784906; final help/report packaging is not
timed as that build. The original E:/codes/ExactEBRP is still at Round61
4a9cbd0e3d43870e953b3a6678b343a9ac4fc25a with user modifications. New isolated
worktree E:/codes/ExactEBRP-round63 inherits the accurate Round62 head.
Remote main is 1459308492a5eceed523dee53b5f9d79141b5242, not our base.
Read both complete final reports, Round62 mathematics/research log/selected
candidate, protocol, runs and pairs; inspect threshold generation and passive
coverage implementation. Preserve historical interpretations and failed gates.

A: unchanged service projection may avoid inventory projection's D3/C3
regressions. Predeclare qualification relative to OFF with joint 10 seconds
and 10% time / 0.001 and 5% absolute-gap gates; certificate changes separate.
Do not demand dominance over every historical research configuration. Plan
full Single-S D3 and D4 OFF/inventory/service, plus full K1 C3 triple; if the
evidence supports it, spend remaining A launch on C2 service against a shared
same-build full K1 OFF needed for B. No dictionary or threshold search.

B1: cumulative prepaid handling plus incoming travel resource, explicit flow
and mincut projection. Keep every base row. First verify integer embedding,
flow-cut equivalence and the numerical implementation, then compare actual F0
objective optima in D3/D4/D6/D7. Separate full set, singleton and proper multi-
station supports. A cut can strengthen the region without raising the objective.
Reuse deterministic Dinic infrastructure with no optimizer in callbacks.

Initial execution choices are explicit block for diagnostics and a bounded
MIPNODE separator with OFF / dry / cuts isolation (PreCrush-only if used).
Only select these after strength/cost measurements. If the long-T objective
LP remains weak, investigate a justified cumulative-resource refinement or
native-root/tree separation before stopping. No pair-threshold fallback.

At least 20 launches remain earmarked for long D3 or C3 protection, D7,
D4 protection, complete multi-call K1, stable and official references, and
two previously public but Round63-unopened confirmation roles. Candidate,
execution and tolerances freeze before C4 then C5 opens. They cannot be
called new sealed data. Every optimizer/proof batch, failure and repeat is
charged. Compiler, Git maintenance and optimizers never overlap performance.

## B1 results and B2 execution screen (before native performance)

Frozen v1 passes 40 solver-free CTests and 12 build-only model preflights.
Charged micro 1 performs 24 LPs: all feasible/infeasible flow classifications
agree with mincut and exhaustive subsets. Four charged original-objective
diagnostic batches follow. D3 closes in 25 calls/1.328 s with 61 generated
rows and no objective gain. D4 closes in 23 calls/2.437 s: F0 0.09394825539,
simple 0.25687585126, full projection/explicit 0.26294355430. Simple-optimum
violations on true 2/3/4-station supports show an increment beyond simple rows.
D6 closes in 14 calls/6.625 s with 18 generated rows, unchanged F0 0.12569183095.
It has original optimum proper supports of 27 and 3 stations; simple-optimum
proper supports of 16 and 18. D7 spends 117.437 s under 120 s, 36 LPs and
106 generated rows, still not closed; objective stays 0.17514318461, matching
the explicit objective but not demonstrating a closed projected point.
D7 proper supports remain after simple rows (31/8/16 stations in the first
simple optimum). Thus long-T rows have real fractional activity beyond the
whole-set/singleton cases, despite no objective gain. Fresh-model closure LPs
are too costly to propose for every outer call without further evidence.

B2 screen: same v1, D4 and D7, each OFF / explicit / simple / PreCrush-only /
dry / cuts at 120 s. Twelve launches, not a parameter product search. This
separates explicit representation cost, cheap activation/local rows, presolve
configuration, mincut work and actual user-cut submission. Root/tree supports
and Work matter alongside original witnesses and certificate endpoints.
No new candidate/PREFIX/archive is enabled. Then decide a uniform long-run
candidate or one justified refinement using these observations. A's full
protection and final long/K1/confirmation allocation remain reserved.

The independent audit initially grouped cut terms solely by query/vehicle.
The probe's first closure inspection reuses the original F0 point after the
simple LP and shares the displayed last-query number. The complete ordered
per-cut term stream is intact. Fix the read-only auditor to consume each cut's
own ordered terms and verify query/vehicle/name/count. All 262 emitted cut
occurrences pass raw-activity/coefficient checks; no optimizer rerun or source
model change. Keep this trace-label limitation explicit. Also use actual
post-insertion native row/column/nonzero counts in tables, retaining the
inherited pre-insertion backend nonzero counter as a separate raw field.

During charged launch 7 (D4 explicit), an independent audit of saved large LP
files overlapped for about 6.9 seconds. Its CPU interference cannot be isolated.
Keep launch 7 charged, exclude performance attribution and reserve one exact
same-build/cap repeat. Thereafter perform large LP/route audits only between
performance queues. The small read-only tables may still be inspected.
Also correct analysis-module import rebinding of the reused Round61 runner:
Round62's import had reset its global ledger in analysis processes only.
Experiment processes import Round63 directly and used the correct ledger,
commands and destinations. Explicitly rebind before reused runner operations;
recompute summaries after the queue. This changes no solver/model mechanism.

## B2 endpoints and B3 one-pass execution hypothesis

v1 measured-source commit is 2e55f4d96; executables are preserved in
build/round63-v1. All 12 physical witnesses and 4 dynamic cut traces pass
independent recomputation after the queue. D4 OFF/simple/PreCrush/dry/cuts
certify in 90.125/115.828/89.593/89.766/95.890 seconds. Simple materially
regresses; dynamic separation costs 0.015-0.018 s and has no qualifying gain.
D7 (120 s, uncertified) absolute gaps are OFF 0.4761606753, explicit
0.1695257352, simple 0.5152904098, PreCrush=dry 0.3111209086, cuts 0.3642580016.
Thus PreCrush confounds a naive OFF-versus-cuts improvement claim. Actual
user cuts worsen gap relative to dry. Explicit flow independently improves
the native UB to 0.3650270766 (OFF 0.6712367708), with small LB gain; it is
not a proof-tail speed result. Simple rows cannot replace the useful full
resource experiment on this evidence.

D7 cuts submitted 40 valid rows, then disabled at query 15 / graph 57 by its
optional failure guard. All API returns were zero; v1 did not persist the
exception reason. First/last inherited root samples are nonnegative, so they
cannot establish the failing intermediate point. Report this fallback and
do not call it a complete 64-query execution. Add failure reason and one
failure-point snapshot in the next build; retain original tolerances until
the actual reason is known. No invalid cut or false certificate was found.

B3 is a representation/execution alternative using the same proved resource,
not a new threshold search: on the *first actual LP optimum*, run mincut once
per vehicle, retain at most M most-violated rows, then add this small static
set to subsequent MIPs. Full K1/Single-S reuse their already-required first
LP; extraction, graphs and recording are new costs. A fixed-MIP harness pays
one explicit preparation LP. No LP closure, callback, PreCrush, candidate,
archive, start, local bound or historical point enters this arm. Root-dry
performs the same preparation but adds no rows. All supports are global
physical rows, so reuse across Gini intervals/epochs remains valid.

Hypothesis: a few current-LP resource rows may retain useful long-route
information with less native representation/search disruption than thousands
of continuous variables or repeated user cuts. Before qualification, compare
OFF/root-dry/root on D4 and D7 in one new frozen build, and inspect actual
static row insertion, raw violations, native cost and original witnesses.
Keep long/protection/K1/reference/two-confirmation reservations. First complete
the charged same-v1 D4 explicit repeat required by interference record 7.

The clean repeated v1 D4 explicit launch 18 again fails to certify at 120 s
(118.094 s wall), whereas the same-build OFF launch 6 certifies at 90.125 s.
No timing claim is drawn from excluded launch 7. v2 diagnostic launch 20
identifies the dynamic fallback: `invalid raw route arc`, minimum raw x
-2.5152396252603651e-8, after 15 queries / 57 graphs / 40 successful API
submissions. The frozen -1e-8 search-input guard is unchanged. The optional
separator stops safely and saves the failing raw point. All 40 earlier rows
pass independent raw-activity verification. Do not label this a full-budget
dynamic execution or relax the original certificate tolerance to hide it.

The root-static native micro (launch 19) pays two LP/MIP optimizer calls,
generates one valid global row and inserts exactly one ordinary MIP row.
Independent route and resource checks pass. Screen_root_v2 now compares
D4/D7 OFF, root-dry and root at 120 s (six launches). The pure-root modes
never set PreCrush; their inherited `precrush=-1` summary is an unset telemetry
sentinel, not a parameter setting. Core solver parameters retain readback.

A's bounded supplement is fixed at nine launches: Single-S D3 and D4, and
full multi-call K1-S C3, each OFF/inventory/service at cap 600. If C2 is useful
after these outcomes, add only its service arm against the same-build K1-S
OFF reserved for B, for at most ten A-attributed launches. This is a role
selection for the experiment, not an instance-conditioned solver rule.

The final development allocation is set before opening confirmations: after
the root screen, run one bounded full-K1 root micro (third of at most four
native micro launches), then A's nine runs. For B compare the same OFF /
explicit / root rules in full K1 on C2 and D7 at 600 s, and Single-S D4 at
600 s using the same-build A OFF as shared baseline. These eight additional
B launches test both representations at the long budget without a parameter
grid. Select at most one uniform B execution for C3 regression follow-up and
both confirmations; a mathematically correct negative candidate may be
selected for diagnostic integration, never described as promoted. Reserve
four confirmation OFF/candidate runs (600 s each) and eight unchanged
K1-H/P-GRB runs on C2, D7, C4 and C5 at the same 600 s cap. Candidate and
driver/source/build hashes must be frozen before C4 input is opened, then
C5 follows without intervening mechanism changes. Maximum forecast is 59
charged launches including C2's optional service supplement, leaving reserve.

v2 full-K1 micro launch 27 reveals a real integration defect before long runs:
the retained LP model reaches the existing additional-row guard and the MIP
is rejected before optimize (`additional_rows_require_fresh_canonical_model`).
The process exits zero but the semantic engine status is failed. Preserve
and exclude it from performance; count three optimizations and four backend
attempts, not four native optimizations. The initial physical route remains
valid, but this is not a successful full-algorithm check. Source commit
11f5139b09e638355539cfb99b0c5d10fbb33024 records that version.

v3 fixes the required lifecycle: both root and root-dry use a fresh canonical
model per native call, so MIP-only resource rows cannot leak into later LPs
or be duplicated in a retained MIP. The required first LP is still reused as
the separation source, no extra optimizer is called, and all additional
model reads are charged. Dry pays the same read policy. OFF and explicit
retain their original reuse policy. Add a full K1 root-dry control on C2
at 600 s to isolate this cost. A has not started: all subsequent core A/B,
long/reference/confirmation pairs use one frozen v3 build. v1/v2 screens
remain separately identified evidence. Add actual PreCrush get-return/value
telemetry without changing its setting. All 40 solver-free tests pass.
The fourth/final native micro now rechecks the complete K1 root lifecycle.

Launch 28 passes: full K1 performs three LP optimizations and one terminal
MIP, inserts the one prepared row once, reads PreCrush=0 successfully, and
certifies original objective 0.325 with independent physical verification.
v3 measured-source commit is b1bde3eab6c6fb9c4e1c4575acbdfa9141a46eaf.
v3 D4/D7 OFF/root/root-dry build-only exports and A D3/D4/C3 three-way
build-only exports all succeed before performance. Four native micros are
now exhausted. A starts on this frozen build with stage `full_dev_v3`.

## B4: prepaid time coupled to the existing post-service load

Before any B4 measurements, examine an additional physical relation. Empty
departure gives load_i <= cumulative pickup through i; hence the canonical
route embedding satisfies sum_j f_ij >= (c/scale)*load_i. The repository has
post-service node loads, not arc load variables. Use that existing variable
and the same safely downward-rounded handling coefficient. The coupled arm
keeps the explicit time-flow extension and adds only M*V rows (none if c=0).
Unused loads are already zero through load_i<=Q*z_i. No new capacity rule,
arrival-time interpretation or total-pickup cap is introduced. Loaded returns,
multiple pickup/drop blocks and heterogeneous Q remain valid. Route enumeration
will additionally check this lower bound. No simple s-t mincut equivalence
is claimed for these extra node-throughput lower bounds.

Hypothesis: the MTZ load variables and accumulated time flow may otherwise
choose incompatible fractional histories. First test D6/D7 actual explicit
LP optima, then coupled LP, with all other old variables pinned for an
explicit-control/coupled feasibility pair: four bounded LP optimizations per
120 s charged batch, zero maxflows. Pinning control guards against numerical
infeasibility from fixing a saved point. Violating one selected f assignment
alone does NOT prove stronger projection if another f completion exists.
If useful or still plausibly relevant to integer propagation, run just one
same-build D7 explicit/coupled 120 s native pair before selecting long arms.

A continues in the already-frozen v3 executable. Compile B4 only after that
performance queue ends, preserve v3 binaries, run all regression tests and
freeze v4. All subsequent B long/reference/confirmation comparisons receive
new v4 OFF baselines; never reuse v3 A timings as their direct control. The
two LP batches, optional two native screens and needed new OFF controls fit
within 68 projected launches, retaining the required long/K1/reference/two
confirmation roles. No additional native micro is permitted. B3 root stays
a correctly integrated mixed execution alternative; choose final long-arm
allocation using B4 evidence, and document any stopped branch.

A runtime-label discrepancy is explicitly resolved: result.json and the
compatibility C6 split ledger retain rho=0.01 and an inherited generic
implementation-boundary sentence. PaperK1AmSf.cpp enables the first-class
controller and sets split_threshold=0.08; PaperExternalGiniTree.cpp selects
that threshold when first_class_k1 is true. The actual
adaptive_mass_decision_ledger.csv for C3 reads K0=1, tau=0.08. Preserve these
historical compatibility fields but never interpret rho as the active K1
threshold. The read-only report now verifies every actual adaptive decision's
K0/tau. Single-S does not exercise child decisions. This changes no search.

## A completed: bounded qualification decision

All nine v3 launches (29-37) finish within their 600 s physical caps and
pass independent original-route and unchanged-threshold proof verification.
D3 Single-S OFF/inventory/service certify in 316.047/462.531/308.843 s.
Service removes the inventory arm's 46.3% regression on this full role but
its own 7.20 s / 2.28% gain is below the dual threshold. D4 certifies in
90.140/55.109/78.547 s: service gains 11.59 s / 12.86% against actual OFF,
although inventory is faster. The predeclared relative-to-OFF criterion
therefore recognizes this service gain. C3 full K1 makes three LP calls and
one terminal MIP in all arms, with declined refinement. None certifies:
absolute gaps OFF/inventory/service are 0.09852784389 / 0.10583249243 /
0.11007479251. Service's 0.01154694862 / 11.72% gap regression fails the
uniform qualification criterion. Retain its D3/D4 value as a default-off
research result, not a promoted uniform candidate, and do not rewrite the
Round62 historical gate. Stop A at nine launches: an extra C2 success could
not repair this observed protection failure. No A+B combination or new
service confirmation is claimed. B long/K1/reference/two-confirmation work
remains required and reserved.

v4 measured source is dc8d3e4a0ee3f63f0858b2c3b38a59a92cd1e783. All 40
solver-free tests pass, including carried-load embedding on the enumerated
legal routes. OFF/explicit/coupled preflight succeeds on D4/D6/D7/C2 before
measurements. B4 LP launches 38/39 finish in 1.719/12.406 s, four calls each.
For D6 and D7, coupled and explicit objective LP values agree; the explicit
optimum violates no carried-load row, and both pinned explicit/coupled
controls remain feasible. Full LP row residual and pin consistency checks
pass. This supplies no strict projection or objective-strength witness at
these target points. One D7 v4 explicit/coupled native pair at 120 s will
close the remaining integer-propagation question at screening scale; it
does not turn a zero LP gain into a presumed negative MIP result.

B4 native pair 40/41 completes in 118.485/118.484 s on the same v4 build.
D7 explicit has UB 0.3650270766, LB 0.1955013413 (gap 0.1695257352);
coupled has native UB about 0.7774662749 and LB 0.1948323900 (gap about
0.5826338848). No certificate. The coupled variant materially worsens
primal quality with a slightly weaker bound. Stop B4 here: no target-LP
gain, no pinned-point projection witness, and negative native propagation
screen. It remains an implemented, valid default-off diagnostic prototype;
full K1/confirmation for coupled is deliberately not claimed.

The remaining development uses uniform OFF/explicit/root on v4: Single-S
D4 (three 600 s runs), full K1 C2 (those three plus root-dry, 600 s each),
and full K1 D7 (three 600 s runs). Then take one uniform candidate through
C3 OFF/candidate regression follow-up on v4, both confirmations and the
unchanged K1-H/P-GRB references. This keeps the forecast at 65 charged
launches and leaves seven reserve launches; A stops at nine. Root-dry pays
the same fresh-model policy as root. No A+B combination is opened.

Long D4 v4 runs 42--44 all certify. OFF/explicit/root process walls are
90.141/136.469/121.391 seconds. Both resource executions fail the predeclared
time protection against actual OFF, even though they remain correct research
integrations. The prescribed full-K1/confirmation diagnosis continues; later
positive results cannot erase this development regression.

C2 v4 runs 45/46 use their 600-second caps without certification. OFF ends
at UB/LB 0.82996341317/0.82245410139 (gap 0.00750931179), explicit at
0.83024848649/0.81078670517 (gap 0.01946178132). OFF has 3 LP calls plus a
target-bound interrupted MIP and a terminal MIP; explicit has 6 LP calls
plus those two MIP roles, because its changed native evidence triggers the
existing controller's re-evaluation. Actual calls and all cost are charged.
Root-dry/root were pending at this observation; do not select a final
candidate from these first two arms.

C2 root-dry #47 completes in 552.454 seconds with a strict original-problem
certificate, UB/LB 0.8299634131717752/0.8299634131717734. It has three LPs,
one target MIP and one terminal MIP, all on fresh canonical models. The
first LP observation takes 0.004184 seconds, selects two supports and adds
none. The certificate gain versus OFF is consequently evidence for the
changed native lifecycle, not for adding resource rows. Root #48 is now
running with the same two-support preparation and common fresh-model policy.
If long D7 later shows a root gain, reserve one extra D7 root-dry run to
isolate that effect before selecting the confirmation candidate. This would
raise the forecast from 65 to 66, leaving six reserve launches.

C2's first target MIP native root relaxations are OFF/root-dry 0.6064756,
explicit 0.6428263 and root 0.6129122. Native matrix sizes are respectively
8663/2402/48314 (rows/columns/nonzeros), 9503/3202/52314 and
8665/2402/48858. Thus explicit's stronger initial native relaxation did not
prevent its worse final gap, while root-dry's certificate gain occurs
without changing that initial relaxation or adding rows. Fresh models
discard retained native state as well as paying model-read cost. These
observations concern the first native target MIP, not an assertion that
the diagnostic F0 objective LP or every later cutoff/epoch is identical.

C2 root #48 certifies in 485.719 seconds, UB/LB
0.8299634131717752/0.829963413171746. This is a certificate gain versus
actual OFF and a further 66.735 s / 12.08% certified-time gain versus
root-dry. The added two global rows thus have an isolated incremental
benefit in this full multi-call role, in addition to the lifecycle gain.
The four C2 witnesses and both prepared row pools pass independent checks;
all 41 parameter records pass, as do actual balanced-normalized-score
recomputations. D4 regression remains disqualifying. Launch D7 full K1
OFF/explicit/root at 600 s each on unchanged v4, charged 49--51.

D7 full K1 49--51 ends without certification. OFF/explicit/root absolute
gaps are 0.176324583005 / 0.110623925824 / 0.158178585231; both candidates
improve relative to OFF by the declared dual gap gate (37.26% / 10.29%).
The LB improvements are only 0.000638461 / 0.000092449; about 99% of the
gap gains are native primal changes. All three final witnesses pass the
original physical/objective audit. Root's supports are 34,17,6 out of 50,
prepared by four maxflows in 0.018437 s. Explicit/root both pick up 206 and
deliver 204, with maximum route durations 17972.466/17937.569 under 18000.
All three follow the actual 3-LP/1-terminal-MIP path with declined refinement.
Charge reserved D7 root-dry #52 at 600 s, same v4/stage, to isolate the
positive root effect. Forecast is now 66 launches, six remaining reserve.
Before confirmation, finish C3 OFF/one-uniform-candidate on v4, the unchanged
C2/D7 K1-H/P-GRB references, and the already selected C4/C5 roles in order.

Before opening confirmation, the Python driver now also enforces the frozen
protocol and selection hashes in addition to driver/build identity. This
affects only the closed confirmation guard, not native code, commands or
the ongoing development optimization. Final confirmation freeze will bind
this exact driver version. No confirmation input or performance is opened.

D7 root-dry #52 completes in 597.344 s with exactly the OFF UB/LB,
0.3718940096799275/0.19556942667467492, no certificate. Its independently
verified route and all parameter/row evidence pass. This isolates root's
D7 gap gain from model lifecycle changes; C2's separate multi-MIP lifecycle
gain remains real. Select one uniform diagnostic candidate, root, in
selected_candidate.json now, before C3 follow-up. C2 isolated row benefit,
D7 long-route gap gain and lower size support this choice; explicit's larger
D7 gain does not outweigh its C2 regression for this diagnostic selection.
The D4 regression permanently fails this round's promotion gate, and later
outcomes will not change the mode. C3 v4 OFF/root build-only succeeds;
launch its 600 s full-K1 pair as #53/#54. Confirmation inputs remain closed.

C3 #53/#54 finishes without certification. Both UBs are 0.8179955412057756;
OFF/root LBs are 0.719467697315918 / 0.7127806955675012. Root's absolute
gap grows from 0.098527843890 to 0.105214845638: +0.006687002 / 6.79%, a
second material protection failure under the original declared rule.
Its three supports (22,17,17) take 0.008741 s to prepare and have no failure.
Both final physical witnesses and all traces pass; 47 parameter records
are verified. Keep the already chosen root mode for diagnostic confirmation,
with no default promotion and no candidate change. Launch unchanged
C2 then D7 P-GRB/K1-H references as #55--#58, cap600, same v4/stage.

Final per-call review confirms C2 OFF/explicit/root-dry/root use 5/8/5/8
optimizations. Root, as well as explicit, triggers a second three-LP
evaluation after changed native evidence. The final report text now reflects
that complete ledger rather than assuming equal call counts. No native
calls were added by this reporting correction; the original accounting and
measured process costs already include them.

References #55--#58 and both confirmations #59--#66 are complete. C2 P-GRB
ends with gap 0.043440251; stable K1-H certifies in 525.719 s, so root's
40 s / 7.61% advantage is below the relative time gate. D7 P-GRB ends at
UB/LB 0.290186246296/0.196954926915; stable K1-H at
0.215644075316/0.195865015973. Its unchanged HGA takes about 543 s and
leaves time for six native calls; its gap is nevertheless much better than
both cold resource arms. Official fingerprints match; D7's hex log and
signed API/manifest integer represent the same 32-bit value.

Confirmation freeze follows #58 and precedes C4 input/build. C4 finishes
all four arms before C5 opens. OFF/root/P-GRB/K1-H certify zero objective
on C4 in 3.188/3.203/2.453/21.203 s, and on C5 in
59.344/290.422/17.312/193.328 s. Both K1-H confirmation runs make zero
native optimizer calls; readback is explicitly not applicable. C4 selects
no rows. C5's two rows materially slow zero-route discovery, a confirmation
regression under the frozen gate, not a nonzero proof-tail result. The
OFF zero witness satisfies both rows (maximum activity -0.957609347).
No candidate, runtime parameter or guard changes after opening confirmation.

A final reporting correction prevents noncharged build-only entries (which
carry the most recent counter number) from overwriting the charged run's
displayed optimizer count. Explicit charged flags now accompany call/index
rows. Every charged per-run count matches its call ledger; native records,
total accounting and measured timings are unchanged. Zero-native early
certificates are counted as zero calls and do not claim parameter readback.

Final audits pass 59 original-route witnesses, 20 resource traces including
cross-witness checks, 10 threshold proofs, 8 coupling LP/control records and
262 strength-cut occurrences. Submitted-only route verification passes 59.
All frozen v4 source/executable/test-log and confirmation hashes remain
unchanged. Final budget: 66 charged, four native micro, 278 optimizer calls,
971 recorded maxflow/separator calls (including guarded attempts), no cap
overruns, exclusions #7/#27 retained, six reserve launches unused. Evidence
index covers 3,305 local files / 1,030,702,641 bytes; 267 native matrix/root
log records are summarized. Raw logs, large LP/point data and binaries stay
local. Remote PR #123/base branch is rechecked at the original 71e955a head.

Native adoption evidence is narrower than API acceptance: D4 screen cuts
has 57 API-success submissions and a native `User: 23` aggregate. D7's
native summary omits User, so adoption count is unavailable, not assumed to
equal its 40 successful submissions. Reporting now preserves both fields.
