# Round 88 A1 — constructive-only decoded descent

Status: implementation and microscopic qualification complete; independent review pending. No eight-instance performance campaign was started.

The default ENS-C preset `research-round83-vds-equal-net-exchange` still runs its 24 random decoded-descent seeds followed by the one independently verified joint-insertion seed. The default decoder, cache limit, guided neighborhood, strict improvement rule, physical closure and full exact proof were not changed. The new, default-off `--round88-constructive-only-descent true` switch is accepted only with that ENS-C preset. It retains joint insertion and its physical verification, but initializes the existing decoded-descent loop with only that constructed order. It makes no instance-, clock-, Work- or hardware-based choice. The inherited `iterations=10` is ignored by the active compact-full decoder and does not control this ablation.

The mathematical distinction is the initial route-order set (one instead of 24+1); all later acceptance and proof rules are inherited. On full completion, the single path is the same logical constructive-seed path that ENS-C runs as seed 25, with its local seed index renumbered to 1. Whole-run interruption remains an incomplete result, and a verified zero may still stop through the existing mathematical rule. Physical closure and exact optimization receive the best verified constructed/descended witness as before.

Candidate identity is `research-round88-ensc-constructive-only` in normal result JSON, candidate model identity, candidate source label, phase journal label and emergency result JSON. The internal `SolveOptions.algorithm_preset` remains Round83 so all inherited ENS-C dispatch stays intact. The default Round83 result identity and output feature list remain unchanged. The switch rejects any other preset; the runner also rejects a missing joint seed, a non-interroute mode or a generation quota, and the GA rejects enabling it without a validated permutation seed.

## Reproduction

Build from the project root using the installed VS CMake/Ninja and MSYS2 UCRT64 compiler:

```powershell
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' -S . -B build/research/round88-a1 -G Ninja -DCMAKE_MAKE_PROGRAM='D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe' -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64 -DCMAKE_BUILD_TYPE=Release
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' --build build/research/round88-a1 --target ExactEBRP Round70DescentTests Round71InterrouteTests Round73JointInsertionTests Round73ConstructiveSeedTests Round83ExchangeDiagnostic --parallel 4
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build/research/round88-a1 --output-on-failure -R '^(Round70DescentTests|Round70DescentCliTests|Round71InterrouteTests|Round71InterrouteCliTests|Round73JointInsertionTests|Round73JointInsertionCliTests|Round73ConstructiveSeedTests|Round73ConstructiveSeedCliTests|Round83ExchangeDescentTests|Round83ExchangeDescentCliTests|Round88ConstructiveOnlyCliTests)$'
```

The research invocation is the ENS-C command with `--round88-constructive-only-descent true` added. Do not change `--primal-heuristic-runs` or use the old joint-insertion-only preset: neither expresses this intervention. The exact microscopic command and all output paths are in `tests/round88_constructive_only_cli_test.cmake`.

## Qualification and costs

Source reference: frozen ENS-C `4496078f25c0cdad1cf7a5c39835fd23121e8978`; Round88 branch parent `0bf04b71268d6a39d127a8a692b6410b1b66edfb`; documentation HEAD at build `15121fdfe08a5a31eefb38bdc81fae316e611eb6`. This A1 code is an uncommitted worktree change, not a commit of either reference. `qualification/a1_source_hashes.json` records the exact modified source bytes. The final `ExactEBRP.exe` SHA256 is recorded in `qualification/a1_build.json`.

Fresh configure took about 2.9 s; initial five-target build about 65.4 s and added joint-insertion test target 2.1 s. The identity repair rebuilt the affected core/main and links in about 30.0 s. Existing source produced compiler warnings (notably dynamic-library function casts and `AVLCalculator.h` signedness); no compile or link error occurred. `qualification/a1_ctest.log` preserves the first 11/11 pass before identity repair. `qualification/a1_ctest_final.log` preserves the final 11/11 pass (2.47 s), including both CLI certificates and the new identity checks. No test or build failure occurred; an initial local PowerShell result-inspection expression had a `-join` syntax error and was immediately corrected without changing artifacts.

The Round88 tiny CLI returned `optimal`, strict original-problem certificate, one completed decoded path, and U=L=0.208333333333333; the same-build default ENS-C CLI completed 25 paths and retained its Round83 identity. The tiny path has zero neighbor checks, so the extended Round73 structural fixture additionally compares every logical constructive-seed descent pass with the Round88-only pass and requires positive checks. The new CLI also verifies physical closure exhaustion, native optimization calls, Round88 candidate ledger source, correct emergency identity and rejection under a non-ENS-C preset. Unit checks cover absence of a seed and incompatible descent mode.

Remaining risks for independent review: the source identity is now split deliberately between internal Round83 dispatch and external Round88 attribution; verify all downstream consumers treat the external name as a candidate, including any third-party aggregation scripts. These micro fixtures establish semantics and certificate integration, not A1 performance value or robustness on the eight-case screen. Complete candidate timing and UB/LB comparisons remain a later authorized stage.
