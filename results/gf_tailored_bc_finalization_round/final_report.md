# GF Tailored BC Finalization Round

Starting point: `paper-gf-tailored-bc` remains the paper-facing algorithm. Plain CPLEX rows are benchmark-only.

## Theoretical Document

`docs/tailored_bc_convergence_and_exactness.md` now states fixed-interval coverage, valid relaxation lower-bound projection, callback B&C convergence conditions, and the benchmark-only role of plain CPLEX.

## Best-Bound Finalization

The CPLEX native time-limit parameter used by the callback API is `CPX_PARAM_TILIM` (`1039`) and it is set before `CPXmipopt`. The code now records the parameter id, requested time, and set return code in result JSON. Callback loops also check the same wall deadline and request `CPXcallbackabort` from inside long separation/candidate paths.

Observed hard-leaf behavior remains partially blocked: the moderate low-Gini callback leaf continues relaxation/branch callbacks past the requested native limit and does not expose a valid CPLEX best bound before parent termination. The dedicated worker/parent wrapper therefore writes noncertified final JSON from heartbeat checkpoints.

## Hard-Leaf Classification

| row | variant | budget | classification | checkpoints | abort requests | LB | UB | gap |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| moderate_low_gini1_plain_60s | plain_fixed_interval | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini1_static_60s | static_tailored | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini1_callback_off_60s | callback_no_gini | 60 | wrapper_timeout_no_valid_bound | 10 | 0 | 0.0 | 0.0491525426647 | 1.0 |
| moderate_low_gini1_callback_auto_60s | callback_auto | 60 | wrapper_timeout_no_valid_bound | 1 | 0 | 0.0 | 0.0491525426647 | 1.0 |
| moderate_low_gini1_plain_300s | plain_fixed_interval | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini1_static_300s | static_tailored | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini1_callback_off_300s | callback_no_gini | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini1_callback_auto_300s | callback_auto | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini1_callback_auto_1200s | callback_auto | 1200 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_plain_60s | plain_fixed_interval | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_static_60s | static_tailored | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_callback_off_60s | callback_no_gini | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_callback_auto_60s | callback_auto | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_plain_300s | plain_fixed_interval | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_static_300s | static_tailored | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_callback_off_300s | callback_no_gini | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_callback_auto_300s | callback_auto | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_callback_auto_1200s | callback_auto | 1200 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.0491525526647 | 1.0 |
| high_imbalance_seed3201_hard_plain_60s | plain_fixed_interval | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 2.44340319194 | 1.0 |
| high_imbalance_seed3201_hard_static_60s | static_tailored | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 2.44340319194 | 1.0 |
| high_imbalance_seed3201_hard_callback_off_60s | callback_no_gini | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 2.44340319194 | 1.0 |
| high_imbalance_seed3201_hard_callback_auto_60s | callback_auto | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 2.44340319194 | 1.0 |
| high_imbalance_seed3201_hard_plain_300s | plain_fixed_interval | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 2.44340319194 | 1.0 |
| high_imbalance_seed3201_hard_static_300s | static_tailored | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 2.44340319194 | 1.0 |
| high_imbalance_seed3201_hard_callback_off_300s | callback_no_gini | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 2.44340319194 | 1.0 |
| high_imbalance_seed3201_hard_callback_auto_300s | callback_auto | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 2.44340319194 | 1.0 |
| tight_T_seed3102_hard_plain_60s | plain_fixed_interval | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.600704436685 | 1.0 |
| tight_T_seed3102_hard_static_60s | static_tailored | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.600704436685 | 1.0 |
| tight_T_seed3102_hard_callback_off_60s | callback_no_gini | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.600704436685 | 1.0 |
| tight_T_seed3102_hard_callback_auto_60s | callback_auto | 60 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.600704436685 | 1.0 |
| tight_T_seed3102_hard_plain_300s | plain_fixed_interval | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.600704436685 | 1.0 |
| tight_T_seed3102_hard_static_300s | static_tailored | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.600704436685 | 1.0 |
| tight_T_seed3102_hard_callback_off_300s | callback_no_gini | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.600704436685 | 1.0 |
| tight_T_seed3102_hard_callback_auto_300s | callback_auto | 300 | wrapper_timeout_no_valid_bound | 0 | 0 | 0.0 | 0.600704436685 | 1.0 |

## Plain CPLEX Vs Tailored

Plain CPLEX and plain fixed-interval rows are retained as benchmark-only. No benchmark bound is merged into paper evidence.

| row | variant | budget | status | LB | UB | gap |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| control_v12_m1_cplex_60s | cplex | 60 | not_certified | 0.34202602197 | 0.357200583208 | 0.0424819049905 |
| control_v12_m2_cplex_60s | cplex | 60 | not_certified | 0.56364750056 | 0.748207757399 | 0.246669798614 |
| control_high_imbalance_seed3202_cplex_60s | cplex | 60 | not_certified | 1.0096334603 | 5.04160189596 | 0.799739550814 |
| control_tight_T_seed3101_cplex_60s | cplex | 60 | not_certified | 0.013330322812 | 1.12858569854 | 0.988188470907 |
| moderate_low_gini1_plain_60s | plain_fixed_interval | 60 | wrapper_timeout_noncertified | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini1_plain_300s | plain_fixed_interval | 300 | wrapper_timeout_noncertified | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_plain_60s | plain_fixed_interval | 60 | wrapper_timeout_noncertified | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_plain_300s | plain_fixed_interval | 300 | wrapper_timeout_noncertified | 0.0 | 0.0491525526647 | 1.0 |
| high_imbalance_seed3201_hard_plain_60s | plain_fixed_interval | 60 | wrapper_timeout_noncertified | 0.0 | 2.44340319194 | 1.0 |
| high_imbalance_seed3201_hard_plain_300s | plain_fixed_interval | 300 | wrapper_timeout_noncertified | 0.0 | 2.44340319194 | 1.0 |
| tight_T_seed3102_hard_plain_60s | plain_fixed_interval | 60 | wrapper_timeout_noncertified | 0.0 | 0.600704436685 | 1.0 |
| tight_T_seed3102_hard_plain_300s | plain_fixed_interval | 300 | wrapper_timeout_noncertified | 0.0 | 0.600704436685 | 1.0 |

## Controls

| row | status | certified | LB | UB | gap |
| --- | --- | --- | ---: | ---: | ---: |
| control_v12_m1_tailored_60s | wrapper_timeout_noncertified | False | 0.0 | 0.357200573208 | 1.0 |
| control_v12_m1_cplex_60s | not_certified | False | 0.34202602197 | 0.357200583208 | 0.0424819049905 |
| control_v12_m2_tailored_60s | wrapper_timeout_noncertified | False | 0.0 | 0.718504060755 | 1.0 |
| control_v12_m2_cplex_60s | not_certified | False | 0.56364750056 | 0.748207757399 | 0.246669798614 |
| control_high_imbalance_seed3202_tailored_60s | wrapper_timeout_noncertified | False | 0.0 | 1.74931344205 | 1.0 |
| control_high_imbalance_seed3202_cplex_60s | not_certified | False | 1.0096334603 | 5.04160189596 | 0.799739550814 |
| control_tight_T_seed3101_tailored_60s | wrapper_timeout_noncertified | False | 0.0 | 0.107252724134 | 1.0 |
| control_tight_T_seed3101_cplex_60s | not_certified | False | 0.013330322812 | 1.12858569854 | 0.988188470907 |

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

## Cut Boundary

Paper-core callback rows use only documented valid rows. Transfer-network/Benders-like cuts remain diagnostic-only and were not promoted.

## Next Bottleneck

The immediate bottleneck is the CPLEX generic-callback process boundary on moderate low-Gini leaves: native `CPXmipopt` does not return in time despite `CPX_PARAM_TILIM` and callback abort requests, so no valid best bound can be extracted. The concrete next design is a stricter dedicated callback worker executable/process boundary that can preserve CPLEX finalization data if CPLEX returns, and otherwise reports only noncertified diagnostics.
