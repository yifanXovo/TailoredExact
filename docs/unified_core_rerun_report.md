# Unified Core Rerun Report

Command template:

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-gf-bpc-core `
  --paper-run-sealed true `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <budget> --out <raw.json>
```

Key outcomes are summarized in
`results/paper_core_realignment_round/unified_core_summary.csv`.

Findings:

- `tight_T_seed3101` remains certified by relaxation-only full-frontier evidence.
- `V12 M1`, `V12 M2`, `high_imbalance_seed3202`, and `moderate_seed3301` do not
  certify under the realigned core budgets used here.
- No paper-core row uses interval oracle evidence.
- No paper-core row uses complete route-mask enumeration as certificate evidence.
- BPC was not reached from full-frontier scheduling before time-limit/reserve in
  these rows; direct leaf validation was run separately.

This is an intentional semantic cleanup: previous certificates that depended on
route-mask/oracle portfolio evidence are no longer counted as BPC-core success.
