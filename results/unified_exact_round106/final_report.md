# Round106: structural route conflicts at integer candidate events

**Decision: RETAIN_COMPONENT_ONLY.** Dynamic MST certificate A, balanced-three-stop
exact/threshold certificate B, and the qualified single-MIPSOL event contracts
are retained as default-off components. The complete assignment-master
candidate is not admitted. All eight preregistered development arms completed
with passed physical/native audits; the candidate certifies neither role,
loses the important F2 ENS certification role and remains far behind P/ENS
in C2 own feasible-route quality. All three unstarted confirmation groups
are cancelled; their sealed inputs are preserved as untested scope.

The sole next research question is whether uniformly valid strengthening of
this retained assignment master can reduce unrealizable inventory/ownership
candidates enough to reach P's feasible-route frontier while protecting ENS's
certification role. No new configuration or parameter search was started.
The permitted substantive research revision was not used: observed separator
cost is small, and another mode-rejection tuning cycle lacks a demonstrated
route-conversion benefit. This decision concerns frozen events-v1 on these
two inputs/caps; it does not reject all tailored exact algorithms or all
decomposition interfaces.

## Actual change and preserved problem

This is stacked on R105 PR167 delivery
8dc274eb34ee6d8a575f0b94b57ef04476efc0f1. Historical R105 production source
91ff7da1b319577bf2fe703417bdd7d994a790a3 and PE
8b17e33c612d9768edec0047df5ca9efdc088ee8fc5a67acfbf0dd1b5f5e19c9 remain
historical identities. Round106 production source is
8a2af86155fa2ef206d8d5156a9efc14d0acb102; measured campaign commit
94860fd3515a5b18f408e3c64449dec2e52fa5a8 adds source-admission binding.
All eight contemporary controls/candidates use PE
1ad7b9128288ff06eed64ac91154c1863963827c5399083b1b233a24ee2d09b4 and
Gurobi13.0.2 DLL
9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88.
Later delivery commits change readers/evidence/docs, not measured production.

The original inventory objective, zero-denominator Gini branch, empty
departure, legal loaded return, load prefixes, unique station service and
full travel+h*pickup duration remain. Inventory conservation remains
sumY=sumb-sum(return_load); cumulative pickup may exceed vehicle capacity.
EVENT retains the R105 global VD-P/F0 compact columns, objective and rows;
only arc/load integer types are relaxed. Its self-paid unchanged ENS
startup supplies a verified U0 and non-strict F<=U0 domain. Every relevant
original solution and legal Start embeds. Y/state/ownership/direction/pickup/
delivery retain their integer declarations. No AM or new root-processing
family is added to EVENT. Original P cold compact and ENS startup/AM paths
are unchanged, and the prototype defaults off.

One production master Optimize invokes MIPSOL lazy separation, with a
distinct serial inner environment/model. No manual master restart or
recursive Optimize of the active model occurs. STRUCT scans every car for
A/B before new full route calls; any proved reliable rejection is enough.
Unviolated cross-car rows stay pooled. FULL/CORE disable A/B and use their
own isolated run evidence; STRUCT's native fallback is FULL. CORE performs
IIS and released-template confirmation only after proved full INF. One
monotonic deadline begins before startup and covers all callbacks, oracle/
IIS, audit, mapping, logging and cancellation. Threads1, Seed0, PresolveAuto,
original tolerances and zero gap are pinned; reserve30 is inside every cap.
There is no instance/size/stagnation or independent per-car/per-node budget.

Actual master retention and oracle assumptions are recorded in
[mathematical_algorithm.md](mathematical_algorithm.md),
[master_retention_table.md](master_retention_table.md), and
[oracle_assumption_map.md](oracle_assumption_map.md). Raw original.lp,
variables.csv, embedding.json, start.mst and all candidate vectors are
packaged. Fresh P reference counts/fingerprints/SHAs match the original
canonical models: F2 1591 columns/3689 rows/fingerprint788240696;
C2 4242 columns/10627 rows/fingerprint-2089989534.

## Completed development comparison

Times below are fully observed launch-to-drain seconds, including reserve
policy. Exact fields are reconstructed from raw completion/audit/result and
physical routes in [reports02/arm_results.csv](reports02/arm_results.csv).
Relative gap is (ownUB-qualifiedLB)/abs(ownUB); it is not a projected time.

| Role | Arm | Cap | Observed seconds | Own UB | Qualified LB | Gap % | Certificate |
|---|---|---:|---:|---:|---:|---:|---|
| F2 | P-GRB |1200|1170.796|.8659435203|.7622100781|11.979|No |
| F2 | ENS-C |1200|577.344|.8659435203|.8659435203|0|Yes |
| F2 | EVENT-STRUCT |1200|1170.344|.8699780578|.7680964300|11.711|No |
| C2 | ENS-C |1800|1770.375|.2167930653|.1896916167|12.501|No |
| C2 | EVENT-FULL |1800|1770.765|.3912235843|.1896260335|51.530|No |
| C2 | EVENT-CORE |1800|1770.500|.3916208967|.1891268592|51.707|No |
| C2 | P-GRB |1800|1770.344|.1983028486|.1866225684|5.890|No |
| C2 | EVENT-STRUCT |1800|1770.702|.3750564073|.1891247571|49.574|No |

F2 ENS process time is577.094s and safely observed time577.344s; historical
R105's569.235s is motivation only, not this same-PE comparison. STRUCT
has a slightly stronger qualified LB than P but a worse own UB and no
certificate. This does not compensate for losing ENS's certification.

All five C2 arms are censored. Their final own UB can be compared at the
registered caps, but [paired_results.csv](reports02/paired_results.csv)
does not rank eventual certificate times or extrapolate gaps. P finds the
best own feasible objective. STRUCT improves its own startup UB and its
own UB is better than FULL/CORE, but remains materially worse than P/ENS.
These controls identify conflict-strategy net behavior under the shared
event interface; they do not isolate every historical AM/handoff effect.

## Actual candidate learning, physical UB and cost

| Role/strategy | MIPSOL events | Distinct fleets / Y | Car modes: vehicle / physical | Repeat events | Actual A / B / fallback lazy | Full oracle / IIS / core confirmation | New physical UBs |
|---|---:|---:|---:|---:|---:|---:|---:|
| F2 STRUCT |104|103 / 101|134 / 126|1|0 / 32 / 85|89 / 0 / 0|1 |
| C2 FULL |2509|2509 / 2497|4432 / 4432|0|0 / 0 / 2506|2640 / 0 / 0|1 |
| C2 CORE |150|148 / 143|365 / 365|2|0 / 0 / 147|150 / 147 / 145|0 |
| C2 STRUCT |2357|2352 / 2337|4755 / 4755|5|71 / 0 / 2276|2500 / 0 / 0|4 |

The source summary/CSV distinct_car_modes retains the production key's car
label. The separately recomputed physical key omits it only when full
input/operation/Q/T/handling parameters coincide. The initial mode-index
terminology error is preserved in mode_correction.json; authoritative
[real_modes_report02.json](real_modes_report02.json) corrects F2 to126
physical modes. These are repeated observations on two formal inputs,
not thousands of independent instances. The index selects eight distinct
noninitial informative modes: F2 B events2/5/8; C2 A events5/90; F2 FULL
fallback event4; C2 CORE event2; and accepted C2 FEAS event1555. All full
source candidates, Y, assignment, operations, proof/witness SHAs and next
native events are retained. Historical nine INF modes have three complete
candidate sources; they are not nine independent inputs.

F2's naturally generated event2 car1 has support {13:+5,16:-15,17:+10},
P=D=15, Q30, L=1785.584s. Four orders fail a load prefix and two legal-prefix
orders exceed3600s. L+120*16=3705.584>3600. Actual exact and threshold lazy
activities are6 with RHS5; Start activity3, API0, followed by native event3.
The global mathematical threshold certificate has79 terms; the actual
native row has37 nonzeros after absent root-domain states are fixed zero.
The exact native row has6 nonzeros. This source differs from the
historical6/7/9 anchor, demonstrating actual dynamic extraction. The
threshold row LP-dominates its corresponding exact positive row, while
density and runtime costs remain separate questions.

C2 STRUCT event5 car2 extracts six pickup stations {3,5,13,22,23,30} with
(12,6,7,8,6,8), total47. Its true conservative MST is1742.919s, producing
a7382.919s duration lower bound against7200. The12-coefficient row is
reliably violated by182.919, keeps the paid Start, is submitted with API0
at15.05238s, and native event6 follows. Seventy-one source A proofs generate
213 compatible pooled rows; only71 A rows are actually submitted. A is
NOT_EXPOSED naturally on F2 and B is NOT_EXPOSED naturally on C2. Integer
coverage enlargement alone does not establish A's LP dominance or speed.

All four event arms use exactly one master Optimize. F2 has one improved
physical UB but its canonical submission is not observed accepted. C2
STRUCT verifies four improved complete fleets. Only event1555's submitted
witness is observed later at native event1559 and matches the final native
vector; the other three API0/
deferred submissions remain separate from their valid physical UBs.
Event1555 has modelObj=.3761856153904>Ftrue=.3750564072918, natural evidence
that a nonoptimal epigraph must be allowed. Independent physical reading
checks every final/startup route and inventory objective.

C2 FULL ends on an unresolved candidate. Its native log temporarily reports
objective .2227302947886, which is not promoted to an original-problem UB.
Published own UB stays .3912235843422; final_native_bound_qualified=false,
and only the previously qualified LB is retained. CORE and STRUCT finish
after valid lazy rejection. Actual CORE inner IIS cancellation and outer
termination are recorded, preserving the proved full conflict; no UNKNOWN
or provisional native solution is converted to INF or certification.

| Role/strategy | Master inclusive | Master exclusive | Callback | Full oracle | IIS | Core confirmation | Separation | Audit/mapping | Callback other |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F2 STRUCT |1166.764|1163.484|3.280|.529|0|0|.047|.202|2.501 |
| C2 FULL |1762.120|1575.306|186.814|47.245|0|0|0|13.349|126.221 |
| C2 CORE |1761.917|278.129|1483.788|2.888|1455.208|8.580|0|.728|16.385 |
| C2 STRUCT |1761.983|1589.160|172.823|38.270|0|0|.346|12.865|121.342 |

Master inclusive already contains callback; exclusive plus its disjoint
callback parts sums to inclusive. Startup/model/remaining process costs
remain in full observed and paid outer times. Nested times are never added
again to fees. STRUCT avoids CORE's expensive IIS path and obtains more
native events, but the table supports no competitive original certification
or route-quality conversion claim.

## Mathematical/native qualification and independent evidence

A uses actual Prim MST on a conservative symmetric millisecond metric
closure derived from actual arcs. It selects current nonzero pickups and
deterministically deletes only while reliable impossibility survives.
B uses deterministic balanced triples from any actual service set, checks
all six closed orders, and requires strict L+h(P0+1)>T with numerical
margin. Exact positive and threshold lifting preserve ownership/state
semantics; unbalanced operations, zero handling, equality and incomplete
order proofs fail the gate. All absence deletions and cross-car A transfer
have explicit proofs in the mathematical document.

Independent C2 anchor MST2387.254251416504s becomes conservative2387.252;
P43 handling5160 plus travel exceeds7200 by347.252. Independent F2 anchor
has four invalid-prefix orders and two durations3629.3192304/3795.7147314;
min unconstrained travel1661.135564 (produced1661.133) forbids a seventeenth
pickup. Ordinary MST978.553 is insufficient for B. The Euclidean balanced
helper example at Q3/h2/T20 remains feasible with helper pickup1 and loaded
return1 exactly at20, so the strict budget gate correctly does not trigger.

Qualified tests retain unique-supplier/integer-ownership counterexamples,
auxiliary capacity repair, cumulative pickup>Q, loaded return, alternative
feasible order, zero-denominator objective and all service mappings.
Scripted API contracts on real audited vectors cover repeated INF lazy
resubmission, repeated FEAS cache, unviolated rows, one-car INF/other UNKNOWN,
unrejected UNKNOWN and high epigraph; their scripted layer is explicit.
Separate actual native fixtures/replays expose lazy continuation, deferred
physical-UB submission, one master and actual inner/outer global deadline.
C2 CORE cap12 qualification cancels inner IIS at12.0001934s and outer at
12.0138728s, retaining one proved FULL lazy, own UB .39162089675 and LB0.
Preexpired zero-call qualification is recorded separately.

Before performance the third-view gate independently checked201 source/test
bindings,437 evidence SHAs, actual PEs/DLL/header and native numerical/threads/
gap contracts, and recomputed Decimal/MST/six-order/physical results without
calling production A/B. Historical retained-model replay, scripted contracts,
native fixtures and complete performance are distinguished. Final delivery
review additionally reads the new formal candidate/proof/lazy/continuation
chains, complete feasible route, repeated/deadline outcomes, all arm/fee/
native totals and fresh restored reader. Independent mathematics/physical
checks do not constitute an independent-engine performance reproduction.

## Fixed-Y diagnosis, history and cancelled confirmation

Four R105 optimal-master C2 events have the same exact30-station Y and
F=.19293317528184106, with distinct assignments. The frozen cap1200/reserve30
full-fleet feasibility model fixes this Y, releases assignment/service/order,
retains T7200/Q20,25,30 and all physical semantics, removes Gini/cutoff, and
has objective zero. Its Tstar<=T formulation is equivalent to that fixed-Y
original feasibility question.

Result: **UNKNOWN**, native11, no incumbent and no INF, one Optimize/no IIS.
Native1168.7722448s, algorithm1170.0320245s, outer1170.0963021s. It was not
retried or transferred to formal arms. This exact Y remains unresolved; no
Y-only exclusion or switch to a Y-master follows.

R105 F2 FULL/CORE ran about1170s with zero oracle/IIS/cuts and therefore did
not test core-learning payoff. R105 C2 CORE had four same-Y/different-owner
optimal-master events, master1707.612s (96.44%), full oracle about.014s and
no improved own UB. R104/R105 STOP remains limited to those tested families.
Historical R51/R52 duration, R54 inventory-route, R60/R61 fleet and R62
threshold ideas are acknowledged; dynamic extraction and event integration
are the present increment, not a claim of new subset-duration theory.

Pre-development confirmation recipe and seed froze F5, generated N36
(clustered shortage, Q24/30/36) and S12 (bent-corridor surplus, Q8/12).
P/ENS/STRUCT9 arms would use35100 nominal seconds. All inputs are retained
unchanged. Complete development fails the frozen admission rule: no candidate
original certificate or credible compensation for the F2 ENS/C2 P advantages.
All groups are unstarted/cancelled; no confirmation result, generalization
claim or feedback-based redraw is reported. See admission_decision.json.

## Accounting, inherited repair and recovery

All research receipts are closed. Conservative charged starts30/72,
paid outer13089.59282640001/80000 seconds; remaining42 starts and
66910.40717359999 seconds unused. Raw ledgers have5778 starts and5778
returns; adding the separately audited12 P/ENS calls yields5634 Optimize
and156 IIS, missing-after0. Native nested durations are not added to outer
fees. [reports02/fees.csv](reports02/fees.csv) and native_calls.csv reproduce
all entries, not just successful arms.

The failed development_batch01 guard charged9 starts/.9406832s but launched
zero native children; the inherited OT expression matched its management
Python's round88-ot path. Moving management to D:/msys64 stdlib Python fixed
the environment guard without PE/source/contract change. batch02 charged9
starts/11783.2904182s and completed all8 children. Builds, readers, selected
indexes and restore attempts are separate zero-solver engineering receipts;
failed builds/readers/path-length/collision attempts remain retained.

The first full reader mistakenly included two R105 master ledgers inside a
failed inherited restore copy, giving5636 Optimize. reader_correction.json
withdraws reports/ and replaces it with reports02/ (5634); raw production
evidence and fees did not change. Independent review also corrected only
the F2 mode-index terminology126/134. Both original outputs and failed
engineering identities remain available.

R105's compact omitted66 original native01/02/03 calls.csv files. Their
exact recovered bytes/SHAs restore76 Optimize and17 IIS; no fake per-call
records were synthesized. The old raw layer reconstructs148 Optimize/
37 IIS with one missing-after;12 P/ENS and3 independent-review Optimize
have explicit original frozen audit-summary layers, yielding published
163/37. Old55 starts/12081.441783100076s and reports02 are unchanged.
F5 diagnostic04 is corrected only in this supplement: native550.0507931s,
algorithm571.422s, paid outer572.174668s.

The compact packet includes complete current raw calls/results/candidates/
conflict coefficients/physical routes, models, all failures/fees, frozen
source/inputs/protocols and the66 historical raw ledgers. The exact inherited
R105 archive is an explicit base-branch dependency. Binaries/DLL/license/
credentials are excluded. Delivery prose and later actual recovery/review/
remote receipts are ordinary public files outside the archive to avoid
circular hashes. Actual archive and exclusive fresh recovery/field-comparison results follow.


Final independent delivery review is **ACCEPT**, with no pending blocker:
[delivery_review.md](review/delivery_review.md) and its JSON approve the
component-retention conclusion, not whole-candidate performance adoption.
The reviewer verifies all5120 snapshots/5117 lazy/103 structural certificate
files and actual natural chains. Its final restored execution reads10695
source files wholly within E:/r106-fresh-03, without original-worktree
fallback, and matches every semantic result/source SHA against frozen08.
[The actual independent output](restoration/independent_portable_fresh03.json)
SHA is d488dac1d65d28729ec7832b63b9364261875dff5d05088a86acef1b308d00fb.
Engineering independent_fresh02 returns0 in41.0337045s, zero Optimize/IIS.

The archive contains45827 current files,1,518,790,341 uncompressed bytes;
its283,820,721 compressed bytes have SHA
c196bb62c84d7775c239fe466b436466b327988a031c2c6f75814fca5609ec3c.
Public delivery uses six sequential byte parts (five48MiB, one32,162,481
bytes) with exact SHA/length in compact_evidence/parts_manifest.json; original
manifest SHA8391081b0db0188e108fe4d84a190e518fca541f1b3ed9bcff3c3cf444bcb87e,
parts manifest SHA7e8dc4a84052202c3cf423ecf3ce0e6a9c3d8ca455bfb5c6a724a97b195c92a9.
All130 selected calls.csv include66 historical supplements and64 current
native ledgers. The whole oversized local archive is not committed.

Actual final recovery **E:/r106-fresh-03** uses only public parts, exact public
inherited-manifest bytes and the public base archive, restoring45827 current/
1556 inherited files plus66 recovered original ledgers. The explicit old
manifest supplement solves LF/Windows CRLF Git-carrier differences without
rewriting R105. The base archive's public Git blob matches SHAfd546a170...
and the supplemental old manifest blob matches exact f197505615...;
parsed JSON matches the base LF blob. New -text attributes cover only R106
paths. The reviewer and root each actually read13 Git index blobs for
carrier/dependency/scripts and checked every byte/length/SHA.

[The stdlib reader execution](restoration/reader_portable_public03.json)
passes all arm/pair/fee/native/current-event/current-conflict/mode CSV fields
and old/new summaries. Reader SHA
4c929ba80337661baef2e0dbd99ee2301e81d4e15ba9904c5b0365cc60dd1a31,
Optimize/IIS/native subprocess0. Actual restore command source SHA
ced99b3bbd7bdcec429fa997f8c81921583cf6b22c4351483cf89eaffd42938c.
Recovery/compare commands and payload-versus-late-public-carrier source
boundaries are in reproduce.md. Earlier whole restore01 and parts restore02
successes, split01 overwrite-protection failure and split02 correction all
remain recorded; final03 is the portable public-only admission.

Original user workspace stays on R105 HEAD and its same three tracked
modification paths. Pre-publication and final-publication SHA checkpoints
are recorded separately; an exact initial byte-SHA baseline was not saved,
so those later checks do not claim an unavailable initial byte comparison.
All task edits occur in the attached R106 worktree. Original PR167 and main
are not modified. Draft-PR publication and remote verification follow.
