# Round 65: bounded proof services around a complete F0 search

## Scope and qualification

This round implements a production, default-off separation of complete-domain
F0 MIP search from optional LP lookahead and shared-resource proof. Gurobi remains
the complete MIP engine. The selected uniform research policy is
`uniform-bounded-verified-zero`: credit-seed controller, seed 30 Work / 30 seconds,
replenishment 0.1 from actual core search, verified-zero HGA termination, projection
OFF. Selection occurred after 32 charged launches, before any C8/C9 optimization.
No instance name, historical winner, known optimum or operational threshold is
used by the policy. Cold starts are diagnostics, never a runtime selector.

The campaign is complete: 62 charged launches, including 3 native micros and
4 disclosed HGA timing diagnostics, plus 5 build-only reference fingerprints.
The 42-test v5 suite and independent audits pass. The verified-zero reliability
increment is recommended for a later, explicit integration. Cost control has a
real same-formulation C6 scheduling benefit, and projection is now a production
research service. The complete frozen F0 candidate does not qualify as a mainline
upgrade: D7 exceeds both regression gates against K1-H, and D4's JOINT advantage
is not recovered. Both confirmations are retained without policy revision.

## Inheritance and what was actually integrated

The branch starts at Round 64 PR125 head
`8f23af309079b605f73e0e780a753d806aaf0b46`, branch
`codex/round64-shared-load-time`. A successful remote fetch confirmed that head
unchanged. The user's dirty original worktree was left untouched; this work uses
the isolated `ExactEBRP-round65` worktree. Round 64's main measurements used v3
`438e9a286957370df2f962893f43a1026902839f`; stopped QCAP v4 and the report head
are not recast as those measurements. Historical Round 64 timings only motivate
the experiments below and are not same-build Round 65 comparisons.

* Stable algorithm components retained: original compact/F0 objective and input,
  verified incumbent and non-strict F<=U cutoff, midpoint/balanced-normalized
  closure, complete-frontier minimum, atomic coverage replacement, and existing
  Round29 model reuse/Round31 target-pause contracts. The literal stable
  `paper-k1-am-sf` and plain P-GRB defaults remain unchanged.
* Correct research components integrated: the original HGA event observer and
  verified-candidate store now support immediate verified-zero termination and
  memory retention on audit-write failure. Initial and child LP work now shares
  one bounded account with optional resource separation and proof reoptimization.
  Unknown lookahead retains authoritative coverage and sends it to MIP.
* Previously offline facilities now have a production path: Round 64 physical
  shared q/f rows are decomposed by vehicle, instantiated once per vehicle,
  updated through affine RHS, and used to generate conservatively checked global
  projection rows from this run's actual F0 points. PROOF and SPARSE use the same
  bounded service. This implementation does not by itself qualify projection for
  the selected policy. QCAP remains an inherited stopped experiment.
* Round 60–62 event and PASSIVE contracts were read and reused where applicable;
  no free archive route, earlier LP point, bound or native start is supplied.

See `actual_algorithm_contract.md` for the implemented pseudocode and lifecycle,
and `mathematics.md` for coverage, containment and rounding arguments.

## Exactness and cost control

F(I,U) embeds into the shared relaxation and then F0 on the same original domain.
The complete F0 MIP remains available when every optional component stops.
Only complete, residual-qualified LP optima/infeasibility and inherited safe
bounds are used; no interrupted primal ObjVal is exported as a lower bound.
Per-domain valid bounds combine by maximum. The reported global lower bound
uses the minimum over the full authoritative frontier, including the existing
accounting for omitted non-improving space. An auxiliary infeasible point is
never interpreted as an infeasible interval or original-objective certificate.

Admission limits optional Work by the remaining seed plus 0.1 actual core Work,
with a 30 Work per-call ceiling in the selected credit-seed revision. Each call
also has a 15-second and half-remaining-wall ceiling. Construction, interface,
verification, copying and persistence are charged to elapsed optional cost.
Gurobi stopping overshoot is retained as debt; the implementation does not claim
an exact post-call hard Work inequality. Work is per optimize and is read back;
core calls restore an unrestricted optional Work limit and retain the process
deadline. Wall guards mean logical trajectories need not be fully deterministic.

If an initial LP or either speculative child is unknown, the complete parent
remains authoritative until an atomic replacement succeeds. Speculative child
models are discarded and the parent is marked core-due. This marker prevents an
immediate repeat and persists conservatively through later tightening; it also
deliberately gives up further optional probing of that leaf. Core MIP may remain
hard. The guarantee is safe coverage and an opportunity to search, not universal
runtime dominance or eventual certification within a finite cap.

In the complete production account records, no positive-Work optional call
follows a positive-Work core call.
Credit replenishment is implemented and unit-tested, but it is not an observed
performance contribution of these runs. The demonstrated scheduling effect is
the finite shared initial allowance followed by protected MIP opportunity.
The terminal-MIP/core-due design limits how later earned credit can be used.

## Direct scheduling evidence

The C6 causal pair uses the same v5 executable, full HGA configuration, verified
startup routes/U, initial interval and ALL-JOINT matrix. Only optional control
changes. The paired-state audit checks byte-identical startup witnesses,
initial coverage and first canonical model. Both caps are 300 seconds; these
measurements are distinct from the historical 600-second/438-second observation.

| C6 warm JOINT, cap 300 | Original control | Credit-seed control |
|---|---:|---:|
| Process elapsed seconds | 297.313 | 297.094 |
| Native LP / MIP calls | 4 / 0 | 1 / 1 |
| Initial/final UB | 1.693523057335 | 1.693523057335 |
| Final global LB | 1.434081910971 | 1.580095291649 |
| Absolute gap | 0.259441146364 | 0.113427765686 |
| Original-problem certificate | No | No |

The controlled run pays 30.000047 optional Work and 779.398469 core Work. Its
optional elapsed charge is 13.958738 seconds; actual core search consumes
280.298129 seconds. It meets both absolute-gap improvement gates. This isolates
the prevention of LP starvation under the same formulation; it does not promote
JOINT into the selected final policy or prove superiority to K1-H/P-GRB.

The lighter C6 v5 credit-seed run also exercises multiple calls/domains: its
initial F0 LP completes at 12.4295135 Work, then an incomplete child consumes
the remaining 17.5714126 Work. The parent stays active and its MIP runs. Three
native micros cover zero credit, construction exhausting tiny wall credit, and
a reusable projection service across multiple leaves/MIPs. They are correctness
stress evidence, not performance gains. No fourth native micro was needed.

A certified, nontrivial full-K1 budget-exhaustion case is run32, cold C5 with
credit-seed/released PROOF at cap120. It visits the root and both child LP domains,
makes12 auxiliary and3 proof calls, and exhausts30.000352540 optional Work. The
last proof reoptimization returns WORK_LIMIT and retains the right child's safe
0.49 bound. The authoritative parent then receives a complete MIP, consumes
104.549275220 core Work and certifies an independently verified zero route.
Total process time is63.438 seconds. This is a completed production algorithm
with bounded incomplete proof, multiple domains and safe continuation; the
micro stress tests are not used as its substitute.

## Production projection: genuine evidence, limited utility

Each vehicle model has only its own station-origin q/f arcs, including return;
depot departure is empty. The test suite compares the coefficient multiset of
the decomposition against the actual emitted Round 64 shared matrix, including
heterogeneous capacities, c=0, recycled pickups and loaded return. Finite q/f
bounds and outward-rounded residual compensation support the submitted rows.
An independent Decimal80 audit recomputes multipliers, signs, coefficients,
finite-bound corrections and the actual-point violation for every retained row.

The fixed-L service and the named released-load service are different research
representations. Released-load deletes q_load and B4 from the auxiliary block;
it is a relaxation yielding global x/p/d rows. It neither repairs nor validates
the current F0 L vector. Original main-model L constraints remain in force.
There is no tolerance coefficient deletion or unsupported residual omission.

Auxiliary models retain their matrix and update RHS serially. Basis retention
is implicit, with no claim of guaranteed free reoptimization. The global pool
is bounded at 64 rows; at most 8 currently violated rows and 4 proof reoptimizations
are used per base LP. Lack of objective progress, unknown evidence or exhausted
credit stops additional work. No callback nests an optimizer. PROOF uses a paid
continuous model copy. SPARSE additionally attaches selected rows to the retained
main model, with a separate row ledger and no guard-bypassing rebuild.

| v5 warm D4, cap 180 | Elapsed seconds | Certificate | Core Work |
|---|---:|---|---:|
| Credit-seed F0 | 128.828 | Yes | 208.576109 |
| Same + fixed-L PROOF | 129.250 | Yes | 208.576109 |
| Same + released-load PROOF | 129.297 | Yes | 208.576109 |
| Same + released-load SPARSE | 145.610 | Yes | 242.142780 |

Released-load PROOF raises D4's root bound from 0.0939483 to 0.1711731894 and
the right child from 0.3249693 to 0.3913068904. This is real objective strength,
but it does not change the resulting core MIP Work or yield an end-to-end
improvement. SPARSE changes search and regresses by 16.782 seconds/13.0%, exceeding
both time gates. Fixed-L SPARSE in v3 loses the D4 certificate at cap 180; it is
retained as preliminary negative evidence rather than silently replaced by v5.

C6 v5 released PROOF generates 8 auxiliary calls/2 proof reoptimizations, but
raises its initial bound by only about 3.5e-6 and leaves the final gap unchanged
within the gates. Cold D7 released PROOF likewise has 8 auxiliary calls/2 proof
reoptimizations and no final gap benefit. D4 PROOF keeps 1404 main columns; C6
keeps 23533, compared with 43533 for C6 ALL-JOINT. PROOF attaches zero native rows;
SPARSE adds only its selected rows and no q/f columns. These are actual lifecycle
records, not a prediction from nominal model size.
The separate original P-GRB C6 compact model has 13330 columns. F0's 23533-column
count includes the pre-existing interval machinery; this round avoids the extra
20000 resident q/f columns of JOINT.

The negative result has three distinct causes: fixed-L rays often repair local
load consistency without changing F; released rows can strengthen F without
changing the outer decision/core search; attaching rows can worsen native search.
The selected policy consequently has projection OFF. The production service and
its valid rows remain research facilities, not a claimed performance upgrade.

## Independent HGA reliability increment

The original completed initialization/strict-improvement decode is verified by
the original evaluator before requesting termination. Only F in[0,1e-12], with
the original F>=0 bound, closes the existing certificate. Positive objectives
retain the genetic operators, random calls and original stagnation rule. Audit
failure keeps the verified memory witness and reports the failure separately.
Runtime verification and the independent post-run route recomputation are
distinct; neither unverified fitness nor historical zero objective is accepted.

| Same-build v1 reliability pair, cap 300 | Full-HGA arm: process seconds | Zero-stop arm: process seconds | Logical prefix |
|---|---:|---:|---|
| C5 | 252.110 | 3.594 | Identical first 11 records; 2010 vs 10 generations |
| C7 | 37.812 | 2.187 | Identical first 58 records; 2057 vs 57 generations |
| C2, positive protection | 297.062 | 297.063 | Identical complete2794-record HGA trace |

C5/C7 both certify zero. C2 has the same nonzero startup incumbent and no
meaningful capped-gap change. The final v5 integration pair compares the frozen
candidate with literal K1-H at cap 300: C5 certifies zero in 3.641 versus 195.954
seconds, again with identical first 11 logical records (10 versus 2010
generations). Both make zero optimizer calls, so this gain comes entirely from
verified-zero startup termination; neither the budget nor projection contributes.

A limited check of the differing full-HGA times across v1 and v5 finds the
complete 2011-record logical trajectory identical. The first zero is also found
at similar HGA times, 3.503233 versus 3.557235 seconds; the wall variation occurs
during the remaining 2000 non-improving generations (last records at 252.050343
versus 195.900750 seconds). No change in proof search explains it, since neither
run calls an optimizer. Its machine/build timing cause is not identified; no
cross-build time difference is claimed as a structural improvement. Each
reliability conclusion uses its own same-build pair and passes both time gates.
The earlier v1–v3 research guard missed startup witness persistence; final
routes independently verify, but those measurements are preliminary evidence.
v4 added complete startup/native-return snapshots and the observational audit
flag is paid equally by the formal K1-H controls.

C5's completed-cache event occurs at HGA-relative 3.5404697 seconds; verification
takes 0.0000122 seconds. The verified-zero phase is at process 3.5436209 seconds,
the genetic loop ends at 3.5437857, final UB publication is at 3.5445283, and the
process-exit phase is at 3.5575732. C7 has the corresponding cache event at
HGA-relative 2.1348880 seconds, verification 0.0000040, zero phase2.1376127,
loop exit 2.1377560, publication 2.1386041 and process exit 2.1514592. These clocks
are labeled separately in `zero_event_phases.csv`. The full-K1 adapter exports
the completed-cache event but not an individual winning-decode duration.
Four separately charged diagnostics clarify the timing scopes. Runs 59/60 link
the unchanged v5 core, but expose a disabled decoder counter: it is enabled only
in the old fixed-generation PREFIX mode. Their raw zero is preserved and marked
unavailable, never interpreted as free decoding. Runs 61/62 compile the unchanged
HGA adapter against a copied header with only the two decoder timing guards
enabled, then link that object before the retained core archive. Main v5 source,
binary, policy and confirmation bindings are unchanged. Both diagnostic pairs
match the complete production reliability prefixes and independently verify routes.

| Counter-enabled diagnostic | C5 | C7 |
|---|---:|---:|
| Charged process seconds | 3.688 | 2.110 |
| HGA seconds | 3.617439 | 2.084934 |
| Completed generations / decoder calls | 10 / 306 | 57 / 1098 |
| Initialization seconds | 0.059114 | 0.010633 |
| `decode_routes` cache-miss seconds | 1.281070 | 0.791706 |
| Observer seconds | 0.000540 | 0.000347 |
| Cached-route conversion seconds | 0.0000289 | 0.0000145 |
| Original verification seconds | 0.0000971 | 0.0000347 |
| Candidate-ledger publication seconds | 0.0001637 | 0.0001768 |
| Verified-zero event, HGA seconds | 3.616808 | 2.084244 |

These are nested scopes, not additive costs: decoder time covers cache misses
through `decode_routes`, and does not label all other HGA work as decoding.
The individual winning-decode duration remains unavailable; completed-cache
discovery and verification/publication/certification phases are recorded separately.
The auxiliary executable is observational and makes zero optimizer calls. Its
timings do not replace formal full-K1 performance. The two measurement corrections
and the build-only import failure are preserved in the research log.

Cold C5 protects primal behavior independently of warm zero certification.
At cap 120, cold OFF/credit-seed/released-PROOF all certify zero in
59.468/60.141/63.438 seconds, with the identical104.549275 core Work. The last
PROOF call ends WORK_LIMIT and returns its inherited bound, not its partial
objective. Differences remain below both time gates. This does not erase the
historical cold JOINT regression or justify choosing cold startup per instance.

## Frozen formal campaign and confirmations

The nine-role panel is fixed in `protocol.json`, with original file hashes and
manifest parameters. Mathematical route T is separate from the process cap.
All listed scenarios use pickup/drop handling 60/60 seconds and lambda 0.15.

| Role | Source/operating condition | V / M / Q | Mathematical T, seconds | Selection role |
|---|---|---:|---:|---|
| D3 | Round39 small-medium, seed 1343324363 | 12 / 3 / 30 | 2850 | Public protection |
| D4 | Round39 small-hard, seed 1288546114 | 12 / 3 / 30 | 2400 | Public shared-structure control |
| D7 | cb443 regional r1 shortage | 50 / 4 / 30 | 18000 | Public long-route protection |
| C2 | cb443 compact r1 surplus | 20 / 2 / 30 | 1800 | Public positive-HGA protection |
| C5 | cb443 compact r1 surplus | 50 / 4 / 30 | 18000 | Public warm-zero/cold-primal protection |
| C6 | cb443 compact r1 shortage | 50 / 4 / 30 | 1800 | Public probing bottleneck |
| C7 | cb443 regional r2 balanced | 20 / 2 / 20 | 10800 | Public zero-HGA role |
| C8 | cb443 regional r1 shortage | 30 / 3 / 30 | 3600 | Preselected confirmation |
| C9 | cb443 compact r1 balanced | 20 / 2 / 20 | 10800 | Preselected confirmation |

C8/C9 were chosen from public metadata before Round 65 outcomes and did not
participate in mechanism selection. They are not represented as sealed or new
holdout data. Their cap 600 and three arms were bound to the exact driver,
protocol, build and policy hashes before optimization; C8 must finish all three
arms before C9 can start. No confirmation result changes the frozen rule.

The final v5 campaign uses actual K1-H and original P-GRB references. Of the eight
formal candidate/K1-H roles, C5 and C9 gain time through verified-zero startup,
D7 loses capped-gap performance, and the other five are below the dual gates.
There is no demonstrated nonzero proof-performance gain over stable K1-H.

| Confirmation, cap 600 | Process seconds | Verified UB | Global LB | Absolute gap | Certificate |
|---|---:|---:|---:|---:|---|
| C8 candidate | 597.094 | 0.801649961457 | 0.629319151851 | 0.172330809606 | No |
| C8 K1-H | 597.094 | 0.801649961457 | 0.629319151851 | 0.172330809606 | No |
| C8 P-GRB | 597.047 | 0.806818916787 | 0.576956749593 | 0.229862167194 | No |
| C9 candidate | 0.500 | 0 | 0 | 0 | Yes |
| C9 K1-H | 36.141 | 0 | 0 | 0 | Yes |
| C9 P-GRB | 0.953 | 0 | 0 | 0 | Yes |

C8 is the V30 nonzero difficult confirmation. Candidate and K1-H have identical
startup witnesses, canonical root, logical HGA trajectory and final bounds;
each makes three LP and two MIP calls. The candidate spends 4.757863 optional
Work, so its allowance does not bind. Both improve on P-GRB's final gap, by
0.057531358 for the candidate (25.0%); this shared advantage is not attributed
to new scheduling. C9 confirms the zero-stop gain: 35.641 seconds saved against
K1-H, with the same logical prefix and no optimizer call in either K1 run.
The 0.453-second difference from P-GRB is below the gates, not a claimed gain.
No confirmation led to replacement, tuning or extra performance trials.

The completed D3/D4 protection runs use cap 300:

| Role / arm | Process seconds | Verified UB | Global LB | Absolute gap | Certificate |
|---|---:|---:|---:|---:|---|
| D3 candidate | 297.047 | 0.045054161581 | 0.043894676861 | 0.001159484719 | No |
| D3 K1-H | 297.062 | 0.045054161581 | 0.043893848783 | 0.001160312798 | No |
| D3 P-GRB | 297.125 | 0.045054161581 | 0.041577109992 | 0.003477051588 | No |
| D4 candidate | 128.844 | 0.506343307565 | 0.506343307327 | 0.000000000239 | Yes |
| D4 K1-H | 129.219 | 0.506343307565 | 0.506343307327 | 0.000000000239 | Yes |
| D4 P-GRB | 297.078 | 0.506343307565 | 0.195859704247 | 0.310483603318 | No |
| D4 warm JOINT | 53.390 | 0.506343307565 | 0.506343303197 | 0.000000004368 | Yes |

D3 is below both comparison gates against K1-H, while its gap improves on
P-GRB by 0.002317567. D4 candidate and K1-H perform the same native Work
(208.951923 including LPs); their small time difference is not a gain. Both
certify where P-GRB remains open. The actual JOINT structural control retains
its known advantage: 53.390 seconds is 75.454 seconds faster than the F0
candidate. Its root LP bound is 0.317302644; the released PROOF screen reaches
only 0.171173189. JOINT also proves two child intervals empty and reaches a
smaller controlling domain. Thus the bounded projection service has not
recovered D4's resident shared structure benefit. A smaller matrix is not a
substitute for that missing proof strength.

C2's cap 600 candidate and K1-H both certify U=0.829963413172 with
LB=0.829963402950 in 526.906 and 529.735 seconds. They execute the same five
LPs, one child-bound target MIP and one resumed terminal MIP. The terminal
call has identical 1067.615529 Work, 44825 nodes and 3923480 simplex iterations.
This is positive-objective protection with no demonstrated scheduling gain;
the small time difference is below the gates. The optional budget does not
truncate useful probing here. Original P-GRB remains uncertified at 597.078
seconds with the same UB, LB=0.786482853507 and absolute gap 0.043480559665.
Candidate and K1-H each use 1069.636749 total native Work; P-GRB uses
1168.155996. This is a certificate advantage over the official benchmark,
shared with stable K1-H.

The completed C6 cap 600 trio is already independently checked:

| C6 cap 600 | Process seconds | Verified UB | Global LB | Absolute gap | Certificate |
|---|---:|---:|---:|---:|---|
| Frozen candidate | 597.093 | 1.693523057335 | 1.496731380915 | 0.196791676420 | No |
| Literal K1-H | 597.109 | 1.689157237950 | 1.498479846432 | 0.190677391518 | No |
| Original P-GRB | 597.094 | 1.689100732213 | 1.375090107858 | 0.314010624355 | No |

The candidate is worse than K1-H by 0.006114285 absolute gap (3.21%), below the
joint 0.001/5% gate, and improves on P-GRB by 0.117218948 (37.33%). This preserves
an advantage over the official benchmark; it is not an improvement on stable
K1-H. K1-H completes both child LPs, pauses parent MIP at the child-disjunction
target and resumes; the candidate retains the parent after unknown lookahead
and runs one MIP. Native incumbent improvements are independently recomputed.

The D7 cap1200 trio is also independently checked:

| D7 cap1200 | Process seconds | Verified UB | Global LB | Absolute gap | Certificate |
|---|---:|---:|---:|---:|---|
| Frozen candidate | 1197.125 | 0.215644075316 | 0.196069024230 | 0.019575051086 | No |
| Literal K1-H | 1197.140 | 0.215644075316 | 0.197729722520 | 0.017914352796 | No |
| Original P-GRB | 1197.093 | 0.277320865934 | 0.197286478715 | 0.080034387219 | No |

The candidate's gap deteriorates by 0.001660698 (9.27%) relative to K1-H,
exceeding both gates. This is a failed protection case for the complete policy.
The candidate still beats P-GRB's gap by 0.060459336 (75.54%); here its better
incumbent supplies that advantage, while P-GRB's LB is higher than the
candidate's. The inherited specialized HGA's contribution is not relabeled as
a new proof-scheduling benefit. Both K1 runs pay their full HGA independently,
543.636/540.635 seconds, and have identical logical trajectories/startup state.

D7 supplies a real committed-split continuation case: the root LP and both child
LPs complete, the right child is proved empty, and the full-coverage transaction
commits. The next grandchild LP reaches WorkLimit; its complete parent remains
active and receives 638.068 seconds of core work. The account records 30.001187
optional Work/15.378842 seconds and 1548.909193 core Work. K1-H completes one more
LP and one more split, then searches a narrower controlling interval. Its final
bound is better despite having paid for that optional work. Lower Work or fewer
calls therefore do not establish better proof performance. All unknown-child,
empty-half, frontier-minimum and type-restoration audits pass.

## Failures, numerical gates and evidence limitations

All charged launches, including discarded development branches and micros, remain
in `processes.jsonl`. v2 exposed repeated CSV headers from Windows append tellp;
v3 fixes header creation, and the reader skips only exact repeated headers in
retained v2 evidence. v3 D7 and v4 C6 proof copies return a nominal optimum that
fails the unchanged1e-7 residual gate (C6 DualVio about 9.94e-7). These bounds are
rejected and optional proof stops; they are not promoted to certificates.

v5 requests and reads back1e-8 feasibility/optimality tolerances only on the proof
copy, so the unchanged gate can be met. Main/official solver tolerances are not
relaxed or changed. A fresh matched v5 screen follows; earlier timings keep their
own build identity. Final packaging must match v5's complete C++ source hashes
and measured executable SHA256
`2de84014cd49a3a272161105ef5cfc6408c1fd91f7ad5d932bcea9e1bd16a0c9`.

| Measured build | C++ source commit | Charged performance/micro launches |
|---|---|---|
| v1 | `c109cbfc5fbd1b7d0b055f4470beea126593bc24` | 1–7 |
| v2 | `f764aacaed3fc9c32b4e7f94a4a78253dbde0e35` | 8–9 |
| v3 | `0355168f0f0561b6a57416ca64e5edbcb5a0d12b` | 10–18 |
| v4 | `f5ceb41e037b8797243dcf608cc53ebe6dba1e2b` | 19–21 |
| v5 | `b1d3bf53a6ab70680e7b60c999f374f2eb92c121` | 22 onward, formal policy frozen after 32 |

Each build record includes its executable SHA256 and test log. Later commits
package scripts and evidence without changing the measured solver source.
The HGA timing executables have separate harness/core-archive bindings, with the
counter-enabled adapter and transformed header identified explicitly. They are
not a sixth full-solver measurement or a replacement for the formal campaign.

The 42-test suite passes in v5. Together with the production audits it covers
default-off identity, physical block
equivalence, multiplier signs/finite bounds/rounding, actual-point cuts and scopes,
unknown versus infeasible, inherited LP bounds, atomic parent/child coverage and
empty-child inheritance, credit/debt and MIP fallback, no repeated unknown probe,
epoch/cutoff invalidation, cross-leaf physical rows, type/lifecycle rules, and HGA
zero/positive-prefix/memory persistence boundaries. `Round65Tests` adds direct
algebra, emitted-matrix, budget/debt, atomic coverage and HGA tests; inherited
scheduler/domain/certificate tests retain their existing coverage. Actual MIP
fallback, no repeated unknown probe and LP/MIP restoration are additionally
checked in the completed production traces. The independent audit recomputes
routes, each new UB snapshot, complete-frontier bounds, optional admission/cost
totals, row algebra and original P-GRB fingerprints/readbacks. These distinctions
avoid describing a budget unit test as an executed native lifecycle test.

The full native optimizer counts, auxiliary/proof query counts, caps and statuses
are in `runs.csv`, `native_calls.csv`, `optional_call_costs.csv` and the compact
receipts. No partial-dual bound implementation or full projection closure is
claimed. Elapsed process time includes paid startup, modeling and shutdown;
uncertified elapsed time is not labeled solution time. Gurobi Work is explanatory
evidence on this machine, not an end-to-end or cross-machine speed metric.
For legacy K1-H/P-GRB, zero in the optional/core account columns means that the
new account is absent, not zero solver cost. `optional_account_present`,
`main_native_work`, `main_native_seconds` and `total_accounted_optimizer_work`
make that distinction explicit; P-GRB's single optimizer invocation is one MIP.

The final budget is 55 performance runs, 3 native micros and 4 HGA-only timing
diagnostics: 62/72 charged launches. Five original-reference builds call no
optimizer. There are 308 recorded optimizer calls: 123 main LPs, 60 main MIPs,
94 vehicle auxiliary LPs and 31 proof-copy LPs. No 1800/3600-second run was used.
The reserved final campaign contains 26 launches, including the mandatory
C6/D7/C8 long trios, C2 and both confirmations. All launched solver/HGA processes
return successfully within their caps; rejected numerical proofs and unavailable
timers remain explicit negative evidence. The reliability category grew from
the suggested eight to twelve launches to include the four disclosed timing
diagnostics; this did not displace the required production comparisons.

Final independent checks cover 116 route snapshots and 91 projection rows.
The 67 compact receipts and 2279 local artifact hashes are packaged. A fresh
`--submitted` replay passes and reconstructs `runs.csv` byte for byte, while
checking the original selection-ledger prefix, confirmation order/bindings and
test-log hashes. Large native files remain local. Scoped Git attributes preserve
frozen evidence and driver bytes; inherited C++ checkout text may differ only
by LF/CRLF conversion. The actual packaged working C++ tree matches v5 exactly.
A second replay from a clean snapshot of 1540 staged files, containing neither
`local_raw` nor a solver binary, also passes. See `audit_final.log`.

## Artifacts and next design question

`reproduce.md` gives a separate-output reproduction entry point. Build freezes,
confirmation binding, small witnesses/projection rows, paired results, test logs
and receipts are submitted. Large native logs, models and executables remain
local with path/size/SHA256 in `local_artifact_index.csv`. No credentials, license
or unrelated user files are included.

The next proof design should decide whether a bounded strong bound can change
the controlling frontier or eliminate a relevant interval before paying for it.
The current D4 experiment shows why generating stronger valid rows alone is
insufficient: the core search can remain identical. Preserving complete-domain
search opportunity and targeting decision-relevant evidence are the substantive
questions; another larger resident formulation is not the inferred remedy.
The D7 result also identifies a control limitation: persistent core-due fallback
can give up useful later decomposition, and credit earned during a terminal MIP
cannot be spent before that call returns. A future design should investigate
paid, resumable lookahead after meaningful core progress while checking actual
native continuation costs. That is an untested next design question, not a
post-confirmation change to this policy or a claim that small repeated MIP
slices necessarily preserve solver progress.
