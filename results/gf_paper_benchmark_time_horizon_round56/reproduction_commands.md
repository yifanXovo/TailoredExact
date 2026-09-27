# Round 56 reproduction commands

The source freeze is `75e58521158aba8628ebc9444444ec3841415285` and the sole official executable SHA-256 is `34e992060e3adffd3a7795c2c783672044996edd7234bf7e9f58a662b1c32fea`.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
D:\msys64\ucrt64\bin\python.exe scripts\run_round56_official.py --prepare
D:\msys64\ucrt64\bin\python.exe scripts\run_round56_official.py --run
D:\msys64\ucrt64\bin\python.exe scripts\round56_route_archive.py --all-completed
D:\msys64\ucrt64\bin\python.exe scripts\analyze_round56_results.py
D:\msys64\ucrt64\bin\python.exe scripts\run_round56_repeatability.py --run
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build\official-round56-paper-dataset-75e585211 --output-on-failure
D:\msys64\ucrt64\bin\python.exe -B -m unittest discover -s tests -p 'round*_protocol_tests.py' -v
D:\msys64\ucrt64\bin\python.exe scripts\verify_round56_preservation.py
D:\msys64\ucrt64\bin\python.exe scripts\finalize_round56_evidence.py --reports --inventory
```

The 50 exact commands, mathematical-instance hashes, run identities, T values, and process caps are frozen in `execution_manifest.json`. Bulky native logs remain local but are path/size/SHA-256 inventoried.
