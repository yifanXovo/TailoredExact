# Compact-BC Time-Profile Benchmark Protocol

`results/gf_compact_bc_timeprofile_round/` records the controlled time-profile
round for `paper-gf-compact-bc`.

The controlled exact rows use one compact-BC thread:

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-gf-compact-bc `
  --paper-run-sealed true `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <budget> --threads 1 --mip-threads 1 `
  --compact-bc-threads 1 `
  --compact-bc-cut-profile balanced `
  --compact-bc-root-cut-rounds <N> `
  --compact-bc-progress-interval 30 `
  --progress-log results\gf_compact_bc_timeprofile_round\progress_traces\<row>.progress.csv `
  --out results\gf_compact_bc_timeprofile_round\raw\<row>.json
```

Plain CPLEX comparisons use one thread and remain benchmark-only:

```powershell
build\ExactEBRP.exe --method cplex --plain-baseline `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <budget> --threads 1 --cplex-threads 1 `
  --out results\gf_compact_bc_timeprofile_round\raw\cplex_<row>.json
```

The 300s rows are comparison points, not a certification requirement. Longer
rows are reported with their own `time_budget_seconds` and
`actual_runtime_seconds` fields.
