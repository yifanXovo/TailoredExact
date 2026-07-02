# GF Compact-BC Effectiveness Round 3 Final Report

Status label: `compact_bc_closes_hard_leaves`.

1. Source/diagnostic semantics: clean if `source_semantics_audit.csv` passes. Leaf solver rows explicitly set `compact_bc_called_this_row=true`; parent rows aggregate child Compact-BC evidence.
2. Tailored vs plain fixed-interval MIP: tailored wins clearly on some hard intervals (`tight_T_seed3102_hard`, `high_imbalance_seed3201_hard`) but does not win on the current moderate low-Gini leaf at 60s/300s.
3. Hard low-Gini leaf closure: no new moderate low-Gini closure was obtained in round3. Inherited natural moderate leaves still include Compact-BC infeasibility closures, but the two low-Gini bands remain the blocker.
4. moderate_seed3301: not certified in this package. The main low-Gini leaf improves with time for both tailored and plain MIP, but tailored safe cuts were slightly weaker than plain at 300s.
5. Low-Gini strengthening: safe mode records and activates existing proved centering/domain/objective-estimator families, but current evidence says they are insufficient for moderate_seed3301 low-Gini closure.
6. Dynamic root cuts: the impact table is present. Hard-leaf bound impact is mixed; useful gains are visible on tight/high-imbalance fixed intervals, not on the moderate low-Gini bands.
7. Generated diagnostics: 5 deterministic hard/general instance files were generated under `reference/hard_compact_bc_diagnostics/`; they are ready for controlled follow-up runs and are marked not-run unless raw rows exist.
8. Full-row Compact-BC vs CPLEX: single-thread full-instance CPLEX comparison from the previous package is preserved as benchmark-only evidence, with round3 interval-level comparisons added separately.
9. Main bottleneck: low-Gini denominator/objective-estimator strength and branch-bound progression on moderate_seed3301. New cuts should target denominator bounds and root-bound improvement, not only additional rows.
10. Correct paper claim: Compact-BC is an unresolved-interval subsolver inside the Gini-frontier compact certification framework. It is not claimed to dominate relaxation closure, and diagnostic evidence is not imported into certificates.

Relaxation-only certified rows: 3.
Compact-BC-assisted certified or mixed rows: 1.
Forced/diagnostic Compact-BC activation rows recorded: 18.
Natural hard-leaf Compact-BC rows summarized: 42.
Matched tailored-vs-plain fixed-interval rows recorded: 18.

Matched interval comparison highlights:
- high_imbalance_seed3201_hard at 60s: tailored LB delta vs plain = 0.178282797
- moderate_seed3301_hard_low_gini at 20s: tailored LB delta vs plain = 0.00089305369
- moderate_seed3301_low_gini_1 at 300s: tailored LB delta vs plain = -0.000248824186
- moderate_seed3301_low_gini_1 at 60s: tailored LB delta vs plain = -0.000370026624
- moderate_seed3301_low_gini_2 at 60s: tailored LB delta vs plain = -5.564119e-05
- tight_T_seed3102_hard at 300s: tailored LB delta vs plain = 0.216307276
- tight_T_seed3102_hard at 60s: tailored LB delta vs plain = 0.223467292
- v12_m1_easy at 20s: tailored LB delta vs plain = 0.00153386589
- v12_m1_easy at 60s: tailored LB delta vs plain = 0

Final commit SHA: recorded in the assistant final response after the final amended commit.
