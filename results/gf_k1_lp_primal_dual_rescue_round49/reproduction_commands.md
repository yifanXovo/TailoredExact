# Reproduction commands

Run from `E:/codes/ExactEBRP` with the bundled/available Python and CMake.

```powershell
cmake -S . -B build/official-round49-36990fc47 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/c++.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
cmake --build build/official-round49-36990fc47 --config Release -j 2
ctest --test-dir build/official-round49-36990fc47 -C Release --output-on-failure -j 2
$env:EXACTEBRP_ROUND49_EXE="E:/codes/ExactEBRP/build/official-round49-36990fc47/ExactEBRP.exe"
python -m unittest -v tests.round49_protocol_tests
python scripts/run_round49_default_off_equivalence.py --executable $env:EXACTEBRP_ROUND49_EXE --process-cap 120
python scripts/run_round49.py stage3 --executable $env:EXACTEBRP_ROUND49_EXE
python scripts/analyze_round49.py
```

Offline LP evidence was extracted only before live runtime with `Round49RCOfflineExtract`; exact commands and all 27 solve rows are in `offline_diagnostic_solve_log.csv`. No command has a process cap above 1800 seconds.
