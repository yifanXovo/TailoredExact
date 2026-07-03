# CPLEX Comparison Low-Gini Round

`results/gf_compact_bc_lowgini_round/full_instance_cplex_comparison.csv`
combines prior audited one-thread V12/V20 CPLEX rows with this round's generated
diagnostic CPLEX rows. `interval_level_cplex_comparison.csv` contains matched
fixed-interval plain/tailored comparisons for the moderate low-Gini leaves.

All plain CPLEX rows remain benchmark-only. Their lower bounds and incumbents
are never imported into `paper-gf-compact-bc` certificate evidence.
