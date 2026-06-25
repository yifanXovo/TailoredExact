# Generated Variant Round Commands

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\generate_capacity_inventory_variants.py --variants-per-base 3 --seed-base 260626 --out-dir reference\generated_variants
```

For each row in `reference/generated_variants/manifest.csv`:

```powershell
build\ExactEBRP.exe --method primal-heuristic --algorithm-preset paper-bpc-core --input <output_path> --lambda 0.15 --T 3600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 3 --primal-heuristic-runs 6 --export-incumbent results\generated_variant_round\incumbents\<variant>_heuristic.json --out results\generated_variant_round\raw\<variant>_heuristic.json
```

For the first ten variants:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input <output_path> --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --primal-heuristic none --incumbent-json results\generated_variant_round\incumbents\<variant>_heuristic.json --incumbent-format route_json --progress-log results\generated_variant_round\progress\<variant>_paper_core_60s.csv --progress-interval-seconds 30 --out results\generated_variant_round\raw\<variant>_paper_core_60s.json
```

Audit:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\generated_variant_round\raw --csv-out results\generated_variant_round\certificate_audit.csv --fail-on-error
```
