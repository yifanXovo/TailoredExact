# GF Tailored BC Long-Run Convergence Round

Run profile: `otherhard60`.

Plain CPLEX and plain fixed-interval MIP rows are benchmark-only and are not imported into the Tailored-BC certificate ledger.

## Worker Boundary

Fixed-interval callback solves run as child workers. When a worker exceeds the parent hard wall-clock cap, the parent terminates the worker tree and preserves only CPLEX-native `CPXCALLBACKINFO_BEST_BND` progress rows as diagnostic lower-bound trajectory points. Heartbeat-only rows are not valid bounds.

## Targeted Optimization

This round adds opt-in `--tailored-bc-callback-separation-pacing bound-aware`, which keeps cheap valid rows active while pacing expensive subset/support/transfer separation until either a native best-bound improvement is observed or a configured relaxation-callback interval elapses. This is an exact-safe overhead optimization because it can only skip optional valid cuts, never reject feasible solutions.

## Hard-Leaf Trajectories

| row | variant | budget | status | class | valid checkpoints | LB | cutoff | gap_to_cutoff | improvements | plateau |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| moderate_seed3301_low_gini_1_plain_fixed_interval_cplex_benchmark_60s | plain_fixed_interval_cplex_benchmark | 60 | wrapper_timeout_no_valid_bound | plain_benchmark_no_valid_checkpoint | 0 | 0.0 | 0.0491525526647 | 1.0 | 0 | False |
| moderate_seed3301_low_gini_1_static_tailored_compact_bc_60s | static_tailored_compact_bc | 60 | wrapper_timeout_no_valid_bound | mixed_behavior | 0 | 0.0 | 0.0491525526647 | 1.0 | 0 | False |
| moderate_seed3301_low_gini_1_callback_tailored_bc_gini_auto_60s | callback_tailored_bc_gini_auto | 60 | wrapper_timeout_valid_checkpoint_bound | converging_bound_progress | 9 | 0.0463089837667 | 0.0491525526647 | 0.05785190684597284 | 9 | False |
| moderate_seed3301_low_gini_1_callback_tailored_bc_paced_60s | callback_tailored_bc_paced | 60 | wrapper_timeout_valid_checkpoint_bound | converging_bound_progress | 9 | 0.0463089837667 | 0.0491525526647 | 0.05785190684597284 | 9 | False |
| moderate_seed3301_low_gini_1_plain_fixed_interval_cplex_benchmark_300s | plain_fixed_interval_cplex_benchmark | 300 | wrapper_timeout_no_valid_bound | plain_benchmark_no_valid_checkpoint | 0 | 0.0 | 0.0491525526647 | 1.0 | 0 | False |
| moderate_seed3301_low_gini_1_static_tailored_compact_bc_300s | static_tailored_compact_bc | 300 | wrapper_timeout_no_valid_bound | mixed_behavior | 0 | 0.0 | 0.0491525526647 | 1.0 | 0 | False |
| moderate_seed3301_low_gini_1_callback_tailored_bc_gini_auto_300s | callback_tailored_bc_gini_auto | 300 | wrapper_timeout_valid_checkpoint_bound | converging_bound_progress | 11 | 0.048388162834 | 0.0491525526647 | 0.015551376058012196 | 11 | False |
| moderate_seed3301_low_gini_1_callback_tailored_bc_paced_300s | callback_tailored_bc_paced | 300 | wrapper_timeout_valid_checkpoint_bound | converging_bound_progress | 11 | 0.048388162834 | 0.0491525526647 | 0.015551376058012196 | 11 | False |
| moderate_seed3301_low_gini_2_plain_fixed_interval_cplex_benchmark_60s | plain_fixed_interval_cplex_benchmark | 60 | wrapper_timeout_no_valid_bound | plain_benchmark_no_valid_checkpoint | 0 | 0.0 | 0.0491525526647 | 1.0 | 0 | False |
| moderate_seed3301_low_gini_2_static_tailored_compact_bc_60s | static_tailored_compact_bc | 60 | wrapper_timeout_no_valid_bound | mixed_behavior | 0 | 0.0 | 0.0491525526647 | 1.0 | 0 | False |
| moderate_seed3301_low_gini_2_callback_tailored_bc_gini_auto_60s | callback_tailored_bc_gini_auto | 60 | wrapper_timeout_valid_checkpoint_bound | plateau_weak_bound | 9 | 0.0489209015481 | 0.0491525526647 | 0.0047129010405672234 | 3 | True |
| moderate_seed3301_low_gini_2_callback_tailored_bc_paced_60s | callback_tailored_bc_paced | 60 | wrapper_timeout_valid_checkpoint_bound | plateau_weak_bound | 9 | 0.0489209015481 | 0.0491525526647 | 0.0047129010405672234 | 3 | True |
| moderate_seed3301_low_gini_2_plain_fixed_interval_cplex_benchmark_300s | plain_fixed_interval_cplex_benchmark | 300 | wrapper_timeout_no_valid_bound | plain_benchmark_no_valid_checkpoint | 0 | 0.0 | 0.0491525526647 | 1.0 | 0 | False |
| moderate_seed3301_low_gini_2_static_tailored_compact_bc_300s | static_tailored_compact_bc | 300 | wrapper_timeout_no_valid_bound | mixed_behavior | 0 | 0.0 | 0.0491525526647 | 1.0 | 0 | False |
| moderate_seed3301_low_gini_2_callback_tailored_bc_gini_auto_300s | callback_tailored_bc_gini_auto | 300 | wrapper_timeout_valid_checkpoint_bound | plateau_weak_bound | 11 | 0.0489209015481 | 0.0491525526647 | 0.0047129010405672234 | 1 | True |
| moderate_seed3301_low_gini_2_callback_tailored_bc_paced_300s | callback_tailored_bc_paced | 300 | wrapper_timeout_valid_checkpoint_bound | plateau_weak_bound | 11 | 0.0489209015481 | 0.0491525526647 | 0.0047129010405672234 | 1 | True |
| moderate_seed3301_low_gini_1_callback_tailored_bc_paced_1200s | callback_tailored_bc_paced | 1200 | interval_unresolved_timeout | plateau_weak_bound | 20 | 0.048388162834 | 0.0491525526647 | 0.015551376058012196 | 11 | True |
| moderate_seed3301_low_gini_2_callback_tailored_bc_paced_1200s | callback_tailored_bc_paced | 1200 | interval_closed | closed_by_solver_final | 16 | 0.0491525526647 | 0.0491525526647 | 0.0 | 3 | False |
| moderate_seed3301_low_gini_1_callback_tailored_bc_paced_3600s | callback_tailored_bc_paced | 3600 | interval_unresolved_timeout | plateau_weak_bound | 21 | 0.048388162834 | 0.0491525526647 | 0.015551376058012196 | 11 | True |
| high_imbalance_seed3201_hard_plain_fixed_interval_cplex_benchmark_60s | plain_fixed_interval_cplex_benchmark | 60 | interval_closed | closed_by_solver_final | 0 | 2.44340319194 | 2.44340319194 | 0.0 | 0 | False |
| high_imbalance_seed3201_hard_callback_tailored_bc_paced_60s | callback_tailored_bc_paced | 60 | interval_closed | closed_by_solver_final | 1 | 2.44340319194 | 2.44340319194 | 0.0 | 1 | False |
| tight_T_seed3102_hard_plain_fixed_interval_cplex_benchmark_60s | plain_fixed_interval_cplex_benchmark | 60 | interval_closed | closed_by_solver_final | 0 | 0.600704436685 | 0.600704436685 | 0.0 | 0 | False |
| tight_T_seed3102_hard_callback_tailored_bc_paced_60s | callback_tailored_bc_paced | 60 | interval_closed | closed_by_solver_final | 1 | 0.600704436685 | 0.600704436685 | 0.0 | 1 | False |
| moderate_seed3302_hard_plain_fixed_interval_cplex_benchmark_60s | plain_fixed_interval_cplex_benchmark | 60 | interval_closed | closed_by_solver_final | 0 | 0.120018073519 | 0.120018073519 | 0.0 | 0 | False |
| moderate_seed3302_hard_callback_tailored_bc_paced_60s | callback_tailored_bc_paced | 60 | interval_closed | closed_by_solver_final | 1 | 0.120018073519 | 0.120018073519 | 0.0 | 1 | False |

## Variant Comparison

| target | best callback LB | best callback gap | plain/static comparison |
| --- | ---: | ---: | --- |
| high_imbalance_seed3201_hard | 2.44340319194 | 0.0 | interval_closed |
| moderate_seed3301_low_gini_1 | 0.048388162834 | 0.015551376058012196 | wrapper_timeout_no_valid_bound |
| moderate_seed3301_low_gini_2 | 0.0491525526647 | 0.0 | wrapper_timeout_no_valid_bound |
| moderate_seed3302_hard | 0.120018073519 | 0.0 | interval_closed |
| tight_T_seed3102_hard | 0.600704436685 | 0.0 | interval_closed |

## Controls

| row | status | certified | LB | UB | gap |
| --- | --- | --- | ---: | ---: | ---: |
| test_certificate_basis | diagnostic_passed | False | 0.0 | 0.493696053863 | 1.0 |
| test_option_consistency | diagnostic_complete | False | 0.0 | 0.493696053863 | 1.0 |
| test_callback_smoke | diagnostic_passed | False | 0.0 | 0.493696053863 | 1.0 |
| test_branch_callback_smoke | diagnostic_passed | False | 0.0 | 0.493696053863 | 1.0 |
| control_v12_m1_tailored_60s | wrapper_timeout_valid_checkpoint_bound | False | 0.357200583208 | 0.0 | 1.0 |
| control_v12_m2_tailored_60s | wrapper_timeout_valid_checkpoint_bound | False | 0.651671657614 | 0.0 | 1.0 |
| control_high_imbalance_seed3202_tailored_60s | wrapper_timeout_valid_checkpoint_bound | False | 1.5933718053 | 0.0 | 1.0 |
| control_tight_T_seed3101_tailored_60s | wrapper_timeout_valid_checkpoint_bound | False | 0.0575543995845 | 0.0 | 1.0 |

## Audits

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

## Conclusions

Main bottleneck after this round: `plateau_weak_bound`.

Callback hard leaves produced valid CPLEX-native bound trajectories on 14 callback rows.
The paced optimization was evaluated on 10 rows.

Rows synthesized from wrapper checkpoints remain diagnostic-only unless a future parent-ledger rule explicitly audits and accepts checkpoint-bound evidence.

## Required Answers

1. Do callback hard leaves now always produce valid CPLEX-native bound trajectories?

   For the tested callback hard-leaf rows, yes: every callback hard-leaf diagnostic row in this package has either solver-final fixed-interval status or valid CPLEX-native checkpoint trajectory rows. Heartbeat-only rows are not counted as valid bounds.

2. Which hard leaves show converging bound progress?

   `moderate_seed3301_low_gini_1` shows converging progress from 60s to 300s, improving from `0.0463089837667` to `0.048388162834`. It then plateaus at 1200s and 3600s. The short `high_imbalance_seed3201_hard`, `tight_T_seed3102_hard`, and `moderate_seed3302_hard` fixed-interval rows close rather than expose long convergence behavior.

3. Which hard leaves plateau?

   `moderate_seed3301_low_gini_1` plateaus at valid LB `0.048388162834` with gap-to-cutoff `0.015551376058012196` through the 1200s and 3600s paced callback rows. Earlier `moderate_seed3301_low_gini_2` checkpoint rows plateau near the cutoff, but the 1200s paced row closes solver-final.

4. Which variant dominates on each hard leaf?

   For the moderate low-Gini leaves, callback Tailored-BC dominates plain/static diagnostics because plain/static rows did not emit valid bounds under the worker caps. On the other hard leaves, both plain and callback fixed-interval variants close in the short run, so there is no decisive long-run dominance claim.

5. What is the strongest observed bottleneck?

   The bottleneck is weak low-Gini bound progress on `moderate_seed3301_low_gini_1`, not missing finalization. The solver returns noncertified timeout rows with valid best bounds at 1200s and 3600s, but the bound does not improve after the 300s value.

6. What optimization was implemented and what did it improve?

   The implemented optimization is `--tailored-bc-callback-separation-pacing bound-aware`, which throttles expensive optional separation families while preserving cheap valid cuts. It is exact-safe. It did not improve the final low-Gini bound in this package; it diagnosed that expensive separation overhead is not the remaining primary blocker for `moderate_seed3301_low_gini_1`.

7. What remains diagnostic-only and why?

   Wrapper-preserved checkpoint bounds remain diagnostic-only because the parent frontier does not yet have an audited merge rule for checkpoint-bound evidence. Plain CPLEX/plain fixed-interval MIP rows remain benchmark-only. Transfer/Benders-like rows remain diagnostic unless separately proved and audited.

8. Which controls remain certified?

   This package contains 60s diagnostic control reruns only, and they are not claimed as replacement certificates. They produced wrapper checkpoint diagnostics, not audited full-frontier final certificates. Previous certified controls are therefore not superseded by this package.

9. Are there any paper-core contamination risks?

   The audits report no contamination: plain CPLEX rows are benchmark-only, wrapper checkpoint rows are noncertifying diagnostics, BPC/route-mask/archive/known-UB evidence is not used, and all optimal claims in the raw directory pass `audit_bpc_certificate.py --fail-on-error`.
