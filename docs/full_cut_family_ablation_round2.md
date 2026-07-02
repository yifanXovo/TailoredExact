# Full Cut-Family Ablation Round 2

The round produced an audited cut-family activity table at:

`results/gf_compact_bc_strengthening_round2/full_cut_family_ablation.csv`.

This table is truthful about actual rows added and effective families, but it is
not a fully exhaustive long-budget matrix. It includes the controlled rows and
interval child activity available in this run. `no_new_cuts` semantics are
audited by `scripts/audit_gf_compact_bc_summary.py`; disabled families are not
reported as effective.

The strongest observed activity in this round came from static compact-BC
families and dynamic visit-inventory linking on the interval smoke row. Dynamic
root cuts did not close the remaining V20 low-Gini leaves.

