# V20 Replication Round Commands

Start head: `7845588656e5a184677f65077ecc0251052e04ff`

Build:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/ColumnPool.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/hga_tgbc/HgaTgbcGreedy.cpp src/HgaTgbcRunner.cpp src/Logger.cpp src/main.cpp -o build/ExactEBRP.exe
```

High-imbalance seed3202 replication commands used the same options and only changed output stems:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --lambda 0.15 --T 3600 --time-limit 1200 --frontier-intervals 3 --route-mask-max-v 12 --v20-safe-relaxation-cuts true --v20-cover-cuts true --v20-cover-max-size 4 --station-residual-cover-cuts true --large-compact-flow-relaxation mip-light --large-compact-flow-time-limit 20 --large-compact-flow-connectivity true --relaxation-portfolio-mode fixed --progress-log results\v20_replication_round\progress\high_imbalance_seed3202_rep1.csv --progress-interval-seconds 60 --ub-event-log results\v20_replication_round\progress\high_imbalance_seed3202_rep1.ub_events.csv --log results\v20_replication_round\logs\high_imbalance_seed3202_rep1.log --out results\v20_replication_round\raw\high_imbalance_seed3202_rep1.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --lambda 0.15 --T 3600 --time-limit 1200 --frontier-intervals 3 --route-mask-max-v 12 --v20-safe-relaxation-cuts true --v20-cover-cuts true --v20-cover-max-size 4 --station-residual-cover-cuts true --large-compact-flow-relaxation mip-light --large-compact-flow-time-limit 20 --large-compact-flow-connectivity true --relaxation-portfolio-mode fixed --progress-log results\v20_replication_round\progress\high_imbalance_seed3202_rep2.csv --progress-interval-seconds 60 --ub-event-log results\v20_replication_round\progress\high_imbalance_seed3202_rep2.ub_events.csv --log results\v20_replication_round\logs\high_imbalance_seed3202_rep2.log --out results\v20_replication_round\raw\high_imbalance_seed3202_rep2.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\high_imbalance_seed3202.txt --lambda 0.15 --T 3600 --time-limit 1200 --frontier-intervals 3 --route-mask-max-v 12 --v20-safe-relaxation-cuts true --v20-cover-cuts true --v20-cover-max-size 4 --station-residual-cover-cuts true --large-compact-flow-relaxation mip-light --large-compact-flow-time-limit 20 --large-compact-flow-connectivity true --relaxation-portfolio-mode fixed --progress-log results\v20_replication_round\progress\high_imbalance_seed3202_rep3.csv --progress-interval-seconds 60 --ub-event-log results\v20_replication_round\progress\high_imbalance_seed3202_rep3.ub_events.csv --log results\v20_replication_round\logs\high_imbalance_seed3202_rep3.log --out results\v20_replication_round\raw\high_imbalance_seed3202_rep3.json
```

V20 mini-suite full-frontier commands used this template with each instance name and output stem:

```powershell
build\ExactEBRP.exe --method primal-heuristic --primal-heuristic hga-tgbc --primal-heuristic-seed 20260626 --primal-heuristic-runs 12 --primal-heuristic-seconds 10 --input reference\hard_stress\V20_M3\<instance>.txt --lambda 0.15 --T 3600 --export-incumbent results\v20_replication_round\incumbents\<instance>.hga_incumbent.json --out results\v20_replication_round\raw\<instance>.primal_heuristic.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\<instance>.txt --lambda 0.15 --T 3600 --time-limit 3600 --frontier-intervals 3 --route-mask-max-v 12 --v20-safe-relaxation-cuts true --v20-cover-cuts true --v20-cover-max-size 4 --station-residual-cover-cuts true --large-compact-flow-relaxation mip-light --large-compact-flow-time-limit 20 --large-compact-flow-connectivity true --relaxation-portfolio-mode fixed --progress-log results\v20_replication_round\progress\<instance>.full_3600.csv --progress-interval-seconds 60 --ub-event-log results\v20_replication_round\progress\<instance>.full_3600.ub_events.csv --log results\v20_replication_round\logs\<instance>.full_3600.log --out results\v20_replication_round\raw\<instance>.full_3600.json
```

The template was run for `high_imbalance_seed3201`, `tight_T_seed3101`, `tight_T_seed3102`, and `moderate_seed3301`. `moderate_seed3302` was run with the same options but output stem `moderate_seed3302.full_1200` and requested `--time-limit 1200`; the resulting row completed noncertified after exceeding that requested budget.

Oracle and merge commands:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\run_interval_cutoff_oracles.py --ledger results\v20_replication_round\raw\high_imbalance_seed3201.full_3600.intervals.csv --instance reference\hard_stress\V20_M3\high_imbalance_seed3201.txt --exe build\ExactEBRP.exe --output-dir results\v20_replication_round\oracle --summary-out results\v20_replication_round\oracle\high_imbalance_seed3201.oracle_results.csv --time-limit 30 --execute

D:\msys64\ucrt64\bin\python.exe scripts\run_interval_cutoff_oracles.py --ledger results\v20_replication_round\raw\tight_T_seed3102.full_3600.intervals.csv --instance reference\hard_stress\V20_M3\tight_T_seed3102.txt --exe build\ExactEBRP.exe --output-dir results\v20_replication_round\oracle --summary-out results\v20_replication_round\oracle\tight_T_seed3102.oracle_results.csv --time-limit 30 --execute

D:\msys64\ucrt64\bin\python.exe scripts\run_interval_cutoff_oracles.py --ledger results\v20_replication_round\raw\moderate_seed3301.full_3600.intervals.csv --instance reference\hard_stress\V20_M3\moderate_seed3301.txt --exe build\ExactEBRP.exe --output-dir results\v20_replication_round\oracle --summary-out results\v20_replication_round\oracle\moderate_seed3301.oracle_results.csv --time-limit 30 --execute

D:\msys64\ucrt64\bin\python.exe scripts\run_interval_cutoff_oracles.py --ledger results\v20_replication_round\raw\moderate_seed3301.full_3600.intervals.csv --instance reference\hard_stress\V20_M3\moderate_seed3301.txt --exe build\ExactEBRP.exe --output-dir results\v20_replication_round\oracle --summary-out results\v20_replication_round\oracle\moderate_seed3301.oracle_long_interval1.csv --target-ids 1 --time-limit 600 --execute

D:\msys64\ucrt64\bin\python.exe scripts\merge_interval_oracle_results.py --ledger results\v20_replication_round\raw\moderate_seed3301.full_3600.intervals.csv --oracle-results results\v20_replication_round\oracle\moderate_seed3301.oracle_combined.csv --merged-ledger results\v20_replication_round\moderate_seed3301_merged_ledger.csv --audit results\v20_replication_round\moderate_seed3301_ledger_merge_audit.csv
```

Exact BPC interval diagnostic:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\hard_stress\V20_M3\moderate_seed3301.txt --lambda 0.15 --T 3600 --time-limit 600 --frontier-focus-only true --frontier-focus-range 0.0163841842216,0.0327683684432 --frontier-focus-time-limit 600 --frontier-focus-relax-seconds 60 --frontier-focus-tree-nodes 31 --frontier-closure-mode tree --closure-final-exact-pricing true --progress-log results\v20_replication_round\progress\moderate_seed3301.interval1_bpc_fallback.csv --progress-interval-seconds 60 --log results\v20_replication_round\logs\moderate_seed3301.interval1_bpc_fallback.log --out results\v20_replication_round\raw\moderate_seed3301.interval1_bpc_fallback.json
```

V12 stability commands used the same `paper-bpc-core` preset with native HGA-TGBC UB and no archive scanning:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --progress-log results\v20_replication_round\progress\v4_smoke_30s.csv --out results\v20_replication_round\raw\v4_smoke_30s.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --progress-log results\v20_replication_round\progress\v12_m2_canonical_300s.csv --out results\v20_replication_round\raw\v12_m2_canonical_300s.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --progress-log results\v20_replication_round\progress\v12_m1_diagnostic_300s.csv --out results\v20_replication_round\raw\v12_m1_diagnostic_300s.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 600 --progress-log results\v20_replication_round\progress\v12_m1_600s.csv --out results\v20_replication_round\raw\v12_m1_600s.json
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-exact-v20-certificate --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --progress-log results\v20_replication_round\progress\v4_v20_preset_smoke_30s.csv --out results\v20_replication_round\raw\v4_v20_preset_smoke_30s.json
```

Audit and summary commands:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\summarize_v20_replication_round.py
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
build\ExactEBRP.exe --method certificate-basis-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\v20_replication_round\raw\certificate_basis_test.json
build\ExactEBRP.exe --method option-consistency-test --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\v20_replication_round\raw\option_consistency_test.json
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\v20_replication_round\raw --csv-out results\v20_replication_round\certificate_audit.csv --fail-on-error
```
