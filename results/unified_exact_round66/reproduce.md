# Reproduction

Use the Round66 PR checkout and Gurobi 13.0.2 on the recorded machine for a
strict timing recheck. Other machines/builds are separate reproductions. The
tested configuration is Windows Release, MinGW UCRT64, one optimizer thread,
Seed=0, Presolve=Auto and zero requested gaps. See machine.json and build_v1.json.

Example PowerShell build in a fresh checkout (adjust installed tool paths):

```powershell
$env:PATH = 'D:\msys64\ucrt64\bin;D:\gurobi1302\win64\bin;' + $env:PATH
$r66Cmake = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$r66Ctest = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'
& $r66Cmake -S . -B build/round66 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe -DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
& $r66Cmake --build build/round66 -j 6
& $r66Ctest --test-dir build/round66 --output-on-failure | Tee-Object -FilePath build/round66/tests.log
```

Do not overwrite the original build/evidence while verifying a new build. The
following wrapper records a new source/binary identity and run ledger in a new
directory, makes a fresh build-only official P-GRB fingerprint export, then
runs the requested bounded batch serially. It refuses an existing output path.

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts/round66_reproduce.py --output results/round66_recheck_d6 --ids D6 --arms P-GRB K1-R ARC --cap 600
```

Original batches, all with their complete-run deadlines:

| Role | Arms | Cap | Stage |
|---|---|---:|---|
| micro | P-GRB, ARC | 20 | native_correctness |
| E7, E8 | P-GRB, K1-R, ARC | 120 | small_rebind |
| D4, D3 | K1-R, ARC | 300 | proof_screen |
| D6 | P-GRB, K1-R, ARC | 600 | citibike_screen |
| C2 | P-GRB, K1-R, ARC | 300 | citibike_screen |
| D4 | Q-PLUS | 300 | proof_screen; resource revision 2 |

The last control is entered with scripts/round66_q_control.py only after the
initial panel. The original scripts/round66_research.py and build_v1.json are
immutable; a newly compiled binary must not be made to impersonate that hash.
For a fresh tiny check request only P-GRB and ARC at cap 20.

`analyze_round66.py` recomputes original-route inventories, loads, duration and
objective, checks native parameters and interval coverage, and retains signed
gap discrepancies. `package_round66.py` also copies compact raw evidence and
hashes. Run them between optimizer queues. The original local raw directory
is E:/codes/ExactEBRP-round66/results/unified_exact_round66/local_raw; models,
native logs and binaries are not committed. The committed evidence manifest
identifies source paths and hashes. Full bound traces are losslessly gzip
compressed in the compact evidence; decompression recovers the source bytes.
Historical small-instance attribution is
separate and uses scripts/round66_historical_small.py; it launches no solver.

The native value 5/24 on the tiny fixture, the existing numerical certificate
and the algebraic model proof are different forms of evidence. No strict
rational certification or broad performance qualification is implied.
