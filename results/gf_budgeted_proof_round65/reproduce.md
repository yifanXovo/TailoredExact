# Reproduction

The paper artifacts are under `results/gf_budgeted_proof_round65`. `processes.jsonl`
is write-ahead: failed starts remain charged. `runs.csv` and `pairs.csv` separate
certificates from capped gaps; `receipts` and `local_artifact_index.csv` bind the
small submission to full local logs/models/binaries. No optimizer is called by:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/verify_round65.py
& D:/msys64/ucrt64/bin/python.exe scripts/report_round65.py
```

For a checkout containing only the compact submitted evidence, use
`python scripts/verify_round65.py --submitted`. It reconstructs temporary audit
inputs from receipts, complete logical HGA traces, submitted routes/rows and call
tables, then runs the same independent checks and requires byte-identical
`runs.csv`. It neither calls an optimizer nor overwrites the published evidence.
Use the documented Windows checkout/runtime. Scoped Git attributes preserve the
byte hashes of the evidence and frozen driver; submitted source checks allow
only LF/CRLF checkout conversion for inherited C++ text. The actual measured
working source was checked byte for byte before packaging. The derived
`source_checkout_binding.json` records those raw hashes and their LF-normalized
text hashes, including files with mixed Windows line endings.
The ordinary mode requires the full local raw campaign and refuses an empty
campaign. Native benchmark parameter headers are retained; full search logs
remain locally hashed.

Use the current reproduction scripts with the C++ source hashes recorded in the
relevant `build_freeze_v*.json`. The final receipt checks that its C++ tree matches
the active measured build; packaging-only changes are not relabeled as new
measurements. For older revisions use their recorded source commit and launch
commands. Use CMake Release, C++17, Gurobi13.0.2,
`EXACT_EBRP_ENABLE_GUROBI=ON`, `GUROBI_ROOT=D:/gurobi1302/win64`. On this machine
the compiler/make are under `D:/msys64/ucrt64/bin`; CMake is the Visual Studio2022
bundled executable. Configure a separate build directory, build all targets and
write `ctest --output-on-failure` to its `tests.log`. Retained measured binaries
live in `build/round65-v1` through `build/round65-v4`; the active v5 build is in
`build/round65`. Exact hashes are in the build records and local artifact index.

To make a new campaign without overwriting this study, set these environment
variables in the same PowerShell session as the driver:

```powershell
$env:EBRP_ROUND65_BUILD='build/reproduce-round65'
$env:EBRP_ROUND65_OUTPUT='results/reproduce-round65'
New-Item -ItemType Directory -Force $env:EBRP_ROUND65_OUTPUT | Out-Null
Copy-Item results/gf_budgeted_proof_round65/protocol.json $env:EBRP_ROUND65_OUTPUT
New-Item -ItemType File -Path (Join-Path $env:EBRP_ROUND65_OUTPUT 'processes.jsonl') | Out-Null
& D:/msys64/ucrt64/bin/python.exe scripts/round65_research.py build-freeze --version reproduce-v5
```

The protocol fixes mathematical T/handling and file hashes. `--cap` is a separate
process wall budget. Defaults are native Threads1, Seed0, Presolve Auto and zero
MIP gaps. The native main remains Gurobi. For bounded mechanism reproduction:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round65_research.py run --ids D4 --arms seed-bounded seed-proof-free seed-sparse-free --cap 180 --stage reproduce
```

Every call is serial and capped; the driver refuses an existing destination,
concurrent run, altered binary or a launch beyond its72/4 limits. `seed-*` means
the credit-seed per-call ceiling30; non-seed bounded arms use ceiling10. `-free`
means the released-load resource matrix; both projection variants retain F0
native columns. `cold-` is a diagnostic empty-route start, not a per-instance
algorithm selector. `off` retains full HGA and the original controller;
`reliable` changes only verified-zero termination. `K1-H` selects the literal
stable preset; `P-GRB` invokes the plain original compact benchmark.

For the reliability-only integration candidate, select `reliable`: the budget
controller and projection are OFF, and verified-zero termination with retained
verified memory is ON. A separate-output reproduction of its isolation package is
`python scripts/round65_research.py run --ids C5 C7 C2 --arms off reliable --cap 300 --stage reliability`.
This explicitly preserves the original controller rather than bundling the
reliability result with the selected budget policy.

The selected `candidate` is read uniformly from `main_policy.json`. Recreate that
file and confirmation binding using `confirmation-freeze` with exactly the policy,
controller, release-load setting and cap recorded in this study's freeze. This
must precede any C8/C9 optimization. Run `reference-build --ids C8 C9` to obtain
original model fingerprints without optimization. The build-only tool never
resolves GRBoptimize. C8's three declared arms must finish before C9 can run.
The final report states which policy was actually selected; confirmation outcome
does not change it. No initial candidate, bound, route or LP point is replayed
from historical evidence.

In the separate campaign prepared above, the exact selected policy and formal
long/confirmation entry points are:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round65_research.py confirmation-freeze --policy bounded --controller credit-seed --cap 600
& D:/msys64/ucrt64/bin/python.exe scripts/round65_research.py reference-build --ids D3 D4 C6 C8 C9
& D:/msys64/ucrt64/bin/python.exe scripts/round65_research.py run --ids C6 --arms candidate K1-H P-GRB --cap 600 --stage long
& D:/msys64/ucrt64/bin/python.exe scripts/round65_research.py run --ids D7 --arms candidate K1-H P-GRB --cap 1200 --stage long
& D:/msys64/ucrt64/bin/python.exe scripts/round65_research.py run --ids C8 C9 --arms candidate K1-H P-GRB --cap 600 --stage confirmation
```

The complete historical launch commands, including development/protection arms,
are retained in `processes.jsonl`. Each run generates its own HGA and native
evidence. Do not execute these commands into the frozen submitted campaign.

`package_round65.py` copies compact receipts and test logs and hashes bulky local
artifacts. Run it only after the optimizer queue is terminal. Building, Git auto
maintenance and heavy audit/packaging are kept outside performance intervals.

After performance stops and C5/C7 reliability trajectories exist in a separate
campaign, the following reproduces all four disclosed HGA timing diagnostics:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round65_hga_timing.py build
& D:/msys64/ucrt64/bin/python.exe scripts/round65_hga_timing.py run
& D:/msys64/ucrt64/bin/python.exe scripts/round65_hga_timing.py decoder-build
& D:/msys64/ucrt64/bin/python.exe scripts/round65_hga_timing.py decoder-run
```

The first pair links the unchanged core and demonstrates that its decoder
counter is unavailable in original stagnation mode. `decoder-build` enables only
the two timing guards in a copied header under build, compiles the unchanged
HGA adapter against that copy, and links its object before the retained archive.
No main source, binary, genetic operator or stopping rule changes. Separate
`hga_timing_build.json` / `hga_decoder_timing_build.json` records bind both builds,
including the transformed header/object and complete reference trajectories.
Each fresh HGA run is charged, cap 120, optimizer calls zero. The first pair's
raw zero decoder counter remains unavailable rather than being reported as free.

Use a separate build/output directory, as above, to preserve all retained files.
The builder refuses a running campaign or existing diagnostic executable. After
the diagnostics, run verify_round65.py, report_round65.py, package_round65.py and
verify_round65.py --submitted. The last command also validates their logical
trajectories and independently recomputes their routes.
