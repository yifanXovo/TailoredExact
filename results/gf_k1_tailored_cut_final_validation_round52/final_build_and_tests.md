# Round 52 final build and tests

## Outcome

The full Round 52 build and test audit passes. The complete CMake build exited zero, all 30 registered CTest executables passed, and `Round52TailoredCutTests.exe` passed all 44 named cases. The frozen validation/holdout executable remains byte-identical after the build:

`d245c76f6397c757894610d8f5238cfeb971761ff7e05edf51058e451d810151  build/round52/ExactEBRP.exe`

The Round 52 tailored-cut test executable is:

`2733c894b411f9aee711de435248ed71259113f4d3ffde296810e91536f8b1ac  build/round52/Round52TailoredCutTests.exe`

## Counts

| Audit | Passed | Failed | Notes |
| --- | ---: | ---: | --- |
| Full CMake build | 1 | 0 | all configured targets, parallel 4 |
| Registered CTest executables | 30 | 0 | total real test time 2.43 s |
| Round 52 named tailored-cut cases | 44 | 0 | separator, manager, callback, policies F0-F4 |
| Support-duration separator audit | 14 | 0 | exact ranks 2-4 and mapping/error cases |
| Live native `GRBcbcut` submissions | 1 | 0 | one successful globally valid user cut |
| Plain-LP monotonicity states | 15 | 0 | `LP_M1 >= LP_v0 - 1e-7` |
| Tau replay rows | 334 | 0 | zero action changes at tau 0.08 |
| K1 integration properties | 12 | 0 | no integration rerun needed because backend is v0 |
| P-GRB fingerprint probes | 24 | 0 | all expected fingerprints frozen and matched |
| Official final-panel method rows | 48 | 0 | 24 validation + 24 holdout |

## Final-panel gates

- Official completion markers: 48/48.
- Validation rows: 24/24; maximum process time 1780.3707046 seconds.
- Holdout rows: 24/24; maximum process time 1783.2027537 seconds.
- Process-cap violations: 0 (cap 1800 seconds).
- False certificates: 0.
- Lower/upper trajectory monotonicity failures: 0 at the frozen certificate tolerance.
- Model-fingerprint mismatches: 0.
- Missing entered rows: none.
- Invalid discovery attempts counted as official: 0; two attempts are retained and explicitly invalidated.

## Repository gates

- `git diff --check`: pass.
- Forbidden algorithm dispatch: pass; `forbidden_dispatch_audit.json` records zero policy dispatches on instance identity, size, difficulty, progress, resource, or historical-winner fields.
- Lazy constraints: unused; no base feasibility row was removed.
- Tracked files below `local_raw/`: 0.
- Final validation and holdout executable hashes: one unique hash.
- Post-freeze algorithmic changes: 0.
- Pre-existing user-file blobs remain exactly:
  - `98bcd60c3c5542772f101d5c73643033b78c58da`
  - `730b12307ff356aad1972158312c3c791f4492ec`
  - `c6ea164aec30b59fbee030476ed9cd6a4ffa315f`

## Commands

```powershell
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' --build build/round52 --parallel 4
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build/round52 --output-on-failure
& build/round52/Round52TailoredCutTests.exe
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/finalize_round52_final_panels.py
Get-FileHash -Algorithm SHA256 build/round52/ExactEBRP.exe
git diff --check
```
