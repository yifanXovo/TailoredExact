# Round 87 reproduction entry

Use the R86 research base or this branch on Windows with Python 3, Gurobi
13.0.2, and the exact R83 binaries identified in `protocol.json`. The default
local binary directory is `E:/codes/ExactEBRP-round66/build/round83/v1`; a
relocated copy may be selected with `ROUND87_BINARY_DIR` only when both binary
hashes match. `ROUND87_RUNTIME_ROOT` may relocate the fresh raw-output root.

Preparation is zero-Optimize and may run once:

```powershell
$env:PYTHONUTF8 = '1'
& 'D:\msys64\ucrt64\bin\python.exe' scripts/round87_research.py prepare
```

Review and commit `campaign/identity.json` and `preflight.json`, then push the
prelaunch commit. The formal serial campaign is:

```powershell
$env:PYTHONUTF8 = '1'
& 'D:\msys64\ucrt64\bin\python.exe' scripts/round87_research.py run
```

Do not invoke `run` a second time. A fresh process after interruption is a new
realization and must use a separately declared output root; times may not be
spliced. `runtime_status.json` is an observational heartbeat, not a formal
checkpoint or certificate. After all solver processes close, run:

```powershell
$env:PYTHONUTF8 = '1'
& 'D:\msys64\ucrt64\bin\python.exe' scripts/round87_analyze.py
```

Final packaging, independent byte verification, plots, and publication happen
only after the native campaign has ended. Historical results and archived
routes are never inputs to an R87 arm.
