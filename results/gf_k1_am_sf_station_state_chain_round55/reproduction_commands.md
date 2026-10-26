# Round 55 reproduction commands

Use the frozen one-thread executable and manifests. Bulky native logs remain local and are hash-inventoried.

```powershell
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build\official-round55-final-6d0818126 --output-on-failure
D:\msys64\ucrt64\bin\python.exe scripts\run_round55_stable_requalification.py --executable build\official-round55-final-6d0818126\ExactEBRP.exe
D:\msys64\ucrt64\bin\python.exe scripts\run_round55_k1_integration.py --executable build\official-round55-final-6d0818126\ExactEBRP.exe --cap 1800 --jobs 4
D:\msys64\ucrt64\bin\python.exe scripts\run_round55_k1_integration.py --executable build\official-round55-final-6d0818126\ExactEBRP.exe --cap 3600 --instances tight_T_seed3102,tight_T_seed3101,moderate_seed3301,moderate_seed3302,round54_generalization_moderate_3600_V50_M2_Q20_seed1123418787 --jobs 4
D:\msys64\ucrt64\bin\python.exe scripts\analyze_round55_k1_integration.py --cap 1800 --output results\gf_k1_am_sf_station_state_chain_round55\k1_integration_1800s.csv --decision results\gf_k1_am_sf_station_state_chain_round55\k1_integration_1800s_decision.json --split-diff results\gf_k1_am_sf_station_state_chain_round55\k1_split_action_diff_1800s.csv
D:\msys64\ucrt64\bin\python.exe scripts\finalize_round55_k1_integration.py --rows-1800 results\gf_k1_am_sf_station_state_chain_round55\k1_integration_1800s.csv --rows-3600 results\gf_k1_am_sf_station_state_chain_round55\k1_integration_3600s.csv --diff-1800 results\gf_k1_am_sf_station_state_chain_round55\k1_split_action_diff_1800s.csv --diff-3600 results\gf_k1_am_sf_station_state_chain_round55\k1_split_action_diff_3600s.csv --split-output results\gf_k1_am_sf_station_state_chain_round55\k1_split_action_diff.csv --decision results\gf_k1_am_sf_station_state_chain_round55\k1_integration_decision.json
```

Do not run the sealed or expansion runners for this evidence freeze: their opening audits record false gates.
