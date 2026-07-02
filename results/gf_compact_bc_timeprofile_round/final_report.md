# GF Compact-BC Time-Profile Round Final Report

## Answers

1. There is no hard requirement that V20 closes in 300s. 300s is a controlled
   comparison budget.
2. Certified V20 rows: `tight_T_seed3101` at 300s and
   `high_imbalance_seed3202` at a controlled one-thread 1200s static recovery
   row. No other V20 row certified in this round.
3. `moderate_seed3301` did not certify. Best solver-final row:
   LB `0.044391`, UB `0.0491525526647`, gap `0.096872947723`, two unresolved
   leaves.
4. Moderate gap trajectory did not improve in the interrupted dynamic rows; the
   useful evidence is the bounded static row and its two-leaf diagnosis.
5. Same-budget CPLEX comparison: compact-BC beats CPLEX on high-imbalance
   V20 and tight_T_seed3101 at 300s, but CPLEX is stronger on some interrupted
   compact-BC rows.
6. Dynamic root separation is implemented and audited, but hard V20 rows did
   not receive decisive dynamic cuts in this run.
7. Dynamic cuts did not improve final hard-leaf gaps enough to certify new V20
   rows.
8. The most useful current families remain the static compact-BC/domain
   strengthening families. The targeted ablation is not exhaustive.
9. V50/V100 diagnostics still show model-size/native-exit limitations; final
   JSON artifacts are present and noncertified.
10. The algorithm is not ready for broad benchmark claims. It is ready for
    continued controlled compact-BC strengthening and time-profile comparisons.

## Audit Status

- `audit_bpc_certificate.py --self-test`: pass.
- Certificate audit over raw JSONs: 49 rows, 0 failures.
- Summary cleanup audit: 49 rows, 0 failures.
- Thread fairness audit: 49 rows, 0 failures.
- Objective convention audit: 49 rows, 0 failures.
- No-instance-special-case audit: pass.

## Commit

Final commit SHA: pending at report generation time.
