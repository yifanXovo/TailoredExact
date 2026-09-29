# Reproduce and inspect Round96

All 67 planned starts have already been spent. These instructions prioritize zero-Optimize reproduction. Do not rerun prepare/recover/run into existing paths, restart either failed serial queue, or overwrite an old label. No additional paid run is needed to review this PR.

## Identity and environment

Repository: E:/codes/ExactEBRP; branch codex/round96-external-primal; PR base Round95 bfa4c90f19e19b922f831c7ee97affe1785aff98. Report commits do not identify the production binary source.

|Campaign|Source ref|Executable SHA256|
|---|---|---|
|Frozen R90 LP-G/P/ENS|a71bd53ca412e9b9e529e7237446687d360a94ce|bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2|
|New primal P/OFF/ON|9ab0a2b1064022913295c8da02a5f57288d91f44|75915292d0df67ab48e3a9e396ec013a4a2c8b5a0aef50a983ae17ff5e135f56|

Executable paths are build/research/round90-lp-g-split/ExactEBRP.exe and build/research/round96-route-order/ExactEBRP.exe. Source capsules and per-file hashes are in the stage archives and production_build_identity.json. Gurobi13.0.2 at D:/gurobi1302/win64/bin/gurobi130.dll, single thread, Seed0, PresolveAuto, MIPGap/MIPGapAbs0, FeasibilityTol1e-6, IntFeasTol1e-5, OptimalityTol1e-6; original certificate/physical gates unchanged. Windows, inherited affinity mask4, GCC14.2. CMake build type was blank, not Release. The exact configure/build commands and source/binary hashes are retained; do not silently reproduce with different optimization flags and mix timings.

New optional CLI: --round96-route-order true (default false), preset research-round96-ensc-route-order. It is admitted only on the frozen ENS startup; LP-G/H-ACT combinations are rejected by tested CLI gates. All 30 exact per-arm commands, caps, inputs, hashes and environments are in external/identity.json and primal/identity.json and raw launch.json files. Independent generated H1–H6 and V1/V2 inputs are tracked under reference/round96_external.

## Effective evidence and original failures

Use external_v2/summary.jsonl (18 rows) and primal_v2/summary.jsonl (12 rows). Respect each row's audit_path when present. Original external row16 and primal row3 failed audits remain immutable. H6/LP is an administrative hard stop with a verified committed observational endpoint, not a normal final result; missing full Optimize/phase CSV is not reconstructed. Its 5 native calls are counted from the verified journal. F5/ON was a native-reader arm-label dispatch repair; the actual preset and all settings/physical/scope/trace checks remain enforced. Neither recovery reran Optimize.

Raw destinations retain normal result.json or journal observations, input/model identities, native logs, call settings, witnesses and ledgers. Extract archives into a separate review directory if desired; relative paths preserve repository layout. Do not overlay user data blindly. Each archive's JSON index contains member hashes; exact source and original frozen executable identities remain independently bound even though executables/licenses are not redistributed.

## Zero-Optimize summary reproduction (PowerShell)

Run from E:/codes/ExactEBRP with a fresh output label, e.g. reviewer1 if absent:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round96_external_report.py reviewer1
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round96_primal_report.py reviewer1
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round96_trajectory.py external_v2 reviewer1
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round96_trajectory.py primal_v2 reviewer1
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round96_cost_report.py reviewer1
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round96_derived_numeric.py external_v2 reviewer1
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round96_derived_numeric.py primal_v2 reviewer1
```

Run heavier model replays only without an optimizer/build active. Existing complete outputs are already provided; these commands are optional reviewer reproduction, not unperformed checks. The derived check uses declared domains as inputs and does not replace the scope/coverage audit. It covers listed current-model families only. Re-running micro/build/solver tests would be another research execution; retained qualification artifacts already establish the reported outcomes.

## Navigation

final_report.md gives all decisions and negatives; mathematical_algorithm.md gives model and controller proofs; fixed_route_report.md and fixed_route_protocol.md define the restricted diagnostic; route_order_protocol.md / route_order_mechanism.md / route_order_admission.md define the prototype; primal_final_decision.md gives complete validation. evidence_index.md maps archives and primary machine-readable summaries. RESUME.md records the final stopped state; nothing is scheduled to resume automatically.
