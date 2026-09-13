# Round64 reproduction and evidence map

The research checkout is `E:/codes/ExactEBRP-round64`, branch
`codex/round64-shared-load-time`, based on Round63
`f734d6781fd7125703489245cdb4dc27fb74625c`. The original dirty checkout at
`E:/codes/ExactEBRP` is separate. See `restoration.json` for the inherited
Round63 service/resource/packaging identities; they are different commits.

## Build and optimizer-free checks

The measured environment uses Windows, MinGW UCRT64, Gurobi 13.0.2 and a
Release build. No license or credential is included. With CMake on PATH:

```powershell
$env:PATH = 'D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;' + $env:PATH
cmake -S . -B build/round64 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
cmake --build build/round64 --parallel 4
ctest --test-dir build/round64 --output-on-failure
```

All 41 CTests are optimizer-free, including `Round64Tests`. They cover
route embeddings, resource identities, physical edge cases, mapping and
default-off model isolation. Native feasibility and Farkas checks are charged
experiments, not hidden in CTest.

`build_freeze_v1.json` through `build_freeze_v4.json` bind
source commits, source-file hashes, executables, test logs and protocol.
v2 adds the auxiliary projection executable; its main/fixed executables are
identical to v1. v3 adds current-run startup witness persistence without
changing model/search rules. v4 adds QCAP and its eight-LP diagnostic; all
existing F0/Q model identities remain unchanged. Formal pairs always use one
executable hash. Local retained v1/v2/v3 binaries are under `build/round64-v1`,
`build/round64-v2` and `build/round64-v3`; current v4 binaries are under
`build/round64`.

## Inspect and recompute existing evidence

```powershell
python scripts/report_round64.py --audit
python scripts/verify_round64.py --preflight
python scripts/verify_round64.py
python scripts/verify_round64.py --package
python scripts/verify_round64.py --submitted
python scripts/report_round64.py --index
```

Run large audits/indexing only when no optimizer process is running.
`processes.jsonl` is the immutable write-ahead launch ledger; all native calls,
including interrupted/infeasible calls and diagnostics, are counted in
`optimizer_calls.csv` and `budget.json`. `runs.csv`, `pairs.csv` and
`measured_tables.md` are generated, rather than hand-transcribed endpoints.
Uncertified wall time is consumed budget, not solve time. Fixed-F0 certificate
scope is distinct from the full original-problem certificate.

The independent verifier reconstructs original physical route feasibility and
F, complete LP rows/bounds and fixed-original-variable controls. For Farkas
evidence it reconstructs the physical auxiliary matrix from input Q and the
safe resource data; it checks signs, finite-bound corrections, every column,
the projected row and raw violation. These diagnostic certificates do not
certify original-objective optimality and are never submitted to search.

`warm_state_verification.csv` and `warm_pairs_verification.csv` bind actual
current-process HGA routes/U/initial domains and disabled native starts.
`native_lifecycle.csv`, `native_model_shapes.csv`, `native_call_costs.csv` and
`parameter_verification.csv` expose actual reuse, row/column cost and readback.
`primal_timing.csv` uses accepted, verified original U events on the process
clock. `native_incumbent_observations.csv` separately preserves per-call native
discovery lines at the log's integer-second precision; those rounded native
values are not independently verified witnesses until extraction at call end.

## Re-run an experiment without overwriting evidence

Every launch stores its complete argument array, executable SHA, cap and
destination. Use that array to reproduce exactly the same physical and
algorithm settings. The driver refuses reused destinations and enforces a
single optimizer lock, charged maximum 72 and native-micro maximum 4. Do not
re-run native micro in this completed research ledger. No free replay is used
for formal warm results.

For a separate reproduction campaign, set `EBRP_ROUND64_RESULTS` to a new
directory under the checkout, copy the frozen `protocol.json` to that directory,
and create a new build freeze using `build-freeze --version reproduction`.
Use unique stage names. For example, the C2 development matrix is:

```powershell
python scripts/round64_research.py warm --ids C2 --modes off q sep joint --stage warm_reproduction --cap 600
```

The D7 warm matrix uses cap1200 and the same four modes. Cold full K1 uses
`cold`; the fixed-F0 harness uses `fixed`; `reference` runs unchanged P-GRB and
stable K1-H. Structural `probe` uses seven LPs under one shared cap;
`qcap-probe` uses eight LPs, including re-completion at Q and SEP optima;
`projection` uses two auxiliary LPs under one shared cap. Their required
canonical inputs/pins and expected identities are explicit in the driver.
Confirmation needs an independent candidate freeze before opening either
role; the original confirmation cannot be retrospectively relabeled as new.

Large original logs/models/points/binaries remain under
`results/gf_shared_load_time_round64/local_raw` and `build`, excluded from Git.
`evidence_index.csv` records local paths, byte counts and SHA256. Submitted
route snapshots are in `witnesses`, and their physical checks can be repeated
without the large native logs. `projection_evidence/D4.json` and `D7.json`
preserve sparse SEP completions, normalized dual support, the physical point
and the safe resource matrix data. The submitted verifier reconstructs the
physical equations and rechecks feasible SEP versus strict JOINT exclusion.
Unlisted auxiliary values are exactly zero; no tolerance pruning occurs.
Their membership in the full target F0 is separately tied to the original
point SHA and complete local LP residual audit. Packaging creates no new
projection experiment and calls no optimizer. All negative and failed-run identities remain
in the launch ledger. No model or performance data from the user's dirty
workspace is used.
