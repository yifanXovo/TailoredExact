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
