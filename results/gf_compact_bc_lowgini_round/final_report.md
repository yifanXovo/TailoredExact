# GF Compact-BC Low-Gini Round Final Report

Status label: `compact_bc_improves_moderate_low_gini_bounds`.

1. Tailored was weaker than plain on moderate low-Gini leaves because the prior safe estimator used a loose global `S_U`; the new run tests variable-S and SP estimator rows directly.
2. S-range refinement is implemented as diagnostic bucket infrastructure. The selected low-S buckets close by infeasibility, but this is not paper-core parent-leaf evidence because all S buckets are not yet coverage-merged in the full ledger.
3. Variable-S centering is paper-safe and logged by row count.
4. The S*P estimator is paper-safe via McCormick relaxation over valid S/P bounds.
5. Best low_gini_1 plain LB: 0.045502061979; best combined-safe LB: 0.048723364.
6. Moderate certification status is reported in the interval comparison CSV; nonclosed rows remain honest fixed-interval timeouts.
7. Generated hard diagnostic rows: 15; they expose mixed behavior, including small certified cases and larger wrapper/native exits that remain scalability diagnostics rather than certificate evidence.
8. Cut/domain mechanism impact is in `low_gini_strengthening_ablation.csv`.
9. Full-row and CPLEX comparison CSVs in this focused script reuse the generated and interval-level comparisons; benchmark rows remain one-thread and benchmark-only.
10. Correct paper claim: Compact-BC is a paper-safe unresolved-interval subsolver inside the Gini-frontier compact certification framework, with diagnostic S-range refinement held out until coverage-aware ledger support is implemented.
