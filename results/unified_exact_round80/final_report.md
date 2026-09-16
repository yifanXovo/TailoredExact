# Round80: E8 regression repair and D6 long-window proof gains

The unchanged BDS-C method repairs E8's current small total-time regression and
materially improves the genuine D6 K1/P proof deficit at a fresh common3600s
cap. D6 absolute gap falls73.6448% against P-GRB and80.5825% against K1-R;
the gain comes from a stronger global lower bound despite a slightly worse
upper bound. All six original runs return normally and pass independent audits.
This is successful exposed-data validation, not overall goal completion.

Base R79 final c29173a6cb34c299cd818310eee59844ed36d8f6 / draft PR140.
Branch codex/round80-bdsc-primary-deficits. No C++, algorithm parameter, default
or main change. Reuse qualified R78 source4a0561e0f8193e3e874c1bd0bfa8bc381fb66f5e,
binary build/round78/v1/ExactEBRP.exe, SHA256
3fae847a75c3c9d07d8f5f0444daeafb73559865e6bffb816746802b9e2f43ab.
The single uniform preset remains research-round78-vds-balanced-descent.
R78 mathematics.md/final_report.md define the inherited exact method and scope.
publication.json will record the independent draft PR after evidence closure.

## Fresh common-budget results

E8 is the unchanged V12/M3/Q30/T3600 small-easy case, input SHA256
587737b9d000c1712220232a0fe957073f1f03ac649a63a4775abd9166603acd.
All three arms certify the same nonzero original optimum .021337006039780566
within their common120s cap. Paid times: P-GRB1.781s, BDS-C2.516s, K1-R7.359s.
BDS-C is .735s slower than P, below the frozen2s/20% material rule; it is
practically close, not faster and not statistically equivalent. K1's5.578s P
regression exceeds the frozen5s/50% severe rule. BDS-C gains4.843s against K1
and removes that material P regression. Tiny signed E8 gaps around1e-18 remain
in the raw table; these are original-tolerance numerical certificates, not
strict rational proofs.

D6 is original CitiBike V30 compact-r1 shortage, M3/Q30, mathematical T18000,
handling60/60, lambda.15, input SHA256
070c2c1413840a09a264d238bdfa320ef76d293a45cab919095851afdea8c01d.
All three remain uncertified at their common3600s cap:

|Arm|Paid wall s|Physical U|Global L|Absolute gap|Relative gap|
|---|---:|---:|---:|---:|---:|
|P-GRB|3597.172|.157241175852|.150782310390|.006458865462|.041076171|
|BDS-C|3597.125|.157509803615|.155807553801|.001702249813|.010807263|
|K1-R|3597.141|.157083131103|.148316568882|.008766562222|.055808426|

Relative gap is(U-L)/abs(U). BDS-C's U is worse than P by.000268628 while L
is better by.005025243, reducing gap by.004756616. Against K1, U is worse by
.000426673 and L better by.007490985. These are clear proof-gap gains, not
claims of primal dominance or optimality. Both pass the frozen>.001/>10%
material criterion. K1's gap is35.7291% worse than P, a material but not severe
regression under the frozen absolute/relative rule. D6 is therefore a current
P proof-deficit role, not an invented K1 protection role. Its better K1 upper
bound is retained explicitly rather than hidden by the gap comparison.

|Observed checkpoint s|P gap|BDS-C gap|K1-R gap|
|---|---:|---:|---:|
|300|.014008044|.011614535|No recorded physical U|
|600|.012255293|.007783892|.013742165|
|1200|.010462680|.005027935|.011304543|
|1800|.008478474|.003821158|.010241477|
|2400|.007531548|.003092202|.009446740|
|3600|.006458865|.001702250|.008766562|

BDS-C materially improves P at every declared D6 checkpoint. The27 total E8/D6
checkpoint rows use availability=max(payload closure, completed observer read),
with normal final outputs used only after completion. K1's D6 starter first
becomes available at319.891s, so it is not backdated into300s. Checkpoints from
one long run are not independent replicates. All arms use Gurobi13.0.2,
Threads1/Seed0/PresolveAuto, zero requested gaps and unchanged tolerances,
serial logical2/mask4 execution with restored affinity. P remains the original
compact model/native defaults, no added Start/cut/imported bound. Input/model
fingerprints match retained R66 E8 and R71 D6 original references. No historical
route, bound or optimum enters a formal algorithm.

## Actual mechanism and attribution

Both BDS-C runs complete all25 current-run startup paths. D6 matches all25
qualified R78 paths, then accepts two balanced relocations and four quantity
moves: startup F .160027280604 to.157849712515. Original physical replay,
independent balanced-move enumeration and the actual outer handoff all pass;
D6 hands the final improved route to the outer algorithm. Its startup serves
all30 stations with122 pickup/drop units and max duration10831.913s.

E8 illustrates the inherited handoff threshold honestly. Two neutral moves
reduce the module's maximum route duration3189.308 to1626.504s at exactly the
same inventory/F .022295597484. No strict move follows. The outer incumbent
rule retains the initial route because F did not improve; actual native Starts
use that retained initial witness. Thus E8's end-to-end repair cannot be
attributed to a changed native route from those two neutral relocations.
The isolated replay label 'fixed-witness diagnosis' describes the offline
oracle, while each formal run constructed its own witness from its own input.

E8 K1 enters its exact phase at4.910315s, BDS-C at.017645s; most of its paid
time improvement is startup. The old R39 large non-startup-loss label was
already reclassified in R66 and is not retroactively counted as repaired.
D6 exact-phase entry is5.768566s for BDS-C versus319.823854s for K1. All costs
remain paid. The stronger D6 proof against P, which has no HGA, cannot be
explained solely by removing K1 startup. K1 also starts with a better D6 U
(.157083131 versus.157849713), yet has the weaker final proof. These are
complete-method observations, not a matched ablation isolating neutral moves,
Start acceptance, formulation or decomposition as the unique cause.

D6 BDS-C uses five LP calls and one MIP; P uses one MIP, K1 five LP calls and
two MIP invocations. BDS-C's actual MIP has30485 rows/8273 columns and records
34692 nodes,20469900 simplex iterations and3586.69 native seconds. P records
72758 nodes/17926777 iterations; K1's final call72198 nodes/11319135 iterations.
BDS-C uses more simplex work than P despite the better final bound: neither
model size, node count nor Work is substituted for the primary endpoint.
E8 BDS-C has three LP and two MIP calls. Its first MIP stops after attaining
the valid child-disjunction bound target; terminal proof follows. That is a
mathematical target stop, not a private time/Work slice. Every call is charged.

Three actual BDS-C Starts are eligible and accepted. Independent complete-vector,
actual-row and readback checks pass; maximum row violation1.11e-16, readback
difference0. Four control arms have no explicit Start path. D6 K1 has no native
MIPSOL witness; its original-verified same-run HGA witness remains a valid U.
Acceptance alone is not proof of a causal speed effect. No new mathematical
novelty is claimed by this validation stage; inherited finite descent and exact
coverage remain distinct from performance evidence.

## Evidence, cost and stage decision

All25 Optimize calls return: P2, BDS-C11, K1-R12. Independent audits validate
90 physical journal witnesses(86 native,4 startup),9567 global-bound events and
all9713 committed events. No unseen receipt or uncommitted payload is promoted.
All normal endpoint, numerical, original physical and complete-coverage gates
pass. The original P models remain935/2089 columns/rows on E8 and4198/10561 on D6.

Full paid process wall totals10803.094s within the11160s declared maximum, plus
.192120s separate per-run replay. Preflight.325078s includes.157s for two
zero-Optimize reference exports. Joint analysis1.769534s, actual mechanism
checking.770794s, packaging/verification7.872809s, separate documented byte
verification.800255s. No new build/test/qualification, solver or supervisor
failure, rerun, extra seed, long extension or confirmation occurs. Two progress
pushes succeed; final publication transport is recorded separately. No reset
credit is consumed. Interactive work is not a complete machine-time census.

Seven lossless bundles retain19648 files,59705185 raw bytes and9790348
compressed bytes. The compact bundle_manifest.json binds a compressed ordinary
JSON per-member manifest, including every source/path/length/SHA256. Both its
index agreement and every archived byte verify. Raw logs, models, receipts,
routes and actual vectors remain retained. See reproduce.md; executables remain
local with hashes and full cross-OS replay is untested.

The inherited default-off architecture remains admissible, evidence is valid,
and this bounded stage passes both primary questions. No instance-specific
parameter or selection rule is introduced. Combined with R79, the candidate
repairs the exposed small total-time regressions and important nonzero proof
roles; R78 supports D7 protection only at1200s. D6/E8 are development data,
not independent confirmation, and no statistical equivalence is asserted.

Overall goal remains unmet. After publishing this independent draft PR,
separately admit consequential common3600 D7 protection, justified limited
replication and diverse unadapted confirmation. confirmation_scope_pending.md
records provenance cautions, not additional experiment authorization. Retain
this one uniform candidate for that validation. Do not merge main or declare
universal superiority from this successful two-role stage.
