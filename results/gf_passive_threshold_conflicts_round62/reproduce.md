# Round 62 reproduction

Base: `4a9cbd0e3d43870e953b3a6678b343a9ac4fc25a`, branch
`codex/round61-transfer-block-native-time-oracle` (PR #122). This round is a
stacked research change; it does not promote an option in the stable preset.

## Build and solver-free checks

The measured host is Windows 10, Intel i7-12700KF, Gurobi 13.0.2. The compiler
and CMake configuration are recorded under `local_raw/preflight/` and in the
final build/test evidence. On this host, from the Round 62 worktree:

Measured solver implementations are frozen as v1/v2/v3. After all 72 runs,
v4 only adds the already-implemented `projection-service` value to the CLI
help string; it has no timing observations. `final_validation.json` verifies
that reversing this single byte-string edit exactly restores the v3 source
hash, while every other source file is unchanged. All 39 solver-free CTest
targets pass for both v3 and v4 (`tests_v3.log`, `tests_v4.log`).

```powershell
$cmake62 = 'D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$ctest62 = 'D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
$python62 = 'D:/msys64/ucrt64/bin/python.exe'
$env:PATH = 'D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;' + $env:PATH
& $cmake62 -S . -B build/round62 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/c++.exe -DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
& $cmake62 --build build/round62 --parallel 4
& $ctest62 --test-dir build/round62 --output-on-failure
```

Use a separate checkout/build directory for a fresh campaign. Do not compile
while a performance process is running. The runner refuses to overwrite a
destination or exceed 72 charged launches, uses an exclusive process lock,
checks input and executable hashes, and includes failures in the ledger.

For a fresh, bounded local pair without touching this campaign's ledger:

```powershell
$env:EBRP_ROUND62_RESULTS = 'results/round62-replay'
& $python62 scripts/round62_research.py freeze
& $ctest62 --test-dir build/round62 --output-on-failure > build/round62/tests.log
& $python62 scripts/round62_research.py build-freeze --build-id replay
& $python62 scripts/round62_research.py solve --ids D4 --modes off projection --stage replay --cap 120
& $python62 scripts/round62_research.py full --ids D3 --modes off passive-cert --stage replay --cap 600
Remove-Item Env:EBRP_ROUND62_RESULTS
```

The environment variable changes only the destination under this checkout.
It does not change the inputs, physical budgets or optimizer settings. A new
compilation is a new paired build; do not substitute its times into old pairs.

`protocol.json` freezes input paths/hashes, actual lambda/handling/T, eight roles,
PREFIX and the unchanged F0/K1 policies. D3 T=2850 and D4 T=2400. C2 is
development. C1/C3 are previously public instances not used for Round 62 rule
selection. Confirmation requires `confirmation_freeze.json` before launching.

## Explicit research interfaces

- Full Single-S: preset `research-round59-f0-single-s`.
- Full K1-S: preset `research-round59-k1-s`.
- `--round62-archive-mode off|passive-observe|passive-cert|outer|submit`.
  `outer` is the retained Round 61 post-native merge (`archive`) behavior.
- `--round62-threshold-mode off|events|conflicts|projection|service|service-conflicts|projection-rlt|projection-service`.
- Fixed F0 harness: `Round50IntervalMipExperiment --round59-empty-state
  --round59-current-f0 --round61-candidate-mode off`, with the same threshold
  option. Candidate modes and fixed/full certificate scopes must not be mixed.
- `Round62ThresholdProbe` generates bounded automatic proof records. Its
  optional `--events` is explicitly a regression diagnostic and does not seed
  the production generator.
- `Round61TimeOracle --threshold-decision --thresholds i:sign:q,...` keeps
  all nonlisted inventories free and all original stations available. Sign -1
  means pickup, +1 means drop. `--force-native` is a charged diagnostic bypass
  of the cheap proof, never an automatic callback subproblem.

The initial dictionary contains at most 2V maximal feasible direction events;
the shared generator permits 50,000 clique-search nodes, 64 seed cliques,
4,096 weakening checks and 32 retained conflicts. These limits are not tuned
by input name or observed performance. No added user cuts, PreCrush, starts,
hints or native branching settings are used by the threshold ablations.

## Executable experiment examples

The following commands are examples for a fresh campaign; the archived
campaign has already used these destinations. Each starts charged processes:

```powershell
& $python62 scripts/round62_research.py proof --ids D4 D3 D6 D7 --stage proof_v1
& $python62 scripts/round62_research.py lp --ids D4 --modes off events conflicts projection service service-conflicts --stage lp_v1 --cap 120
& $python62 scripts/round62_research.py solve --ids D4 --modes off events conflicts projection service service-conflicts projection-rlt --stage mip_v2 --cap 120
& $python62 scripts/round62_research.py full --ids D3 C2 D7 --modes off passive-cert --stage long_v2 --cap 600
& $python62 scripts/round62_research.py k1 --ids C2 --modes off passive-cert --threshold projection --stage k1_v2 --cap 600
```

`processes.jsonl` and each launch record contain the **complete actual command**,
build freeze, executable hash, input identity, cap and unique charged number.
All measured v1, v2 and v3 binaries are preserved in
`E:/codes/ExactEBRP-round62/results/gf_passive_threshold_conflicts_round62/local_raw/paired_executables/`;
`paired_executables_v1.json`, `paired_executables_v2.json` and
`paired_executables_v3.json` bind names to hashes.
Recompiling final source is not a byte-identical replacement for those binaries.

## Read-only analysis and independent verification

```powershell
& $python62 scripts/analyze_round62.py
& $python62 scripts/verify_round62.py
& $python62 scripts/report_round62.py
& $python62 scripts/package_round62.py
```

To verify only the committed evidence in a clone without local raw logs, use
`python scripts/verify_round62.py --submitted`. It checks all saved physical
witnesses and distinct mathematical threshold proofs without overwriting the
measured tables. Full LP-point and native-lifecycle reconstruction additionally
requires the local raw artifacts identified by path and hash.

These commands do not call an optimizer or generate new candidates. They
recompute route inventory, original arc travel, every load prefix, original
T feasibility and F from inputs; recompute every retained threshold edge and
row (using rational ratios for box coefficients); check legal continuous event
completion; aggregate recorded passive snapshots; and generate measured pairs
and budget tables. Oracle routes have a separate diagnostic scope.
Run packaging only after every performance process has ended: it hashes the
local raw artifacts into `raw_evidence.csv`, retains compact native lifecycles
and diagnostic results, and writes `evidence_index.json`. The complete campaign
cannot be extended beyond its 72 charged launches.

`solver_calls_planned` is a prelaunch hint; some inherited hints use the old
`native_lifecycle.csv` name. The actual full-algorithm counts and per-call
evidence come from `external/paper_optimize_ledger.csv`, as recorded in
`budget.csv`'s `call_evidence` field. The immutable launch records are retained.

The separate `Round62ProjectionAudit` executable is a **charged** diagnostic:
it runs at most 33 LP optimizations under one process cap, minimizing each
generated box projection's activity over a frozen OFF LP with its original
cutoff row (up to 32 calls), then restoring the original F objective and
adding service projection for one extra LP. The required
`--expected-model-sha256` binds that source model. Binary
bounds remain [0,1] when integrality is relaxed. `native_calls.csv` records
each call before optimization; `queries.csv` records finalized status/quality.
`verify_round62.py` checks the saved maximum-violation point against every
original LP row and domain. This distinguishes containment from improvement
of the original objective bound and does not feed a candidate into formal runs.

`runs.csv` keeps full and fixed-domain certificate fields separate. `pairs.csv`
uses one frozen executable, common cap and common scope per pair; it applies
the predeclared 10 s + 10% certification-time and 0.001 + 5% uncensored-gap
thresholds. Certificate changes are always separate. An uncertified wall time
is reported as budget use, never as the time needed to solve the instance.

The raw canonical LPs, native logs, progress/node samples and binaries remain
under the ignored `local_raw/` directory. Compact necessary witnesses, proof
records, independent verification and measured tables are committed. Source
and build hashes, together with launch commands, distinguish measurements
from later metadata-only packaging fixes.
