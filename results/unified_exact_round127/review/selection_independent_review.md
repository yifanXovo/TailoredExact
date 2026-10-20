# Independent finite training-selection review

Status: PASS. Review UTC: 2026-10-20T21:29:59.105663+00:00.

A separate executor implemented the selection and timestamp arithmetic in a standard-library-only script. No campaign selection, portable checker or clock-recovery function was called. No Optimize, build or native rerun was performed. This is a finite evidence review, not third-party replication or a full rational audit of every native matrix.

The independently selected configuration is **q2** (MIPFocus=2, Cuts=-1). It agrees with the sealed pipeline output and may be committed as the frozen selection before formal evaluation.

| q | N | N Seed 2 | N Seed 3 | N min | S q | Eligible nondefault |
|---|---:|---:|---:|---:|---:|---|
| q0 | 3 | 2 | 1 | 1 | 0.7424456108499456 | default |
| q1 | 2 | 1 | 1 | 1 | 0.8937937787285558 | no |
| q2 | 4 | 2 | 2 | 2 | 0.6568870237580052 | yes |
| q3 | 0 | 0 | 0 | 0 | 1.0000000000000000 | no |
| q4 | 4 | 2 | 2 | 2 | 0.6575466736599251 | yes |
| q5 | 0 | 0 | 0 | 0 | 1.0000000000000000 | no |

Only q2 and q4 meet the nondefault eligibility rule. Both improve certificate count over q0; q2 wins on the smaller score after the equal N/N min comparisons. No extra configuration or alternative test result enters the rule.

All 36 positions are retained, unique and complete; each q has six positions over the three frozen input SHA identities and Seeds 2/3. The manifest rotation matches actual singleton launch names and chronological, nonoverlapping original outer fee intervals. Every position has its own native creation record/destination, one native model and Optimize call, actual requested MIPFocus/Cuts, and NumStart_before_optimize=0. For each input, all 12 actual compact LP byte hashes match the reference and native model-domain readback. The frozen actual E1 PE, DLL and source bindings were checked.

For every position, the selection clock was independently recalculated as producer.t_produce_unix minus the original fee PID.launched_unix. The latter is the real parent logical admission marker before launch.json/Popen, not an invented OS wrapper birth time. T_total adds the original monotonic verification interval. All 36 complete producer intervals satisfy their cap; admission prefixes range from 0.000895 to 0.395232 seconds; the maximum raw wall/performance discrepancy is 0.008496 seconds. Raw receipts, complete-clock sidecars, selected rows and receipt hashes agree. The outer fee already includes this prefix and was not increased again.

The 23 valid open positions retain null T_cert; their sorting value of 1 is only a censored training penalty. The sealed audits and final verification-closeout/total receipts establish qualification; the retained preliminary independent_evidence clock/qualification-pending flags describe the earlier pre-total-receipt stage and are not silently edited. Raw Seed2/3 native_preconditions metadata is likewise preserved; final returned-model qualification follows the already reviewed offline scope policy. Finite required-output and proof-closeout file hashes were checked, without a full raw journal sweep or proof-reader rerun.

At review time, no main/tiny/core formal output directory or formal fee launch exists. No formal-role historical performance was opened or used to select parameters. All training outcomes, including open runs, remain in the denominator.

selected_P.prm SHA256: `e7cc6a9d9567f5f1b8d7c8887e5dfdf18f6632b8e97051583f2a2080c22e1f6f`.

Machine evidence: `review/selection_independent_receipt.json`; implementation: `review/selection_independent_audit.py`. The substantive audit is charged through round127_common.metered as verification; its outer fee receipt is in `fees/independent_selection_review_02/receipt.json`. The first audit attempt retained its failure fee/log; it reached all 36 positions and stopped on the review script's incorrect selected_P.prm directory assumption. Only the reviewer script path was corrected; no experiment, evidence or selection was changed.
