# Adaptive S-Domain Refinement Final Report

Status label: `compact_bc_improves_moderate_low_gini_bounds`.

1. Did paper-safe adaptive S-bucket refinement close `low_gini_1`?
No. The adaptive-open final frontier has exact S-domain coverage, but one child bucket remains open, so the parent interval is not paper-safe closed.

2. If not, which S-bucket remains open?
The best open paper-safe bucket is the K4 child `bucket_id=2`, `S in [16.59546103547, 23.272821182835]`, after the 3600s K4 run. Adaptive-open narrowed the open region to `[18.26480107231125, 19.9341411091525]` at 300s, but that narrower child did not yet beat the 3600s K4 bound.

3. What is the best paper-safe LB and remaining gap-to-cutoff?
Best paper-safe LB is `0.0487820084447`; cutoff is `0.0491525526647`; remaining gap-to-cutoff is `0.0003705442199999978`.

4. Did the best bound improve over `0.0487233640003`?
Yes. The 3600s K4 paper-safe bucket ledger improves the previous best by `0.0000586444444`, about 13.7% of the previous remaining gap. This is meaningful progress but below the 50% trigger threshold for a full convergence benchmark.

5. Which denominator estimator helped most?
The bucket-tight S-domain estimator plus paper-safe `S*P` McCormick envelope remains the useful denominator mechanism. The standalone `adaptive_denominator_estimator` matched the best combined 1200s LB (`0.048388162834`) but did not improve over the 3600s K4 bucket run.

6. Did bucket-tight SP McCormick help?
It remains active and paper-safe in all tailored rows (`compact_bc_sp_product_mccormick_rows_added=4`, `compact_bc_sp_product_estimator_rows_added=1`). Its isolated incremental impact is not separable from the combined tailored model in this run, but it is retained because it is valid and consistently present in the best safe variants.

7. Did any H/S/P coupled cutoff row become paper-safe?
No new H/S/P row was promoted beyond the existing bucket-tight estimator. The lower-S guarded row is rejected for paper evidence; the H upper cap is valid but mostly dominated; the H lower row remains diagnostic until exact-H semantics are audited.

8. Did low-Gini centering still help?
Low-Gini centering remains active (`local_centering`, `local_q`, subset cross-H, and variable-S/SP rows), but in this round the best long-run improvement came from longer K4 S-bucket search rather than a new centering variant. The new `dominant-bucket` subset cross-H profile is implemented and logged.

9. Did transfer/inventory cuts activate?
Yes, but weakly on the low-Gini rows. Required external-source transfer rows appear in the best rows, while compatible-source transfer cuts are often inactive. Transfer validity audit passed with zero failures.

10. Did `low_gini_2` remain closed or improve?
`low_gini_2` did not close in the 300s comparison, but tailored improved the bound versus plain fixed-interval MIP: tailored LB `0.0489209015481` vs plain LB `0.048894652654`.

11. Did secondary hard leaves regress?
Mixed. Tailored strongly improved over plain on `high_imbalance_seed3201_hard` (`2.27669085412` vs `2.1614382751`) and `tight_T_seed3102_hard` (`0.517898731718` vs `0.31231711932`). `moderate_seed3302_hard` was slightly worse than plain at 300s (`0.14256670012` vs `0.14433282147`), so this row is flagged as a targeted follow-up rather than a paper-core win.

12. Is S-bucket ledger paper-core eligible now?
Yes for coverage mechanics and row validity; no for parent closure of `low_gini_1`. `s_bucket_coverage_audit.csv` and `s_bucket_ledger_audit.csv` both pass. Parent closure remains false because at least one final child bucket is open.

13. If not, exactly why not?
The ledger cannot certify the parent because `all_buckets_closed=False`. The open 3600s K4 bucket has valid LB `0.0487820084447`, still below cutoff by `0.0003705442199999978`.

14. Was a full convergence benchmark triggered?
No. The interval did not close, the gap is not below `1e-5`, adaptive-open did not leave only a very small near-closed bucket by the configured criterion, and the improvement did not reach 50% of the previous remaining gap.

15. If yes, how did tailored compare to plain CPLEX in certified runtime?
Not applicable. The full convergence benchmark was not triggered. Matched fixed-interval evidence still shows tailored outperforming plain on `low_gini_1` at 3600s: tailored LB `0.0487233640003` vs plain LB `0.048296011755`.

16. If no, why not?
The remaining low-Gini S bucket remains open with a valid but insufficient bound. The observed progress is monotone with budget but not decisive enough to justify broad full-frontier convergence claims.

17. Are there any evidence contamination risks?
No audit-visible contamination remains. Plain fixed-interval MIP rows are benchmark-only; diagnostic-only rows are excluded; S-bucket closure requires exact coverage and all child closure; BPC, archive scanning, known UB injection, and route-mask enumeration are not used.

18. What is the next exact algorithmic target?
The next target is stronger paper-safe denominator/objective theory for the dominant bucket, specifically tighter S-domain propagation or a new valid lower estimator that improves root/final bounds inside `S in [16.59546103547, 23.272821182835]`, plus follow-up on the `moderate_seed3302_hard` regression.

Audits: `certificate_audit.csv`, `tailored_bc_callback_audit.csv`, `summary_cleanup_audit.csv`, `thread_fairness_audit.csv`, `objective_convention_audit.csv`, `timeprofile_finalization_audit.csv`, `certificate_source_audit.csv`, `plateau_bound_trace_audit.csv`, `model_identity_audit.csv`, `s_bucket_coverage_audit.csv`, `s_bucket_ledger_audit.csv`, `low_gini_cut_validity_audit.csv`, `transfer_cut_validity_audit.csv`, and `no_instance_special_case_audit.txt` pass.
