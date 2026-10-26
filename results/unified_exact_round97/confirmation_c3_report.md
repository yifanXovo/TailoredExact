# C3 completed: useful against P, material regression against OFF

All three original C3 arms returned normally and passed their endpoint audits.
The once-generated, design-isolated anisotropic-cloud shortage instance has
50 stations, 4 vehicles Q25 and mathematical T7200s; input SHA256 is
`8f440bf70eb96e51c709d36d6b29a12d5ba2539ac03798ff2512e69b3026991e`.
The original FEEDBACK/OFF/P order, common3600s cap and uniformly frozen r83
candidate were preserved. There were no retries or confirmation-driven changes.

|Arm|Process seconds|U|Legal global L|Absolute gap|Relative gap|Certificate|
|---|---:|---:|---:|---:|---:|---|
|FEEDBACK r83|3597.204|.2407305856097514|.17655043121661848|.06418015439313293|26.6606%|No|
|OFF|3597.234|.225048358657428|.176284229385694|.048764129271734014|21.6683%|No|
|P-GRB|3597.281|.37053773513155164|.17380747762830803|.1967302575032436|53.0932%|No|

FEEDBACK improves U/gap against P by35.0321%/67.3766%, but worsens them against
OFF by6.9684%/31.6135%. Both differences are material under the frozen rules.
Its slightly stronger L does not offset the worse feasible endpoint against
OFF. All arms remain uncertified: this is a common-budget quality comparison,
not an eventual certification ranking, and no reliable F* is established.
The similar full process times are budget exhaustion, not a speed tie between
completed proofs. P is the primary benchmark; the OFF regression remains a
separate, important limitation on adopting the added feedback mechanism.

## Real later-state feedback, with the same native call continuing

FEEDBACK records23 MIPSOL events,15 unique physical inputs,4 excluded Start
matches and19 eligible events, all at positive nodes. Seven strict-improvement
records produce4 distinct candidates and4 submissions. Events8/9 reproduce
the event7 output; event13 reproduces event12's output. Each is blocked by the
per-call duplicate-submission guard. Eight predeadline checkpoint witnesses
are independently verified. There are4 full-vector observations and4
per-submission threshold records with4 recorded(call,value)pairs. These do
not prove unique candidate provenance or count unique incumbent updates.

|Submission event|Nodes|Input true F|Candidate true F|Submission record seconds|Vector observation seconds|
|---|---:|---:|---:|---:|---:|
|7|14|.2710405284548253|.25711705248653965|596.7975043|649.8063225|
|12|281|.25221029639156006|.25085270695118433|1523.5578299|1584.8119024|
|15|518|.25051658349664024|.2504759429833703|2140.2935898|2140.9989125|
|19|528|.2503351122451452|.25031732566034937|2633.4955400|2687.0455026|

All four complete vectors pass105400 actual model rows, with zero recorded
maximum row residual, plus independent physical/vector audits. Submission
API return codes are0 and returned objective fields are null; later vector
observations provide separate handling evidence. There is no R96 ordering
activity and no archive handoff. Actual-model audits pass19 retained vectors
for FEEDBACK and31 for OFF.

Every submission occurs in native call2. After event19 and its later vector
observation at node529, the same call reaches node540 at3529.4793386s and
records a new native physical F=.2407305856097514. It needs no strict closure
improvement and becomes the final physical endpoint. Subsequent events22/23
retain that same physical state. The best direct closure output is only
.25031732566034937; the later native endpoint is not relabeled as a closure
output or assigned unique causal ancestry. Native event times above are not
interchangeable with independently committed journal availability times.

OFF and FEEDBACK have the same input hashes through the first submitted
source event7, including four excluded Start matches and the node14 source
F=.2710405284548253. This supports a shared early opportunity. It does not
make all subsequent, feedback-altered events common-input comparisons.

## Original target boundary, cost and trajectory interpretation

Each ENS arm has5 verified complete Optimize calls:3 LP and2 MIP. The first
MIP returns native status11 at the pre-existing child-disjunction bound
target, with unchanged seed U and before any feedback submission. Its target
ledger explicitly records `target_reached_requeue` and
`c6_child_bound_reached_parent_requeued_no_forced_split`. This is the original
mathematical target boundary, not a new feedback-triggered interruption.
The second MIP continues until normal overall time-limit return. P has1 MIP
Optimize. No new solve is introduced to inject a candidate.

Complete new callback costs are.9948101s FEEDBACK and1.0791012s OFF. The former
already includes nested closure.1574584s and mapping/validation.0856360s;
these are not added again. OFF sees36 MIPSOL records and31 unique states, so
the callback difference is not a controlled estimate of incremental closure
cost. Neither small closure cost nor altered node counts identify the internal
branch/cut cause of the endpoint regression.

Committed-witness trajectories show FEEDBACK ahead of OFF at900s
(.25397442 versus.25662445) and1200s (.25397442 versus.25507015), but behind
at1800s (.25085271 versus.24615787),2400s (.25047594 versus.23402818) and
3000s (.25031733 versus.23287686). Its late native improvement still leaves a
worse endpoint. This prevents an early lead from being substituted for the
long-window result. At600s the trajectory contains the native witness
.27103684, not the then-unobserved submitted candidate. Closure checkpoints,
native handling and journal availability are kept separate. No gap integral,
first-optimal-witness time or proof-completion speed claim is made.

## Executed evidence and accounting

Actual zero-Optimize analysis1.2029673s produced
`analysis_views/confirmation01_C3_v4_analysis`; trajectory replay.8666678s
produced `trajectories/confirmation01_c3`; export1.3409957s wrote
`confirmation01/evidence_C3.json`, endpoint witnesses and three byte-verified
journal/observation archives with119/145/739 members. Their original bytes
remain retained; large matrices, vectors and binaries stay local with hashes.
All nine confirmation arms now form the completed prefix. The C3 cross-arm
contradiction check passed, without constructing a combined certificate.

Actual vector wrapper costs are5.4646590s FEEDBACK and8.4906610s OFF, with
zero Optimize calls. C3 consumes10791.719 outer solver seconds,3 starts and
11 complete Optimize calls. Snapshot `costs/confirmation_c3_complete` records
36 solver starts and73371.419 solver seconds,150 verified complete Optimize
calls plus11 observed failed-run scopes whose complete counts remain unknown.
With8 micro and8 diagnostic starts, the experimental count is52. Its87
receipted engineering commands and373.0878889 non-solver seconds are separate;
the snapshot excludes its own1.1188571s wrapper until the next ledger.

C3 completes the original third confirmation role and second required
long-window group, the design-isolated confirmation group. It establishes real later-state feedback at hundreds of
nodes and after2600s, with continued proof search, but rejects a claim of
uniform incremental benefit over ENS-C. Together with C1's similar complete
certification times and C2's quality gain, the confirmation outcome is mixed.
Stable eventual superiority to P remains unproved. Full-stage synthesis,
compact final evidence index, reproduction and independent whole-stage audit
are recorded separately in final_report.md, final_summary, reproduce.md and
root_final_review.md. Defaults remain protected; no promotion or merge.

Independent read-only review checked the report against endpoints, original
events/target ledger, vector receipts, trajectories and cost snapshot. It
confirmed the material OFF regression, P quality gain, four positive-node
submission/observation chains and original pre-feedback target return. The
review clarified that F5 and C3 are the two required long groups, only C3
being the design-isolated confirmation group. No Optimize or file mutation
was performed by the reviewer. The whole-stage audit is separately recorded
in root_final_review.md.
