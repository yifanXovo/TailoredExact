# Round105 reproduction

Run from the repository root in Windows PowerShell. The stacked inheritance
is R104/PR166 delivery `aa1d0e5b268cf95442b3713b2af8fc505974f6c2`.
Production mathematics was frozen at source
`91ff7da1b319577bf2fe703417bdd7d994a790a3`; subsequent test/report/reader
commits are not new measured production builds. The measured PE SHA is
`8b17e33c612d9768edec0047df5ca9efdc088ee8fc5a67acfbf0dd1b5f5e19c9`.
`control01/identity.json` is the actual pre-launch source/helper/input/PE/DLL
freeze. The delivered source need not reproduce the same PE timestamp/hash;
a rebuilt PE requires a fresh freeze and contemporary controls.

Management Python: `D:/msys64/ucrt64/bin/python.exe`. Numerical Python:
`build/research/round88-ot/venv/Scripts/python.exe`. Gurobi13.0.2 production
DLL: `D:/gurobi1302/win64/bin/gurobi130.dll`, SHA
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
Executables, DLL, license and credentials are not committed. Pin the actual
production DLL before importing gurobipy; its packaged DLL is not silently
substitutable.

## Exact-byte evidence

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round105_evidence.py verify
& D:/msys64/ucrt64/bin/python.exe scripts/round105_evidence.py restore
```

These invoke the inherited R104 bounded, missing-files-only archive engine.
Existing different bytes cause an error. Verification makes zero Optimize,
IIS or DP calls. The compact manifest retains original/master/oracle/core
LPs, complete solutions, quality/parameter records, every call/conflict row,
paid witnesses, input bytes, frozen launches, closed failures and reviews.
Scalar bound journal duplicates are omitted; complete observations and
non-bound witness/call commits remain. Earlier repeated qualification models
stay local; their paid receipts and enumeration CSVs remain.

## Build and correctness qualification

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round105_build.py FRESH_BUILD_LABEL ExactEBRP Round105Tests Round105Oracle Round65ReferenceBuild
& D:/msys64/ucrt64/bin/python.exe scripts/round105_common.py FRESH_PURE_LABEL 30 engineering build/research/round105-decomposition-v1/Round105Tests.exe
& D:/msys64/ucrt64/bin/python.exe scripts/round105_common.py FRESH_NATIVE_LABEL 240 research build/research/round105-decomposition-v1/Round105Tests.exe native results/unified_exact_round105/qualification/FRESH_NATIVE
& D:/msys64/ucrt64/bin/python.exe scripts/round105_common.py FRESH_ADDED_LABEL 180 research build/research/round105-decomposition-v1/Round105Tests.exe native-added results/unified_exact_round105/qualification/FRESH_ADDED
```

All labels/destinations are exclusive. `native` independently enumerates 21
fixed-mode cases and exercises the two-round B conflict loop; the current
test source also includes A's integer-assignment master and expired-deadline
extension. `native-added` runs only those latter native extensions after the
pure contracts. Tests are outside inherited production bindings: their actual
source/PE provenance is separately recorded in `qualification_identity.json`.
The already delivered native04 and native-added evidence are different
executions/source identities, not silently merged into one historical run.

## Fresh diagnostic and complete runs

Copy the delivered role/parameter bytes to a new protocol path. Do not reuse
an existing output directory or relabel its measurements. A fresh prepare
builds and pays for the original P reference for each role, without Optimize.

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round105_common.py FRESH_PREP_FEE 180 research D:/msys64/ucrt64/bin/python.exe scripts/round105_campaign.py prepare FRESH_CAMPAIGN FRESH_PROTOCOL.json
& D:/msys64/ucrt64/bin/python.exe scripts/round105_common.py FRESH_ARM_FEE 1860 research D:/msys64/ucrt64/bin/python.exe scripts/round105_campaign.py run FRESH_CAMPAIGN 1
```

Run later arm numbers only after normal return and successful audit of the
entire previous prefix. Alternatively the finite serial batch runner declares
the exact arm range and every native child, using the same per-arm supervisor:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round105_common.py FRESH_BATCH_FEE 10400 research D:/msys64/ucrt64/bin/python.exe scripts/round105_batch.py FRESH_CAMPAIGN 1 7 FRESH_BATCH
```

`control01_protocol.json` specifies F2's four 1200s arms and R98-C2's three
1800s arms. The common 30s shutdown reserve is inside each total budget and
is identical for P/ENS/FULL/CORE; native calls receive the remaining work
deadline. P receives no external Start, VD-P master or imported optimum;
ENS keeps its unchanged startup/AM. Each candidate starts its own paid ENS
startup, then one global master without AM. No historical/P route or earlier
diagnostic core/cache is fed into a formal arm.

For mode diagnostics, `round105_modes.py extract CAMPAIGN FRESH_MODES` reads
actual integer master solutions and saves complete signed operation vectors.
Nonoptimal incumbents are diagnostic-only sources. `run LABEL NUMBER CAP
core|full` invokes the finite oracle; wrap it with a new paid receipt.
`batch FRESH_PLAN.json` declares at most12 such child calls and records each
before/after. These 120s local diagnostic caps never enter production.
`Round105Oracle`'s positional interface is in its source. Every native
Optimize/IIS is in calls.csv; parent elapsed time is billed once.

The first F2 label audit failed despite a normal numerical endpoint; its
original result remains unchanged, and a separately paid, explicitly scoped
legacy-identity reader produced audit_recovery.json. The first F5 hard-stop
has no endpoint/solution/summary and is not recoverable from its last native
log. Diagnostic04 is a separate paid same-PE reserve-30 retry. Neither failure
is erased, converted into a certificate or called an executed confirmation.

## Independent reproduction and exercised deadline

The independent reviewer authored `review/independent_native_reproduction.py`;
root executed it once under paid fee independent_delivery_native01. It performs
three serial Optimize calls, no IIS/subprocess/DP, independently enumerates
all six actual F2 orders and decodes/checks an actual C2 native route. Pinning
and exact original numeric readback are assertions; only the same frozen
engine/retained-model scope is claimed. Existing output is exclusive; use a
new script output/counter identity for a genuinely fresh paid rerun rather
than overwrite this evidence.

`deadline_qualification_protocol01.json` and deadline01 freeze a separate
400s whole-process C2 CORE qualification, with reserve30 inside that cap.
It actually expires in optional IIS and keeps the proved full conflict,
strongest LB and own UB; it does not restart or confirm an unknown core.
It is not an extra performance arm.

Final zero-solver readers:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round105_common.py FRESH_REPORT_FEE 60 engineering D:/msys64/ucrt64/bin/python.exe scripts/round105_report.py FRESH_REPORT_DIR
```

The delivered successful final tables are reports02; failed report01's
engineering receipt and completed old files remain distinct. All paid
failures and child launches are counted. No archived executables/DLL/license
are restored. The compact selector SHA and inherited pack engine SHA are
both recorded in its manifest.
