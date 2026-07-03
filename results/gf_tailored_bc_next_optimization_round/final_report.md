# GF Tailored BC Next Optimization Round

Starting commit: `793fa151265d1092dc4e9479decade1659605e5e`.

Paper-facing line remains `paper-gf-tailored-bc`: Gini-frontier decomposition, valid interval relaxation fathoming, CPLEX-managed tailored branch-and-cut fixed-interval subproblems, and full frontier ledger certification.

## Implemented

- Added callback heartbeat progress CSVs for fixed-interval callback solves.
- Added explicit compact-BC best-bound availability/fail-reason fields.
- Added timeout/plateau fields in final JSON.
- Added Gini subset-envelope callback de-duplication and allowed later-node separation up to the configured global cap.
- Tested CPLEX callback wall-clock abort. The generic abort call does not stop the moderate low-Gini leaf in this build; wrapper-managed finalization remains required for those rows.

## Fair Baseline

| row | status | certified | LB | UB | gap |
| --- | --- | --- | --- | --- | --- |
| fair_high_imbalance_seed3202_tailored_60s | wrapper_timeout_noncertified | False | 0.0 | 1.74931344205 | 1.0 |
| fair_tight_T_seed3101_tailored_60s | wrapper_timeout_noncertified | False | 0.0 | 0.107252724134 | 1.0 |
| fair_v12_m1_tailored_60s | optimal | True | 0.357200583208 | 0.357200583208 | 0 |
| fair_v12_m2_tailored_60s | wrapper_timeout_noncertified | False | 0.0 | 0.718504060755 | 1.0 |
| fair_v4_smoke_tailored_60s | optimal | True | 0 | 0 | 0 |

## Hard Leaf Classification

| row | status | checkpoints | best bound available | classification | evidence |
| --- | --- | ---: | --- | --- | --- |
| moderate_low_gini1_callback_60s | wrapper_timeout_noncertified | 15 | False | no_valid_bound_emitted | native_solver_exceeded_time_limit_before_final_best_bound_api |
| moderate_low_gini1_callback_auto_10s | wrapper_timeout_noncertified | 26 | False | no_valid_bound_emitted | native_exit_before_solver_final_best_bound_api |
| moderate_low_gini1_callback_auto_60s | wrapper_timeout_noncertified | 12 | False | no_valid_bound_emitted | native_exit_before_solver_final_best_bound_api |
| moderate_low_gini1_plain_60s | wrapper_timeout_noncertified | 0 | False | no_valid_bound_emitted | native_exit_before_solver_final_best_bound_api |
| moderate_low_gini1_static_tailored_60s | wrapper_timeout_noncertified | 0 | False | no_valid_bound_emitted | native_exit_before_solver_final_best_bound_api |
| moderate_low_gini2_callback_auto_60s | wrapper_timeout_noncertified | 12 | False | no_valid_bound_emitted | native_exit_before_solver_final_best_bound_api |

## Audit Summary

| audit | return code | passed |
| --- | ---: | --- |
| audit_bpc_self_test | 0 | True |
| audit_bpc_certificate | 0 | True |
| audit_tailored_bc_callback_round | 0 | True |
| audit_gf_compact_bc_summary | 0 | True |
| audit_thread_fairness | 0 | True |
| audit_objective_convention | 0 | True |
| audit_timeprofile_finalization | 0 | True |
| audit_certificate_sources | 0 | True |
| audit_no_instance_special_cases | 0 | True |

## Boundary Status

No BPC, route-mask enumeration, archive scanning, known UB, external incumbent JSON, focus-only evidence, or plain CPLEX benchmark bound is used as paper-core certificate evidence in this round.

Transfer-network/Benders-like cuts remain diagnostic-only; no proof-gated promotion occurred.

## Diagnosis

Moderate low-Gini hard leaves are not merely missing a final JSON anymore: heartbeat checkpoints show active relaxation/branch callbacks and a small number of valid user cuts, but no valid CPLEX best bound is exposed before wrapper termination. The present bottleneck is native callback solve finalization/bound extraction on hard low-Gini fixed intervals, plus weak bound progress from the currently active cut families.

Next step: run hard leaves through a dedicated out-of-process worker that owns the CPLEX callback solve and writes wrapper-final JSON on timeout, or switch hard-leaf long runs to the command-file/static tailored path when callback finalization is required for reliable wall-clock control.
