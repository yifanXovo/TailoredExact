# Round 97 — active, incomplete

## Current authoritative checkpoint

C1 independent interpretation review PASSED (short report/CSV/receipt read only), no blocker to original C2. Actual candidate and batch remain unchanged. C1 report now records this review. Commit/push C1 then launch C2 exactly once; do not rerun C1 or initial admission test.

LATEST TERMINAL C1: session61992 exited0; Python48296/FB50576/OFF all gone, machine idle verified. Original three arms NORMAL/auditpassed and cross-arm checkpassed. P897.203s U.45199469967931727/L.32091716320543384 uncertified; FB202.484s sameU/L.4519946996793168 certified; OFF201.766s sameU/L.451994698207464 certified. FBvsOFF+.718s similar. FB4realpositive-node submissions/3vectorobservations/4thresholdrecords4recordedpairs/0handoff; bestclosure.45395943176136955 is worse than laternativeoptimal. Actualvectors15/14passed,wrapper.9209822/.8911554s. Analysis1.1109253s,trajectories4.0724750s,byte-exactexport8.8987836s executed0Optimize. Output analysis_views/confirmation01_C1_v4_analysis, trajectories/confirmation01_c1, confirmation01/evidence_C1.json+compactarchives/endpoints, reportconfirmation_c1_report.md. Costsnapshot confirmation_c1_complete:30starts57188.293s,130verifiedOptimize+11failedobservedscopes,46experimentalstarts. RemainingC2/C3maximum16200s =>73388.293s/52starts. C2unstarted; next original run-role --role C2 after C1 report commit. No candidate changes. final_report draft+mathcoverage are current incomplete stage docs; all new C1 outputs pending commit. Independent short C1 interpretation review pending; no blocker known. This terminal checkpoint supersedes live statements below.

LATEST C1 TRANSITION: P-GRB arm1/solver34940 TERMINAL NORMAL,897.2029999997467s,4180commits,U.45199469967931727/L.32091716320543384/gap.13107753647388343,uncertified,status time_limit,auditpassed. Same queue/session61992/Python48296 launched C1 FEEDBACK arm2 at unix1790754477.128795; solver50576 OS-confirmed live. OFF arm3 remains unstarted and follows only normal audits/vectors. No change to r83 candidate or original caps. Current local edits while live: final_report.md newly drafted with explicit incomplete status, mathematical_algorithm.md updated with actual v2 micro/reader/production-gate coverage and final selected version, RESUME.md. These are documentation only, uncommitted; no heavy tests/build/compression were performed during C1. Previous turn made concrete progress by these docs and verified waiting through P completion. Do not restart session or run heavy work until all C1 arms terminal.

LIVE UPDATE: after committed/pushed fdad7690f9cbe6c09628de6665c4aa5fdd176c31 and verified PR159 OPEN/DRAFT/baseR96, original C1 group was actually launched via round97_confirmation.py run-role --role C1. Unified exec session61992. First P-GRB arm1 launchedunix1790753577.9610171, original900s cap, then FEEDBACK/OFF only if normal audited. Do not repeat this command, build, heavily audit or compress while live. Below prelaunch checkpoint is historical; candidate/input/operator/schedule remain frozen. RESUME live update is locally dirty and will be committed when idle.

All original13 development02 attempts and all three attribution01 controls are terminal. Attribution queue/session35687 exited0; Python46636 and final solver37040 are gone. No performance process is active at this checkpoint. Never restart completed queues.

The uniform research candidate is now frozen: r83 old R83/R76 physical closure, modefeedback, common v2 build and unchanged ENS-C startup/settings. `confirmation_candidate_freeze.json`, `operator_selection.json`, `attribution_report.md` and `review_operator_selection.md` contain the decision and evidence. Combined ordering has only V1 as a material quality-positive role, below the predeclared two-role rule; F5 is negative, D7 below threshold and F2 similar. Old V1 U is materially worse than OFF; preserve this tradeoff. ENS-C protected default is unchanged; no promotion/merge.

Confirmation01 is PREPARED, NOT LAUNCHED. Current-build Round65ReferenceBuild was built5.4095280s; preparation2.8038351s exported three original reference models with0Optimize. Actual admission test passed.9845628s: full identity, original P isolation, same inputs/settings, uniform candidate and all destinations absent. `prepared_batch.json` holds one batch SHA across roles. Independent read-only review of actual freeze/manifest passed with no blocker; see confirmation01/prelaunch_review.md. Next is C1 after the prelaunch evidence commit/push.

Registered confirmation only:
- C1: P-GRB / FEEDBACK / OFF, each900s, mathematical T5400.
- C2: OFF / P-GRB / FEEDBACK, each1800s, mathematical T5400.
- C3: FEEDBACK / OFF / P-GRB, each3600s, mathematical T7200.

Use scripts/round97_confirmation.py run-role --role C1, then analyze the completed role before continuing C2/C3. Each role stops on any new interruption/failure. Never retry or extend caps automatically. No confirmation tuning/replacement inputs. Candidate freeze is immutable. All performance serial; no builds/heavy audit/compression while solver live.

## Just completed and actually verified

Attribution OLD-FEEDBACK, same v2 input/T/caps:
|Role|Process seconds|U|L|Certificate|Actual vectors|
|---|---:|---:|---:|---|---:|
|D7|3597.234|.21695912392615452|.20446533268379222|No|19|
|V1|1797.203|.17336978885889465|.1535547475327636|No|21|
|F2|550.500|.8659435203229894|.8659435203229897|Yes|10|

All three normal, all audits/vector checks passed. F2 signed gap-3.33e-16 retained. Added scopes4/5/5 allcomplete. Vector wrappers5.5072644/2.1446681/.8220338s,0Optimize.

Actual16-arm/24-pair merged analysis: analysis_views/development_with_attribution_analysis (wrapper2.6228347s). Added trajectories attribution01_d7/v1/f2 ran.7100140/.6981602/2.8351863s. New normal-batch exporter ran6.2045868s: three byte-verified journal+observations archives,187/207/10873members, plus physical endpoints and evidence_complete.json. Large raw models/vectors stay local with hashes. Do not rerun analysis/exports over existing outputs. The attribution analyzer intentionally requires no freeze, so its historical execution preceded the freeze.

Confirmation guard checks01 failed only because the fixture used an exclusive-create writer for a deliberate mutation (1.3043092s0Optimize); failed fixture/receipt preserved. checks02 passed1.4422082s after a fixture-local writer fix. It rejected operator/command/panel/batch mutations and preceding-role terminal failure before dispatcher. Static independent review confirmed both production guard holes fixed. Production algorithm did not change.

Cost snapshot costs/attribution_complete:27solver starts55886.840s;121verified complete Optimize plus11observed failed-run scopes with unknown full counts;43experimental starts including8micro+8diagnostics. Original9-arm confirmation maximum adds18900s, giving74786.840s and52experimental starts. Snapshot excludes its own1.1014234s wrapper and subsequent selection/freeze/reference/admission receipts until the next snapshot. No nested cost double counting.

## Immutable provenance and interruptions

Branch codex/round97-native-incumbent-closure, R96 parent93a29e7290e7e92821482c7f4e2c47dfe2f1e84e. Draft PR159 targets codex/round96-external-primal. Last pushed HEAD e9eb585876197e10b1dafe109a51571d1c670f75; new attribution/freeze/docs pending commit.

Actual production C++ source f0bdaed3f2b9c2205b05584cca29337ee9640c58; binary build/research/round97-native-closure-v2/ExactEBRP.exe SHA2567ea6b0eb3500084f6b93748ca43bedfb7ac7ec04591dd19c889a195e1ad31943. Gurobi13.0.2 GCC14.2UCRT64 Threads1 Seed0 PresolveAuto, original tolerances and requested0gaps. Frozen production/helper identities remain unchanged. Candidate selection does not rebuild ExactEBRP or turn on R96 startup ordering.

Original D7/P arm5: hardstop, acknowledged auditpassed interruption, no final result/certificate. Original V1/combined arm9: hardstop and original auditFAILED, preserved. Separate hard_stop09_recovery.json independently recovers108commits with root-MIP-only lower bounds; certificate, exact full Optimize count and complete callback cost remain unknown. Never overwrite original failed rows or treat recovered values as normal completion. Other normal-return certificates have untimed final-result sidecars, not invented first-certificate timestamps.

Telemetry native_incumbent_change means per-submission threshold satisfaction, not unique actualupdates or provenance. SHADOW candidates never enter officialU. H1 SHADOW3600 and v2 SHADOW900 belong to distinct versions. No production archive handoff has yet occurred. U6 zero evidence is inherited, not a new R97 experiment.

## Remaining stage work

Complete original three confirmation roles including C3 design-isolated long group; summarize every positive/negative/no-trigger result; finish final_report, final pseudocode/test-coverage references, unified CSV/trajectory/evidence index/cost ledger and reproducibility entry; obtain final independent whole-stage audit, commit/push and update existing stacked draft PR. Goal remains active/incomplete. No permission is needed and no completion/default-promotion claim is authorized by current evidence.

Preserve three unrelated tracked user modifications: gf_compact_bc_round/handling_convention_test/handling_convention.json; gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv; gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json. Never broad git add. Use curated exact path lists and git -c gc.auto=0 commit while machine idle.
