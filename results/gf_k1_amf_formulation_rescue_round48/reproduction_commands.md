# Reproduction commands

From `E:/codes/ExactEBRP` using `D:/msys64/ucrt64/bin/python.exe`:

```powershell
cmake -S . -B build/official-round48-4c08f3645 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
cmake --build build/official-round48-4c08f3645 -j 4
ctest --test-dir build/official-round48-4c08f3645 --output-on-failure
$env:EXACTEBRP_ROUND48_EXE = "E:/codes/ExactEBRP/build/official-round48-4c08f3645/ExactEBRP.exe"
python -B -m unittest discover -s tests -p "round*_protocol_tests.py" -v
python -B scripts/run_round48_default_off_equivalence.py --executable $env:EXACTEBRP_ROUND48_EXE --process-cap 120
python -B scripts/run_round48.py counterfactuals --executable $env:EXACTEBRP_ROUND48_EXE
python -B scripts/run_round48.py stage3 --executable $env:EXACTEBRP_ROUND48_EXE
python -B scripts/analyze_round48_offline.py
python -B scripts/analyze_round48.py
```

Completed rows resume from their sealed completion markers. Stage 4/5 have no reproduction command because the frozen offline gate made them ineligible.
