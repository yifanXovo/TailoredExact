# Reproduction commands

```powershell
cmake -S . -B build_round45 -DCMAKE_BUILD_TYPE=Release -DENABLE_GUROBI=ON
cmake --build build_round45 --config Release --parallel 4
ctest --test-dir build_round45 --output-on-failure -C Release
D:\msys64\ucrt64\bin\python.exe -m unittest discover -s tests -p '*protocol_tests.py' -v
D:\msys64\ucrt64\bin\python.exe scripts/analyze_round45_part1.py
D:\msys64\ucrt64\bin\python.exe scripts/analyze_round45_part2.py
D:\msys64\ucrt64\bin\python.exe scripts/finalize_round45.py
```

Official run commands and environments are preserved losslessly in each
`runs/*/command.json` and `command_environment.json`. Use
`scripts/round45_experiment.py --help` to replay an individual frozen row.
