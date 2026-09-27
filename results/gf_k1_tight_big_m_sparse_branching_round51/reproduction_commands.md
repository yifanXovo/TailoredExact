# Round 51 reproduction commands

Run from the repository root on the frozen machine/toolchain. The commands below use the contracted caps and do not grant adaptive runs extra terminal-MIP time.

## Configure, build, and test

```powershell
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' -S . -B build/round51-m1 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/c++.exe -DGUROBI_ROOT=D:/gurobi1302/win64
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' --build build/round51-m1 -j 4
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build/round51-m1 --output-on-failure
```

## All-state formulation/model audits

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/run_round51_model_audit_builds.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --run-root results/gf_k1_tight_big_m_sparse_branching_round51/model_audit_runs --cap 120 --policies interval-mip-v0,m1-tight-big-m-v0
D:/msys64/ucrt64/bin/python.exe scripts/audit_round51_big_m_models.py
D:/msys64/ucrt64/bin/python.exe scripts/run_round51_model_audit_builds.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --run-root results/gf_k1_tight_big_m_sparse_branching_round51/model_audit_runs_a1r --cap 120 --policies m1-tight-big-m-v0,a1-root-sparse-2x2,a1r-root-sparse-top1
D:/msys64/ucrt64/bin/python.exe scripts/audit_round51_a1_correctness.py
D:/msys64/ucrt64/bin/python.exe scripts/audit_round51_a1r_correctness.py
```

## M1 core

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy interval-mip-v0 --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/m1_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/m1_core_v0_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-tight-big-m-v0 --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/m1_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/m1_core_m1_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/analyze_round51_m1_core.py
```

## Symmetry re-audit and D1-D14 development

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/prepare_round51_symmetry_model_audit.py
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-tight-big-m-v0 --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_core_m1_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-s1-route-start-order --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_core_s1_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-s1r-used-first-route-start-order --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_core_s1r_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/analyze_round51_symmetry_core.py
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-tight-big-m-v0 --states D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13,D14 --cap 300 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_development_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_development_m1_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-s1-route-start-order --states D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13,D14 --cap 300 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_development_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_development_s1_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-s1r-used-first-route-start-order --states D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13,D14 --cap 300 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_development_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/symmetry_development_s1r_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/analyze_round51_symmetry_development.py
```

## A1 core

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-tight-big-m-v0 --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/a1_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/a1_core_m1_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy a1-root-sparse-2x2 --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/a1_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/a1_core_a1_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/analyze_round51_a1_core.py
```

## Sole A1-R1 revision core

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy m1-tight-big-m-v0 --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/a1r_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/a1r_core_m1_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/run_round50_fixed_interval_panel.py --executable build/round51-m1/Round51IntervalMipExperiment.exe --policy a1r-root-sparse-top1 --states D1,D2,D3,D4,D5,D6,D9,D10,D11 --cap 120 --run-root results/gf_k1_tight_big_m_sparse_branching_round51/a1r_core_runs --summary results/gf_k1_tight_big_m_sparse_branching_round51/a1r_core_a1r_raw.csv --gurobi-home D:/gurobi1302/win64
D:/msys64/ucrt64/bin/python.exe scripts/analyze_round51_a1r_core.py
```

## Final cross-stage audit

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/finalize_round51_evidence.py
```

Confirmation, key-long, interaction, and K1-AM commands are intentionally absent: the frozen gates did not authorize those stages. Raw logs remain local under the directories listed in `raw_evidence_inventory.csv`; compact summaries and audits are committed.
