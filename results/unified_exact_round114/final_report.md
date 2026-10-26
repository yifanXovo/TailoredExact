# Round114 final scientific report

**Execution: BLOCKED. Scientific attribution: INCOMPLETE_ATTRIBUTION for ENS-C and M-B.** The admitted fixed group executed cold P-GRB and ENS-C once. P-GRB is a qualified open measurement; ENS-C returned normally and completed all necessary evidence writes, but its true whole exceeded cap. The unchanged cap gate stopped before P-S and M-B. Six new pair positions are UNEVALUABLE. No rerun, extra Seed or replacement model was used.

The final layer is `R112_COMPLETE12_PLUS_R113_G50_4_PLUS_R114_G100_4`: 20 arm positions, 16 qualified original measurements (15 inherited plus one current), 30 pair positions, 21 evaluable inherited pairs and nine unevaluable positions. Three historical G50 cold-P pairs remain missing; six G100 pairs are also unevaluable. The four historical R113 G100 unstarted records remain in a separate execution ledger. Neither qualification CLI is a performance measurement.

## Current G100 evidence

Input SHA b3f3a1270f062e9f3af64d5b00392f51821bb775818edc6cd383fcd62550618f; V100/M8/Q30×8, physical T18000, lambda .15, pickup/drop 60/60. The admitted original argv, native Seed0, one thread, affinity, Presolve Auto, zero MIP gaps, tolerances and H semantics were retained.

|Method|Actual execution|Formal U|Formal L|Gap|Certificate|True whole seconds|Qualification|
|---|---|---:|---:|---:|---|---:|---|
|P-GRB|One cold original compact MIP; rc0|.03994210048354935|8.782082104514013e-7|.039941222275338896|false|3573.223369550775|Qualified open; native claims retained|
|ENS-C|Three LP + one terminal MIP; rc0|null|null|null|null|3605.688342700014|WHOLE_ARM_CAP_EXCEEDED|
|P-S|Not started|null|null|null|null|null|Fixed stop after ENS-C|
|M-B|Not started|null|null|null|null|null|Fixed stop after ENS-C|

P-GRB raw readback U=.03994210048354933 and raw gap=.039941222275338875 are retained; the table uses the reader's independently recomputed physical U and gap. ENS-C raw diagnostic U=.005528455284552843, raw L=2.20888241772054e-7 and raw gap=.005528234396311071 are preserved; its independently recomputed own physical U is .005528455284552848. Its over-cap diagnostics do not enter a WIN, dU/dL/dGap, or formal source-reduced endpoint. Its native claims were not contradicted by the available G100 witnesses. No current call was rejected and no current arm is SOURCE_REDUCED_OPEN. Final cohort reconciliation uses both actual physical witness sets, is invariant under reversing their order, and does not rewrite the closed clocks. The independence and validity of a physical witness is distinct from its performance-clock eligibility.

The blocking receipt is the actual ENS-C whole, 5.688342700014 seconds over the 3600-second cap. Native process wall was 3570.359999999986 seconds; necessary audit inclusive time was 34.928690399974585 seconds and admission/necessary postexit observation was 35.32834270002786 seconds. All own physical/floor evidence, claim records, audit, metrics, progress receipt and closeout digests were written before the real whole timestamp. The cap was enforced immediately thereafter. The observed failure is insufficient completion reserve on this evidence path; no online algorithm or unique internal cause is inferred from these durations.

## Integer completion and native exposure

Both eight-vehicle fleets passed independent original physical checks: integer single-direction service, at most one vehicle per station, all prefix capacities, inventory bounds, return unloading and physical duration. `physical_completion.json` binds the full Y/D vectors and raw results.

P-GRB differs from D only at station22 (Y6/D12) and station55 (Y18/D10), total absolute difference 14 bicycles. Maximum route duration is 17920.573658299618. ENS-C differs only at station19 (Y11/D9), surplus two bicycles, maximum duration 17824.6158647965. Neither has strict Y=D. G100 zero optimality remains unknown.

The best committed P witness is sequence143, conservatively available by 2732.372561250697 seconds. ENS-C best witness is sequence22, available by 3323.963134400081 seconds. These availability bounds include admission offset and are separate from postreturn independent audit. Actual native first discovery is unknown. Checkpoints use only committed own witnesses available at the listed times; ENS-C checkpoint values are explicitly diagnostic, and no final fleet is backfilled.

P has one declared, actual, journal-returned and independently verified returned Optimize. Original compact: 260160 rows/91969 columns; 1576 nodes, 2131919 simplex iterations, log Work8243.32, root relaxation0; API runtime3562.822000026703 seconds. ENS-C has four declared/actual/journal-returned/verified-returned calls, zero explicit not_started: three LPs and one terminal MIP. Its MIP has 421423 rows/176866 columns, nine nodes, 2112211 simplex iterations, Work6616.05 and root relaxation0. Settings/model SHA/true G interval/cutoff/logs/cleanup and cover observations remain in raw and reconstructed native_calls/native_bounds/covers tables. No actual atomic parent replacement occurred. Lookahead calls are not counted as split events. Hidden search causes are unknown.

ENS-C paid H275.7322666 seconds, LP inclusive153.73300004005432, MIP inclusive3052.1360001564026. The observed H own U was .1584580742872275. These are inclusive observations, not subtractable causal contributions. P-S and M-B did not expose a backend or complete H; their absence prevents the required full 25-seed same-H comparison. Missing same-H and exposure are explicit, rather than inferred from ENS H's scalar U.

## Scientific qualification and history

All six G100 pair positions remain UNEVALUABLE, with null deltas and cap/missing-arm reasons. Existing strict materiality/severity, signed gaps and 1e-7 policy are unchanged. ENS/P-S is not evaluated from ENS's better diagnostic UB; M-B/P-S is not inferred from other roles.

ENS five-role vector: W/W/L/W/UNEVALUABLE. M-B: W/W/L/T/UNEVALUABLE. Four roles are eligible for each; the fifth lacks strict pairs, full same-H and both backends. Both statuses remain INCOMPLETE_ATTRIBUTION. This finite blocked collection does not establish geographic win rates, an independent new sample, universal exactness or an adoption threshold.

R113 remains BLOCKED. Its original cold G50 P has no whole/metrics and cannot be recovered by this protocol. G50 ENS strict own zero and whole322.5586690000491 remain; M-B/P-S own U .008182628062360805, whole1777.2817804088118/1771.3991304999217 and station20 one bicycle short remain. ENS/P-S WIN, M-B/P-S TIE and M-B/ENS severe LOSS are preserved. R112 twelve measurements/eighteen pairs plus R113 three measurements/three pairs retain original clocks and identities. No partial13 or excluded old arm is promoted.

## Protocol, numerical evidence and qualification

This round explicitly repairs the research audit/closeout protocol omitted in R113's preflight. It inherits R110's known G50 bound contradiction and independent floor/own-UB endpoint, and R111's limited signed return authority. It does not search again for the same contradiction or identify a unique Gurobi internal cause. Exact saved-matrix checks reproduce all 13326 columns and 35567 rows with zero rational violations: objective2.9256256379999997e-16 for printed decimal and1.979712144217771e-16 for the specified same-SHA P-S API binary64 matrix. The API snapshot is not an unsaved cold API readback. Original bad event52/53 bounds, returned event82 and final readback/log remain bound. `numerical_evidence.md` explains the construction and the limits of the conclusion.

The prospective method-symmetric claim contract rejects only directly proven same-domain claims and their dependent native proofs. A bad call's later smaller bound cannot restore trust. Independent own UB, floor0/own zero and complete original clock are mandatory for a replacement endpoint. The narrow missing-returned exception requires the known terminal MIP latch plus all independent normal-return evidence and committed own strict zero; unknown lifecycle, model, identity, physical or necessary I/O still stops. Supported zero-Optimize fields now require status0/0/false and lifecyclefalse. None of these branches was a real numeric fault injection in this run.

Production206 source files, inherited PE a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8, Gurobi DLL9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88 and47 frozen performance helper files are unchanged. The final two H100 CLI passed under exactly the admitted performance bytes; independent performance admission was ACCEPT before any formal launch.

Finite01's fixture-schema error is retained and billed; finite02 passed. Exactly H100 P then M-B, cap120/Seed0, returned and audited, followed by billed actual-evidence post01. Qualification: six conservative starts,189.472980260849 outer seconds; six actual Optimize calls. Formal: one wrapper/four declared child slots charged as five starts, two actual children, five Optimize calls,7178.921706250752 outer seconds, exit1. Total:11 conservative starts and7368.394686511601 outer seconds; all fees closed after actual OS exits, no nested time added, failed/unexecuted declared slots not refunded. Limits16/17000 and qualification8/900 were respected. Unused budget is not a rerun allowance.

After formal stop, the admitted offline reader failed on the true over-cap receipt. Only the offline report path was corrected to retain the real whole and output an unqualified/null endpoint. Original bytes/traceback, diff and actual timed repair/check receipts are in engineering/offline_reader_repair01; candidate/admission were not rewritten. The targeted checks preserve the healthy P, both qualification CLI and all historical15/21 fields. Frozen runtime helpers, raw and clock bytes remain unchanged.

Public manifest/archive, export/empty-root reconstruction, exact core comparison, independent postformal/whole-goal/restored reviews and remote actual-object receipts are separate delivery evidence. Engineering elapsed receipts are recorded where measured; orchestration/human wall time without an instrument is unknown and is not solver nominal time. Scientific payload precedes those actual restore/remote receipts; no receipt claims to verify a future commit containing itself.

**Only next priority:3.** This finite round ends with one qualified G100 cold baseline, an over-cap ENS diagnostic and two unstarted controls. Strict G100 attribution remains unavailable. No new mechanism, qualification cycle, longer cap, parameter grid or automatic next-stage work follows. ENS-C remains default, cold P the primary benchmark, and uniform M-B the research candidate supported only by the retained qualified history.
