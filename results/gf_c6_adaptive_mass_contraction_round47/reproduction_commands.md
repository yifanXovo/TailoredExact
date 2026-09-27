# Round 47 reproduction commands

```powershell
cmake -S . -B build/official-round47-283f576 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DENABLE_GUROBI=ON -DGUROBI_HOME=D:/gurobi1302/win64
cmake --build build/official-round47-283f576 --parallel 8
ctest --test-dir build/official-round47-283f576 --output-on-failure
python scripts/run_round47.py stage3 --executable build/official-round47-283f576/ExactEBRP.exe
python scripts/run_round47.py stage4 --executable build/official-round47-283f576/ExactEBRP.exe
python scripts/run_round47.py stage5 --executable build/official-round47-283f576/ExactEBRP.exe
python scripts/analyze_round47.py
python scripts/audit_round47.py
python scripts/run_round47_default_off_equivalence.py --executable build/official-round47-283f576/ExactEBRP.exe
```

Official executable SHA-256: `541c496881c7a0f79ffaf50cbdf4acc3bdf106dd86031990c0e6cf56c3deaa16`. Existing completion markers make the experiment runner resume-safe.
