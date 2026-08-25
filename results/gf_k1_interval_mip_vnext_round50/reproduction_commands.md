# Round 50 reproduction commands

Run from `E:\codes\ExactEBRP` in PowerShell. No command below permits a process cap above 1,800 seconds.

```powershell
cmake -S . -B build/official-round50-fe793b20e -DCMAKE_BUILD_TYPE=Release -DENABLE_GUROBI=ON -DGUROBI_HOME=D:/gurobi1302/win64
cmake --build build/official-round50-fe793b20e --config Release
ctest --test-dir build/official-round50-fe793b20e --output-on-failure
$py='C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py tests/round50_protocol_tests.py -v
```

Reconstruct the frozen states and reproduce a sequential fixed-state panel:

```powershell
& $py scripts/run_round50_state_reconstruction.py
& $py scripts/run_round50_fixed_interval_panel.py --executable build/official-round50-fe793b20e/Round50IntervalMipExperiment.exe --policy interval-mip-v0 --states D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13,D14 --cap 300 --run-root results/gf_k1_interval_mip_vnext_round50/reproduction/stage1 --summary results/gf_k1_interval_mip_vnext_round50/reproduction/stage1.csv
```

Reproduce one frozen counterfactual pair (repeat over the seven manifest cases):

```powershell
& $py scripts/run_round50_counterfactual.py --case major_root --arm retain --executable build/official-round50-fe793b20e/ExactEBRP.exe --process-cap 1200
& $py scripts/run_round50_counterfactual.py --case major_root --arm midpoint --executable build/official-round50-fe793b20e/ExactEBRP.exe --process-cap 1200
& $py scripts/analyze_round50_counterfactuals.py
```

Regenerate all compact terminal audits after the raw evidence exists:

```powershell
& $py scripts/finalize_round50_evidence.py
```
