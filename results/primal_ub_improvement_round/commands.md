# Commands

Build:

```powershell
D:\msys64\ucrt64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude src\Parser.cpp src\Evaluator.cpp src\Result.cpp src\Bounds.cpp src\ColumnPool.cpp src\TailoredExact.cpp src\Pricing.cpp src\Cuts.cpp src\Branching.cpp src\Master.cpp src\ColumnGeneration.cpp src\CplexBaseline.cpp src\Logger.cpp src\main.cpp -o build\ExactEBRP.exe
```

Audit:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\primal_ub_improvement_round\raw --csv-out results\primal_ub_improvement_round\certificate_audit.csv --fail-on-error
```

Focused run command files:

```text
results/primal_ub_improvement_round/logs/*.command.txt
results/generated_variant_round2/logs/*.command.txt
```

The generated-variant batch command is saved in:

```text
results/generated_variant_round2/run_variants.ps1
```
