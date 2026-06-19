# Portfolio Certificate Audit

Date: 2026-06-14.

This audit covers every certified target-result artifact used in the portfolio comparison. Compact fallback and plain CPLEX certificates are original-problem certificates when their MIP gap closes, but they are not BPC certificates.

| Label | Scope | Status | Objective | Gap | Audit certified | File |
|---|---|---|---:|---:|---|---|
| V10_M2_average_BPC | original_bpc | optimal | 0.463263009179 | 0 | true | `results\dyn4_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json` |
| V10_M1_average_BPC | original_bpc | optimal | 0.49262512358 | 0 | true | `results\closure3600_v10_m1_average_strong_bpcseed.json` |
| V12_M1_average_BPC | original_bpc | optimal | 0.690938574743 | 0 | true | `results\closure7200_v12_m1_average_strong_bpcseed.json` |
| V10_M1_average_compact | original_compact | optimal | 0.49262512358 | 0 | true | `results\alt_strengthened_v10_m1_average_300s.json` |
| V10_M2_low_compact | original_compact | optimal | 0.824301313135 | 0 | true | `results\alt_strengthened_v10_m2_low_1200s.json` |
| V12_M1_average_compact | original_compact | optimal | 0.690938574743 | 0 | true | `results\alt_strengthened_v12_m1_average_300s.json` |
| V10_M1_average_plain_cplex | plain_cplex | optimal | 0.49262512358 | 0 | true | `results\current2_cplex_v10_m1_average_plain_300s.json` |
| V12_M1_average_plain_cplex | plain_cplex | optimal | 0.690938574743 | 0 | true | `results\current2_cplex_v12_m1_average_plain_300s.json` |

All listed certified rows satisfy `status=optimal`, `gap=0`, `lower_bound=upper_bound=objective`, and `verifier_passed=true`. BPC rows additionally require closed frontier ledgers with no unresolved intervals, no invalid bound intervals, and no open nodes.
