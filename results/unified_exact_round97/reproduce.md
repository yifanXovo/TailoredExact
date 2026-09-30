# Round97 reproduction and evidence entry

C1/C2/C3 and all selected development/attribution arms are complete. No solver
is currently scheduled. All launch commands below are historical records or
fresh-reproduction instructions; never rerun them into existing destinations.
Qualification01's two superseded, never-started arms remain explicitly unrun.
The final stage decision and independent completion audit are in final_report.md
and the final review named there. Protected ENS-C defaults remain unchanged.

## Inspect the delivered result

Start with final_report.md, mathematical_algorithm.md and the role reports.
`final_summary/all_solver_arms.csv` contains all36 actual solver attempts once,
including the failed qualification and interrupted development runs. It retains
batch purpose, source/build/input identity, mathematical T, cap, true U, legal L,
signed gap, certificate status and full process cost. Unknown fields stay blank.
`final_summary/within_build_pairs.csv` copies only existing reviewed comparisons,
with an explicit version/context column; short qualification comparisons are
not complete-performance evidence. Detailed event and nested-cost columns stay
in the indexed source views. No cross-build pair is fabricated.

`final_summary/evidence_index.json` binds these tables and the main immutable
source artifacts. The final cost snapshot named in final_report.md supersedes
earlier snapshots; do not add snapshots together. Original failed audits and
all recovery sidecars remain separate. See `costs/*/unstarted.csv` for genuinely
unexecuted arms, not missing successful results.

Read-only hash verification of the final summary's listed files, from the
repository root (requires the indexed local evidence to be present):

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' -c "import json,hashlib;from pathlib import Path;j=json.loads(Path('results/unified_exact_round97/final_summary/evidence_index.json').read_text());bad=[p for p,h in j['source_bindings'].items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h];print(bad);assert not bad"
```

A clean clone includes compact evidence sufficient for the main reported
endpoints, original physical witnesses, event chains, receipt identities and
cost tables. Full LP matrices, CSV vectors, native logs and binaries are local
artifacts indexed by hashes; their absence does not count as a passed matrix
re-audit. Compact tar.gz journal/observation archives were byte-checked member
by member at export. Extract only into a separate inspection root, never over
raw runs. The per-role evidence JSON files list archive hashes and contents.

## Frozen builds and numerical environment

Repository `yifanXovo/TailoredExact`, branch
`codex/round97-native-incumbent-closure`, draft PR159, base R96
`93a29e7290e7e92821482c7f4e2c47dfe2f1e84e`.

The H1 executable source is `ea37fbfcd`; binary
`build/research/round97-native-closure/ExactEBRP.exe` has SHA256
`73516d12a7ff81770e9460394fda8a784bd65ab5a0d4003a723ec96b628bb524`.
The v2 actual C++ source is `f0bdaed3f2b9c2205b05584cca29337ee9640c58`;
`build/research/round97-native-closure-v2/ExactEBRP.exe` has SHA256
`7ea6b0eb3500084f6b93748ca43bedfb7ac7ec04591dd19c889a195e1ad31943`.
`production_v2_identity.json` binds actual source files, compiler, CMake cache,
DLL, tests and build receipts. Later reporting commits do not redefine the
compiled source identity. Do not mix H1 and v2 timings as a same-build pair.

The recorded host uses Windows PowerShell, Python and GCC14.2 UCRT64 under
`D:/msys64/ucrt64/bin`, and Gurobi13.0.2 at `D:/gurobi1302/win64`.
Paid arms use Threads1, Seed0, PresolveAuto, affinity mask4 and original
feasibility/integrality/objective/certificate tolerances. Requested native gaps
are zero, not a rational exact certificate. Blank CMake build type and original
flags are part of the identity; changing flags requires new common bindings.

On a separate clean checkout with the same dependencies and an empty build/
output location, the recorded v2 build entry is:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_build_v2.py fresh_reproduction_build
```

This creates an exclusive engineering receipt. It must run only while no solver
is active. It builds ExactEBRP and the R95/R96/R97 micro/diagnostic targets.
Compiler availability and a licensed Gurobi environment are prerequisites;
this document does not install or alter them. A fresh binary must be rebound
in a fresh manifest. Existing production identities deliberately reject changed
binaries, helpers or inputs rather than silently calling them equivalent.

## Exact executed experiment entry points

Complete command arrays, input/hash/T/caps and original orders are in each
batch identity and individual launch.json. These are the authoritative commands,
including expected reference-model fingerprints and plain-baseline isolation.
To print them without launching any solver:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' -c "import json;from pathlib import Path;j=json.loads(Path('results/unified_exact_round97/confirmation01/identity.json').read_text());[print(json.dumps(x['command'])) for x in j['launches']]"
```

|Executed stage|Entry/receipt and evidence|
|---|---|
|Failed initial qualification|qualification01; exact administrative stop and failed audit retained, remaining arms superseded|
|H1 functional qualification|qualification02, qualification_report.md|
|H1 common3600 F5 SHADOW/FEEDBACK/OFF/P|development01 and development01_analysis; failed queue then guarded recovery, no duplicate solver|
|Eight fixed-state order replays|native_order_replay/identity.json; zero Optimize, nested child costs retained|
|v2 build/micros/reader|engineering/revision02_* and production_v2_identity.json|
|Real v2 qualification|qualification03 and qualification03/gate.json; all69 actual vectors passed|
|Four-role development|development02, development02_analysis and four role reports|
|Three old-operator controls|round97_operator_attribution.py prepare/run-all; attribution01 and attribution_report.md|
|Uniform candidate selection|round97_candidate_selection.py analyze then freeze, after controls and before confirmation|
|Three confirmation roles|round97_confirmation.py prepare, then run-role --role C1/C2/C3 once, each previous role terminal/audited/analyzed|

D7/P's cap hard-stop and V1/combined's missing buffered ledger row are not
normal results. Their reviewed exact-exception continuations ran only previously
unstarted arms. See development02_d7_interruption.md, development02_v1_interruption.md,
review_v1_recovery.md and the bound sidecars. Do not use those exceptions to
accept an arbitrary future failure or rewrite original audit status.

The initial confirmation admission test required all nine raw destinations
absent; rerunning it after completion is expected to fail. Selection, freeze,
preparation and analysis scripts also use exclusive-create and chronological
guards. Fresh timed reproduction therefore needs separate outputs and newly
bound manifests, not deletion of existing evidence or disabling safeguards.
It is a new experiment and cannot replace the retained original result.

## Analysis and independent validation

The following commands actually ran after each role became terminal, with
zero Optimize; replace C3 only when inspecting another already recorded role:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_analyze_role_v4.py confirmation01 C3
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_trajectories_v3.py confirmation01 C3 confirmation01_c3
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_export_normal_batch.py confirmation01 --role C3
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_final_summary.py
```

These exact output directories already exist and must not be overwritten.
A new cost snapshot uses `scripts/round97_cost_ledger.py FRESH_LABEL`. Run
receipted engineering commands through round97_build.run, with a fresh label,
so their costs appear in the next snapshot. The final ledger's own wrapper is
reported separately to avoid an infinite self-accounting loop.

With original large matrices/vectors available and the machine idle, the
independent actual-vector audit is a Python function (the module has no CLI):

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' -c "import sys;from pathlib import Path;sys.path.insert(0,'scripts');import round97_campaign_v2 as c;import round97_vector_audit as v;c.ext.ensure_idle();v.check(Path('results/unified_exact_round97/confirmation01/raw/07_C3_FEEDBACK'),'fresh_c3_vector_check')"
```

It loads saved actual LP matrices with zero Optimize and checks full columns,
bounds, types, rows and objective independently of candidate construction.
The physical reader separately validates original route/operation witnesses,
source hashes, actual Start matching and non-feedback isolation. Artificial
micro registries alone do not prove actual-model mapping qualification.

Recorded trajectories use committed evidence availability. Untimed final
certificates remain separate; no missing history, instantaneous acceptance,
unique provenance or gap integral is invented. Callback/closure/map costs are
nested inside full solver wall time. SHADOW candidate quality never changes
its official U. No confirmation-driven tuning, default promotion or merge is
part of this reproduction.
