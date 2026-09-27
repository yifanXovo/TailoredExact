# Round92 G1 narrow repair qualification 002

Signed repair admission: [`g1_repair_admission.json`](../g1_repair_admission.json),
SHA-256 `773c571d1dcea1c37670779b9085c5f8d2e95a3a8599c8dfeb7d2e1b505dcb55`.
The sole source change at commit `b3698af57890b6252f58e1e144e3c17aafc59b23`
clears the K1 legacy F0 alias in the intentional F1-rejection test fixture.
All 12 admitted source hashes matched again after this qualification.
The original algorithm files, main executable and core static library did not
change. The previous pure and CLI CTests passed in attempt 001 and were not
repeated. No configure or Optimize was run in this repair attempt.

| Stage | Exact command/UTC/log/return evidence | Exit | Nested stage wall | Complete outer invocation wall |
| --- | --- | ---: | ---: | ---: |
| Preserve old test executable inside the same build | [`started`](preserve.started.json), [`stdout`](preserve.stdout.log), [`stderr`](preserve.stderr.log), [`receipt`](preserve.receipt.json) | 0 | 0.2114262 s | 0.5720356 s |
| Incremental build of **only** `Round92HandlingIntegrationTests`, `--parallel 4` | [`started`](build.started.json), [`stdout`](build.stdout.log), [`stderr`](build.stderr.log), [`receipt`](build.receipt.json) | 0 | 2.0665008 s | 2.4022058 s |
| Fresh fixed canonical exporter, once | [`started`](export.started.json), [`stdout`](export.stdout.log), [`stderr`](export.stderr.log), [`receipt`](export.receipt.json) | 0 | 1.1797593 s | 1.5200397 s |
| First Gurobi Python LP parser/readback, **zero Optimize** | [`started`](readback.started.json), [`stdout`](readback.stdout.log), [`stderr`](readback.stderr.log), [`receipt`](readback.receipt.json) | 0 | 1.0849545 s | 1.4123546 s |

Nested command walls sum to **4.5426408 s**; complete separately invoked
outer walls sum to **5.9066357 s**. The latter includes each PowerShell launch
and receipt write; neither sum is added to the other. Exact argv, environment
prefix and start time are in each `*.started.json`; full stdout/stderr are
preserved. Build stdout shows only recompilation of the repaired test object
and relinking of its executable. The old failure executable is preserved at
`build/research/round92-handling-activation/failed_001/Round92HandlingIntegrationTests.exe`
with SHA-256 `1cd17808cbde8dddf4028b1ab6c51394c39769d76799d7ac9886322017054180`.
The new test executable SHA is
`c806fcaf6321884e95b738438ad54c8904f90ad3179feb474bab0824dbe9310a`.
Main executable SHA remains
`bf99199172b9d783bcb55ad532d25f748348d08907a9f8b5b5de92bf9afe2524`;
core library SHA remains
`fd977d68e87ea5c116d33a25943abc8a036295e33c72c60c36bdf357c2e26be6`.

The exporter passed its fixed off/on row, exact-key reuse/invalidation,
candidate-only F0 rejection and emitted `c=0` valid-no-row branches. Off LP
SHA is still the frozen Round91 L0
`9872d149c970c99f2b0175929221fb42692c6915a68a4e57e94dd1492fb79a29`.
On and same-key reused LPs both hash to
`fd4e3134e34c378682740836983a97880f51c23f1e4ad50f4589a3819c78ec57`;
the changed-arc model hashes to
`55cf181a00e4617734b84a83d27c3ee7dee2dc900bb44bb02c615e6b66f67fef`.
All six generated input/LP identities and sizes are in the artifact index.
The first Gurobi readback found exactly two additional handling/activation
rows; the parsed original row multiset, objective, verified cutoff, G domain,
F0 connectivity columns, integer pickup and binary depot activation domains
matched the off model. Each new row followed its actual original duration
row with the expected coefficients. This is **zero-Optimize structural
qualification**, not a solver-validity or performance result.

Attempt 001 remains intact under `qualification_001`, including its failed
stderr, logs and partial LPs. Its index names the integration executable at
the original build path as it existed then; that path was overwritten by this
admitted incremental relink. The archived `failed_001` executable above
retains the old indexed bytes and SHA. No original raw LP/log was overwritten.
At `2026-09-27T10:25:21.7033108Z`, postflight found no matching ExactEBRP,
Round92, Gurobi, CMake, CTest, Ninja or compiler process; the exclusive
computation slot was released. No G2 native solve or G3 screen was started.
