# Round138 continuation

User requested strict execution of `goal.md` A-J. Goal remains ACTIVE until
science, manuscript increment, independent final review, English Draft PR,
finite public byte recovery and bounded current-round cleanup are complete.

- Use `E:/codes/ExactEBRP-work/worktrees/paper-current` explicitly. Original
  `E:/codes/ExactEBRP` is protected. WORKSPACE_POLICY conventions inherited.
- Branch: `codex/round138-shared-product-resource-coupling`, based on accepted
  R137 `72fdcd31716d7b4798727b4ea964b32059c630d1`. main is still
  `b2b940c1e517a72e226ec60fc49ff19651737632`; PR base must be R137 branch.
- Production/source pin: `839283773` (full hash in candidate_manifest.json).
  Default-off CLI `--round138-stock-rlt`, exactly four stock product rows,
  no extra variables. R137 entry/config/PE remain intact. Candidate PE in
  `E:/codes/ExactEBRP-work/build-cache/round138/ExactEBRP.exe`.
- New solve budget: 86400 s total. Actual fee ledger uses
  `scripts/round138_common.py budget`; nested H/LP/MIP not added twice.
  All new unqualified experiments Seed0; only explicit limited repeats Seed1.
  Full own H seed remains 20260626. Single thread, affinity4, serial.
- New runtime: `D:/msys64/ucrt64/bin/python.exe` for scripts; Python LP runtime
  `E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe`,
  Gurobi13.0.2 bound to `D:/gurobi1302/win64/bin/gurobi130.dll`.

Completed: actual refs/idle processes/policy checked; mathematical/history
review and exact J2/J3 four-cell replay; heterogeneous product counterexample;
four R137 saved roots including three specified points; seven-domain actual
default-off matrix bridge and exact four-row/full-precision/RHS checks;
20 preregistered same-domain LPs, all OPTIMAL. See roots/*/result.json,
math/exact.json and review/{pre_math,pre_implementation,LP_admission}.md.

Stock LP increments over newly reoptimized base: K35 +.0179111171,
RX20 +.0459632140, RX35T2 +.0070363188, K20 +.0094412867.
TC+stock adds further information on K20/RX35. Main full candidate is uniformly
stock-only (minimum four rows), AP/TC off. GS controls were independent and
shared aggregate envelopes on K35/RX20, with justified same-domain S bounds.

Three offline preparation bugs/corrections are disclosed in
infra/preflight_corrections.json. In particular initial RX20 stock export used
a recomputed U differing from native cutoff by one ULP; exact matrix comparison
refused it before Optimize. That export is preserved. Corrected exports reuse
the original stored beta/native cutoff and differ from each saved matrix only
by four rows. Gap denominators still use the independently validated U.

Full plan: experiment_plan.json and matrix_frozen.json. Eight physical/objective
configurations / six base inputs / 16 nominal core method positions; eight
strictly matched accepted R137 baselines reused, eight new STOCK runs. Also
one contemporaneous K15 frozen-PE BASE bridge and two 90s micro runs, total11
new positions. Independent reviewer must write full_admission.json with exact
matrix SHA and ACCEPT before run. Pilot is positions1-4; do not launch duplicate
healthy processes or overwrite failed evidence. `round138_campaign.py run 4`
executes pilot, later `run 11` completes remaining entered panel. Every run
uses inherited complete producer, physical/H/Start/certificate reader, plus
actual new stock rows audited in every used model. Baseline full costs were
paid independently in R137 and are not newly charged.

Update 2026-10-29 02:14 Asia/Shanghai: full admission ACCEPT. Position1 BASE
native returned OPTIMAL and was sealed; its first postreader incorrectly used
legacy rather than modern event ordering for `baseline-r137`. Original failed
fee/log retained; no native rerun. Strict modern lifecycle private namespace
and the narrow two-helper amendment were independently reviewed (including
three negative controls) and accepted in review/reader_amendment.json. Original
matrix bytes remain unchanged. Only verification was resumed under engineering
fee arm_001_verify02; it passed. Formal T_produce=122.57938176719472s; U and L
match R137. Failed native fee charged the original producer once. The next
`run 4` skips sealed/qualified position1 and starts positions2-4. Current active
session identity/PID and fee files determine progress; never restart a healthy
running position. Production source/PE, solve commands and original policy
were unchanged by this postreader correction.

Update 02:22: all four pilot positions have sealed qualified results. STOCK
certifies K15 in33.818226547s, RX20 in15.340479234s, K20 in101.635384901s;
matching R137 times112.769303117s,20.506461604s, and K20 open at cap1200.
pilot_decision.json authorizes completing positions5-11 with identical frozen
candidate and commands. Ordinary commit2b0dd40bf records only postreader/paper
scaffolding and pilot decision; production source pin and PE remain839283773.
`round138_campaign.py run 11` has now been launched. It skips1-4, runs K35,
the four n35 resource roles, then BASE/STOCK micro. It may need about3.3h if
the five n35 positions all exhaust caps. Inspect small active_position/runtime
metadata and owned fee PID; do not start another run. Avoid build/heavy I/O/PDF
while native timing is active. Need choose and preregister limited Seed1 after
Seed0 outcomes, still no new source/profile changes during the comparison.

Update around02:50: current long runner session61535 is healthy on position5
K35 (startUTC18:21:45, local02:21:45; cap2400). It will automatically proceed
to6-11; inspect owned fee/PID and small active_position/runtime metadata before
any action. No extra experiments during this timed sequence. Avoid build,
heavy I/O, Git commits and PDF exports until it closes. Native LP/seed/row/Start
checks for1-4 passed. Pending5-11 may take until about05:40 local in worst case.

New code scaffolding, not yet executed: round138_documents.py (assemble/PDF only
after final decision), round138_delivery.py (additive local checks/carriers only
after no open fee), round138_tiny_read.py (prepare7 selected old members after
native closes; portable exact tiny replay). Public byte-read script is still
to be written. Source C++ and PE have not changed; do not rebuild them.

Optional E offline checks actually completed in round138_offline_products.py:
four stock LP vectors have zero handling-product violation; RX20 and RX35-T2
handling caps >=B make those products locally VD-P implied (proof appended to
mathematical_analysis.md). Four existing GS optimal vectors also satisfy the
products for tighter safe lower S bounds, using exact stored-double arithmetic.
These are point checks, not new LP optima/redundancy claims. Reports are in
reports/offline_products.json; zero new Optimize and no new Seed invented.
Independent reviewer requested four prose fixes, now applied: full VD-P incl
sum(q)=g, full-precision claim limited to new rows, D>0/weights/lambda>=0,
and reports/LP.json distinguishes report Optimize0 from source LP Optimize20.

Update03:02: position5 K35 completed and qualified open. STOCK U=.6695955692140068,
L=.556776897983438; R137 BASE U=.6928543586313136,L=.565765681464995. Opposed
endpoints: stock has better U but worse L; smaller signed/relative gap cannot
hide the L regression. It is a clear Seed1 mixed-role candidate (K20 is the
main certificate-benefit candidate). Position6 R-B35-S-T1 automatically started
UTC19:01:21/local03:01:21. Running session remains61535. Completed experiment
G1=2658.7819087004755s; active position6 is additionally reserved/ongoing.

Additional scaffolds now present: round138_plots.py, round138_public_read.py,
round138_ordinary.py, round138_tiny_read.py. Syntax was checked, but no plots,
PDF, archives, additive replay, public read or cleanup has yet run. Post-native
ordinary steps should use round138_ordinary.py (not common.meter), since child
guards require no open experiment fee; it records disjoint ordinary seconds.
Publication uses finite binary carriers with internal member index. Public
script needs publication_pin.json after science commit/push and performs only
anonymous new-carrier/member byte checks within cumulative1800s, same owned
E-work restore root on resume, no Git fallback/Optimize/native DLL.

Update04:22: position6 RB35-T1 qualified open, STOCK U=.5699751069873084,
L=.5008429884159913 vs BASE .59151763477047/.45590389125187164 (both better).
Position7 RB35-T2 qualified open, STOCK U=.4012002178390506,L=.22918159966432358
vs BASE .34464262559194814/.2189859496034747 (better L, materially worse U
and gap). Preserve this adverse result. Position8 RX35-T1 startedUTC20:20:31.746,
same live session61535, then9 RX35-T2,10/11micro automatically. Seed0 primary
should finish by about05:40 local if both remaining n35 exhaust2400s.

Accounting correction actually applied (not a solve):26 native zero-Optimize
export processes total28.38460709922947s conservatively reclassified into
diagnostic G1 via infra/external_costs.json; original fee receipts unchanged.
cost_report.json subtracts the same amount once from ordinary net. Last closed
G1 afterposition7 =7429.463991399389s plus ongoingposition8. Update accounting
again at final. Source LP Optimize20, not zero; report-generation Optimize0.

Reviewer's latest static fixes applied: tiny_read now dots original objective
coefficients against all4 exact witnesses and matching IP/zero fleets; ordinary
wrapper finally records exceptions/timeouts; Seed1 requires unique selected
roles. Reviewers accept the scripts' design. New pending post-native qualification:
round138_native_rows.py uses the existing GP Python runtime to read actual new
coefficients/RHS for7 domains with zero Optimize. Execute only after timed
campaigns under common.meter kinddiagnostic (actual wall charged); this script
has no own no-open-fee guard, unlike ordinary stages.

Independent candidate entry now exists, still research-only:
config/gi_tbc_stock_rlt_round138.json + scripts/paper_s2_stock_rlt.py. They reuse
the unchanged original paper_s2.plan/execute and only appendstockflag/newPE;
parent profile byte SHA checked. Static review passed. Pending actual dry check
round138_entry_check.py (9 main/micro STOCK vectors +2refusals, noOptimize/DLL).

round138_seed1.py scaffold is ready but UNEXECUTED. After Seed0 all11 qualify,
run analyze full, then write seed1_selection.json with1-2 unique roles and
English rationale tied to actual results; strong default candidates now K20
(certificate benefit) and RB35-T2 (adverse), subject to last2 outcomes. `prepare`
freezes at most4 fresh BASE/STOCK runs, Seed1,H20260626, samePE/controller.
Get independent review/seed1_admission.json with exact matrixSHA before `run`.
Both methods independent own H/cost; no favourable repeat replacesSeed0.

Further pending post-native helpers: round138_traces.py collects actual guarded
controller U/L curves on selected known roles (separate diagnostic native-process
clock, final values must agree with endpoints), old baselines only3members each.
Use bundled DOCUMENT_PYTHON for this/matplotlib. round138_plots.py produces
two additional static figures; documents.py now includes physicalT/lambda/cap
and G/Pavg/S tables plus guarded traces. Do not run any until no live experiment.
Public/delivery/archive/ordinary/plots/tiny dependencies/entry/native coeff
scaffolds remain unexecuted. R137 main entry/config/PE and C++ source/PE839
remain untouched; no Git operations/build/PDF during native timing.

round138_analyze.py full currently works and writes a PARTIAL report:4 new
positions,3 core pairs, missing5-11. Re-run only after the sequence or a closed
stage, and never call a partial report a complete study. After Seed0, choose
max2 result-selected roles (prioritize main certificate benefit + adverse/mixed
n35 outcome) and implement a separately frozen paired Seed1 script/matrix with
fresh BASE/STOCK runs. Keep the8 historical Seed0 baselines and K15 bridge
distinct. Full source/PE remains839283773; postreader2-helper changes bound by
review/reader_amendment.json. New auxiliary scripts were created after helper
freeze and do not change admitted production helpers.

Independent reviewer agent is `/root/independent_review`; user goal H explicitly
authorizes this delegation. It has completed math/static/LP admission reviews
and is reviewing the frozen full matrix. Use collaboration followup, not app
thread tools. No other agents required.

Remaining: full pilot and justified completion; finite Seed1 selected on actual
results (max two roles paired); optional resource exploration only if informative;
aggregate U/L/certificates/times/trajectories, explicit research decision;
paper increment in current R137 lineage and affected-page PDF QA; source/raw
carriers/portable pure reader, final independent review; normal push and English
Draft PR (no merge/force push), attach PR; bounded public new-carrier read and
current-round cleanup/retention receipt. Preserve R137 historical recovery
limitations, do not reopen all historical recovery or delete old rounds.

PDF skill has been read; before the first PDF authoring command, run the bundled
mark_artifact_operation_started.mjs once. Use existing document assembly rather
than old Manuscript sources; keep R137 complete manuscript unchanged. No PDF
export, build or heavy I/O during timed formal solves.

Update05:01: position8 RX35-T1 qualified open atUTC21:00:10.379,
STOCK U=.5920260898638284,L=.49102330473230565 vs BASE
U=.5921904488701923,L=.46335799724827287; both improve (mainly L).
Position9 RX35-T2 startedUTC21:00:10.433858, live session61535 remains.
Then10/11micro automatic. Closed G1=9804.289947399404s plus liveposition9.
New auxiliary scaffolds added UNEXECUTED: round138_report.py (six-question
report with stable cost snapshot), round138_pdf_qa.py (Poppler render and
manifest only; actual visual inspection still needed), round138_closeout.py
(new-carrier finite screen and exact-manifest preview-only cleanup).
Guide docs/round138_research.md prepared; final stage decision still pending.
Public_read resume now handles valid complete.part and preserves full corrupt
part before retransmission; publication_pin must include manifest_bytes. PDF
export receipt actual-source identity corrected. Independent lightweight
postprocessing design review ACCEPT, with cleanup binding currentcarrierSHA
and exact rendered PNG names/hashes applied. New helper sources not committed
or executed while formal native runs remain active; frozen helpers untouched.
Tiny_read CLI now accepts optional --receipt; final local run should use
math/selected_replay.json. Report requires that/nativecoeff/entry/localsemantic
PASS before generation. No new Optimize, compile, archives or PDF occurred.

Update06:03 (IMPORTANT repair and live continuation): Primary ALL11 newSeed0
positions completed/qualified, reports/full.json complete8corepairs. LastRX35T2
STOCK U=.40985548222597845,L=.21498016272542564 vsBASE
.4032719988628547/.2108870198670429 =>betterL/worseU/slightlyworse signedgap;
relativegap slightlysmaller doesNOT hide U regression. Micro bothcert ~1s.
Primarysession61535 finished. Allprimarydata/source839/PEa41 remain V1.

Actual GP coefficient readback failed tiny_alpha1e-13 (fees/native_coeff_readback,
4.3128927s charged): native reader drops negative tinyY terms, possibly unsafe
on upperrow. HeldSeed1 before ANYOptimize. Preserved exactV1source/frozenhelpers
artifacts/source_v1_and_frozen_helpers.zip and unusedoldSeed1 selection/script/
matrix/gate/identity tree underrepair/seed1_pre_coefficient_fix. NoNative rerun.
Fixed ONLY newstockrows writer: for0<abs(slope)<1e-12 minimal positive2^k scale
until>=1e-12, allcoeffs andALREADY-outwardRHS via exactldexp, finiteguards.
Ordinaryrows keepidenticalbytes. V2 productionsource
04506fa613446d2ef2bd19794f778909422c51fd; PE
E:/codes/ExactEBRP-work/build-cache/round138-coefficient-fix/ExactEBRP.exe SHA
f4c764ff7164bf042ef612403f82b850698b97c80018bf06b2feff1167d65403.
V1 PE/source/manifest untouched. Newcandidate_repair_manifest/build separate.
Inheritedmetadatafields fixedexplicitly (v1build/qual/time renamed), priorrecords
preserved repair/before_metadata_binding_fix.json and amendment.

V2 seven-domain off/stock qualification PASS: off equalsV1/historical, exactly4
rows0vars, tinyalpha scales16,1,1,16, Fractionexactwholepositive scaling. Actual
GP native readback PASSED7domains+25uniqueusedV1models (33primarySTOCKcalls),
32modelreads0Optimize. EveryusedV1positivealpha/beta>=.21232492258, soV2branch
NOTentered; originalfourNativecoefficientmaps/RHScheckedexact; no primaryrerun
or retagging. qualification/native_coefficients.json and
repair/primary_native_bridge.json bindthese. New0Optdiagnostics charged, G1
closed12209.893986799987s plusongoingSeed1. DoNOT rerunlegacy failing
round138_native_rows.py asif finalqualification; itis retainedbugreproducer.

Newprivateadapter scripts/round138_scaled_read.py uses originalreaderwithonly
newexpectedstockrowgenerator scaled; tiny/ordinarypuremodelpreflightPASS.
NewSeed1privateadmission retainsoriginalprimarygate using preservedV1source
carrier check, separatelychecksCURRENTV2source/PE. Frozen4oldR138helpers unchanged.
NewSeed1 matrix EXACTSHA60f9c2fdb91c1ccdc94b4d9bc32a60cb48fd507e212118dedcb586dd2bbdaebc,
independentlyACCEPTEDandadmissionpreflightPASS. RoleK20BASE->STOCK,
RB35T2STOCK->BASE, Seed1/H20260626,4freshpositions capstotal7200. Explicitly
V2buildconfirmation +secondSeed, nothiddenpureSeed-onlychange. SourcePE frozen.
LIVESESSION **5441**, startedrunUTC22:03aroundlocal06:03, currentposition1K20BASE.
Automaticallycontinuesall4. DO NOTrestartorparallelOptimize/Git/build/plots/PDF.
DO NOTedit scripts/round138_seed1.py,round138_scaled_read.py,round138_repair.py,
ororiginal4frozenhelpers whilethiscampaignactive. Native sourceCppunchanged.
NewgitHEADfaa179638; productionCppsource045 notHEADsourcehelpersmetadata.

Completedpostprimary/preSeed1 ordinarychecks: V2entry9vectors+2refusalsPASS;
tiny_read prepare7necessarymembers/check exactbothJ2J3 PASS withreceipt
math/selected_replay.json. Threefiguresgenerated (traces,paired_evidence,
heterogeneous_product), use bundledDOCUMENT_PYTHON +existingR137python-packages
cache +MPLCONFIGDIRunderR138temp; initialmissingmatplotlib failuresretained,
noinstall/globalmod. ActualguardedU/Ltraces selectedK20/RB35T2 finalendpoints
match; Native-processclock isdiagnosticnotTcert. InitialsidebysidePNGswere
inspected thenchangedtovertical6.8in panelsforPDFlegibility; lateststacked
figuresneedreinspection. NoPDFauthoring/markerhasrun.

REMAINING: after4Seed1runs, summarySeed1actualbothendpoints; updateversion
prose/guide/paper/report fromV1source839 toexplicitV1primary+V2delivered/Seed1
045/f4 (doNOTretag). Stage likelyresearch-only givenprimarymixedresults;
needactualSeed1. Newreportgeneratorrequires allNativequal/entry/tiny/localPASS
andcostcurrentbudgetequality; stablecostsnapshotnotyetcreated. candidate_decision
notyetwritten. DefaultGI-TBCentry/config/compat bytesunchanged.

IMPORTANT deliveryscriptstillV1-scaffold: afterALLtimedNativeclosed, update
round138_delivery.py local_check tochooseV2privateArmModels/expectedscaledrows
forSeed1STOCK (originalforV1), archivedeliverycurrentcandidate fromrepairmanifest,
includeexistingsource_v1carrier plusnewV2source/helpers. Assertoldsourcecarrier
hash ratherthancurrentCppagainstV1oldmanifest. Preserveordinary_steps/costsegments
andrepair failures innewdiagnosticcarrier. source_publication mustexplicitlybind
primaryV1vsdeliveredV2/Seed1. DoNOTeditdeliveryduringNative sinceprivate reader
importsrepair whichimportsdelivery.make_zip; changeonlyafterNativeclosed.
NootherarchivebesidesV1sourceZIP, noadditionallocal-semanticreplay, finalpaper,
PDF/QA, PR/push/publicread/cleanup hasrun. Needalltheseplusfinalindependentreview.
Use--sparse for explicitR138Gitadd (doNOTglobaladdA, lotsOLDuntrackedR137assets).

Light primary interpretation for finaldecision (no newsolve): RB35T2
ho1
candidatebothG(.200289 vs.181545) andPavg(.200911 vs.163098) worsen, explaining
U+.0565576. RX35T2 G worsens(.190995 vs.182550) whilePavg improves(.218861 vs
.220722); netU+.00658348. Its signedgap worsens(.1948753195 vs.1923849790)
even though relativegap is slightlysmaller(.4754732533 vs.4770600973): explicitly
showallfields, doNOTcallitoverallimprovement. K35betterU/worseL remains.
Mathematicalanalysis/docs/reportgenerator now disclose V1primary vsV2delivered/
Seed1 identity and exactrowtransportrepair. AddedofficialGurobinumericguide
bibliography entry in documents.py (actualprimarysourcebrowsed29Oct).
FrozenSeed1/helper/repair/scaled-reader sources remainunchangedwhileNativeactive.

Update06:26: Seed1positions1/2 completedqualified. K20BASEopenU
.7168065462777502,L=.7016685009666251 (cap1200,Tproduce~1172s);
V2STOCKcertifiedTcert90.2347981010098,U=.7168065462777502,
L=.7168065462777444. BenefitextendsselectedsecondSeed (notdistributionclaim).
LIVESESSION5441 nowposition3 RB35T2 STOCK startedUTC22:24:47.764704,
thenposition4sameRoleBASE2400. ClosedG1=13472.36543510016s plusongoingpos3.
Expectedatcaps: pos3~local07:04,pos4~07:44; waitserial, noheavyIo/Git/build/PDF.

Update07:05: Seed1pos3 RB35T2 V2STOCK completedqualified OPEN,
U=.32224484174746326,L=.2311394490964326. DO NOT comparecrossSeedasformalwin
orreplaceS0adverseU.4012002. AwaitsameSeedBASEpos4. LIVESESSION5441 nowLAST
position4 R138_S1_004_R-B35-S-T2_BASE startedUTC23:04:22.891922,
cap2400 ->aboutlocal07:44ifcap. ClosedG1=15843.50016080006s pluslivepos4.
No Git/build/archive/PDF/heavyreads whilelive. Source/PE/4frozenoldhelpers plus
newSeed1/scaled_read/repair frozen unchanged. Report.py now has `decide` action
(prepared,UNEXECUTED) that afterall4S1summaries createscompleteRESEARCH_ONLY
decision/discussion/nextquestion dynamicallyshowingS1RB U/L directions; `main`
generates6-questionreportafterlocalPASS/currentcostfreeze. Needreviewactualtext
notblindlyassumeS1RB outcome. No candidate_decision.json orPDF yet.
PDF.py exporter now usesXeLaTexcwdOUT (sameasR137 forrelativefigurelinks).
PDF_QA.py now usesexistingPopplerpdfinfo/pdftotext/pagePNGcount, noextraPython
PDFdependency; actualvisualQAallincrementpagesstillpending. Latestfigures are
verticalpanels (6.8inwidth), havenotyetre-viewedlatest/PDF; noheavyIOnow.

Finaldeliverydesign reminders: whenaddingordinary_steps todiagnosticZIP, include
ONLYclosedstepdirectorieswithreceipt.json; archiveoperationitselfhasopenstdout/
noownreceiptandmustnotself-capture. Latearchive/public/cleanupfeesremaininfinal
cost_report ordinary_step_receipts andcommittedmetadata, no recursive science
repack. accounting.py nowincludesper-stepreceiptdata/SHAandsaysinteractive
reading/editing/review/intermediateGitnotexhaustivelytimed. closeout.py nowalso
bindspublication_screen.currentmanifestSHAandchecksfinalPDFhashagainstthe
publiclycheckedscience_and_paper memberindexbeforedeletingonlyexactQApagePNGs.
Theseareauxiliarypostprocessingchanges, nofrozenNative/readerhelperedits.

Update07:30: StillLASTSeed1BASEpos4 healthy, sameSession5441, expectedcapend
~07:44local. Added an independentlyverified purelymathematicalGS corollary to
mathematical_analysis section5 anddocument/report prose: if Sl/Su validfor
selectedcontinuousstockP (asactualfractionalknapsackGScontrols), endpointdecomp
implies4MCrowsforWshared, henceideal Fstock subset FsharedGS subset projection
FindependentGS(chooseWindep=Wshared,commonbaseHrow). No strictfullBRPclaim,
no arbitraryhistoricalGSdominance, no literalnative/outwardmatrixdominance;
givenheterowitnessonlystrictreversefailureproductblock. Reviewerconfirmed
actualSboundderivationfits. NoOptimize/codecandidatechange. Includeinfinal
integratedmathreview; oldpre-admissionfilesnotedited. Noextrascientificrun.
