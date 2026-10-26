# Round 55 final build and tests

The algorithmic source freeze is commit `6d0818126cd1d1c00029ea30f346c129d6093bfa`.
No file under `src/`, `include/`, `tests/`, or `CMakeLists.txt` changed after
that freeze. The clean Gurobi Release build is
`build/official-round55-final-6d0818126/`.

Executable SHA-256 values:

- `ExactEBRP.exe`: `3af8caf33b0437c6609871d11855be32e9a65f3e351e645de1c0751a10c3f397`
- `Round50IntervalMipExperiment.exe`: `5151efab9fbd82b91004e2255e60f112707278033d74549a4b0705000b681264`
- `Round55StationStateChainTests.exe`: `c1e6219d5f5f190b7de8cfb79f7c87f2895a289c2f9eb2a4dbaca1bd4f987267`

CTest passed 33/33 targets. `Round55StationStateChainTests` passed its 58
internal checks. Historical Python protocol discovery covered 237 distinct
tests; 195 passed in the complete discovery run, while four old suites lacked
their historical local executables. Those suites expose supported executable
overrides and then passed all 42 of their tests against the frozen backward-
compatible Round 55 executable. No behavior failure remained.

`git diff --check` passed. Post-freeze source-scope count is zero. The changed
code-file count after the final source freeze is zero, the secret-pattern scan
found zero matches, and no new third-party code or license obligation was
introduced. The host lacks compatible libasan/libubsan for the Gurobi build;
the non-Gurobi sanitizer limitation is recorded in `sanitizer_report.md` and
is not hidden as a pass.
