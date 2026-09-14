# Reproduction

Use the Round67 PR checkout and Gurobi 13.0.2 on the recorded machine for a
strict timing recheck. Other machines/builds are separate reproductions. The
tested configuration is Windows Release, MinGW UCRT64, one optimizer thread,
Seed=0, Presolve=Auto and zero requested gaps. See machine.json and build_v1.json.

Example PowerShell build in a fresh checkout (adjust installed tool paths):

```powershell
$env:PATH = 'D:\msys64\ucrt64\bin;D:\gurobi1302\win64\bin;' + $env:PATH
$r67Cmake = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$r67Ctest = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'
& $r67Cmake -S . -B build/round67 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe -DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
& $r67Cmake --build build/round67 -j 6
& $r67Ctest --test-dir build/round67 --output-on-failure | Tee-Object -FilePath build/round67/tests.log
```

Do not overwrite the original build/evidence while verifying a new build. The
following wrapper records a new source/binary identity and run ledger in a new
directory, makes a fresh build-only official P-GRB fingerprint export, then
runs the requested bounded batch serially. It refuses an existing output path.

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts/round67_reproduce.py --output results/round67_recheck_d6 --ids D6 --arms P-GRB K1-R VD-P LOG --cap 600
```

Original declared batches use full-run deadlines: micro P-GRB/VD-P/LOG at20;
micro-zero P-GRB/K1-R/LOG at20; D4,D3,C2 P-GRB/K1-R/VD-P/LOG at300; D6 the same
four arms at600. `micro-zero` uses a separate correctness-only T3/zero-handling
counterfactual. It is not a changed performance instance. All are development.
The original scripts/round67_research.py and build_v1.json are immutable. The
reproduction wrapper creates a fresh binding and refuses existing directories.

`analyze_round67.py` recomputes original-route inventories, loads, duration and
objective, checks native parameters and interval coverage, and retains signed
gap discrepancies. `package_round67.py` also copies compact raw evidence and
hashes. Run them between optimizer queues. The original local raw directory
is E:/codes/ExactEBRP-round66/results/unified_exact_round67/local_raw; models,
native logs and binaries are not committed. The committed evidence manifest
identifies source paths and hashes. Full bound traces are losslessly gzip
compressed in the compact evidence; decompression recovers the source bytes.
P-GRB's existing read-only native progress CSV is also copied losslessly from
its recorded gurobi_work path. Its timestamps are native elapsed runtime;
phases.csv provides the process launch offset. Intermediate native incumbents
are identified as native reports, since complete vectors were not independently
retained at every event. The formal end-state UB is independently route-verified;
never backdate that final witness into an earlier common-time checkpoint.
Prior historical attribution remains in Round66; it is not new same-build timing evidence.

Git attributes preserve the Round67 evidence and Python driver bytes, including
recorded hash manifests. The full measured solver working-file hashes remain
in build_v1.json/source_snapshot.json. A fresh source checkout or compiler can
have different text line endings and binary bytes; the reproduction wrapper
records that fresh identity rather than pretending it is the measured binary.

The native value 5/24 on the tiny fixture, the existing numerical certificate
and the algebraic model proof are different forms of evidence. No strict
rational certification or broad performance qualification is implied.
