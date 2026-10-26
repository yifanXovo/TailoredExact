# Round92 physical-envelope v2 G1 attempt 003 — stopped at pure fixture

The root-signed admission `../g1_v2_execution_admission.json` (SHA-256
`e5af7fc2b73528f4bea4688abd520017c1faebce1fd1f1965c6129355aedefd0`)
authorized one zero-Optimize run of committed v2 source
`ea190d909bbc8fbb0caaaada78c928f71be18bc1`. Exactly one external Python
launch occurred. Its real child exit was **1** and full launch-to-exit wall
was **13.9437196 s**, recorded in `../g1_v2_outer_001.receipt.json` with
original stdout/stderr. No retry, source repair, exporter, Gurobi LP readback,
native solver or Optimize occurred.

| Ordered stage | Child exit | Complete stage wall | Result |
| --- | ---: | ---: | --- |
| Preserve four qualified v1 binaries | 0 | 0.6316054 s | Exact SHA/size matched each copy in internal `build/research/round92-handling-activation/qualified_v1`. |
| Incremental three-target build, parallel 4 | 0 | 11.8333492 s | New main/core/pure/integration binaries produced; actual commands and warnings retained. |
| Focused pure + CLI CTest | 8 | 0.8463497 s | CLI passed; pure `Round92HandlingActivationTests` failed: `2-station independent integer route oracle differs`. |

`run.receipt.json` reports full **in-run** wall 13.7513060 s and the failed
stage prefix; this is nested inside the external 13.9437196 s and is not
added to it. The CTest stdout/stderr and actual native exit code are retained.
The failure points to a pure oracle expectation left in the v1 form: it
compares the upper-floor row with the exact `T`-only integer floor while v2
uses the uniform physical acceptance horizon. This is a source-level
diagnosis, **not** an assertion of the expected corrected result or permission
to edit/retry. Root must separately review any narrow repair and freeze a new
execution admission.

The pre/post build rule SHA-256 values matched: CMakeCache
`25249ecdcb27b7d4d427e0a36050ebe4c743a774786df8688d66aa60ed6074a3`,
`build.ninja`
`76c4914506ff9b71dd30e18a8b0957405d644685426a5d69ad404bbe0416a8a3`,
`CMakeFiles/rules.ninja`
`ae3a93ffbfcad280135a6a4d134aa91de5deaaf395f32cd2080b1f821f498bf8`.
`CMAKE_BUILD_TYPE` was empty; actual compile flags were
`-std=c++17 -Wall -Wextra -Wpedantic`, with no fast-math/reassociation flags
in the captured rule lines. Full rule and command evidence is in
`compile_contract.before.json`, `compile_contract.after.json` and build logs.

`v2_binary_hashes.json` records the new main/core/pure/integration SHA-256
values. `preserve.stdout.log` records the four v1 source/copy identities;
the previous Q001/Q002 reports and raw LPs remain unchanged. The frozen R90
binary was untouched. Postflight process inspection found no residual
ExactEBRP/Round92/Gurobi/CMake/CTest/Ninja/compiler/runner process. The
exclusive computation slot was released immediately after the stopped run.
