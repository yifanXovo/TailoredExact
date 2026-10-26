# Round 58 reproduction commands

All official benchmark attempts use the source-frozen executable built from
commit `8ec0e1e151a5f25cb0594852f896b04303c0ba34`:

```
build/official-round58-citibike443-8ec0e1e15/ExactEBRP.exe
SHA-256 0f7570d4c421b9d2f4cb2941bf4d426fe396a25b26ef1c0618df0f3a675333f2
```

On the qualified Windows/Gurobi 13.0.2 host, configure and test with:

```powershell
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' `
  -S . -B build/official-round58-citibike443-8ec0e1e15 `
  -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON `
  -DGUROBI_HOME=D:/gurobi1302/win64
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' `
  --build build/official-round58-citibike443-8ec0e1e15 --config Release -j
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' `
  --test-dir build/official-round58-citibike443-8ec0e1e15 --output-on-failure
```

The P-GRB expected model fingerprints were frozen before the first benchmark
solve:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts/run_round58_pgrb_fingerprint_preflight.py `
  --executable build/official-round58-citibike443-8ec0e1e15/ExactEBRP.exe `
  --source-freeze-commit 8ec0e1e151a5f25cb0594852f896b04303c0ba34
```

Do not repeat that discovery command after benchmark execution begins. Run the
frozen stages sequentially; each invocation resumes only from hash-valid
completion markers:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts/run_round58_paired_benchmark.py --preflight
& 'D:\msys64\ucrt64\bin\python.exe' scripts/run_round58_paired_benchmark.py --stage screen
& 'D:\msys64\ucrt64\bin\python.exe' scripts/run_round58_paired_benchmark.py --stage long
& 'D:\msys64\ucrt64\bin\python.exe' scripts/run_round58_paired_benchmark.py --stage near
& 'D:\msys64\ucrt64\bin\python.exe' scripts/run_round58_paired_benchmark.py --audit
```

Finalize native archives and compact evidence only after the audit reports the
protocol complete:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' tests/round58_protocol_tests.py
& 'D:\msys64\ucrt64\bin\python.exe' scripts/finalize_round58_evidence.py
& 'D:\msys64\ucrt64\bin\python.exe' scripts/audit_round58_delivery.py
```

Full official raw directories are local-only under
`results/gf_citibike443_k1_vs_pgrb_round58/local_raw/official_runs/`. The
compact stage tables, completion/result hashes, route-package hashes, and raw
inventory are committed. Never add an HGA start, imported incumbent, known
bound, alternative preset, scenario replacement, or instance-specific solver
setting to these commands.
