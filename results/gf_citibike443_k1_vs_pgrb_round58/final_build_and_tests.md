# Round 58 final build and test record

Date: 2026-09-10 (Asia/Shanghai)

## Frozen executable

- Source freeze commit: `8ec0e1e151a5f25cb0594852f896b04303c0ba34`
- Source freeze tree: `1b42e96c03bcc646788a4b50b0bb0b43ba8fdda4`
- Executable: `build/official-round58-citibike443-8ec0e1e15/ExactEBRP.exe`
- Executable SHA-256: `0f7570d4c421b9d2f4cb2941bf4d426fe396a25b26ef1c0618df0f3a675333f2`
- Post-freeze diff over `CMakeLists.txt`, `include/`, and `src/`: empty.

## Benchmark protocol audit

Command:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts/run_round58_paired_benchmark.py --audit
```

Result: PASS. The audit reported 50 panel rows, 400 command variants checked, 149 completed authorized runs, 100 completed screening arms, no unauthorized runs, no missing authorized runs, and a maximum entered cap of exactly 21,600 seconds.

## Native tests

Command:

```powershell
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build/official-round58-citibike443-8ec0e1e15 --output-on-failure
```

Result: PASS, 35/35 tests, 0 failures. This includes `Round58CitiBikePairedBenchmarkTests`.

## Python regression and protocol tests

All 46 files matching `tests/*.py` were run sequentially in sorted filename order with `D:\msys64\ucrt64\bin\python.exe`. The historical Round 46--49 protocol tests were pointed at their existing frozen hash-qualified executables through their documented environment overrides:

- Round 46: `build/official-round46-36033fab4/ExactEBRP.exe`, SHA-256 `d574b38b2f44ae2aacf92bf685f439354b5a08dbe257b6c399045b98a157871b`
- Round 47: `build/official-round47-283f576/ExactEBRP.exe`, SHA-256 `541c496881c7a0f79ffaf50cbdf4acc3bdf106dd86031990c0e6cf56c3deaa16`
- Round 48: `build/official-round48-4c08f3645/ExactEBRP.exe`, SHA-256 `bff4943b82d10c4fc082e5ae9add1970d46a1277ab1b398dc77410d94b4cbe34`
- Round 49: `build/official-round49-36990fc47/ExactEBRP.exe`, SHA-256 `f73b40a12590ab432abc201f95fbcea70ba499337239f31175fba589ab0d8ed5`

Result: PASS, 46/46 scripts. Notable terminal checks were Round 53 (31 checks), Round 54 (35 checks), Round 56 (49 tests), and Round 58 (44 checks).

The Round 53 historical test was made forward-compatible: its obsolete comparison of a Round 53 freeze to the current `HEAD` was replaced by verification that the recorded freeze commit still resolves to its recorded tree and that both recorded Round 53 binaries retain their recorded SHA-256 values. The revised test passes all 31 checks and does not weaken current-source or Round 58 validation.

## Pre-existing workspace preservation

`scripts/verify_round56_preservation.py` returned `all_preserved: true`: 57,284 pre-existing untracked files (27,358,038,391 bytes) were verified, and all three tracked user modifications retain their recorded SHA-256 values.

Overall status: PASS
