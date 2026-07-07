# Dominant S-Bucket Round Final Report

Status label: `dominant_s_bucket_still_open`.

1. Paper strictness: `scripts/audit_paper_strict_algorithm.py` reports zero failures. The implementation keeps `paper-gf-tailored-bc` as the mainline and excludes BPC, plain CPLEX, archive/known-UB, route-mask enumeration, and focus-only evidence from paper certificates.

2. Forbidden evidence: none used in paper-core rows. Plain fixed-interval MIP rows in this package are benchmark/reference only.

3. Paper-safe S-bucket refinement closed `low_gini_1`: `False`.

4. Remaining open bucket: `dominant_k4` with S range `(16.59546103547, 23.272821182835)`.

5. Best paper-safe LB/gap: `0.04890059983` / `0.00025195283469999635` against cutoff `0.0491525526647`.

6. Improvement over `0.0487820084447`: `True`.

7. Paper-safe new bucket cuts: singleton bucket ratio-domain rows, subset ratio-domain rows up to configured size, and bucket H cap. See `bucket_ratio_domain_tightening_audit.csv`.

8. Denominator estimator candidates: candidate A H cap is paper-safe; local spread cap and H lower rows remain diagnostic; extra P tightening was rejected as unproved. See `denominator_estimator_candidate_audit.csv`.

9. Adaptive policy vs uniform K4 3600s: no. The fixed dominant K4 bucket with `best_new_combined_paper_safe` at 10800s is the best row. The adaptive child remains at `0.0487233640003` and does not outperform the dominant K4 long run.

10. Runs over 3h: yes. The 10800s dominant K4 row ran for `10804.0151443`s, reached LB `0.04890059983`, processed `481042` nodes, recorded `361` progress checkpoints, and last improved at `10742.9536974`s. This is valid progress, not a stall.

11. Runs over 6h: no. A 21600s continuation was not run because the 10800s row improved the bound but did not close the leaf, did not reduce the gap below `1e-5`, and did not trigger the full convergence benchmark rule.

12. Full convergence benchmark triggered: `False` (`not_triggered`).

13. Certified runtime comparison: not applicable unless full convergence trigger is true.

14. Secondary regression:
- `low_gini_2`: tailored LB `0.0489209015481`, plain LB `0.048894652654`.
- `high_imbalance_seed3201_hard`: tailored LB `2.27669085412`, plain LB `2.1614881406`.
- `tight_T_seed3102_hard`: tailored LB `0.517905880713`, plain LB `0.31244733564`.
- `moderate_seed3302_hard`: tailored LB `0.142568520966`, plain LB `0.14433286301`.

`low_gini_2`, high-imbalance, and tight-T do not regress. The `moderate_seed3302_hard` regression persists; bucket-ratio-domain rows match the previous tailored LB but still trail plain fixed-interval MIP at 300s, suggesting search-overhead/branching effects rather than an invalid cut.

15. Plateau snapshot: CPLEX native bound/node traces are available, but fractional root variables are not exposed by the current callback API. The active structural weakness remains denominator/objective-estimator strength inside the open S bucket.

16. Next target: expose richer root snapshots or add stronger paper-safe denominator cuts that use bucket-local S and low-Gini structure without relying on diagnostic evidence.
