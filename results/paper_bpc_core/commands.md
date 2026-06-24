# Paper BPC Core Commands

Base Git SHA before the compatibility-order validation commit:
`08816508e50120dceea20289cb28b5935bea97f6`

Build command used in this pass:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
```

Audit commands:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\audit\certificate_audit.csv --fail-on-error
```

Completion-LB pruning retest after split-before-tree scheduling:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --pricing-completion-lb-pruning true --progress-log results\paper_bpc_core\progress\v12_m1_average_core_300s_split_completion_lb.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_300s_split_completion_lb.json *> results\paper_bpc_core\logs\v12_m1_average_core_300s_split_completion_lb.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_300s_split_before_tree.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_300s_split_before_tree.json *> results\paper_bpc_core\logs\v12_m1_average_core_300s_split_before_tree.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --pricing-completion-lb-pruning true --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s_split_completion_lb.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s_split_completion_lb.json *> results\paper_bpc_core\logs\v12_m2_average_core_300s_split_completion_lb.log

D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\audit\certificate_audit.csv --fail-on-error
```

V12 M2 split-before-tree 1200s paper-core row:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_1200s_split_before_tree.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_1200s_split_before_tree.json *> results\paper_bpc_core\logs\v12_m2_average_core_1200s_split_before_tree.log

D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\audit\certificate_audit.csv --fail-on-error
```

Adaptive split-depth 5 paper-core validation:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --progress-log results\paper_bpc_core\progress\v4_paper_core_depth5_smoke.csv --progress-interval-seconds 5 --out results\paper_bpc_core\raw\v4_paper_core_depth5_smoke.json *> results\paper_bpc_core\logs\v4_paper_core_depth5_smoke.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --frontier-adaptive-max-depth 4 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s_split_depth4.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s_split_depth4.json *> results\paper_bpc_core\logs\v12_m2_average_core_300s_split_depth4.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --frontier-adaptive-max-depth 5 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s_split_depth5.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s_split_depth5.json *> results\paper_bpc_core\logs\v12_m2_average_core_300s_split_depth5.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --frontier-adaptive-max-depth 5 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_300s_split_depth5.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_300s_split_depth5.json *> results\paper_bpc_core\logs\v12_m1_average_core_300s_split_depth5.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s_depth5_default.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s_depth5_default.json *> results\paper_bpc_core\logs\v12_m2_average_core_300s_depth5_default.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_300s_depth5_default.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_300s_depth5_default.json *> results\paper_bpc_core\logs\v12_m1_average_core_300s_depth5_default.log

D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\audit\certificate_audit.csv --fail-on-error
```

Split-before-tree scheduling validation:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --progress-log results\paper_bpc_core\progress\v4_paper_core_split_before_tree_smoke.csv --progress-interval-seconds 5 --out results\paper_bpc_core\raw\v4_paper_core_split_before_tree_smoke.json *> results\paper_bpc_core\logs\v4_paper_core_split_before_tree_smoke.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s_split_before_tree.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s_split_before_tree.json *> results\paper_bpc_core\logs\v12_m2_average_core_300s_split_before_tree.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_1200s.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_1200s.json *> results\paper_bpc_core\logs\v12_m2_average_core_1200s.log

D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\audit\certificate_audit.csv --fail-on-error
```

Relaxation compatibility-order validation:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --progress-log results\paper_bpc_core\progress\v4_paper_core_compat_order_smoke.csv --progress-interval-seconds 5 --out results\paper_bpc_core\raw\v4_paper_core_compat_order_smoke.json *> results\paper_bpc_core\logs\v4_paper_core_compat_order_smoke.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s_compat_order.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s_compat_order.json *> results\paper_bpc_core\logs\v12_m2_average_core_300s_compat_order.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_300s_compat_order.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_300s_compat_order.json *> results\paper_bpc_core\logs\v12_m1_average_core_300s_compat_order.log

D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\audit\certificate_audit.csv --fail-on-error
```

Smoke and diagnostic runs:

```powershell
build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\paper_bpc_core\raw\option_consistency_paper_core.json

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --progress-log results\paper_bpc_core\progress\v4_paper_core_smoke.csv --progress-interval-seconds 5 --out results\paper_bpc_core\raw\v4_paper_core_smoke.json *> results\paper_bpc_core\logs\v4_paper_core_smoke.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\generated\regen_V8_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --frontier-relax-seconds 0.5 --frontier-focused-reserve-fraction 0 --frontier-focused-intensification false --progress-log results\paper_bpc_core\progress\v8_trace_tree_probe_60s.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v8_trace_tree_probe_60s.json *> results\paper_bpc_core\logs\v8_trace_tree_probe_60s.log
```

V12 paper-core runs:

```powershell
build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 20 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_trace_20s.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v12_m1_average_core_trace_20s.json *> results\paper_bpc_core\logs\v12_m1_average_core_trace_20s.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_60s.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v12_m1_average_core_60s.json *> results\paper_bpc_core\logs\v12_m1_average_core_60s.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_300s.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_300s.json *> results\paper_bpc_core\logs\v12_m1_average_core_300s.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 1200 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_1200s.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_1200s.json *> results\paper_bpc_core\logs\v12_m1_average_core_1200s.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_60s.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v12_m2_average_core_60s.json *> results\paper_bpc_core\logs\v12_m2_average_core_60s.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s.json *> results\paper_bpc_core\logs\v12_m2_average_core_300s.log
```

Completion-LB pricing pruning validation:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe

build\ExactEBRP.exe --method option-consistency-test --algorithm-preset paper-bpc-core --pricing-completion-lb-pruning true --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --out results\paper_bpc_core\raw\option_consistency_paper_core_completion_lb.json *> results\paper_bpc_core\logs\option_consistency_paper_core_completion_lb.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --pricing-completion-lb-pruning true --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --time-limit 30 --frontier-intervals 3 --frontier-retry-passes 1 --frontier-final-closure true --frontier-final-nodes 31 --progress-log results\paper_bpc_core\progress\v4_paper_core_completion_lb_smoke.csv --progress-interval-seconds 5 --out results\paper_bpc_core\raw\v4_paper_core_completion_lb_smoke.json *> results\paper_bpc_core\logs\v4_paper_core_completion_lb_smoke.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --pricing-completion-lb-pruning true --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_60s_completion_lb.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v12_m2_average_core_60s_completion_lb.json *> results\paper_bpc_core\logs\v12_m2_average_core_60s_completion_lb.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --pricing-completion-lb-pruning true --input reference\regen_candidate_V12_M1_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m1_average_core_300s_completion_lb.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m1_average_core_300s_completion_lb.json *> results\paper_bpc_core\logs\v12_m1_average_core_300s_completion_lb.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --pricing-completion-lb-pruning true --input reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 300 --frontier-intervals 3 --progress-log results\paper_bpc_core\progress\v12_m2_average_core_300s_completion_lb.csv --progress-interval-seconds 60 --out results\paper_bpc_core\raw\v12_m2_average_core_300s_completion_lb.json *> results\paper_bpc_core\logs\v12_m2_average_core_300s_completion_lb.log

build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-bpc-core --pricing-completion-lb-pruning true --input reference\generated\regen_V8_M2_average.txt --lambda 0.15 --T 3600 --time-limit 60 --frontier-intervals 3 --frontier-relax-seconds 0.5 --frontier-focused-reserve-fraction 0 --frontier-focused-intensification false --progress-log results\paper_bpc_core\progress\v8_trace_tree_probe_completion_lb_60s.csv --progress-interval-seconds 10 --out results\paper_bpc_core\raw\v8_trace_tree_probe_completion_lb_60s.json *> results\paper_bpc_core\logs\v8_trace_tree_probe_completion_lb_60s.log

D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_bpc_core\raw --csv-out results\paper_bpc_core\audit\certificate_audit.csv --fail-on-error
```
