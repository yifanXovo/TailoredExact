# Stable mainline assessment

Corrected CPLEX S0/F0 remains the stable production/mainline algorithm. C1 is not promoted and no default alias, dispatch rule, solver portfolio, or backend selection was changed.

C1 is exactly C0 because the only uniform prototype, P1, failed the preregistered difficult-instance development guard. The production gate passes 8/10 requirements and fails Gate 3 (v12_regressions_resolved_or_bounded), Gate 9 (broad_c0_nonregression). The decision is fail-closed even though held-out V20, V50, and long-run P-GRB comparisons strongly favor C1.
