# Round92 G1 v2 conditional runner handoff

No execution has been admitted or performed. The 15 relevant source and test
files are enumerated with exact bytes/Git blob identities in
`physical_envelope_source_identity.json` (SHA-256
`02dbca61efb415d64561a9a15a868b7f8822354b8c0afb4c2f76675b8bbf6bbf`),
source commit `ea190d909bbc8fbb0caaaada78c928f71be18bc1`.
`preregistration_g1_v2.json` pins the four **current** qualified v1 binary
hashes from Q001/Q002. The failed Q001 integration executable is a different
historical binary and is not one of the four to preserve.

The thin runner `scripts/round92_g1_v2_qualification.py` requires a later
root-signed `g1_v2_execution_admission.json` with `allow_run=true`,
`allow_configure=false`, `allow_optimize=false`, zero Optimize calls, the
source commit, source-identity SHA, exact runner SHA and preregistration SHA.
Before any output mutation it checks the 15 explicit source files, exact four
old binary hashes and fresh destination paths. No repository/raw tree scan is
needed. Once admitted, its single ordered invocation performs:

1. Copy only the four v1 binaries to fresh internal `qualified_v1` and
   independently hash each copy. Do not copy the whole build or source.
2. Incrementally build `ExactEBRP`, `Round92HandlingActivationTests`, and
   `Round92HandlingIntegrationTests` with existing CMake/Ninja, `--parallel 4`.
   No configure and no changed compiler flags.
3. Run exactly the pure and CLI identity/rejection CTests once.
4. Run the actual canonical fixture exporter once into fresh Q003 evidence.
5. Parse/read the exported LPs once using the qualified Gurobi Python binding,
   without Optimize.

The runner uses structured subprocess argv, binary stdout/stderr files, native
child exit codes even when stderr is nonempty, UTC start/finish and outer stage
walls. It records one full in-run elapsed wall covering preflight/stages and
build-rule/CMakeCache SHA plus selected actual flags/commands before and after
the incremental build; it explicitly rejects fast-math/reassociation flags.
The initial configured build has `CMAKE_BUILD_TYPE` empty and generic
`-std=c++17 -Wall -Wextra -Wpedantic` flags; do not describe it as Release.
The future execution owner must also record the separate **full external
Python launch-to-exit** wall, which the process cannot measure from inside.
Any failed stage leaves its started/receipt/stdout/stderr prefix and terminates
the batch; no automatic repair or retry. Q001/Q002 raw receipts, old binaries
and the separate frozen Round90 executable remain untouched.

Proposed single eventual command, only after an explicit root execution gate
and D6 slot release:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' 'scripts/round92_g1_v2_qualification.py' --admission 'results/unified_exact_round92/g1_v2_execution_admission.json'
```

The venv Python is used only as the child for the zero-Optimize Gurobi readback.
G1 completion is structural/numeric qualification only; native G2/G3 remain
closed until separately reviewed and admitted.
