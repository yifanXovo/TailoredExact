# Round 56 repeatability audit

All three frozen sentinels passed: **true**.

The repeat used the same source, executable, mathematical scenario, K1-AM-SF preset, solver parameter contract, route horizon, and process cap. The run identity changed only because the frozen repetition identifier was `repeat-1` and output paths were repetition-specific.

A different route or final inventory is not treated as a correctness failure when the certified objective, certificate class, and independent verifier outcome agree; such variation can represent an objective-equivalent optimum.

| Scenario | Objective agrees | Certificate agrees | Verifier agrees | Native route identical | Pass |
|---|---:|---:|---:|---:|---:|
| r56_V08_M01_Q30_T01800_seed1760458116 | True | True | True | True | True |
| r56_V20_M03_Q30_T10800_seed1716808955 | True | True | True | True | True |
| r56_V50_M05_Q30_T18000_seed811442003 | True | True | True | True | True |
