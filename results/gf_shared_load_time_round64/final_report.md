# Round64: shared load/time capacity and complete-algorithm qualification

**Campaign status: complete validation is running.** This working report will
be finalized only after the declared protection, reference and confirmation
runs and their audits finish. No stable default is upgraded.

## Research baseline and scope

The branch is based on Round63 PR #124 at
`f734d6781fd7125703489245cdb4dc27fb74625c`, targeting
`codex/round63-cumulative-time-resource`. The original dirty Round61 checkout
is preserved in a separate worktree. Round63 service measurements used
`b1bde3eab6c6fb9c4e1c4575acbdfa9141a46eaf`; its main resource/confirmation
measurements used `dc8d3e4a0ee3f63f0858b2c3b38a59a92cd1e783`. Those identities
are not confused with its final report-packaging head. See [restoration.json](restoration.json).

Both preceding final reports and Round63's mathematical, selection, protocol,
paired and lifecycle evidence were read before implementation. This round
does not revive the service representation matrix, attribute fresh-model
effects to cuts, reinterpret old node-aggregate B4 as arc sharing, or promote
cold-start improvements without a stable-start comparison. C5 is a known
primal/search protection role, never a new confirmation role.

The frozen panel contains nine unchanged inputs: D3 (T=2850), D4 (T=2400),
D6, D7, C2, C3, C5 and two roles selected from published metadata before any
Round64 outcome: C6 V50 compact shortage/T1800 and C7 V20 regional balanced/
Q20/T10800. Every input hash and actual parameter is in [protocol.json](protocol.json).
No role may be replaced after seeing a zero objective or a regression.

## Actual algorithm, lifecycle and startup

The [algorithm contract](actual_algorithm_contract.md) records the actual
implementation rather than relying on round names. The complete controller
keeps F0, K0=1, midpoint splitting, balanced normalized closure, tau=0.08,
native-target, exact-parent and original global coverage. Legacy rho=0.01 is
not the K1 threshold. Native Gurobi uses Threads=1, Seed=0, Presolve=Auto and
zero relative/absolute requested MIP gaps, with parameter readback. Official
P-GRB keeps its original compact model and default heuristics; no HGA, PREFIX,
archive, extra row, start or algorithm bound is supplied to it.

All new resource rows are static, globally physical and present in both LP
and MIP. The inherited per-leaf model-object reuse policy is unchanged, with
fingerprint checks, temporary LP type relaxation and integer type restoration
immediately after a retained LP returns, before any later MIP. No Round63
fresh-model override, copy-model workaround or new
resource callback is enabled. Existing progress/native-target callbacks remain.
Model-object reuse does not mean preservation of the whole B&B tree or a
guaranteed LP basis. Actual model identities/call types are retained in
[native_lifecycle.csv](native_lifecycle.csv).

Cold research arms use verified empty routes, Y=b. The inherited CLI label
"greedy" was misleading; the frozen initial protocol is retained with an
explicit description erratum. Warm research explicitly inherits the stable
full HGA configuration (seed 20260626, population 24, decoder 10, 2000
non-improving generations). Every formal process generates and validates its
own candidate and pays the entire cost. HGA changes U and legal domains;
native MIP starts are disabled identically. Route-based q/f/h mapping is
implemented and tested, but this capability does not silently enable starts.

The v3 C2 and D7 matrices have identical initial route snapshots, HGA hashes,
U and domains within each role. No historical route is replayed for free.
Startup and lifecycle therefore cannot explain differences between arms in
these matched matrices. They do explain why cold and warm comparisons answer
different questions.

## What sharing adds mathematically

The original inventory objective, S=0 convention, weight parsing, one nonzero
unidirectional service per visited station, connectivity and physical duration
are unchanged. Vehicles depart empty, may return loaded, and Q constrains
every prefix, not cumulative pickup. The full proof and formulas are in
[mathematics.md](mathematics.md).

Q adds nonnegative arc load q, capacity q<=Qx, station balance out(q)-in(q)=p-d
and the same exact out(q)=L link used by SEP/JOINT. Return arcs remain;
depot departures are zero, with no incorrect depot balance. Summing these
flows implies the familiar mixed inventory-route capacity cuts. The old
optional aggregate InventoryRouteCuts closure is inactive in actual F0.
Explicit q flow and its benefits are not claimed as new arc-sharing theory.

T is the inherited safe scaled cumulative flow f. SEP adds Q+T and the old
node aggregate B4, cbar L<=out(f). JOINT adds cbar q<=f on each arc. With the
exact same stored coefficients, h=f-cbar q is an invertible transformation:
balance(h)=incoming scaled travel+cbar d, h>=0, h+cbar q<=Bx. Legal integer
routes embed with q as prefix load, f as prefix travel plus prepaid pickup
handling, and h as prefix travel plus prepaid delivered handling. This is
final-route accounting, not a physical arrival clock or a time window.

Zero handling, directed/nonmetric costs, zero-cost arcs, heterogeneous Q,
capacity recycling and loaded return are covered by proof and solver-free
route tests. Original rows remain. Q and T have no asserted dominance;
JOINT projects into SEP, which projects into both Q and T.

### Actual target LP and free auxiliary re-completion

Each role uses exactly the same canonical F0, original objective, interval
and cutoff across the five modes. All original F0 columns are identified
from OFF and pinned at the actual SEP target optimum; new q/f remain free.
SEP must be validly feasible and JOINT strictly infeasible. Full LP rows,
bounds and pin residuals are independently checked.

| Role | OFF | Q | T | SEP | JOINT |
|---|---:|---:|---:|---:|---:|
| D3 | .020550011 | .020550011 | .020550011 | .020550011 | .020550011 |
| D4 | .093948255 | .093969106 | .262943554 | .290096728 | .317302644 |
| D6 | .125691831 | .125691831 | .125691831 | .125691831 | .125691831 |
| D7 | .175143185 | .175143185 | .175143185 | .175143185 | .175143185 |

All four tested SEP-optimal original points are no longer completable in
JOINT, including positive-objective long-T D6/D7. Thus there is actual
projection increment on a target-optimal face even where the target objective
does not improve. This does not establish that the excluded coordinates are
decisive for integer search, or that projection onto a smaller variable set
would be strict after allowing original L and other F0 variables to change.

Independent bounded auxiliary diagnostics for D4/D7 reproduce feasible SEP
and infeasible JOINT. Their normalized Farkas combinations use explicit finite
auxiliary bounds to account for every negative column residual; inequality
signs, original affine RHS, scope, coefficients and raw violation are checked.
Corrected violations are about .310508 and .026835. The resulting rows use
only original x/p/d/L coordinates: 16 nonzero coefficients for D4 and 347
for D7. Thus these particular x/p/d/L points are excluded independently of
how other F0 auxiliaries are chosen. Exclusion after also freeing L, in a
projection onto x/p/d alone, is not established. Submitted sparse evidence
and the verifier reconstruct the physical resource matrix and SEP completion;
membership in the entire F0 is separately linked to full target-LP residual
evidence and original-point hashes. These are numerically checked algebraic
projection certificates, not exact rational proofs or original optimality
certificates. No diagnostic row is submitted to production search.

The network is not treated as Round63's single-commodity time mincut problem.
A particular violating q/f allocation alone would not establish any of these
exclusions. See [strength.csv](strength.csv), [lp_residual_verification.csv](lp_residual_verification.csv)
and [submitted_projection_verification.csv](submitted_projection_verification.csv).

## Cost-controlled alternative: QCAP, tested and stopped

The tested smaller alternative keeps Q and adds only cbar q<=Bx, a necessary
projection of cbar q<=f<=Bx. It has no time-flow variables or balances. Each
row is omitted only if an outward-rounded cbar Q bound proves it redundant
with q<=Qx. This is a uniform physical rule, not a case-name or past-result
switch. QCAP is contained in Q and contains the JOINT projection; there is
no asserted dominance over SEP or T and no complete-closure claim.

On D4/C2 it adds respectively 432/800 rows and no columns beyond Q. On D7
every new row is redundant and the model is byte-identical to Q, so no new
sharing strength or escape from Q's regression can be claimed there.

Two cap120 batches, with exactly eight LPs each, compare OFF/Q/QCAP/SEP and
Q/QCAP re-completion at both the Q and SEP optimal original points. D4's
Q/QCAP target values are .093969106/.108868504; C2's are
.550761385/.594436785. Both Q and SEP points are infeasible in QCAP with free
q, with feasible Q controls. The smaller mechanism therefore has real
increment, not merely fewer variables on paper.

However, the matched v4 D4 native screen triggers the declared certificate
veto: Q certifies F=.506343307565206 in 91.547 seconds, whereas QCAP consumes
118.093 seconds under cap120 and leaves LB=.48960010587766817, gap
.01674320168753779. Both legal final witnesses pass independent original
verification. QCAP is stopped for advancement; its mathematics, code and
negative result are retained. This bounded failure does not reject every
possible shared projection or robust separator.

This loss is not explained solely by root construction overhead. Q/QCAP's
native presolved root objectives are .1189913/.1432834 and final root-cut
bounds .3931858562/.4047008097. Root processing takes 3.184/4.805 seconds;
total work is 147.997/198.462 and explored nodes 14648/20521. The stronger
root is followed by a more costly, incomplete search. Ratios that include
root work are not interpreted as isolated marginal node costs. The smaller
representation therefore removes the doubled f block without establishing
a better complete proof process on this matched screen.

## Cold versus real-start evidence available before complete qualification

Cold fixed-F0 screens and full-original K1 results have different certificate
scopes; they are never pooled as solved instances. At cap120 on D4,
OFF/Q/SEP certify while T/JOINT do not. JOINT leaves gap .023922062. On D7,
all five are uncertified: OFF/Q/T/SEP/JOINT gaps are respectively
.476160675/.088563590/.169525735/.216596814/.153121368. Q is best and much
of the apparent improvement comes from incumbent quality. JOINT improves on
SEP there but is worse than Q; it cannot receive credit for all Q-flow gains.

The complete warm C2 cap600 matrix has the same initial/final verified
F=.8299634131717752 in all arms. OFF/Q/SEP/JOINT certify in
526.281/573.625/325.016/397.156 seconds. Calls are 7/7/8/11 and splits 1/1/2/3.
SEP saves 201.265 seconds (38.2%) and JOINT saves 129.125 seconds (24.5%)
against OFF; JOINT is 72.140 seconds (22.2%) slower than SEP. Thus the
combined representation helps this real-start proof search, but extra arc
sharing does not add a speed gain. Q's 47.344-second slowdown is about 9.0%,
below the joint time gate; that is not equality.

The actual same-v3 stable C2 K1-H reference also certifies this F in
526.204 seconds, with the same seven calls, one split, initial candidate
hash/U/domain, first canonical F0 hash and final bounds as research warm OFF
(526.281 seconds). JOINT therefore saves 129.048 seconds (24.5%) against
the measured stable algorithm; SEP remains faster than JOINT. Official
unmodified P-GRB uses 597.078 seconds without certification, with the same
U=.8299634131717752, LB=.7865231625220372 and gap=.043440250649738.
Its expected compact fingerprint51964193, native domain and parameter
readbacks match. These are complete-policy references, distinct from the
isolated SEP/JOINT resource comparison.

For full warm D7 cap1200, all four keep the same HGA F=.21564407531579505,
and none certifies or improves it. HGA costs about 568--572 seconds, charged
separately in every process. OFF/Q/SEP/JOINT final gaps are
.017914352795947386/.019341441693344674/.019361159959621843/.019405854678165302.
Each resource arm regresses beyond both the .001 and 5% gates. All use six
native calls and two splits; there is no startup or model-lifecycle policy
change. Stronger projection alone did not overcome the positive-objective
proof bottleneck. The actual same-build stable K1-H reference below reproduces
OFF's final bounds, so this regression also holds against the real stable
algorithm rather than only its research adapter.

### Native size and cost explain why strength is insufficient

D7's controlling warm MIP keeps most of the new flow columns after presolve.
The table uses the same recorded leaf L0.0.0; root objectives are the native
log's rounded values, not new independently certified global bounds.

| Arm | Raw rows / columns | Presolved rows / columns | Presolved nonzeros | Printed root objective | Root relaxation seconds | Explored nodes |
|---|---:|---:|---:|---:|---:|---:|
| OFF | 103581 / 23563 | 49478 / 23445 | 500523 | .195378 | 4.50 | 566 |
| Q | 113981 / 33563 | 59682 / 33445 | 533151 | .195378 | 9.55 | 17 |
| SEP | 124381 / 43563 | 70082 / 43445 | 583263 | .195378 | 29.65 | 1 |
| JOINT | 134381 / 43563 | 80082 / 43445 | 604174 | .195378 | 43.02 | 3 |

Presolve does not make the doubled resource representation free. The initial
root LP is substantially more expensive without a visible target-bound
increase at the log's precision, and subsequent root processing leaves much
less tree exploration. These observations support a cost explanation, not
a causal decomposition of every second. Per-call work, simplex iterations
and wall are in [native_call_costs.csv](native_call_costs.csv); its work/time
per-node ratios explicitly include root work and must not be read as pure
marginal node costs. No native incumbent improves on the paid HGA witness
in this matrix. C2 remains a positive proof-search counterexample to a
blanket claim that resource extensions always hurt.

## Complete qualification and independent confirmation

The frozen uniform candidate is JOINT, explicitly a diagnostic research
candidate rather than a mainline recommendation. Its mathematical increment
warrants the remaining full qualification even though D4's fixed-F0 loss and
D7's warm regression already veto adoption. It is not selected as the fastest
mode and its negative results are not removed. [selected_candidate.json](selected_candidate.json)
binds the unchanged rule, startup and retained v3 executable. The tested v4
QCAP alternative is separate; existing same-v3 C2/D7 matrices need not be
repeated simply to change a packaging version.

[confirmation_freeze.json](confirmation_freeze.json) binds the mode,
uniform cap600, active build, driver, original protocol and selection hashes
before either holdout is opened. It enforces C6-before-C7 and the declared
warm/cold OFF/JOINT plus unchanged reference arms. The roles and thresholds
are not changed in response to results.

Warm D3 completes with identical initial routes/U/domain and final original
F=.04500155005562836. OFF/JOINT both certify, using five calls and zero splits,
in 357.141/519.313 seconds. The 162.172-second (45.4%) JOINT slowdown passes
both regression gates; independent final physical route checks pass.

D4 warm protection also certifies the same F=.506343307565206 from identical
startup routes/U/domain. OFF takes 129.000 seconds (four calls, zero splits);
JOINT takes 53.390 seconds (nine calls, two splits). The 75.610-second (58.6%)
gain passes both gates and both original final witnesses verify. Thus the
cold fixed-F0 D4 certificate loss is not a substitute for complete warm
qualification. This positive result does not erase full warm D3/D7 losses.

C3's cap600 warm pair is uncertified with unchanged identical
U=.8142420757383566. OFF/JOINT LB is .702684834668421/.7198986904552764;
gap decreases from .11155724106993559 to .09434338528308017, a
.01721385578685542 (15.4%) gain passing both gates. Calls/splits are 4/0
versus 7/1. The initial routes/domain match and original physical checks pass,
including the loaded return. This is a bound gain, not a primal gain or
certified solve-time improvement.

For C3, the native LP ledger explains the changed outer path without a changed
controller: JOINT raises the initial LP bound to .5756432922 and proves the
right child [G=.4071210379,.8142420757] infeasible. The inherited infeasibility
split rule fires; subsequent decisions still use K0=1 and tau=.08. OFF's
initial LP bound is .3573298053 and the same controller retains the parent.
The later matched SEP control also proves the right child infeasible and
uses seven calls/one split. Thus that split is not attributable specifically
to arc sharing: Q/T/B4 already suffice on this role.

C5 warm OFF/JOINT both certify F=0 from the identical current-process HGA
witness, with zero native calls. Wall is 199.437/204.469 seconds; accepted
zero is at process seconds 199.3910454/204.4206948. The 5.032-second
difference is below both time gates, but is not called equivalence. Both
routes pick up 225, deliver 150 and return 75 to depot; original duration and
prefix capacities verify. Because F>=0 closes the problem before native
search, this warm pair does not exercise the resource block's search cost.

### C5: legal zero preserved, search protection fails

The matched cold cap600 pair reproduces the important failure that the warm
zero shortcut cannot reveal. OFF certifies F=0 in 59.453 seconds; JOINT takes
208.000 seconds, 148.547 seconds more (249.9% slower, about 3.5 times total
time). Initial empty witnesses and domains are identical; both use four
native calls and zero splits. Both final original zero routes independently
verify, with pickup225/drop150/return75. The shared rows have not removed
the zero solution, but they delay its discovery substantially.

| C5 cold event | OFF | JOINT |
|---|---:|---:|
| First original feasible empty witness, process seconds | .0023766 | .0024055 |
| Native zero objective line, rounded per-call seconds | 49 | 176 |
| Terminal native runtime, seconds | 49.851 | 176.30 |
| Accepted original zero, process seconds | 59.4238164 | 207.9746524 |
| Process exit, internal seconds | 59.4341457 | 207.9798957 |
| Accepted-zero-to-exit tail, seconds | .0103293 | .0052433 |
| Terminal native work / explored nodes | 104.549 / 14 | 380.62 / 1 |

Native zero lines are rounded model-objective observations and are validated
as original F=0 only at extraction. Their discovery-to-native-return tail is
short at the log's precision; the precisely recorded original acceptance tail
is also short. The regression is primarily in discovery/root processing,
not a long proof after an accepted original zero. The JOINT native root bound
was already zero. This rejects a claim of robust C5 search protection; its
warm end-to-end pair remains below the time gate. Independently, D3/D7 fail
the actual paid-HGA upgrade tests. No C5-specific disable switch is added.

### D7 cold long result: primal gain, weaker final bound

The same-v3 cap1200 cold pair is uncertified in both arms. OFF has
U=.2760665094310133, LB=.196435140633266, gap=.07963136879774729;
JOINT has U=.26547702332085715, LB=.19588172293058817,
gap=.06959530039026898. The .01003606840747831 (12.6%) gap reduction passes
both gates. U improves by .0105894861 while LB declines by .0005534177:
this is wholly a primal gain, not stronger proof progress. Both have four
native calls and zero splits. Total native work/nodes are 3062.977/570
versus 2908.528/34; fewer nodes do not imply a stronger bound or cheaper
marginal nodes.

The cold JOINT gap .0695953 remains much larger than the same-cap warm JOINT
gap .0194059, despite warm HGA consuming about 570 seconds of its process
budget. This is a paid-startup comparison, not a free route replay. The actual
stable K1-H and official P-GRB runs provide the separate policy comparison.

The actual same-v3 official D7 P-GRB cap1200 run finishes uncertified in
1197.078 seconds, U=.27732086593398886, LB=.1972864787145512,
gap=.08003438721943765. Its original route independently verifies at
F=.27732086593398864; the expected compact fingerprint is -373258443 and
native domain/lifecycle checks pass. Cold JOINT therefore improves this
measured reference gap by .01043908682916867 (13.0%), despite a weaker LB;
warm JOINT's gap is also smaller. This round does not blindly carry forward
Round63's reference ranking.

Actual stable K1-H takes 1197.141 seconds without certification, with
U=.21564407531579505, LB=.19772972251984766 and gap=.017914352795947386.
Its current-process HGA costs about 555 seconds. The startup hash/U/domain,
first canonical F0 hash, six-call/two-split structure and final bounds match
research warm OFF. Warm JOINT worsens this actual stable gap by
.001491501882217916 (8.3%), passing both regression gates. Cold JOINT's gap
is .0516809475943216 larger than stable K1-H's. Thus the answer to whether
D7 beats the real references is mixed: yes against this measured official
P-GRB, no against stable K1-H, including after matched paid warm startup.

| D7 complete policy, cap1200 | UB | LB | Absolute gap | Certificate |
|---|---:|---:|---:|---|
| Official P-GRB | .277320865934 | .197286478715 | .0800343872194 | no |
| Stable K1-H | .215644075316 | .197729722520 | .0179143527959 | no |
| Cold OFF | .276066509431 | .196435140633 | .0796313687977 | no |
| Cold JOINT | .265477023321 | .195881722931 | .0695953003903 | no |
| Warm JOINT | .215644075316 | .196238220638 | .0194058546782 | no |

The actual reference audits are in
[reference_contract_verification.csv](reference_contract_verification.csv);
explicit cross-stage comparison links preserve matching executable, physical
cap and complete-problem scope. These comparisons are not mislabeled as
isolated resource ablations.

### D4 identifies a real complete-algorithm arc-sharing gain

The additional same-v3 warm SEP control certifies the same original
F=.506343307565206 in 263.968 seconds, from byte-identical initial routes and
domain and the same paid HGA U. JOINT takes 53.390 seconds: a 210.578-second
(79.8%) saving. Q, T and B4 are identical in these arms, so this gain is not
misattributed q-only strengthening or an initial-quality/lifecycle change.

The logged LP states show why the unchanged outer algorithm takes different
paths. SEP's root and left-child bounds both remain .2900967277; its right
child G in [.2532113946,.5064227892] is feasible with bound .4929672478.
JOINT raises the root bound to .3173026436 and proves that right child
infeasible, then also excludes G in [0,.1266056973]. The existing exact
infeasibility split rule focuses the subsequent proof on the surviving Gini
region. SEP uses four calls/zero splits and JOINT nine calls/two splits.
This is a concrete setting where the new projection increment matters to
complete proof cost. A separate warm Q runtime was not measured on D4;
no claim that JOINT is its fastest possible representation is made.

The contrast is a development follow-up selected after observing the OFF/
JOINT result, not an independent confirmation. It is retained alongside the
opposite cold fixed-F0 D4 result and the negative C2/D7 SEP/JOINT contrasts.
The frozen candidate, holdouts and decision gates remain unchanged.

The additional C3 SEP control retains the same U=.8142420757383566 and
finishes uncertified at LB=.71780632637948627, gap=.09643574935887034,
wall597.094 seconds. JOINT's gap .09434338528308017 is smaller by
.00209236407579017 (2.2%), below the required 5% relative gate even though
the absolute gate passes. SEP already accounts for most of the observed
OFF-to-JOINT improvement. This is a measured small arc-only bound gain,
not a qualified substantial gain or equality. Initial route/U/domain and
native-start treatment are matched; Q-only warm C3 remains unmeasured.

Pending at the time of this working draft: frozen C6/C7 warm/cold
and reference qualification. The final report must replace this paragraph
with all outcomes, first-feasible/zero/best timings, proof tails and explicit
confirmation classifications. No performance claim is made for these pending
runs.

## Explored mechanisms and scope

| Mechanism | Established evidence | Disposition and limit |
|---|---|---|
| Q-only | Familiar load-flow lift; strong cold D7 primal result, worse D7 warm gap; slower warm C2 below the joint time gate | Retain as an attribution baseline; do not credit its gains to new sharing |
| T and SEP/B4 | D4 target strengthening; SEP warm C2 is faster than JOINT; long-T target objective unchanged | Retain independent-resource control; no claim of a uniformly qualified SEP upgrade or independent SEP confirmation |
| JOINT | Actual SEP-optimal x/p/d/L points excluded, with re-completion and checked D4/D7 dual evidence; mixed complete warm outcomes | Frozen uniform diagnostic candidate; mainline adoption rejected by observed complete warm regressions; finish the declared qualification |
| QCAP | Smaller necessary projection; own target/projection increment on D4/C2, exactly Q on D7 | Stop advancement after the predeclared D4 matched certificate-loss gate; keep implementation and negative result |
| Full auxiliary/Farkas projection | Bounded diagnostic and portable checked row combinations | Evidence tool only; production separator, callback integration and full closure remain unimplemented/unmeasured, not experimentally rejected |
| Fresh-model or native-start changes | Not needed to implement static common LP/MIP rows | No new lifecycle/start policy is introduced; inherited model-object reuse and disabled starts remain the controls |

The paper-facing candidate has one static rule on every instance. Multiple
research modes exist to isolate contributions, not to form an instance-wise
portfolio. No model guard, file-export adapter or telemetry correction is a
theoretical contribution. The next technical priority, if this work continues,
is a cheaper projection tied to the controlling objective/proof difficulty
and tested against the same paid stable start; neither the diagnostic Farkas
timing nor QCAP's failed execution establishes that such a production method
already exists. Another unrestricted representation or parameter matrix is
not supported by this round's evidence.

From a reviewer-facing algorithm description, the candidate is simply the
inherited complete K1-H controller with the static Q/T/B4/arc-sharing lift in
each canonical LP/MIP. The cold counterpart changes only the declared initial
candidate source. The other resource switches belong to controlled ablations
and the stopped QCAP branch, not the final policy. No per-instance selector,
historical-route injection, tolerance relaxation or extra model restart was
introduced. The actual shortcomings are mixed complete cost and failed
protection, which are grounds to withhold a stable upgrade rather than to
introduce a role-specific safety switch.

## Correctness, accounting and reproduction

All 41 optimizer-free CTests pass through v4. Native micro is exhausted at
four launches; full micros verify actual multi-call LP/MIP reuse/type
restoration and current-run warm witness persistence. Physical snapshots are
independently checked in original units/objective. Feasibility and certificate
tolerances are not relaxed. Auxiliary statuses/objectives never substitute
for original certificates.

Every formal native UB update is gated by route reconstruction followed by
the independent original `verifySolution` calculation in GurobiBaseline;
PaperExternalGiniTree accepts only that verified original objective. The
Python verifier additionally checks all persisted initial/final and available
intermediate witness snapshots. Native incumbent log values remain in their
canonical model objective space and are not themselves verified original F.
Their comparison with the final original UB is a numerical observation,
not evidence that the same final route was already accepted at that time.

At selection, accounting is 32/72 charged launches and 152 optimizer calls,
including diagnostic LPs and both alternative screens. No charged failure,
overrun or unknown call count exists. The original preflight D3/Q CLI-guard
failure is retained as build-only, corrected before measured v1 and never
misrepresented as an optimizer run. The remaining declared campaign reaches
62 launches, including the two declared warm SEP attribution follow-ups,
with ten launches left unused unless justified by a new issue.

Every launch has a write-ahead record, physical cap, executable/source
identity, actual native call count and raw destination. Optimization is serial;
builds, Git operations and large audits are separated from performance queues.
All process cost is included. Uncertified wall time is consumed budget, not
time to solve. Gates require both 10 seconds/10% for certified time or
.001/5% for uncertified absolute gap; certificate loss is a separate veto.
Raw values below a gate are still reported.

Each performance cell is one serial launch on the frozen representative
panel. The thresholds classify observed effects; they are not statistical
significance tests or estimates of performance on the full instance family.
Same settings and executable control the comparison, while different native
paths and wall-limited stopping can still affect the final endpoint.

[reproduction.md](reproduction.md) is the entry point. Automatically generated
[measured_tables.md](measured_tables.md), [pairs.csv](pairs.csv), native shapes,
costs, trajectories, warm checks and route snapshots support the conclusions.
Large local models/logs/binaries remain outside Git with paths and hashes;
submitted projection and route evidence can be verified without those logs.
Projection diagnostic timings include their own construction/solve/export,
but exclude the separately charged earlier target-point generation; they are
not advertised as a deployed production separator's end-to-end cost.
