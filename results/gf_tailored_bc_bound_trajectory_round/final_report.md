# GF Tailored BC Bound Trajectory Round

Starting point: `paper-gf-tailored-bc` remains the paper-facing algorithm. Plain CPLEX rows are benchmark-only.

## Theoretical Document

`docs/tailored_bc_convergence_and_exactness.md` now states fixed-interval coverage, valid relaxation lower-bound projection, callback B&C convergence conditions, and the benchmark-only role of plain CPLEX.

## Best-Bound Finalization

The CPLEX native time-limit parameter used by the callback API is `CPX_PARAM_TILIM` (`1039`) and it is set before `CPXmipopt`. This round also wires `CPXsetterminate` as an external CPLEX termination flag and samples `CPXCALLBACKINFO_BEST_BND`, incumbent, and node count from generic callback contexts.

Observed hard-leaf behavior is improved but not fully solved: on moderate low-Gini leaves the child worker may still need parent termination, but progress checkpoints now contain CPLEX-native valid best-bound trajectory points. Wrapper-finalized rows using those checkpoints remain noncertified diagnostics and are not merged into the paper ledger.

## Hard-Leaf Classification

| row | variant | budget | classification | checkpoint bound | checkpoints | LB | UB | gap |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| moderate_low_gini1_plain_10s | plain_fixed_interval | 10 | wrapper_timeout_no_valid_bound | False | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini1_callback_auto_10s | callback_auto | 10 | wrapper_timeout_with_checkpoint_bound | True | 20 | 0.0464098904991 | 0.0491525426647 | 0.055798785106791524 |
| moderate_low_gini2_plain_10s | plain_fixed_interval | 10 | wrapper_timeout_no_valid_bound | False | 0 | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_callback_auto_10s | callback_auto | 10 | wrapper_timeout_with_checkpoint_bound | True | 20 | 0.0489209015481 | 0.0491525426647 | 0.004712698551124121 |

## Plain CPLEX Vs Tailored

Plain CPLEX and plain fixed-interval rows are retained as benchmark-only. No benchmark bound is merged into paper evidence.

| row | variant | budget | status | LB | UB | gap |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| moderate_low_gini1_plain_10s | plain_fixed_interval | 10 | wrapper_timeout_noncertified | 0.0 | 0.0491525526647 | 1.0 |
| moderate_low_gini2_plain_10s | plain_fixed_interval | 10 | wrapper_timeout_noncertified | 0.0 | 0.0491525526647 | 1.0 |

## Controls

| row | status | certified | LB | UB | gap |
| --- | --- | --- | ---: | ---: | ---: |

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

The immediate bottleneck is now narrower: callback hard leaves can expose valid CPLEX-native best-bound checkpoints, but `CPXmipopt` may still fail to return a solver-final JSON under the requested time limit. The next engineering fix is to move callback workers behind a permanent production process boundary and treat checkpoint-bound rows as diagnostic unless the parent frontier explicitly audits and accepts checkpoint-bound evidence.
