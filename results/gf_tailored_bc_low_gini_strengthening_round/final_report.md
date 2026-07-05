# Low-Gini Strengthening Round Final Report

Status label: `compact_bc_improves_moderate_low_gini_bounds`.

1. **Why the moderate low-Gini leaf plateaued:** the blocker is still a weak denominator/objective-estimator relaxation on the low-Gini interval, followed by slow CPLEX branch-tree bound progress. The repaired checkpoint path preserved the best valid CPLEX-native lower bounds; the plateau is not a stale-finalization artifact.

2. **S-range refinement:** diagnostic S-bucket rows closed `low_gini_1` at 60s and 300s, but they remain diagnostic only. The parent S-domain was not split into a complete certified bucket ledger, so S-bucket closure is not paper evidence.

3. **Variable-S/local centering:** paper-safe low-Gini centering remains the strongest safe mechanism. `callback_local_centering` and `callback_local_q_centering` reached LB `0.0487233640003` at 1200s on `low_gini_1`, improving over same-budget plain fixed-interval MIP LB `0.047523686728`.

4. **S*P estimator:** the existing paper-safe S*P estimator stayed enabled in the tailored common profile. It helps the safe variants but did not by itself close the hard low-Gini leaf.

5. **Tailored vs plain after improvements:** tailored paper-safe variants beat plain fixed-interval MIP on `low_gini_1` at 60s, 300s, 1200s, and 3600s. At 3600s, `best_combined_paper_safe` reached LB `0.0487233640003` versus plain LB `0.048296011756`.

6. **Leaf closure:** no paper-safe variant closed the moderate `low_gini_1` leaf. The best paper-safe gap-to-cutoff is `0.0004291886644`. Diagnostic S-bucket closure is explicitly excluded from certificate evidence.

7. **Other hard leaves:** `best_combined_paper_safe` materially improved `high_imbalance_seed3201_hard` and `tight_T_seed3102_hard` over plain fixed-interval MIP at 300s. It was slightly worse on `moderate_seed3302_hard`, so that leaf remains a secondary diagnostic target.

8. **Most useful mechanisms:** local/q-centering and the existing low-Gini/SP objective estimator produced the best safe low-Gini bounds. Subset cross-H centering is valid and active, but by itself was weaker than local/q-centering on `low_gini_1`. Required external-source rows were generated in the combined model; compatible-source cuts were safe but not active on this moderate leaf.

9. **Audit result:** certificate audit, callback audit, model identity audit, S-bucket coverage audit, summary cleanup audit, thread fairness audit, objective convention audit, low-Gini cut validity audit, plateau bound trace audit, and no-instance-special-case audit all pass. `audit_timeprofile_finalization.py` found no selected timeprofile rows in this fixed-interval round and returned zero failures.

10. **Correct paper claim:** Compact-BC/tailored-BC is validated as an unresolved-interval subsolver with paper-safe bound improvements on moderate low-Gini and strong wins on selected hard V20 leaves. It is not yet a certified closure for `moderate_seed3301` low-Gini leaf 1; the next theory target is a certificate-valid S-domain split/merge or a stronger denominator-aware objective estimator.
