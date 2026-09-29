# Round 97 reproduction — active research

This file records completed identities and safe commands. The whole research
stage is incomplete; consult RESUME.md and actual process/receipt state before
starting anything. Never rerun a completed label or resume a failed arm into
its old destination. Do not launch a second solver, compile, load large model
audits, or compress artifacts alongside an active performance run.

Repository: yifanXovo/TailoredExact. Research branch:
`codex/round97-native-incumbent-closure`, stacked on R96
`93a29e7290e7e92821482c7f4e2c47dfe2f1e84e`. Draft PR159 remains a research
proposal, with ENS-C protected and no default promotion or merge.

## Build and environment

The frozen H1 production source is `ea37fbfcd`; its existing executable is
`build/research/round97-native-closure/ExactEBRP.exe`, SHA256
`73516d12a7ff81770e9460394fda8a784bd65ab5a0d4003a723ec96b628bb524`.
Its completed experiments must not be associated with the later C++ sources.

The revised v2 source is `f0bdaed3f2b9c2205b05584cca29337ee9640c58`.
`production_v2_identity.json` binds every C++/header/CMake source, actual
executable and CMake cache, compiler version, Gurobi DLL, passed engineering
receipts and test sources. `scripts/round97_build_v2.py` documents the separate
build. Keep the old binary intact. Blank CMake build type and original flags
are part of the recorded environment; do not add optimization/fast-math flags
and mix the resulting timing with this campaign.

Windows PowerShell; Python `D:/msys64/ucrt64/bin/python.exe`; GCC14.2 from the
same UCRT64 installation; Gurobi13.0.2 DLL at
`D:/gurobi1302/win64/bin/gurobi130.dll`. All paid arms use one solver thread,
Seed0, PresolveAuto, affinity mask4 and the unchanged tolerances/requested
zero MIP gaps. The complete exact command arrays are in each batch's
`identity.json`, then copied into individual launch receipts. Mathematical T
is an input constraint, not the process cap. Startup, improvement, mapping,
normal shutdown and any child optimizer work remain inside paid wall time.

## Completed evidence

`qualification01` retains the administratively stopped no-op submission
attempt. Its remaining planned arms were never started and must not run.
`qualification02` contains all three audited H1 functional runs; its F5 short
arms observed only Start states and do not negate later opportunities.

`development01` contains the four audited common3600s F5 arms, in registered
order SHADOW, FEEDBACK, OFF, P-GRB. `development01_analysis` binds the input
receipts and gives endpoint/pair CSVs. All are censored. The failed original
continuation queue and successful recovery queue both remain recorded; the
failure occurred before a new solver launch and is not a second paid arm.

`native_order_replay/identity.json` fixes the eight completed offline cases
and their inputs, source witnesses and helper identities. These zero-Optimize
diagnostics are not full solver comparisons. Re-running them is unnecessary
for the current research; use their saved candidate witnesses and audits.

`engineering/revision02_*` records configuration/build, three passed micro
executables and the reader fixture. The reader checked55 real saved input
hashes,83actual Start associations and9mutations. Micro registries do not
establish actual VD-P matrix qualification. The build freeze script performs
no optimization and refuses to overwrite its identity.

## Current revised qualification and later development

`qualification03/identity.json` preregisters F5 SHADOW900, F5 FEEDBACK900,
F2 FEEDBACK240, all with the fixed r96 combined operator. F5 mathematical
T=7200 and F2 T=3600. Arm1 is active at this document's initial creation;
inspect its receipts/process before any action. The guarded invocation for a
never-started next arm is:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_campaign_v2.py run qualification03 --number N
```

Each arm checks source/binary/DLL/input/helper/research-plan/build-gate
hashes, requires a fully audited preceding prefix and creates a fresh raw
directory. The supervisor retains full cost and failure evidence. After a
solver exits, the separate matrix audit is:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round97_vector_audit.py RESULTS_DESTINATION FRESH_AUDIT_LABEL
```

This loads the exact saved actual LP matrices with zero Optimize calls and
independently checks every retained source/mapped CSV's complete columns,
bounds, types, rows and objective. Run it only while idle. The production
reader separately validates physical witnesses, initial seed and per-call
actual Start matching, session operator and non-feedback isolation.

`scripts/round97_development_v2.py` is a conditional, not yet executed
development preparer. It requires a future evidence-bound real qualification
gate before preparing the13-arm/33300s campaign from `revision02_plan.md`.
It preserves D7's actual d7dbd018… input/T18000 via the R96 fixed cases and
matched R87 zero-Optimize original reference. V1 uses the R96 primal input
dd841e57…/T7200. Old timing is never reused in new performance pairs.

## Interpretation and confirmation boundary

OFF's observer costs remain paid. SHADOW's optional candidate objective
never changes official U. Submission API success/infinity, later full-vector
observation and native incumbent changes are separate evidence, not unique
source proof. Callback/closure/mapping measurements are nested and must not
be summed as extra process expense. See mathematical_algorithm.md for
state qualification, finite progress, mapping and safe archive handoff.

C1/C2/C3 inputs were generated once and remain unoptimized at this
checkpoint. Their recipe/hashes/caps are in confirmation_inputs.json. Freeze
one uniform candidate after development before running them; do not redraw,
resize or use their results for design while retaining confirmation status.
Whole-stage costs, trajectory analysis, final review and final decision are
still pending. No current censored result establishes final certification
time superiority.
