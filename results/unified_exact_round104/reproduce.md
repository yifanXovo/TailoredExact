# Round104 reproduction

Run from the repository root in Windows PowerShell. This round stacks on
R103/PR165, `7b60d3c1b07429ee96dbf371b4796e635499cb80`. The measured production
source is `339835c46c37f353c7cf9813ef749782098fff5d`; later report/package commits
are not new measured builds. `control01/identity.json` is the actual pre-launch
freeze. `production_freeze.json` consolidates that record after the first arm,
with its own actual creation time. Never backdate the consolidation.

Management Python: `D:/msys64/ucrt64/bin/python.exe`. Numerical Python:
`build/research/round88-ot/venv/Scripts/python.exe`. Production Gurobi13.0.2 DLL:
`D:/gurobi1302/win64/bin/gurobi130.dll`, SHA
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
The measured PE SHA is
`c469e9c9fcd0da968e02b6eb6d534d24473ef7c33975742c4aaab3b178284c4d`.
DLL/license/executables are not committed. The numerical reader explicitly
loads that production DLL before importing gurobipy; do not substitute its
bundled DLL and call it the same runtime.

## Read and verify the delivered evidence

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round104_evidence.py verify
& D:/msys64/ucrt64/bin/python.exe scripts/round104_evidence.py restore
```

Restore writes only missing exact bytes beneath the workspace and refuses
to overwrite existing different files. The manifest includes current complete
vectors, original matrices, finite pools, multipliers, C++ output, support and
ahead-of-call records, frozen launches, closed failures and physical witnesses.
The inherited R103 manifest remains authoritative for its historical pools.
Intermediate generation vectors are intentionally omitted; final members and
all accepted source rows/support calls are retained. Verification makes no
Optimize/DP calls. Native-point objectives are recomputed from their full vector;
the solver's separately reported global bound is not that point objective.

## Build and small qualifications

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round104_build.py FRESH_BUILD_LABEL ExactEBRP Round104Compression Round104CompressionTests Round102ServiceTests Round103HullTests Round65ReferenceBuild
```

Build receipts pin CMake/Ninja/GCC and source bindings. Tests cover signed
interval compensation, wrong multiplier/scope, tiny native coefficients,
subnormal arithmetic and seeded legal-plan reuse. The seven paid LP fixtures
also cover constants, old equalities/bounds, zero/degenerate multipliers and
descendant weakening. A fresh build/changed PE requires a fresh campaign
freeze and complete contemporary pairs.

Every label is exclusive. These are **new-run patterns**, not instructions
to overwrite delivered runs:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round104_common.py FRESH_POOL_FEE 600 research build/research/round88-ot/venv/Scripts/python.exe scripts/round104_pool.py FRESH_POOL F2 590
& D:/msys64/ucrt64/bin/python.exe scripts/round104_common.py FRESH_CPP_FEE 600 research build/research/round88-ot/venv/Scripts/python.exe scripts/round104_qualify.py FRESH_CPP 590
& D:/msys64/ucrt64/bin/python.exe scripts/round104_common.py FRESH_FIXTURE_FEE 120 research build/research/round88-ot/venv/Scripts/python.exe scripts/round104_dual_fixtures.py FRESH_FIXTURES
```

Historical-pool ALL/ACTIVE/GROUPED/FLEET LPs are expression diagnostics;
they do not report end-to-end algorithm performance. `round104_reprice.py`
is the single investigated GROUPED-direction revision: two complete support
calls and one LP, with quantization/UNKNOWN qualification. It requires the
inherited R103 oracle at the SHA recorded in oracle_identity.json; rebuild
that target from its recorded source if absent. No old support campaign is
automatically replayed.

Python GROUPED/FLEET numerical LPs have unqualified native tiny-coefficient
readback; use `cpp_qualify02` and the independent actual C++ compensated-row
recomputation as the qualified aggregate evidence. Numerical retention never
asserts exact rational optimality. The completed production source also has
an untriggered partial-vehicle deadline/Pi-mapping failure boundary. See
`review/delivery_review.md`; a future repair requires a new measured freeze
and contemporary pairs. The current STOP delivery does not claim universal
graceful ALL UNKNOWN fallback.

## Complete original-problem controls

Copy the role bytes and policy from `control01_protocol.json` into a fresh
protocol file. Prepare and then admit each never-started arm in serial:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round104_common.py FRESH_PREP_FEE 180 research D:/msys64/ucrt64/bin/python.exe scripts/round104_campaign.py prepare FRESH_CAMPAIGN FRESH_PROTOCOL.json
& D:/msys64/ucrt64/bin/python.exe scripts/round104_common.py FRESH_ARM_FEE 1260 research D:/msys64/ucrt64/bin/python.exe scripts/round104_campaign.py run FRESH_CAMPAIGN 1
```

Repeat the last pattern with distinct fee labels and the next arm number,
after its predecessor has returned and passed physical/model/clock audits.
The four-arm order is ACTIVE, complete SHADOW, protected ENS-C, principal
P-GRB, each with the original1200s whole-run authorization. Native calls
use Threads1, Seed0, PresolveAuto and unchanged tolerances/gaps. The wrapper's
outer cap is resource supervision, not a component policy. No generation
time/Work/stall gate or historical pool/direction import exists in production.

ACTIVE pays for its fresh finite pool and selected-LP qualification before
native MIP. SHADOW pays for exactly the same preparation policy and changes
no official row/LB/cutoff. P remains the plain compact model with no external
Start. Both research modes default off and reject combination with R101/J/H.
Do not overlap performance with builds, packing or numerical reviews.

`round104_results.py FRESH_REPORT FRESH_CAMPAIGN` reads complete campaigns,
retains signed checkpoint pairs and conservative discovery/certificate clocks,
and launches no optimization. `round104_fees.py` reconciles closed parent
receipts plus conservative nested process counts, without adding nested time
twice. No failed label is retried; fixes always use new labels. Inspect PID,
completion, runtime_status and receipt files before resuming a lost session.

The delivered `reports_final02` and `_clocks` are complete four-arm controls.
Postexit audits are charged inside parent receipts, while original end-to-end
completion retains its inherited boundary. `reader_provenance` preserves the
exact report02 reader, original clock CSV and a metadata-only scope-wording
correction with unchanged numeric cells. The failed first annotation launch
and successful verification are engineering, with zero Optimize/DP.
`fees.csv` is the authoritative paid failure/total ledger; its separate
engineering snapshot in `fees_summary.json` precedes final packing, so final
closed engineering receipts are additionally retained in the evidence and
`delivery_verification.json`. No paid runs remain outstanding. Two new roles
and both long-window groups were never admitted and are cancelled by the
documented STOP condition, not waiting for a background execution.
