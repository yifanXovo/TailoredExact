# Heuristic / Relaxation / Generated Variant Round Commands

## Repository State

- Start branch: `codex/longrun-round17-local-results`
- Start SHA: `a729494ed9a325e2835b38888b51fdbe06d9dfb3`

## Build

CMake was probed earlier in this workspace and was unavailable, so this fallback command was used:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
```

## Smoke / Guard Tests

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
build\ExactEBRP.exe --method certificate-basis-test --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\heuristic_relaxation_dataset_round\raw\certificate_basis_after_patch.json
build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\heuristic_relaxation_dataset_round\raw\option_consistency_after_guard_patch.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --progress-log results\heuristic_relaxation_dataset_round\progress\v4_paper_core_after_guard_patch_30s.csv --progress-interval-seconds 5 --out results\heuristic_relaxation_dataset_round\raw\v4_paper_core_after_guard_patch_30s.json
```

## V12 Heuristic and Paper-Core Checks

```powershell
build\ExactEBRP.exe --method primal-heuristic --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --primal-heuristic hga-tgbc --primal-heuristic-seconds 5 --primal-heuristic-runs 8 --export-incumbent results\heuristic_relaxation_dataset_round\incumbents\v12_m2_hga_tgbc_seeded_after_patch.json --out results\heuristic_relaxation_dataset_round\raw\v12_m2_primal_hga_tgbc_after_patch.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 120 --frontier-intervals 3 --progress-log results\heuristic_relaxation_dataset_round\progress\v12_m2_paper_core_hga_after_guard_patch_120s.csv --progress-interval-seconds 30 --out results\heuristic_relaxation_dataset_round\raw\v12_m2_paper_core_hga_after_guard_patch_120s.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 120 --frontier-intervals 3 --progress-log results\heuristic_relaxation_dataset_round\progress\v12_m1_paper_core_hga_after_guard_patch_120s.csv --progress-interval-seconds 30 --out results\heuristic_relaxation_dataset_round\raw\v12_m1_paper_core_hga_after_guard_patch_120s.json
```

Earlier comparison rows in the same directory used empty, explicit heuristic, BPC-owned, and diagnostic archive incumbents with 120s/300s limits.

## Generated Variants

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\generate_capacity_inventory_variants.py --variants-per-base 3 --seed-base 260626 --out-dir reference\generated_variants
```

For each manifest row a heuristic incumbent was exported, and for the first 10 variants a 60s paper-core row was run with that explicit incumbent JSON.

## Audits

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\heuristic_relaxation_dataset_round\raw --csv-out results\heuristic_relaxation_dataset_round\certificate_audit.csv --fail-on-error
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\generated_variant_round\raw --csv-out results\generated_variant_round\certificate_audit.csv --fail-on-error
```
