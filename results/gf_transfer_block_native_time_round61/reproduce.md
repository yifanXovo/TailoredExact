# Reproduction

All paths below are relative to the repository root. The immutable input panel
and parameters are in `protocol.json`; exact original commands, executable
hashes, caps and charged numbers are in `processes.jsonl`. The runner refuses
overwrites, records before launch, uses a monotonic process clock and permits
one active optimizer. Constructor batches have five fixed methods and no
optimizer calls. Earlier quality_v1 batches had the three prerevision methods.

Machine: Intel Core i7-12700KF (12 physical / 20 logical cores), Windows 10 Pro
10.0.19045, Gurobi 13.0.2, MinGW UCRT64 Release build. Optimizers use one thread.
Builds and CTest ran before performance; no CPU-heavy compilation/testing was
run concurrently with the serial experiment suite.

The first build is frozen in `native_build_freeze.json`. Corrected triples,
long pairs, confirmations, initial K1 lifecycle and same-build references use
`corrected_build_freeze.json`. The final K1 equality-admission pair and D1
protection use `admission_build_freeze.json`. Every comparison matches binaries
within its own pair; these three builds are not interchangeable. The six initial
fixed120 D6/D7 rows must not substitute for their corrected counterparts. See
`mapping_correction.md` and `k1_admission_correction.md`. The mainline rejection
already follows from the recorded C2 confirmation; no final-build performance
claim is inferred from earlier binary identity.
After performance finished, `final_build_verification.json` records one final
compatibility fix and 38/38 tests: a failed legacy generation-log stream remains
silent when the new retention policy is off. No recorded experiment had that
failure. This changes neither the model nor the successful logging/search path;
it does not retroactively replace any paired executable hash.

## Build and tests

```powershell
$round61Cmake = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
& $round61Cmake -S . -B build/round61-reproduction -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/c++.exe -DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
& $round61Cmake --build build/round61-reproduction -j 2
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build/round61-reproduction --output-on-failure
```

Use the recorded source revision from the build freeze to reproduce that source.
Different compilers or rebuild paths may produce different binary hashes. A
reproduction build is valid to study reproducibility, but is not a replacement
for one arm of the original same-build comparison.

## Inspect, replay, analyze

```powershell
$round61Python = 'D:\msys64\ucrt64\bin\python.exe'
# Read-only by default; choose a charged number in processes.jsonl.
& $round61Python scripts/round61_replay.py --charged-number 34 --out results/round61-replay/D6-micro
# Add --run to execute. The replay selects a preserved matching binary when available.
# --allow-different-build explicitly records the use of a different binary.
& $round61Python scripts/analyze_round61.py
& $round61Python scripts/round61_tables.py
& $round61Python scripts/round61_completion_audit.py
```

`round61_replay.py` prints the exact command before execution and refuses an
existing output directory. Replay outputs are separate from the original
append-only ledger. Run replays serially and account for their own budget.
Preserved paired executables are listed in `paired_executables_manifest.json`
and stored locally under `local_raw/paired_executables/<sha256>/`; binaries are
not committed. The final source can also be rebuilt explicitly as a reproduction.
For a different reproduction build, place its executables at the path selected
in the printed command or adjust the standalone command explicitly.

The analyzer requires local raw files under
`results/gf_transfer_block_native_time_round61/local_raw/`. These include native
logs, canonical LPs, full progress and source event files. Their paths and hashes
are in `local_artifacts.csv`. Compact tables, selected proof records, complete
candidate witnesses and independent physical checks are committed. Running the
analyzer on a clone without local raw data is not a substitute for rerunning the
experiments. License files and credentials are neither required in artifacts
nor included in this PR.

`round61_conflict.py` executes the separately frozen bounded conflict attempt;
it is not a reporting command and refuses to repeat an already completed attempt.
`round61_cheap_time.py` is the charged, bounded solver-free proof batch, not an
additional free experiment. Its `--out` option allows a separate replay directory.
The time oracle is diagnostic and never changes original-problem certificates.
