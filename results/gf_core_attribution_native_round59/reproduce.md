# Reproduction and evidence map

Repository: yifanXovo/TailoredExact. Base: Round58
`edd65fe9f5bd37616366c1c6ca48379df062cdcf`, not main.
All paths below are relative to the repository. Use the frozen original
input files in `panel.json`; do not replace T with the harness default.

## Builds

The full-instance attribution executable was built at
`a93685308d68e0269fcb70e857162fa686390ee2`. All four arms, including
confirmation, use that exact SHA256 recorded in `build_identities.json`.
Current fixed-state diagnostics use the model-alignment commit
`2592c1950` and the separate diagnostic executable hash in the same manifest.
Pairwise comparisons always use one executable identity. These separate
series are not presented as a matched direct timing comparison with each other.
The final literal-original/F0 pairs use `d50e1e413`, with both canonical F0
identity and the original P-GRB origin checked before performance. Earlier
`Compact` raw labels mean pack removal with connectivity retained.
The final source also contains analysis scripts and default-off tests.

Configure with CMake, MinGW Makefiles, Release, Gurobi 13.0.2 at
`D:/gurobi1302/win64`, g++ 14.2 at `D:/msys64/ucrt64/bin/c++.exe`.
Build `ExactEBRP`, `Round50IntervalMipExperiment`, and the CTest targets.
The original build directory is `build/round59-core`; compiler and runtime
paths are recorded in the environment audit. For an exact historical
binary comparison, use an isolated checkout of the recorded source commit.
Do not overwrite the existing results or clean the shared checkout.

## Run commands

Every actual command, executable hash, start time and charged process number
is in `processes.jsonl`. Each local run has `launch.json`, `completion.json`,
logs, native model and result. The serial runner refuses to overwrite a
completed successful run and refuses to exceed 80 charged attempts.

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round59_research.py development
& D:/msys64/ucrt64/bin/python.exe scripts/round59_identity_check.py
& D:/msys64/ucrt64/bin/python.exe scripts/round59_research.py roots
& D:/msys64/ucrt64/bin/python.exe scripts/round59_research.py cuts
& D:/msys64/ucrt64/bin/python.exe scripts/round59_research.py focus
& D:/msys64/ucrt64/bin/python.exe scripts/round59_research.py startup_state
& D:/msys64/ucrt64/bin/python.exe scripts/round59_research.py original
& D:/msys64/ucrt64/bin/python.exe scripts/round59_research.py confirmation
```

`freeze` is intentionally not rerun. Original failed/mismatched experiments
are documented in `T_correction_audit.json` and `identity_correction.md`.
Those attempts still consume budget. A new reproduction should use a new
result directory and separately named budget ledger, not resume or overwrite
the original series. The script's unused callback and longer-cap entry points
are infrastructure, not evidence that those experiments were executed.

## Analysis without solver processes

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/analyze_round59.py
& D:/msys64/ucrt64/bin/python.exe scripts/verify_round59_routes.py
& D:/msys64/ucrt64/bin/python.exe scripts/round59_relaxation_census.py
& D:/msys64/ucrt64/bin/python.exe scripts/round59_report_data.py
& D:/msys64/ucrt64/bin/python.exe scripts/round59_tables.py
& D:/msys64/ucrt64/bin/python.exe scripts/round59_finalize_audit.py
```

`full_instance_results.csv` and `paired_results.csv`: original-problem
certificates and common-budget bounds. `certificate_seconds` is blank for
uncertified instances, even if their process reached a limit.

`fixed_state_results.csv`: all diagnostics with explicit current/legacy
model scope. `native_mechanism_results.csv` and `native_mechanism_pairs.csv`:
only identity-corrected current diagnostics. Their certificates remain
restricted-state evidence and are never counted as full-instance wins.

`native_trajectory_checkpoints.csv`: native optimization clock, with no
end-to-end gap-integral claim. `relaxation_census.csv`: original-coordinate
observations and pair-cut necessary-condition/violation counts.
`propagated_inventory_domains.csv`: sum of individual integer domain sizes,
not a product and not a certificate that every inventory vector is routable.

Large artifacts are local under
`E:/codes/ExactEBRP/results/gf_core_attribution_native_round59/local_raw`.
The final local manifest records paths, sizes and SHA256. Raw native logs,
LP models and binaries are not committed. No license files or credentials
are copied into the result directory.
Ten original P-GRB progress CSV files remain in their existing
`results/gurobi_work/...` directories and are also included in the local
manifest. Their legacy callback `solution_count` column is excluded from
analysis because of an integer/double read mismatch; the final source fixes
this telemetry-only issue after all performance runs. Final attributes and
independent route verification, not that column, govern certification.
`full_global_bound_events.csv` keeps selected original events/checkpoints;
the complete traces remain local and no gap integral is inferred.
