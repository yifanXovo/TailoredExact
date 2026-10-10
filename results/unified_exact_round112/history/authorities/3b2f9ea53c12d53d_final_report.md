# Round110: repaired entry, frozen panel confirmation

**Unique stage: BLOCKED.** All 42 actual native processes returned normally
under one final PE; 41 arms have qualifying complete clocks. Arm42, G100-R2
Seed1 M-B, completed its necessary postexit audit at 3600.707823600038 seconds
and its whole receipt at **3600.7215734999627 seconds**, exceeding the frozen
3600-second cap by 0.7215734999626875 seconds. The native-only within_cap flag
does not qualify this clock. The associated Seed1 comparison is UNEVALUABLE;
Seed sensitivity assessment is incomplete. This is a resource/protocol fault,
not an observed Seed loss, ordinary time-limit failure, or candidate rejection
on performance. No cap was extended, time truncated, or performance arm rerun.

The 12 main M-B/P pairs give **11 WIN, 1 TIE, 0 LOSS and no severe P
regression**. ENS/P also gives 11 WIN and 1 TIE. M-B/ENS gives **5 WIN, 3 TIE,
4 LOSS**, with severe losses on G50-C1 and G100-R2. These finite observations
are retained, but the incomplete formal qualification prevents
BROAD_PANEL_SUPPORT. ENS-C remains the default; no merge or new mechanism is
authorized by this report.

## Identity, repair and original panel

The verified starting R109 head is
8977da23a0be50da0ab2fceb69ad3ee04e040855 (PR171, open Draft), on R108
d11c94d81e6a2c5dcd64dad8c54b390f3cb4a027. The production repair is commit
382cbcddc00fad4b1ed44fe8e9d9862f77cf5fba. Its only production change is
Parser.cpp::namedBracketPayload: retain the original unanchored legal
name/whitespace/equals/left-bracket prefix match, then scan iteratively to the
first right bracket instead of recursively matching the payload. First
duplicate/embedded name, empty/multiline payload and missing-close semantics
are preserved. Numeric tokens, stod/llround, legacy max10 weights, min_ratio,
point order/matrix priority and sqrt(dx*dx+dy*dy)/1.5 remain unchanged.

The old fault was 0xC00000FD before parsing completed, in the regex matcher.
The old main fixed frame was 1,414,288 bytes and the PE reserved 2MiB stack;
neither the exact field nor recursive depth was proved by a dump. It was not
reported as OOM. No old crash was deliberately repeated. The minimal repair
was sufficient for this actual input domain; the unchanged prefix-whitespace
regex is not claimed universally stack-safe for arbitrary adversarial inputs.

Final PE SHA256:
c0384284aefd5aa2acc5d885ef37b0cfad6f93d083a5feb9ee693c41a786b411.
Gurobi13.0.2 DLL SHA256:
9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88.
The x64 PE is 21,095,101 bytes, with stack reserve/commit 2097152/4096. The
same GCC UCRT toolchain, C++17, warning flags and inherited empty optimization/
link settings were retained. No heap/object-lifetime restructuring, larger
stack, compiler/library switch or performance build setting was introduced.
production_identity.json binds the actual build command, header, toolchain,
DLL and 205 production files. The measured source and final scientific payload
are distinct identities; later publication receipts follow the payload.

All 12 old/new same-toolchain C++ mathematical dumps match byte for byte,
including integer fields and every binary64 distance. Sixteen finite format
comparisons and 58 active evidence regression cases passed. The final PE
itself passed all 12 common-main/real-Parser entries in three physical-T groups,
with instance_parsing_complete, zero Optimize, no heuristic and no oracle.
Five fixed H100 functional CLIs (Seed0 P/ENS/M-B, Seed1 P/M-B) returned
normally and exercised 17 Optimize calls, actual parameter readbacks, applicable
types/Starts and termination. Active admission04/seal02 accepted 368814 checks
before arm1; its SHA is
d6890ae315b6cc9b4a6e0fad951ff24627d485a0bbc36ca1e33fce2776779b7a.
Superseded qualification failures and source snapshots remain available.

This is the recovery confirmation of R109's original prospective frozen panel.
The same original 12 input bytes, station source, draw, method order, Seed
assignment, physical horizons, caps and thresholds were used. Eight roles
already had R109 observations. Coordinates/capacities come from one public
443-station table (442 eligible); targets, inventory, depot, fleet and horizons
are synthetic, and subsets overlap. These are not independent cities or iid
samples. Round110's 42 fresh attempts alone supply its comparisons; old results
are neither stitched to new arms nor substituted when better.

## Complete paired results and frozen gates

WIN/TIE/LOSS follow the unchanged certificate-first, absolute UB/gap and
complete-time rules. Signed tiny negative gaps remain visible. Unknown exact
clocks remain null; a timing classification is used only when invariant over
the entire recorded interval rectangle. Caps are 900/1800/3600 seconds for
V20/50/100, distinct from physical T and actual whole-arm time.

|Main Seed0 role|M-B/P|M-B/ENS|ENS/P|
|---|---|---|---|
|G20-C1|WIN|WIN|WIN|
|G20-C2|TIE|TIE|TIE|
|G20-R1|WIN|TIE|WIN|
|G20-R2|WIN|TIE|WIN|
|G50-C1|WIN|LOSS, severe|WIN|
|G50-C2|WIN|LOSS|WIN|
|G50-R1|WIN|WIN|WIN|
|G50-R2|WIN|WIN|WIN|
|G100-C1|WIN|LOSS|WIN|
|G100-C2|WIN|WIN|WIN|
|G100-R1|WIN|WIN|WIN|
|G100-R2|WIN|LOSS, severe|WIN|

|Fixed Seed role|Seed0 M-B/P|Seed1 M-B/P|Formal interpretation|
|---|---|---|---|
|G20-C2|TIE|TIE|Own zero fleets certified; time difference below 30s|
|G50-R1|WIN|WIN|Own U/gap improvement; neither certified|
|G100-R2|WIN|UNEVALUABLE|Arm42 full clock exceeds cap; sensitivity unassessed|

Seed1 G50-R1 M-B has U=.8081706967091032, L=.4479472567945393,
gap=.36022343991456396; P has U=1.1867595005433038,
L=.4124813921992838, gap=.77427810834402. Seed1 G100-R2 own physical U is
.031383380198019804 for M-B and .11331278178367776 for P; these descriptive
values do not convert its invalid-clock comparison into a formal WIN.
Its severe flag is null. There is no observed WIN-to-LOSS flip among the two
qualified repeated roles; the third role is unassessed, not a stability pass.

|Frozen condition|Measured outcome|Status|
|---|---|---|
|42 actual attempts under same final PE|42 normal native ends, no unstarted arm|Observed|
|All42 formally valid complete observations|41 qualified; arm42 necessary audit and whole clock exceed cap|FAIL / blocker|
|All12 main P pairs evaluable|12/12|PASS|
|Main P WIN >=6|11|PASS|
|Main P LOSS <=2|0|PASS|
|No severe main P regression|0|PASS|
|WIN in V20/V50/V100|3/4/4 WIN roles|PASS|
|WIN in compact/regional|5/6 WIN roles|PASS|
|All3 Seed1 pairs evaluable|2/3|Not satisfied; third unassessed|
|Seed1 >=2 nonLOSS|2 qualified nonLOSS|Observed; does not complete Seed gate|
|No severe Seed regression / no WIN-to-LOSS flip|None among 2 evaluable roles|Third unassessed|
|No unresolved numerical/scope/identity evidence|Current contradictions rejected with exact-domain proofs; surviving cover rebuilt|PASS for mathematical evidence|
|All ENS losses/MIXED disclosed|4 losses below; 0 MIXED|PASS|

selection_decision.json is the exact report decision. Its sole blocking reason
is ARM42_FULL_CLOCK_EXCEEDS_FROZEN_3600_SECOND_CAP. Performance reason_codes
are empty; UNEVALUABLE_COMPARISON is an unassessed support condition. Summary
formal_arms/completed_formal_arms count actual attempts, not 42 valid formal
observations. all42_valid_formal=false and qualified_formal_arms=41 disambiguate
those inherited field names. seed_severe_P_regressions=0 counts observed cases;
it does not assert that the unevaluable third pair passed.

## Every ENS loss and its decomposition

For candidate A=M-B and control C=ENS, delta_gap=delta_U-delta_L.
Endpoints do not independently identify a cause in p/d declarations, A/B rows,
native branching or search trajectory.

|Role|delta_U|delta_L|delta_gap|Actual loss|
|---|---:|---:|---:|---|
|G50-C1|.008182628062360805|0|.008182628062360805|Only ENS certifies own F=0; severe|
|G50-C2|0|0|0|Both own F=0; M-B 161.7407976s vs ENS 111.2417741s, +50.4990235s; nonsevere|
|G100-C1|0|0|0|Both own F=0; M-B [2325.8637185,2326.2628010]s vs ENS 1613.4624301s; +[712.4012884,712.8003709]s; nonsevere|
|G100-R2|.005906283055368097|-.000000053266149284908935|.005906336321517382|Both open; original UB-and-gap severity thresholds met|

G100-C1 has no exact M-B whole time or exact speedup. The full time rectangle
gives LOSS/nonsevere, with ratio interval [1.4415357154,1.4417830608]. G100-R2
M-B U=.011434738339920945, L=1.6762209248714507e-7 versus ENS
U=.005528455284552848, L=2.20888241772054e-7. Its approximately twofold UB/gap
loss is mostly the worse own UB; the tiny LB difference does not identify the
representation's causal effect. G100-R2 Fstar=0 has not been proved.

## Physical trajectories, one-bike completion gap and objective scale

physical_UBs.csv contains 1830 independently reconstructed own-fleet UB
observations; physical_fleets.csv contains 42 formal and 5 qualification final
fleets, including G, P, lambdaP, weights, stock, target, return load, served
stations and every vehicle's route/operations/travel/handling time. Every own
UB requires station bounds, integer quantities, single-vehicle/direction
service, every prefix/return load and closed physical-T feasibility. Cumulative
pickup is not vehicle capacity. Cross-arm witnesses are only exact-domain
offline bound counterexamples, never that arm's UB, Start or online oracle.

G50-C1 repeats the earlier complete-fleet completion gap. Both new warm arms
start from the same complete fleet and U=.03252017937219731; startup is
10.5223817s (M-B) and 10.4503611s (ENS). Each actually executes 3 LP calls and
1 terminal MIP. ENS F=0 comes from native_MIPSOL; it is not HGA-only or zero
Optimize. Complete physical Start equality does not assert equality of all
native model columns or acceptance. starts.csv binds actual full vectors,
rows, bounds, types, objectives and native readbacks to each own model.

The final M-B fleet serves all 50 stations and has only station20 below target:
Y20=8, D20=9. Its vehicle1 picks up 4 there; another vehicle (vehicle2) returns
the one remaining bike. On vehicle1, recorded loads after stations20/25/48/47
are 4/9/5/0. Replaying only pickup20 minus one makes the load after47 negative
(-1), so this is not a feasible direct repair or a missed-service station.
The replay creates no accepted fleet, solver call, oracle or new operator.

M-B final G=.0021826280623608025, P=.040000000000000015,
lambdaP=.006000000000000002, F=.008182628062360805. Initial/target stock is
527/527, final527-1=526, return1, maximum route7149.0755397s<=7200. ENS has
G=P=F=0, final527, return0, maximum route7197.1883091s. Weights sum25.071106.
Their own one-bike witness availability is bounded by [0,172.565105900052]s
(M-B) and [0,173.80578709987458]s (ENS); ENS zero availability is bounded by
[0,315.57078709988855]s. These are safe committed-evidence intervals, not exact
native first-discovery or disk-commit timestamps.

For G100-R2 the weights sum is20.892031, initial stock1410 and target1259.
ENS Seed0 gives G=.0021951219512195133, lambdaP=.003333333333333335,
final1261/return149, maximum route17824.6158648s. M-B Seed0 gives
G=.00358695652173913, lambdaP=.007847781818181816,
final1263/return147, maximum route17840.0963466s. M-B Seed1 gives
G=.009801980198019802, lambdaP=.0215814, final1270/return140,
maximum route17564.5773477s. All serve100 and satisfy the physical prefixes.
None has Y=D. Fixed lambda=.15 with max-normalized weights does not make
cross-V penalty balance constant; no cross-instance average unnormalized F or
statistical-significance claim is made.

## Native calls, coverage, numerical evidence and time

Across formal plus functional qualification, 158 actual Optimize calls have
156 returned journal events plus two independently proved normal returns
without that event. Formal arms account for141 calls: 93 LP, 7 child-bound-
target MIP, zero NEXT-target MIP, and 41 terminal/cold MIP. Qualification has17.
The child-target calls occur in arms3,11,20,21,29,30,39. Arm29 has a child-target
MIP but no terminal before its deadline. Arm30's follow-up LP/requeue is not a
NEXT target or committed split. There are158 scope/type bindings,119 saved
models and39 full Starts. G20-C2 ENS/M-B each executes4 Optimize; P executes1;
Seed1 M-B38 also executes4. Raw incorrect Seed flags remain unchanged while
eight current computed scopes (including qualification) bind actual readbacks.

Actual warm tree events include31 lp_complete,14 terminal_mip_complete,
6 native_bound_target_reached and2 child_lp_reuse. AM actions are26 exact-close
and7 native-target. There is **no real parent split in this round**, and maximum
relevant active leaves is1. Lookahead models do not demonstrate multi-leaf
decomposition. R108 L48's two real splits/two simultaneous relevant leaves are
separate historical exposure; its selection remains unchanged.

Every qualified bound uses the current matching model, true-G interval,
cutoff/epoch and complete-cover obligations. Exact current-domain
counterexamples reject all native lower claims of damaged calls and their
necessary dependent closures. P15 rejects4 claims and remains own
U=.26019451545210387/L=0, open; P17 rejects3 and certifies its own exact F=0
against the original global floor. M-B25 rejects damaged call4 bounds while
preserving independent LP/domain evidence and its own F=0 certificate against
F>=0. P26 rejects6 and remains own U=.21697499525901037/L=0, open. The P26
complete model-vector proof does not apply to the different G100-R2 cold
model. All original error flags, numerical claims and failed proofs remain
available. This evidence reconstruction does not repair the native numerical
behavior. Missing returned events are formal P17 and M-B25 call4; matching
call/model, complete log, rc, cleanup and normal process end independently
establish their actual returns.

Exact complete clocks for P15/P17/M-B25/P26 remain null, with outward intervals
[1770.4377317999022,1771.3234165931356],
[643.59993320005,644.5207961242414],
[2325.8637184998947,2326.2628009853656], and
[3574.4382823999035,3574.776744435658] seconds respectively. Later recovery
engineering time is never added to these original windows. Arm42 retains its
exact invalid complete time, native3570.359000000055s and postexit overhead
30.36257349990774s; its legacy native-only within_cap=true remains visible.

V100 time partitions below are actual seconds, rounded for display. MIP
includes callbacks; HGA overlaps startup and is never added twice. Independent
AM/mapper timers are unavailable and stay merged in the residual.

|Arm / role|Startup|LP inclusive|MIP inclusive|Model/map/write residual|Pre/post complete overhead|
|---|---:|---:|---:|---:|---:|
|25 M-B C1|487.377|52.926|1694.439|87.352|null complete clock|
|27 ENS C1|489.040|34.617|990.833|87.228|11.744|
|29 M-B C2|55.742|858.691|2588.702|67.146|.751|
|30 ENS C2|56.176|902.674|2471.310|140.106|.881|
|31 M-B R1|34.294|96.495|3353.411|86.159|4.766|
|32 ENS R1|34.284|96.820|3352.897|86.327|.718|
|34 ENS R2|275.647|152.047|3055.735|86.868|9.414|
|36 M-B R2|277.696|117.809|3087.868|86.924|5.624|
|42 M-B R2 Seed1|277.651|169.752|3035.114|87.842|30.363; invalid cap|

C2 has substantial measured LP cost, R1 is predominantly MIP, and C1/R2 have
substantial startup and MIP costs. There is no single identified universal
bottleneck or isolated A/B causal effect.

The 196 checkpoint records mark actual coverage and censoring separately:
300s has30 observed/12 unobserved,600s30/12,900s22/20,1200s21/7,
1800s13/15,3600s1/13. The sole3600 observation is the invalid arm42 necessary-
audit window; **no qualified arm supplies a3600 performance observation**.
There is no5400 observation. No cap endpoint is extrapolated. Reliable Fstar
witnesses cover G20-C1 (.7582840411970833), G20-R2 (.6846043092307704), and
zero roles G20-C2/G50-C1/G50-C2/G50-R2/G100-C1;23 per-arm availability records
are safe intervals. G100-R1/R2 zero optimum is unproved. Examples of earliest
safe upper availability bounds are G20-R2 M-B8.5619131s/ENS5.9327819s,
G50-R2 M-B140.8519994s/ENS298.4187907s/P1027.1357082s, and
G100-C1 M-B2325.7618010s/ENS1612.9624301s; they are not exact discovery times.

For an actually feasible Fstar=0 role, the original L=0 floor is already
optimal. Only when own U>0, zero is embedded in root/left domains, both child
LPs are feasible and the original AM path is entered does exact mathematics
give zero minimum child gain and no positive-score split. Startup own U=0
closes independently; INF children retain the separate partition logic. This
does not say all zero-optimum instances never split and introduces no new cut.

## Historical results, resources and evidence reconstruction

|Campaign|Formal scope|M-B/P|ENS/P|M-B/ENS|Stage|
|---|---|---|---|---|---|
|R109, historical|24 normal arms,8 of original12 roles;25 entry fault;26-42 unstarted|7 WIN,1 TIE|7 WIN,1 TIE|3 WIN,3 TIE,2 LOSS (G50-C1 severe)|BLOCKED|
|R110|42 fresh normal attempts;41 clock-qualified;12 main roles|11 WIN,1 TIE|11 WIN,1 TIE|5 WIN,3 TIE,4 LOSS (2 severe)|BLOCKED, arm42 full clock|

R109's old6 formal Seed1 arms were unrun. Its original denominator12 and
historical51 starts/18618.079987913487s remain unchanged. R108
SELECT_MB_FOR_BROAD_EVALUATION remains a historical selection, not a claim of
R110 broad-panel support.

Round110 fees are all closed: **80 conservative starts / 68982.261508937
outer charged seconds**, below96/110000. The independent fee summation order
gives68982.26150893699 seconds; the approximately1e-11-second rounding
difference does not alter any gate. Qualification is16 starts /
437.9070925555425s, included and below20/2000. Actual research OS launches are
74:52 native (42 formal+10 qualification) and22 wrappers. Conservative80 pays
58 declared native slots, including6 unstarted charged slots, plus22 wrappers.
Formal conservative64/actual60 and qualification conservative16/actual14 are
distinct. The original prospective plan73 starts remains recorded; seven
additional conservative starts are actual fault recovery. Native LP/MIP times
are nested and never added again to wrapper fees. The nominal panel remains
88200s; unused budget is not authorization for extra experiments.

Engineering compilation, static analysis, offline proof/review and packaging
are separate receipts. Unrecorded manual time is unknown. The one complete
local primary mathematical rebuild took1523.944817099953s and successfully
emitted every table and decision, then its extra metadata write failed with
FileExistsError (exclusive mode on an existing summary). That actual exit1,
stderr and source snapshot are retained. The concrete derived-output write
fix and annotation-only receipt final_report_qualifiers01 succeeded in
.0645346s, without repeating mathematics or performance. Actual offline
mechanism_analysis01 succeeded in.837467s and only replayed existing routes.
No solver, new mechanism, extra Seed/input, best-of-two or performance rerun
was used for final analysis.

The final independent raw/decision audit and exact public carrier are recorded
in review/ and compact_evidence/. Public export, empty-root restoration,
restored-root full-field primary comparison and independent raw review must
actually execute using the compatible CPython3.12.7/GCC UCRT runtime and the
original floating-point expression. Their execution receipts and remote
verification are subsequent publication supplements in public_validation.md;
they are not backdated into this scientific payload. The public evidence is
mathematical reconstruction with zero Optimize, not an engine performance
rerun. No PE, DLL, license or credentials are published. reproduce.md specifies
the ROOT-only commands and explicitly pinned small historical dependencies.

## Two bounded follow-up questions

1. Can the necessary whole-arm audit cost be bounded within the existing
   30-second reserve? Arm42 native end was3571.0120709999464s on the receipt
   clock, but necessary audit exceeded3600. Missing identification is a
   validated worst-case write/physical-audit bound on the actual input domain.
   A bound exceeding the reserve would refute adequacy of this envelope. This
   round does not change the cap or run another arm.
2. Why does the G50-C1 joint representation/search trajectory repeatedly
   stop at the same feasible one-bike gap while ENS completes it? Both current
   initial fleets agree and both execute3LP+terminal MIP; direct pickup-minus-
   one violates a prefix. Missing identification is a controlled separation of
   representation and integer-search effects. Evidence that the gap does not
   persist under such a separation would refute a stable representation cause.
   No target oracle, cross-vehicle operator or new optimization is implemented.

The authorized frozen confirmation is closed with a disclosed resource blocker.
Its performance evidence does not license a broad stability claim, completed
paper benchmark or default algorithm replacement.
