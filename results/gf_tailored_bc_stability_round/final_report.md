# Stability Callback Vector Regression Final Report

1. Paper strictness: audits pass and scans found no forbidden instance-specific paper-core branch.
2. Official benchmark: current binary-expansion compact MILP plus CPLEX, benchmark-only.
3. Alternative formulations: not enabled; they remain diagnostic because current route-case models exceed practical caps.
4. Callback vector export: `callback_vector_export_working`.
5. 4h vector run: performed=True; dominant K4 run emitted `interval_feasible_improving_ub` after 13984.2568378s with 560 nonzero sampled callback values.
6. API limitation: not applicable; `CPXcallbackgetrelaxationpoint` returned 0 in relaxation context.
7. Easy full-frontier controls remained stable/certified at available budgets: 4/4.
8. Hard full-frontier reproductions emitted final/logging artifacts: 4/4; tight_T_seed3102 1200s hit wrapper_error/access-violation and is preserved as noncertificate.
9. moderate_seed3302 regression reproduced: yes.
10. Regression cause: baseline, callback_overhead_or_search_path_variance, cut_overhead_or_search_path_variance, no_material_regression.
11. Safe generic configuration fix implemented: none; callback_cheap_cuts reduced the 300s regression and S-bucket diagnostic closed but remains diagnostic-only.
12. Fix impact on low_gini/high_imbalance/tight_T controls: no policy fix was applied; controls were rerun for stability.
13. Paper-core contamination risks: diagnostic vector/S-bucket and benchmark rows are labelled outside paper evidence; audits pass.
14. Next algorithmic step: use exported callback vectors plus root/trajectory diagnostics to target low-Gini denominator/search weakness, and debug the tight_T_seed3102 native crash before broader claims.
