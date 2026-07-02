# GF Compact-BC Effectiveness Round Final Report

Status label: `compact_bc_needs_hard_leaf_strengthening`.

1. Relaxation-only certificates are identified in `certificate_source_summary.csv`; high_imbalance_seed3202 and tight_T_seed3101 are valid framework certificates even when Compact-BC is not the dominant closure source.
2. Compact-BC-assisted noncertified rows are identified separately. moderate_seed3301 has natural Compact-BC leaf closures by infeasibility plus remaining low-Gini timeouts.
3. No false optimality claim is made for hard unresolved leaves.
4. Wrapper-finalized rows use `wrapper_best_checkpoint` when progress evidence is available and expose `best_valid_lb_seen` / `best_valid_gap_seen`.
5. The selected summary de-duplicates conflicting rows, preferring solver-final certified artifacts over wrapper/error rows.
6. Compact-BC hard-leaf effectiveness is in `compact_bc_effectiveness_summary.csv`; remaining blockers are low-Gini/tight leaves with small gap-to-cutoff but time-limit status.
7. Forced BC activation is diagnostic-only; the option is exposed and labelled so it cannot enter paper certificates.
8. Tailored Compact-BC vs CPLEX comparison is reported at full-instance level and interval rows mark plain fixed-interval CPLEX as unavailable where not run.
9. Correct paper claim: Gini-frontier compact certification framework with strong relaxation/domain cuts and Compact-BC subproblems for unresolved intervals.
10. Next cuts should target low-Gini denominator/ratio-band strengthening, objective-estimator tightness, and hard-leaf dynamic separation that improves root bounds, not just row counts.

Certified compact-BC framework rows in this package: 4.
moderate_seed3301 rows carried for diagnosis: 4.

The final commit SHA is recorded in the assistant final response after commit.
