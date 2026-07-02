# GF Compact BC Experiment Protocol

Use `results/gf_compact_bc_round/` for the initial transition round and
`results/gf_compact_bc_strengthening_round/` for the single-thread
strengthening round.

Required checks:

1. `build\ExactEBRP.exe --method certificate-basis-test ...`
2. `build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-gf-compact-bc ...`
3. `D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test`
4. `D:\msys64\ucrt64\bin\python.exe scripts\test_compact_handling_convention.py`
5. A sealed `paper-gf-compact-bc` smoke or mini-suite row.
6. A same-budget plain CPLEX benchmark row, classified as benchmark-only.

Paper-candidate rows must use one template, varying only input, output, time,
and thread budgets.  They must not pass known UB files, external incumbent
files, focus ranges, imported bounds, BPC flags, or archive-scanning options.

For the controlled paper comparison, use:

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-gf-compact-bc `
  --paper-run-sealed true `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <seconds> --threads 1 --mip-threads 1 `
  --compact-bc-threads 1 `
  --compact-bc-cut-profile balanced `
  --compact-bc-root-cut-rounds <N> `
  --out results\gf_compact_bc_strengthening_round\raw\<row>.json
```

Plain compact CPLEX comparisons must be benchmark-only and single-thread fair:

```powershell
build\ExactEBRP.exe --method cplex --plain-baseline true `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <seconds> --threads 1 --cplex-threads 1 `
  --out results\gf_compact_bc_strengthening_round\raw\cplex1_<row>.json
```

Summaries are generated with:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\summarize_gf_compact_bc_round.py `
  --raw-dir results\gf_compact_bc_round\raw `
  --out-dir results\gf_compact_bc_round
```

Audit all final JSONs with:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py `
  results\gf_compact_bc_round\raw `
  --csv-out results\gf_compact_bc_round\certificate_audit.csv `
  --fail-on-error --require-progress-finals results\gf_compact_bc_round\raw
```

Strengthening-round audits additionally run:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_gf_compact_bc_summary.py `
  --results results\gf_compact_bc_strengthening_round `
  --out results\gf_compact_bc_strengthening_round\summary_cleanup_audit.csv

D:\msys64\ucrt64\bin\python.exe scripts\audit_objective_convention.py `
  --results results\gf_compact_bc_strengthening_round `
  --out results\gf_compact_bc_strengthening_round\objective_convention_audit.csv
```

Rows with `thread_fairness_class != one_thread_fair` are diagnostic sensitivity
rows, not fair controlled benchmark evidence.
## Round 2 Controlled Protocol

Controlled compact-BC rows use:

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-gf-compact-bc `
  --paper-run-sealed true `
  --mip-threads 1 --compact-bc-threads 1 `
  --compact-bc-cut-profile balanced `
  --compact-bc-root-cut-rounds 1 `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <budget> --out <raw.json>
```

Plain CPLEX benchmark rows use `--method cplex --plain-baseline
--cplex-threads 1` and are benchmark-only. The thread fairness audit must pass
before any row is included in controlled comparison tables.

## Time-Profile Round

Use `results/gf_compact_bc_timeprofile_round/` for time-profile evidence.
Controlled rows must emit:

- `time_budget_seconds`;
- `actual_runtime_seconds`;
- `thread_fairness_class`;
- `progress_log` and `gap_trajectory_available` when the frontier loop starts.

The current helper is:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\run_gf_compact_bc_timeprofile.py `
  --mode priority --include-cplex --include-large
```

Rows interrupted externally are wrapper-finalized as noncertified artifacts
using the latest safe progress checkpoint only.

## Effectiveness Attribution Round

Use `results/gf_compact_bc_effectiveness_round/` for attribution and repaired
time-profile evidence:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\run_gf_compact_bc_effectiveness_round.py --copy
D:\msys64\ucrt64\bin\python.exe scripts\audit_certificate_sources.py --results results\gf_compact_bc_effectiveness_round --out results\gf_compact_bc_effectiveness_round\certificate_source_audit.csv
D:\msys64\ucrt64\bin\python.exe scripts\audit_timeprofile_finalization.py --results results\gf_compact_bc_effectiveness_round --out results\gf_compact_bc_effectiveness_round\timeprofile_finalization_audit.csv
D:\msys64\ucrt64\bin\python.exe scripts\audit_compact_bc_effectiveness.py --results results\gf_compact_bc_effectiveness_round --out results\gf_compact_bc_effectiveness_round\compact_bc_effectiveness_audit.csv
```

The effectiveness package should be read as attribution evidence. It must not be
used to imply Compact-BC dominance when relaxation/frontier certificates close
the row first.
