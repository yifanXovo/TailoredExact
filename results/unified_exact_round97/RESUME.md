# Round 97 — active, incomplete

ENS-C protected default; no promotion/merge. Branch codex/round97-native-incumbent-closure; parent R96 93a29e7290e7e92821482c7f4e2c47dfe2f1e84e. Draft PR159 targets codex/round96-external-primal. Preserve the three unrelated tracked user modifications in gf_compact_bc_round / gf_compact_bc_timeprofile_round; never broad git add.

## Authoritative current checkpoint

D7 recovery queue/session22877/Python18344 EXIT0; finalsolver15548 terminal. All registeredD7arms5–7 executedonce;5interrupted,6/7normal. Verifiedidle at checkpoint. OFF3597.453s U.22515085005563812/L.20473460962487544/gap.020416240430762678. FEEDBACK3597.312s U.2156425624821821/L.2037872992847437/gap.011855263197438404. Bothnormaluncertified; each4Optimize(3LP1MIP). Vectors52/19passed, wrappers14.3619629/5.6093454s. CombinedU4.2231%/gap41.9322%betterOFF but LBworse; Pcomparison interruptedonly. Currentcompleteprefix18solverstarts42510.559s,90verifiedOptimize plus6observedinterruptedscope; sourcecountsunknownforfailedruns. NEXT preserve/push newD7reporting, then originalV1block7→10 using newcontinuation. No candidatechoiceyet.

Original D7 queue/session78483/Python42684 exited1; P solver40208 terminal. Arm5 P-GRB was whole_run_hard_stop at3598.031s, auditpassed interrupted evidence U.2372849915487284/L.19858649317712468/gap.03869849837160372,1observed call0returned, no result, no certificate. Original queue stopped on normal-only assertion and did not start6/7. Everything preserved; hard_stop05_acknowledgement.json binds exact receipts/observations/LP/log/oldqueue. New continuation allows only this exact interruption, allothersnormal/audited; new failures stop. Independent static/semantic review and actual prefix/vector-receipt checks passed,0Optimize. No rerun/cap/source/algorithm change. Report development02_d7_interruption.md.

Pushed HEAD97195ff13c367aa37154e8254ef6a93d4579366b adds interrupted evidence and new guarded runner; F5 evidence commitfa5320014 remains. PR159 OPEN/DRAFT/baseR96. F5 queue/session19598 terminal; neverrestart. Future V1/F2 MUST use round97_continue_development02.py (7 to10 then10 to13), not old normal-only queue.

Interrupted-support reporting ACTUALLY PASSED: scripts/round97_interrupted_evidence.py, round97_analyze_batch_v3.py, round97_analyze_role_v3.py, round97_trajectories_v2.py. Syntax/realarm5identityacceptance/mutatedrole+receipt rejection/unknowncertificate checks passed (.7213269s0Optimize). D7roleanalysis1.263601s/trajectories4.1940111s/export.2644263s allpassed0Optimize. Outputs analysis_views/development02_D7_v3_analysis, trajectories/development02_d7, endpoint_witnesses/D7_*.json, evidence_d7.json. Pcertificate/completeOptimize/comparisonseveritynull, endpointsourceinterrupted; noresult fabricated. HistoricalF5/H1outputsunchanged. Fullreport development02_d7_report.md.

Important semantics correction (no productionchange): native_incumbent_change is PER SUBMISSION threshold satisfaction, not unique actualnativeupdates or equalcandidateobjective. D7five records reference2distinct(call,value)pairs, not5updates orcomplete2updates. Derived incumbent_observation_semantics.json binds everycompletedeventstream+actualC++; math/F5/D7reports clarify. Independentreviewconfirmed. D7bestsourceevent7 is node0 nonStartmatching, inputF.24561226→oldclosure.21695912→joint.21564256; firstverified586.418507, solutionwritten586.898389, vectormatch707.452203. Fourpositivenodeevents16–19 no newsubmission;5submissions/2vectorobservations/0handoff. No oldoperatorD7fullcontrol, so don'tattribute entire4.22%gain toR96.

|Arm|Process seconds|Official U|Global L|Absolute gap|Certificate|
|---|---:|---:|---:|---:|---|
|OLD-FEEDBACK|3597.234|.2962585864097505|.28144494010980303|.01481364629994747|No|
|FEEDBACK r96|3597.250|.29937554504659036|.2814448437782383|.017930701268352056|No|
|OFF|3597.250|.32950410717326206|.2814538063444285|.04805030082883355|No|
|P-GRB|3597.219|.43423583676402355|.2682505969243228|.16598523983970076|No|

Old/combined U gains versus OFF:10.0896%/9.1436%, versus P:31.7747%/31.0569%. Combined U1.0521%/gap21.0418% worse than old; material quality regression, not a certificate-time conclusion. Early combined lead crosses late. No candidate frozen yet. Full report development02_f5_report.md.

Four reporting scripts ACTUALLY passed syntax/null comparison checks and ran: round97_analyze_batch_v2, analyze_role, trajectories, cost_ledger. Results analysis_views/development02_F5_analysis, trajectories/development02_f5 and development01_f5, costs/development02_f5. Engineering receipts development02_reporting_checks01 / development02_f5_analysis01 / development02_f5_trajectories01 / development01_f5_trajectories01 / costs_development02_f5_01 / development02_f5_export01. Role views are nonlaunchable, not extra starts. Final result endpoints remain untimed sidecars; no fabricated certificate timestamp or SHADOW U. Independent reviewer found no new material reporting/accounting issue and stressed preserving the negative comparison.

Latest costs/development02_d7_complete:18solverstarts42510.559s,90verifiedcompletedOptimize+6observedinterruptedscopes, countscompletefalse. Eight0Optimize diagnostics+8micros separately gives34experimentalstarts. Snapshot includes priorledger receipts andD7export, excludes own1.4101555safterwrittenreceipt untilnextsnapshot. No doublecounting/unrecordedhostwallclaim.

## Frozen identities and completed history

Actual v2 C++ source f0bdaed3f2b9c2205b05584cca29337ee9640c58. Binary build/research/round97-native-closure-v2/ExactEBRP.exe SHA256 7ea6b0eb3500084f6b93748ca43bedfb7ac7ec04591dd19c889a195e1ad31943. Gurobi13.0.2, GCC14.2UCRT64, Threads1/Seed0/Presolve-1, old tolerances, zero requested gaps. Old H1 binary remains separate. production_v2_identity and current development identity bind actual source/helpers/build; do not modify frozen runtime helpers while queued.

qualification01 administratively stopped F2 after76.109s for no-op submission confound; actual OS exit remains abnormal, auditfalse. Other planned arms never started and superseded. qualification02 all3normal: short F5 only Start, F2 real later-state feedback. development01 H1 all four F5/3600 completed; old recovery queue had a status-write failure before extra solve, then successful continuation, no duplicate runs. Detailed H1 report development_interim.md and development01_analysis.

Eight pre-registered native_order_replay cases completed once,0Optimize: F5 three later states have joint increment, F2 three do not; large Start increment motivated excluding immutable initial seed/current actual Start in v2. Never rerun. v2 build/micros/reader fixture passed. qualification03 F5SHADOW900/F5FEEDBACK900/F2FEEDBACK240 all normal/audited;69actual-matrix vectors passed. Gate and analysis actually completed, source/binary unchanged. Gate is functional only, not performance acceptance.

Current F5 independent vector counts41/30/26; API submissions10/6, observations6/3, native changes10/6, archive handoffs0/0 for old/combined. Callback2.7389272/4.0017344s. Every ENS arm7Optimize, P1. Combined recorded16fresh joint increments/60orderaccepts/631652proposals; final nativeU is slightly better than its best strict closure output. Complete compact evidence index development02/evidence_f5.json, endpoint_witnesses/F5_*.json; large LP/CSV local with hashes in vector/trajectory receipts.

## Next registered work (do not duplicate)

Development02 frozen13arms33300s: F5numbers1–4 completed; D7 P/OFF/r96FEEDBACK numbers5–7 complete andanalyzed. NEXT V1 OFF/r96/P numbers8–10 each1800; F2 r96/P/OFF numbers11–13 each900. Recovery commands in development02_d7_interruption.md supersede old normal-only commands in reproduce.md after arm5. Each block stops for root interpretation and checks previous complete/audited prefix. D7 d7dbd018… input/T18000; V1 dd841e57…/T7200; F2 ebdf99e7…/T3600. No old times in new-build comparisons.

After all four development roles, freeze ONE uniform candidate before C1/C2/C3. These inputs were generated once, never optimized or used for design. Confirmation three arms each900/1800/3600 respectively,18900maximum. F5 + C3 can satisfy two long groups once. Preserve U6zero evidence, V1regression and F2certification protection. Overall planned outer solve total~69548s leaves reserve under80000s/~72experimental starts; optional old-operator controls only if evidence warrants.

Remaining: D7/V1/F2 and necessary attribution; uniform candidate freeze; independent confirmation including C3 long group; complete cost/Optimize ledger, final reports/math/reproduce/compact index; final independent whole-stage review; push/update stacked draft PR. Goal active/incomplete. No permission needed. All performance strictly serial; no compilation/heavy audit/compression while solver live. This turn progressed by finishingD7, actually validating/executing interruptedreports/trajectories/costs/export, correcting telemetryinterpretation and preparing originalV1continuation. Not blocked. LatestRESUME activation update is locally dirty; defer nextcommit until idle.
