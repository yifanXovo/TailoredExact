# Round 46 reproduction commands

```powershell
cmake -S . -B build/official-round46-36033fab4 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DENABLE_GUROBI=ON -DGUROBI_HOME=D:/gurobi1302/win64
cmake --build build/official-round46-36033fab4 --parallel 8
ctest --test-dir build/official-round46-36033fab4 --output-on-failure
D:\msys64\ucrt64\bin\python.exe scripts/run_round46.py stage3 --executable build/official-round46-36033fab4/ExactEBRP.exe
D:\msys64\ucrt64\bin\python.exe scripts/run_round46.py stage4 --executable build/official-round46-36033fab4/ExactEBRP.exe
D:\msys64\ucrt64\bin\python.exe scripts/run_round46.py stage5 --executable build/official-round46-36033fab4/ExactEBRP.exe
D:\msys64\ucrt64\bin\python.exe scripts/analyze_round46_decisions.py
D:\msys64\ucrt64\bin\python.exe scripts/analyze_round46.py
```
