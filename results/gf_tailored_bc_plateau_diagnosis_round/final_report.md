# Tailored-BC Low-Gini Plateau Diagnosis Final Report

Status label: `low_gini_plateau_improved_by_local_centering`.

## Main Findings

1. The low-Gini plateau was not a stale-checkpoint artifact. The bound-trace audit passed on all 46 plateau rows, and final JSON lower bounds preserve the best valid CPLEX-native checkpoint bound.
2. The previous plateau on `moderate_seed3301` low_gini_1 was a real hard-leaf root/bound weakness. The callback infrastructure with callback cut families disabled reached only `0.0457974538606` at 300s; cheap cuts reached `0.0468586008099`; the earlier full low-Gini/full profiles plateaued at `0.048388162834`.
3. The new station-wise local-centering cuts materially improved the hard leaf. `low_gini_1` reached `0.0487233640003` by 1200s and held that bound at 3600s, reducing the gap to cutoff from the plain 3600s gap `0.0174261734593` to `0.00873176755141`.
4. `low_gini_2` remains much easier: the non-local full/low-Gini profiles closed it at 300s, while local-centering variants improved but did not close it at the same budget.
5. Diagnostic S-bucket rows closed selected bucket diagnostics quickly, but they are not used as paper-core evidence because the parent leaf is not yet partitioned and merged across exact S-domain coverage.

## Mechanisms Implemented

- `--tailored-bc-callback-cut-profile off|full|cheap|low-gini|local-centering|subset-only|transfer-only|support-only`
- `--tailored-bc-local-centering true|false`
- Static and callback station-wise local-centering rows:
  - `V r_i - S <= sum_{j != i} h_ij`
  - `S - V r_i <= sum_{j != i} h_ij`
- Parent/full-frontier aggregation for the new `local_centering` family.
- Plateau-specific audits for bound traces, model identity, S-bucket coverage, and low-Gini cut validity.

## Numerical Comparison

| Leaf | Variant | Budget | LB | Gap |
|---|---:|---:|---:|---:|
| low_gini_1 | callback_no_cuts | 300s | 0.0457974538606 | 0.0682588924123 |
| low_gini_1 | callback_cheap_cuts | 300s | 0.0468586008099 | 0.0466700452057 |
| low_gini_1 | plain_fixed_interval_mip | 3600s | 0.048296011756 | 0.0174261734593 |
| low_gini_1 | callback_full_gini_auto | 300s | 0.048388162834 | 0.0155513760572 |
| low_gini_1 | callback_local_centering | 1200s | 0.0487233640003 | 0.00873176755151 |
| low_gini_1 | callback_full_paced | 3600s | 0.0487233640003 | 0.00873176755141 |
| low_gini_2 | callback_low_gini_cuts | 300s | 0.0491525526647 | 0 |
| low_gini_2 | callback_full_gini_auto | 300s | 0.0491525526647 | 0 |

## Safety Status

The new local-centering rows are paper-safe under the compact model convention because `sum_j h_ij` upper-bounds `sum_j |r_i-r_j|`, which in turn is at least both `V r_i - S` and `S - V r_i`. S-bucket diagnostics remain diagnostic-only. Plain fixed-interval MIP rows are benchmark-only.

No BPC, archive scanning, known UB injection, external incumbent JSON, route-mask enumeration certificate, or diagnostic S-bucket evidence is used as paper-core proof in this round.

## Audits

All executed audits passed:

- `audit_bpc_certificate.py --self-test`
- `audit_bpc_certificate.py results/gf_tailored_bc_plateau_diagnosis_round/raw --fail-on-error`
- `audit_tailored_bc_callback_round.py`
- `audit_gf_compact_bc_summary.py`
- `audit_thread_fairness.py`
- `audit_objective_convention.py`
- `audit_plateau_bound_trace.py`
- `audit_model_identity.py`
- `audit_s_bucket_coverage.py`
- `audit_low_gini_cut_validity.py`
- `audit_no_instance_special_cases.py`

`audit_timeprofile_finalization.py` and `audit_certificate_sources.py` had zero applicable full-row rows in this interval-only result tree and returned success.

## Remaining Bottleneck

The principal blocker remains `moderate_seed3301` low_gini_1. Local centering improved the bound substantially but did not close the leaf. The next targeted mechanism should strengthen denominator/objective interaction beyond the current linear estimators, likely with exact S-partition merge support or stronger low-Gini branch/split logic that can be certified at the parent-leaf ledger level.
