# Reproduction commands

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\run_round45_completion.py
D:\msys64\ucrt64\bin\python.exe scripts\finalize_round45.py
D:\msys64\ucrt64\bin\python.exe tests\round45_completion_protocol_tests.py
```

The runner resumes sealed rows and executes remaining official Gurobi rows
strictly sequentially.
