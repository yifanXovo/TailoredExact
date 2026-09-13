# Round63 reproduction

Use the isolated research checkout based on
71e955acad596acba2a9e74e738173113116d9f7 (Round62 / PR #123).
The original workspace is untouched. This campaign's measured builds have
immutable build_freeze_v*.json manifests; the active manifest is explicit.
Do not replace measured executable hashes with a later packaging build.

On the measured Windows host:

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

The complete algorithms use the measured v3 source commit
b1bde3eab6c6fb9c4e1c4575acbdfa9141a46eaf (manifest build_freeze_v3.json).
v1 binaries are retained locally in build/round63-v1 and v2 in
build/round63-v2. v2's full-K1 micro safely rejects retained-model row
insertion and is excluded; v3 uses fresh models in root/root-dry and passes
the full-K1 micro. Do not mix these versions' timings.

Full lifecycle commands, with a new output root and frozen build:

```powershell
& $python63 scripts/round63_research.py service-build --ids D3 D4 C3 --stage preflight_A
& $python63 scripts/round63_research.py service --ids D3 D4 C3 --stage full_dev --cap 600
& $python63 scripts/round63_research.py k1 --ids C2 D7 --modes off explicit root --stage full_dev --cap 600
& $python63 scripts/round63_research.py k1 --ids C2 --modes root-dry --stage full_dev --cap 600
& $python63 scripts/round63_research.py reference --ids C2 D7 --stage full_dev --cap 600
& $python63 scripts/report_round63.py
```

The driver rejects semantic engine failures even if the native executable
returns zero. Optimizer counts distinguish write-ahead backend attempts from
actual calls that reach optimize (the failed v2 micro has 4 versus 3).
`report_round63.py --index` hashes the complete local evidence set and copies
sparse cut records for delivery; run it only after all performance ends.
