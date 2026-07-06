# S-Bucket Denominator Strengthening Final Report

Status label: `compact_bc_improves_moderate_low_gini_bounds`.

## Main Outcome

The round implemented and audited S-domain bucket metadata, bucket-tight denominator estimators, bucket merge audits, subset cross-H separation profiles, and transfer-cut validity checks for `paper-gf-tailored-bc`. The principal moderate low-Gini leaf remains open, but the tailored paper-safe rows materially improve over matched plain fixed-interval MIP at every long budget tested.

For `moderate_seed3301` low_gini_1 `[0.0122881381662, 0.0245762763324]`, the best paper-safe LB is `0.0487233640003` against cutoff `0.0491525526647`, leaving gap-to-cutoff `0.0004291886644`. The matched plain fixed-interval MIP at 3600s reached LB `0.048296011755`, leaving gap-to-cutoff `0.0008565409097`.

## Required Questions

1. Why was tailored weaker than plain on moderate low-Gini leaves?

   Earlier short diagnostics were dominated by root/presolve behavior. In this round, longer runs show tailored rows are not weaker overall: static tailored reaches LB `0.0483289243336` at 300s versus plain `0.045486706017`, and reaches `0.0487233640003` at 1200s versus plain `0.047545404397`. The blocker is not cut invalidity; it is that the denominator/objective estimator plateaus about `4.29e-4` below cutoff.

2. Did S-range refinement improve low-Gini bounds?

   Yes as a valid ledger mechanism, but not enough to close the parent. Paper-safe K4 ledgers exactly covered the parent S-domain and passed merge/coverage audits. Their merged LB improved from `0.0455127377348` at 60s to `0.0487233640003` at 1200s, but not all buckets closed, so the parent was not certified by S-bucket merge.

3. Did variable-S centering help?

   Variable-S centering is integrated in the paper-safe combined variants. It contributed to the stronger tailored bound profile, but the ablation does not isolate it as sufficient on its own. The strongest 1200s bounds came from static/subset/local-q tailored variants at `0.0487233640003`.

4. Did the S*P estimator remain diagnostic or become paper-safe?

   The bucket-tight S*P McCormick estimator is paper-safe in the tested rows where the S-domain proof is valid. `sp_mccormick_bucket_audit.csv`, `objective_estimator_cut_audit.csv`, and `low_gini_cut_validity_audit.csv` pass. Diagnostic S-bucket policies remain excluded from paper evidence.

5. Did tailored Compact-BC beat plain fixed-interval MIP on moderate low-Gini after improvements?

   Yes. For low_gini_1, tailored best LB/gap-to-cutoff was:
   - 300s static tailored: `0.0483289243336` / `0.0008236283311`; plain: `0.045486706017` / `0.0036658466477`.
   - 1200s static/subset/local-q: `0.0487233640003` / `0.0004291886644`; plain: `0.047545404397` / `0.0016071482677`.
   - 3600s best combined: `0.0487233640003` / `0.0004291886644`; plain: `0.048296011755` / `0.0008565409097`.

6. Did any moderate low-Gini leaf close?

   No. `low_gini_1` and `low_gini_2` remain noncertified. `low_gini_2` best 300s tailored LB is `0.0489209015481`, leaving gap-to-cutoff `0.0002316511166`.

7. Did generated hard diagnostics show Compact-BC effectiveness?

   This round focused on the existing hard V20 leaves required by the prompt and reused the generated diagnostic infrastructure. The secondary hard-leaf rows show tailored wins on `high_imbalance_seed3201_hard` and `tight_T_seed3102_hard` at 300s, while `moderate_seed3302_hard` slightly favors plain MIP. The generated-diagnostic suite should be run as a follow-up controlled matrix.

8. Which cut/domain mechanism helped most?

   Static tailored model strengthening and callback subset/local-q separation produced the best bound plateau. The S-bucket K4 1200s ledger matched the best LB but did not close all buckets. Transfer rows were audited and did not contaminate paper evidence.

9. How does full-row performance compare with plain CPLEX?

   This round is fixed-interval hard-leaf focused. Full-row CPLEX comparisons from previous rounds remain separate benchmark-only evidence. In this package, matched fixed-interval plain MIP is the direct comparator and is beaten on the primary low-Gini leaf and two secondary hard leaves.

10. What is the correct paper claim now?

   `paper-gf-tailored-bc` is a Gini-frontier compact certification framework whose tailored fixed-interval subsolver improves unresolved low-Gini/hard-leaf bounds over matched plain fixed-interval MIP, while exact certification still requires full coverage of the improving frontier or all S-bucket children. Moderate low-Gini leaves still need stronger denominator-aware theory to close.

## Audit Summary

All optimal claims and paper-safe rows pass the audit stack:

- `certificate_audit.csv`: `audited_rows=98`, `failures=0`.
- `s_bucket_coverage_audit.csv`: `rows=40`, `failures=0`.
- `s_bucket_ledger_audit.csv`: `rows=6`, `failures=0`.
- `low_gini_cut_validity_audit.csv`: `failures=0`.
- `transfer_cut_validity_audit.csv`: `failures=0`.
- `timeprofile_finalization_audit.csv`: `audited_rows=89`, `failures=0`.
- `summary_cleanup_audit.csv`, `thread_fairness_audit.csv`, `objective_convention_audit.csv`, `certificate_source_audit.csv`, `model_identity_audit.csv`, and `compact_bc_effectiveness_audit.csv` all pass with zero failures.

## Decision

The algorithm is not ready to claim moderate-seed certification, but it is stronger than the matched plain fixed-interval MIP on the principal low-Gini leaf under 300s, 1200s, and 3600s budgets. The next targeted mechanism should be a tighter valid denominator lower estimator or an adaptive S-domain partition policy that can close every bucket, not just improve the merged lower bound.
