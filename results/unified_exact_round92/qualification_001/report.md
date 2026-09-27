# Round92 G1 qualification attempt 001 — stopped at exporter fixture

Admission: [`g1_admission.json`](../g1_admission.json), SHA-256
`172771aaffe434993106b8a043e5352bd240bd9ee8340a6b1f1e1c226e25348c`.
Frozen source commit `ac23af96380d22342db7dfd2a0daa75584197257`;
all 12 admitted source SHA-256 values matched again after the stopped attempt.
The installed VS2022 CMake/Ninja and UCRT64 GCC 14.2.0 configured a **fresh**
`build/research/round92-handling-activation` with Gurobi root
`D:/gurobi1302/win64`. No old build or binary was replaced.

| Ordered command | Exact argv/UTC start, logs and receipt | Exit | Nested command wall |
| --- | --- | ---: | ---: |
| configure | [`configure.started.json`](configure.started.json), [`stdout`](configure.stdout.log), [`stderr`](configure.stderr.log), [`receipt`](configure.receipt.json) | 0 | 2.7073477 s |
| build, `--parallel 4`, only main and two R92 tests | [`build.started.json`](build.started.json), [`stdout`](build.stdout.log), [`stderr`](build.stderr.log), [`receipt`](build.receipt.json) | 0 | 31.8415172 s |
| pure + pre-Optimize CLI CTest | [`ctest.started.json`](ctest.started.json), [`stdout`](ctest.stdout.log), [`stderr`](ctest.stderr.log), [`receipt`](ctest.receipt.json) | 0; **2/2 passed** | 1.0872051 s |
| one canonical fixture exporter | [`export.started.json`](export.started.json), [`stdout`](export.stdout.log), [`stderr`](export.stderr.log), [`receipt`](export.receipt.json) | nonzero; wrapper recorded −1 after a PowerShell `NativeCommandError` on the child's stderr | 0.3810888 s |

The exact launched command and environment prefix are in each `*.started.json`.
All outputs/failed prefixes were retained. Configure/build/CTest/export nested
command walls total **36.0171588 s**; separate PowerShell launch/report overhead
is not included in that sum. Build warnings in older Round61/Round62/Gurobi
source are preserved in the build log; there was no compile error.

The exporter created `five_station_input.txt`, `off.lp`, `on.lp`, `reused.lp`
and `invalidated.lp` before failing. The off LP SHA-256 is exactly the frozen
Round91 L0 SHA `9872d149c970c99f2b0175929221fb42692c6915a68a4e57e94dd1492fb79a29`.
Candidate `on.lp` and same-key `reused.lp` have identical SHA
`fd4e3134e34c378682740836983a97880f51c23f1e4ad50f4589a3819c78ec57`;
changed-arc `invalidated.lp` has SHA
`55cf181a00e4617734b84a83d27c3ee7dee2dc900bb44bb02c615e6b66f67fef`.
These are partial exporter observations, **not** a passed full LP readback.

The failure is confined to the negative F1 fixture. The test set explicit
connectivity variant `f1` but left the K1 preset's legacy F0 bool true.
`resolveConnectivityFlowVariant` therefore rejects the contradictory pair
with `conflicting_legacy_and_explicit_connectivity_flow_variants` before the
candidate's own F0 guard. The test expects the later
`round92_requires_canonical_interval_F0...` reason and prints
`candidate accepted non-F0 connectivity`. This message is misleading: the
model was rejected before Optimize, but the fixture did not reach the
intended guard. Narrow test-only repair would clear the legacy bool when
setting explicit `f1`; it requires a new root freeze/admission before any
rerun. Because PowerShell 5 promoted native stderr to a terminating error,
the receipt records wrapper code −1; the child's exact native exit code is
not independently captured. A future admitted launcher should preserve it.

**Stopped as signed.** No exporter retry, Gurobi Python readback, native
solver run, or Optimize occurred. The no-row `c=0` fixture was not reached.
Postflight at `2026-09-27T10:21:24.9665094Z` found no matching Round92,
ExactEBRP, Gurobi, CMake, CTest, Ninja or compiler process. Computation slot
released. See [`artifact_index.json`](artifact_index.json) for exact hashes
and sizes of the build binaries, partial LPs and all retained receipts/logs.
