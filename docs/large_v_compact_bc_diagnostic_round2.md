# Large-V Compact-BC Diagnostic Round 2

Rows:

- `V50_M3_moderate_seed5101.txt`
- `V50_M3_high_imbalance_seed5201.txt`
- `V100_M5_moderate_seed6101.txt`
- `V100_M5_high_imbalance_seed6201.txt`

All large compact-BC diagnostics have final JSON. V50 rows terminate as
`model_size_limit` through the solver emergency finalizer. V100 rows terminate
as wrapper-finalized `model_size_limit` rows after native access violation.

No large-V row is certified. Large-V remains a model-size/scalability
diagnostic, not current paper evidence.

CSV:
`results/gf_compact_bc_strengthening_round2/large_v_diagnostic_summary.csv`.

