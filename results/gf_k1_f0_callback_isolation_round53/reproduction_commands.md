# Round 53 reproduction commands

Run from `E:\codes\ExactEBRP` on the recorded Windows/Gurobi environment.

```powershell
$cmake = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$ctest = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'
$py = 'python'
$build = 'E:\codes\ExactEBRP\build\official-round53-5b1e7d5bb'
& $cmake -S . -B $build -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_HOME='D:/gurobi1302/win64' -G 'MinGW Makefiles'
& $cmake --build $build --config Release -j 4
& $ctest --test-dir $build -C Release --output-on-failure
& $py scripts/run_round53_f0_audits.py --executable "$build/Round50IntervalMipExperiment.exe"
# Resume the frozen panel rows with run_round53_fixed_interval_panel.py and
# run_round53_k1_panel.py using the policies, states, methods, and caps recorded
# in the compact CSVs and their local command.json files.
& $py scripts/finalize_round53_integration.py
& $py scripts/finalize_round53_evidence.py --exact-executable "$build/ExactEBRP.exe" --fixed-executable "$build/Round50IntervalMipExperiment.exe" --official-build $build
Get-FileHash -Algorithm SHA256 "$build/ExactEBRP.exe"
```

All ordinary native processes are capped at no more than 3600 seconds. Only the predeclared tight-panel follow-up may use 7200 seconds, and only when its frozen automatic trigger fires.
