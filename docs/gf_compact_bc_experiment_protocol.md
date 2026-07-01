# GF Compact BC Experiment Protocol

Use `results/gf_compact_bc_round/` for this transition round.

Required checks:

1. `build\ExactEBRP.exe --method certificate-basis-test ...`
2. `build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-gf-compact-bc ...`
3. `D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test`
4. `D:\msys64\ucrt64\bin\python.exe scripts\test_compact_handling_convention.py`
5. A sealed `paper-gf-compact-bc` smoke or mini-suite row.
6. A same-budget plain CPLEX benchmark row, classified as benchmark-only.

Paper-candidate rows must use one template, varying only input, output, time,
and thread budgets.  They must not pass known UB files, external incumbent
files, focus ranges, imported bounds, or archive-scanning options.

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
