# BPC Leaf Validation Report

Diagnostic harness:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\run_bpc_leaf_validation.py `
  --exe build\ExactEBRP.exe `
  --instance <instance> `
  --interval-csv <frontier.intervals.csv> `
  --out-dir <diagnostic-dir> `
  --time-limit 120 --max-leaves <N>
```

Outputs:

- `results/paper_core_realignment_round/bpc_leaf_validation_summary.csv`
- `results/paper_core_realignment_round/bpc_pricing_profile.csv`

Observed bottleneck:

- BPC leaf runs do start and call pricing.
- No nontrivial leaf closed in this round.
- V12 M2 leaf: exact pricing consumed the diagnostic budget and left negative
  reduced cost in the baseline run.
- After BPC preset improvements, the V12 leaf generated many more columns, but
  still did not obtain exact pricing closure.
- V20 moderate/high-imbalance leaves remain dominated by pricing state growth.

Conclusion: BPC is valid as an exact fallback in theorem form, but current
implementation evidence does not support claiming it as an empirically effective
closure path yet.
