# Reproduction and immutable-run entry points

Use Windows, gcc14.2 UCRT and Gurobi13.0.2. Formal process settings are inherited
from the pinned R94 common manifest: one native thread, Seed0, PresolveAuto,
zero MIP gaps, original numerical tolerances and affinity mask4. CMake uses
the same blank build type as the R97 production build. License/runtime files
and binaries remain local; no license is in this research delivery.

Run from the repository root with D:/msys64/ucrt64/bin/python.exe. Building
while no solver is active:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_build.py fresh_label
```

Every label is exclusive. Existing build logs, experiments and matrices must
not be overwritten. For an independent clean reproduction, use a new output
root/campaign label and record its newly generated binary/source/input identity;
do not pretend it has the original timing or original gzip bytes.

Canonical zero-Optimize export executable arguments:

```text
Round98ModelExport input T pickup drop lambda gamma_L gamma_U cutoff directory
```

It produces R0/off, R1/aggregate and R2/projected via the production writer,
with LP SHA and row/column/nonzero metadata. Original plain P identity uses
Round65ReferenceBuild input T pickup drop lambda directory, no Optimize.

The registered Round98StateServiceTests produces complete micro matrices
without Optimize. round98_qualification.py accepts a new output directory and
its micro-model directory; it enumerates original physics independently and
declares12 MIP/LP calls. Use the bundled existing Gurobi Python13.0.2 runtime
build/research/round88-ot/venv/Scripts/python.exe. The five real fixed-state
batches each declare3 raw objective LPs plus1 common-coordinate completion LP.
round98_lp_diagnostic.py role new_label strict requests stricter independent LP
convergence only; production tolerances are unchanged. Every started/completed
call is durable. The original failed F5 default-tolerance batch has3 calls and
is retained alongside its actual-vector projection audit and strict follow-up.

Production campaigns:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_campaign.py prepare new_campaign results/unified_exact_round98/development_protocol01.json
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_campaign.py run new_campaign 1
```

prepare is zero Optimize and binds fresh P matrices, every active source/helper,
runtime, input and native binary. run admits only the next never-started prefix
arm, validates the whole-process receipt, committed journal, physics, coverage,
native parameters, actual P matrix and full Optimize ledger correspondence.
round98_run_batch.py campaign consecutive_numbers executes only that declared
subset and stops on any failure. There is no algorithm-internal time/work
slice, restart, instance dispatch or time-based selection. Caps control the
whole experiment process, and normal certification may return early.

round98_start_audit.py actual_R2_process new_label independently checks all
submitted retained Start columns/rows/readback, including continuous p/d's
original integer semantics, with zero Optimize. Do it only after the solver
has exited. v1 paid prefix is retired due to the final preset-label defect;
round98_legacy_label_audit.py audits its physical evidence without rewriting
old bytes or entering those times in the final formal comparison. v2 is the
corrected formal build and all formal matched arms use it.

After all performance processes exit, round98_results.py new_label campaigns
extracts run/pair CSV and paid costs, including retired v1 processes and failed
diagnostics. round98_checkpoints.py campaign new_label extracts legal long-run
900/1800/3600s endpoints from the same committed process; fresh runs are never
spliced into continuations. Pending confirmation is generated once after the
uniform candidate freeze. Generation recipe and all resulting roles are kept
regardless of outcome.
