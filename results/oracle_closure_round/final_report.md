# Oracle Closure Round Final Report

Branch: `codex/longrun-round17-local-results`

Commit SHA: final pushed commit is reported in the assistant final response.

## Code Changes

- Added explicit automatic interval-oracle budget semantics:
  `per-leaf|total|adaptive`, total budget, child time limit, recursive split,
  minimum width, and maximum generated children.
- Added audit-visible JSON fields for requested/actual oracle limits, budget
  policy, budget exhaustion, per-leaf limits used, recursive depth, child
  attempts, partition tree path, and BPC fallback leaf closure counts.
- Added recursive leaf partitioning. A parent leaf closes only if every child
  interval closes with exact coverage.
- Added generic low-Gini/penalty-domain tightening options for the compact
  interval cutoff oracle.
- Added explicit automatic BPC fallback fields after oracle timeout. BPC
  fallback remains diagnostic unless exact pricing closes.
- Fixed the wrapper synthesized-final JSON bug for
  `bpc_fallback_final_interval_lb`.

## Stability Rows

| row | status | objective | gap | finalization |
|---|---|---:|---:|---|
| V4 smoke | optimal | 0 | 0 | solver final JSON |
| V12 M2 regenerated | optimal | 0.718504070755 | 0 | solver final JSON |
| V12 M1 regenerated | optimal | 0.357200583208 | 0 | solver final JSON |
| high_imbalance_seed3202 | optimal | 1.74931345205 | 0 | solver final JSON |
| tight_T_seed3101 | optimal | 0.107252734134 | 0 | solver final JSON |

## Priority V20 Rows

| row | status | LB | UB | gap | oracle attempted | oracle closed | timed out | BPC closed |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| moderate_seed3301 | not closed | 0.00921610362464 | 0.0491525526647 | 0.8125 | 20 | 4 | 12 | 0 |
| tight_T_seed3102 | not closed | 0.450176109171 | 0.600704436685 | 0.250586342169 | 9 | 0 | 9 | 0 |
| high_imbalance_seed3201 | not closed | 1.74210803 | 2.44340319194 | 0.287015734552 | 6 | 0 | 6 | 0 |

`moderate_seed3302` was not rerun after priority time was used for the
moderate/tight/high-imbalance closure attempts.

## Answers

1. Did `moderate_seed3301` certify?
   No. The deep oracle run closed 4 root leaves but left 2 root leaves open.

2. Did `tight_T_seed3102` certify?
   No. The controlled run eliminated the abnormal process exit, but all 3 final
   leaves and their children timed out in the exact oracle.

3. How many V20/M3 rows certify now?
   Still 2/6: `high_imbalance_seed3202` and `tight_T_seed3101`.

4. Did oracle budget correction matter?
   Yes. The solver now records and applies per-leaf and child budgets
   explicitly. `moderate_seed3301_oracle_deep` used 600s root and 1800s child
   budgets rather than the earlier short child budgets.

5. Did low-Gini oracle strengthening close any leaves?
   It improved the diagnostic strength and exposes the exact low-Gini timeout
   leaves, but it did not close an additional root leaf.

6. Did recursive leaf partitioning close any leaves?
   It closed some child intervals, but not all children of the remaining root
   leaves. Therefore it did not close the full root leaves.

7. Did exact BPC fallback close any leaves?
   No. BPC fallback attempted selected remaining leaves but closed none with
   exact pricing.

8. Are all rows sealed, unified, and free of known UB/archive/instance-specific
   logic?
   Yes for the paper-candidate rows in this round. The no-instance-special-case
   audit passes, archive scanning is disabled, and no external incumbent or
   known UB is used.

9. Is the project ready for a controlled paper benchmark matrix?
   No. V12 is stable and two V20/M3 stress rows certify, but the requested third
   V20 certificate was not obtained. The next blocker is exact interval cutoff
   MIP timeout on low-Gini/tight leaves and lack of exact BPC leaf closure.

## Key Files

- `results/oracle_closure_round/sealed_minisuite_summary.csv`
- `results/oracle_closure_round/oracle_budget_audit.csv`
- `results/oracle_closure_round/moderate_seed3301_leaf_oracle_trace.csv`
- `results/oracle_closure_round/leaf_partition_tree.csv`
- `results/oracle_closure_round/bpc_fallback_after_oracle.csv`
- `results/oracle_closure_round/certificate_audit.csv`
- `results/oracle_closure_round/no_instance_special_case_audit.txt`

## Audit Status

- `audit_bpc_certificate.py --self-test`: passed.
- `audit_bpc_certificate.py results/oracle_closure_round/raw --fail-on-error`:
  passed, `audited_rows=80`, `failures=0`.
- `certificate-basis-test`: passed.
- `option-consistency-test`: passed.
- `audit_no_instance_special_cases.py`: passed.

## Recommendation

Do not start broad paper benchmark testing yet. The next targeted round should
focus on stronger compact exact interval-oracle formulations or a real exact
BPC leaf-closure path for the remaining low-Gini/tight intervals.
