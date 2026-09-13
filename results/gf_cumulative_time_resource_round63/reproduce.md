# Round63 reproduction

Use the isolated research checkout based on
71e955acad596acba2a9e74e738173113116d9f7 (Round62 / PR #123).
The original workspace is untouched. This campaign's measured builds have
immutable build_freeze_v*.json manifests; the active manifest is explicit.
Do not replace measured executable hashes with a later packaging build.

The paths below describe the measured Windows host. Prefer a fresh checkout
of the delivered PR for replay, so rebuilding cannot replace the retained
measurement binaries. New freezes describe replay builds, not historical timings.

```powershell
$cmake63 = 'D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$ctest63 = 'D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
$python63 = 'D:/msys64/ucrt64/bin/python.exe'
$env:PATH = 'D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;' + $env:PATH
& $cmake63 -S . -B build/round63 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/c++.exe -DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
& $cmake63 --build build/round63 --parallel 4
& $ctest63 --test-dir build/round63 --output-on-failure > build/round63/tests.log
```

Never compile, compress, perform Git maintenance or run large independent
audits during performance. All optimizers run serially. Every process uses
a shared monotonic cap, a write-ahead launch record and a shutdown allowance;
all native LP/MIP calls and bounded maxflow work remain in its charged record.

For a separate replay, choose a new output directory in the same checkout:

```powershell
$env:EBRP_ROUND63_RESULTS = 'results/round63-replay'
& $python63 scripts/round63_research.py freeze
& $python63 scripts/round63_research.py build --ids D3 D4 D6 D7 --modes off explicit simple --stage preflight
& $python63 scripts/round63_research.py build-freeze --version replay
& $python63 scripts/round63_research.py solve --ids D4 --modes off precrush dry cuts --stage screen --cap 120
& $python63 scripts/round63_research.py full --ids D3 --modes off --threshold projection-service --stage A --cap 600
Remove-Item Env:EBRP_ROUND63_RESULTS
```

The complete actual commands, input hashes, build identity, physical caps and
internal call bounds are in processes.jsonl and local_raw/*/launch.json.
Round63ResourceProbe accepts `--model PATH --expected-sha SHA` plus original
input/T/handling and a shared `--cap` of at most 300 seconds. Its `--micro`
mode makes at most 24 LP feasibility calls. Normal mode makes at most 67
original-objective LP calls across F0/explicit/simple/bounded mincut closure.
Its results are diagnostics, not original-problem objective certificates.

Run independent audits between performance queues:

```powershell
& $python63 scripts/analyze_round63.py
& $python63 scripts/verify_round63.py
& $python63 scripts/verify_round63.py --submitted
```

`--submitted` needs only the compact submitted witness collection and original
inputs. Full resource coefficient/point/LP checks additionally need the hashed
local_raw directory. The term streams are ordered per cut occurrence; initial
F0 reuse during closure must not be joined solely by the displayed last-query
number. Native optimizer logs give actual post-insertion sizes. API success,
native status, physical witness feasibility and strict certificates are separate.

Service qualification uses measured v3 source commit
b1bde3eab6c6fb9c4e1c4575acbdfa9141a46eaf (manifest build_freeze_v3.json).
Later resource development uses v4 source commit
dc8d3e4a0ee3f63f0858b2c3b38a59a92cd1e783 (build_freeze_v4.json).
v1/v2/v3 binaries are retained locally in build/round63-v1, -v2 and -v3.
v2's full-K1 micro safely rejects retained-model row
insertion and is excluded; v3 uses fresh models in root/root-dry and passes
the full-K1 micro. Do not mix these versions' timings.

For a separate full-lifecycle replay, initialize its own output root and
freeze the already compiled/tested replay build:

```powershell
$env:EBRP_ROUND63_RESULTS = 'results/round63-full-replay'
& $python63 scripts/round63_research.py freeze
& $python63 scripts/round63_research.py build --ids D4 C2 D7 --modes off explicit root root-dry --stage preflight_v4 --cap 120
& $python63 scripts/round63_research.py service-build --ids D3 D4 C3 --stage preflight_A
& $python63 scripts/round63_research.py build-freeze --version full-replay
& $python63 scripts/round63_research.py service --ids D3 D4 C3 --stage service_replay --cap 600
& $python63 scripts/round63_research.py full --ids D4 --modes off explicit root --stage resource_replay --cap 600
& $python63 scripts/round63_research.py k1 --ids C2 D7 --modes off explicit root --stage resource_replay --cap 600
& $python63 scripts/round63_research.py k1 --ids C2 D7 --modes root-dry --stage resource_replay --cap 600
& $python63 scripts/round63_research.py reference --ids C2 D7 --stage resource_replay --cap 600
& $python63 scripts/report_round63.py
Remove-Item Env:EBRP_ROUND63_RESULTS
```

The driver rejects semantic engine failures even if the native executable
returns zero. Optimizer counts distinguish write-ahead backend attempts from
actual calls that reach optimize (the failed v2 micro has 4 versus 3).
`report_round63.py --index` hashes the complete local evidence set and copies
sparse cut records for delivery; run it only after all performance ends.
It also records actual post-insertion native matrix sizes and native root
relaxation summaries where available. `coupling --ids D6 D7 --stage coupling_replay
--cap 120` uses four original-objective/fixed-point LP calls per instance and
expects the matching OFF source in local_raw/preflight_v4/<id>/off. This B4
diagnostic is distinct from the original mincut closure; the `coupled` mode
has no implemented separator for its additional node-throughput lower bounds.
For that optional diagnostic, first build the D6 OFF model in the same output
root with `build --ids D6 --modes off --stage preflight_v4 --cap 120`.

The active first-class K1 tau is read from adaptive_mass_decision_ledger.csv
(0.08). The compatibility C6 rho field remains 0.01 and is not that threshold.
Work is summed Gurobi Work; process wall additionally includes graph/model
construction, heuristic startup, validation, recording and cleanup.

The native research switch is `--round63-time-mode MODE` (default `off`).
The full executable permits non-off values only with the two named cold
research presets; stable K1-H and official P-GRB are not silently extended.

| Mode | Added formulation / execution |
| --- | --- |
| off | Original canonical model and native lifecycle |
| explicit | Full continuous cumulative-time flow block |
| simple | Whole-set and singleton projected rows |
| precrush | PreCrush=1 isolation only |
| dry / cuts | Same bounded native separation and PreCrush=1; only cuts submits rows |
| root-dry / root | Same first-required-LP observation and fresh native models; only root inserts the cached static rows in MIPs |
| coupled | Explicit flow plus carried-load node-throughput lower bounds; no corresponding complete projection separator |

Fresh native models discard retained native state, not merely add read cost.
Only completed process records are suitable for endpoint comparisons; native
CSV streams can remain buffered until finalization. Each actual optimizer
call is still accounted for in the completed native ledger.

The delivered uniform selection is `root`, made after launch 52 and before
the C3 follow-up. A replay of that fixed selection uses the following sequence
inside a new output root; do not run it over the delivered evidence directory.
The selection is for diagnostic confirmation and does not claim promotion.

```powershell
$env:EBRP_ROUND63_RESULTS = 'results/round63-full-replay'
& $python63 scripts/round63_research.py build --ids C3 --modes off root --stage preflight_final_dev_v4 --cap 120
& $python63 scripts/round63_research.py k1 --ids C3 --modes off root --stage full_dev_v4 --cap 600
# Replay the published selection; the new freeze binds the current replay build.
Copy-Item -LiteralPath results/gf_cumulative_time_resource_round63/selected_candidate.json -Destination results/round63-full-replay/selected_candidate.json
& $python63 scripts/round63_research.py confirm-freeze --modes root --cap 600
foreach ($confirmationId63 in @('C4','C5')) {
    & $python63 scripts/round63_research.py build --ids $confirmationId63 --modes off root --stage preflight_confirmation_v4 --cap 120
    & $python63 scripts/round63_research.py k1 --ids $confirmationId63 --modes off root --stage confirmation_v4 --cap 600
    & $python63 scripts/round63_research.py reference --ids $confirmationId63 --stage confirmation_v4 --cap 600
}
Remove-Item Env:EBRP_ROUND63_RESULTS
```

The confirmation freeze binds the selected mode and rationale, protocol,
driver, active build manifest and 600-second cap. Each confirmation launch
checks those hashes and its original input hash. C4 opens before C5; both
are previously public scenarios and both have T=18000. Neither was used in
Round63 mechanism selection. Official P-GRB checks its original Round58
model fingerprint and leaves native heuristics enabled.

Final delivered accounting is 66 charged launches, 278 optimizer calls and
971 recorded maxflow/separator calls (including guarded attempted calls).
All four native micro launches are charged; #7/#27 stay in the ledger with
their performance exclusions. No 1800/3600-second run was used.
The 600-second confirmation caps permit early certification: all four C4
and C5 methods reach F=0. C5 still discriminates execution cost sharply.
Both confirmation K1-H runs have zero native calls, so their parameter
readback is not applicable. Build-only counter labels must be interpreted
with their `charged=false` flag, never joined to a charged run by number
alone. Gurobi's log fingerprint is hexadecimal unsigned notation; compare
its 32-bit pattern with the signed integer API/manifest value.

Final full verification includes the OFF route point against each available
global root pool, in addition to original physical/objective checks. In C5
the known zero-objective OFF witness satisfies both added root rows.
The evidence index covers 3,305 local files; `native_model_shapes.csv` reads
actual post-insertion sizes and distinguishes the native aggregate User-cut
summary from API-success submissions. No native source or executable changed
after the v4 freeze; the later commit packages reports and analysis helpers.
