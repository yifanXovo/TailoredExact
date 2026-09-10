# Reproduction commands

Run from the repository root in PowerShell. The bundled Python path may be
replaced by any compatible Python 3.11+ interpreter.

```powershell
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' -S . -B build_round43 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER='D:/msys64/ucrt64/bin/c++.exe' -DCMAKE_MAKE_PROGRAM='D:/msys64/ucrt64/bin/mingw32-make.exe' -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT='D:/gurobi1302/win64'
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' --build build_round43 --parallel 8
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build_round43 -C Release --output-on-failure
& $python tests/round43_protocol_tests.py
& $python tests/round43_evidence_tests.py
```

Representative selected-candidate command:

```powershell
& $python scripts/run_round43_experiments.py --stage stage3-candidate --instance round39_small_medium_V12_M3_Q30_slot08_seed1343324363 --execution algorithm --K0 1 --depth 2 --rho 0.10 --score d --envelope single --process-cap 3600
```

Final analysis order:

```powershell
& $python scripts/analyze_round43_stage3_mechanism.py
& $python scripts/analyze_round43_default_off.py
& $python scripts/analyze_round43_development.py
& $python scripts/analyze_round43_ablations.py
& $python scripts/analyze_round43_conditional_stages.py
& $python scripts/seal_round43_evidence.py
& $python scripts/finalize_round43.py
```
