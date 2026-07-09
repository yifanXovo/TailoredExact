# Formulation and Snapshot Diagnostics Final Report

Status: diagnostic package complete; no benchmark/plain/alternative/snapshot row is used as paper-core certificate evidence.

1. Exact alternative formulations implemented: current binary-expansion compact MILP metadata; exact S-value coverage enumeration; exact S-selector coverage audit; exact S-parametric cutoff audit. The exact S formulations are implemented as coverage/toy-equivalence audits in this round, not route-level production solvers.
2. Rejected formulations: coarse SOS2 / piecewise inverse-S, coarse S buckets, Charnes-Cooper integer scaling, and Dinkelbach iterations. They are listed in `alternative_formulation_rejection_notes.csv` because exactness or finite certificate equivalence is not proved.
3. Exact alternative outperformance at 300s/1200s: none. No route-level exact S alternative was runnable within the configured complete-coverage cap, so the current binary-expansion compact MILP remains the only runnable plain benchmark here.
4. Plain CPLEX weakness exposed: yes. Complete denominator modelling is exact in principle, but exact S coverage is too large on V12/V20 route domains without stronger domain reduction. The current plain benchmark is therefore labelled `tolerance_exact`, not silently exact.
5. Exact S enumeration / selector feasibility: the V4 direct-algebra toy passes equivalence. V12 M1, V12 M2, moderate low-Gini leaves, high_imbalance_seed3201, and tight_T_seed3102 all exceed the configured exact-S value cap and are reported as `exact_but_too_large`.
6. Variable-level root LP vectors obtained: yes. `root_lp_solution.csv`, `root_lp_reduced_costs.csv`, and `root_lp_constraint_slacks.csv` are produced from exported LP relaxations solved by command-line CPLEX.
7. Relaxation callback vectors obtained: no. `relaxation_callback_snapshots.csv` records the limitation: the C++ callback uses `CPXcallbackgetrelaxationpoint` internally for separation, but there is no audited vector-output path yet.
8. Plain telemetry relaxation vectors obtained: no. Telemetry-only rows remain bound/node diagnostics; `plain_telemetry_snapshots.csv` labels vector extraction unavailable.
9. Remaining API limitation: add an audited callback vector export channel in `TailoredBCCplexApi.cpp` for selected relaxation callbacks and verify variable-name/index mapping before using callback vectors for cut design.
10. Root vectors: root LP rows report S/P/H/G, W_SP when present, reconstructed S*P, SP McCormick slack, top r/Y/e/h/q variables, and fractional z/p/d lists. Missing quantities are explicitly `not_available`; no zero filling is used.
11. Four-hour plain behavior: dominant K4 plain fixed-interval MIP at 14400s stayed open with LB `0.048398566621`, gap `0.0153397128496`, and gap-to-cutoff `0.0007539860437`.
12. Four-hour Tailored-BC behavior: dominant K4 static tailored at 14400s found an integer optimal fixed-interval improving solution with objective/LB/UB `0.0491015319884`, leaving gap-to-old-cutoff `0.0000510206763`. This is subproblem diagnostic evidence and a better incumbent candidate, not a full original-problem certificate by itself.
13. Future cut candidates: see `future_cut_candidates.md`. The immediate direction is denominator-aware low-Gini strengthening informed by the root LP S/P/H patterns.
14. Paper-core evidence boundaries: preserved. Plain, telemetry, alternative formulation, and snapshot rows are labelled benchmark/diagnostic only and are excluded from the `paper-gf-tailored-bc` ledger.
15. Next exact algorithmic step: verify and import the 14400s fixed-interval improving solution through the normal incumbent/verifier path, then rerun the full frontier with the improved UB and add audited callback-vector extraction for best-bound-node pattern analysis.

Key dominant K4 comparison:

| variant | 300s LB | 1200s LB | 3600s LB | 14400s LB | role |
| --- | ---: | ---: | ---: | ---: | --- |
| plain_fixed_interval_mip | 0.045204487708 | 0.048035857993 | 0.048035857993 | 0.048398566621 | benchmark_only |
| static_tailored_compact_bc | 0.048388162834 | 0.0487233640003 | 0.0487638722254 | 0.0491015319884 | fixed_interval_tailored_bc_subproblem |

Audit summary: all generated optimal/certificate claims pass `audit_bpc_certificate.py --fail-on-error`; paper-strict, alternative formulation, LP snapshot integrity, tailored callback, summary cleanup, thread fairness, objective convention, time-profile finalization, certificate source, model identity, and no-instance-special-case audits pass.
