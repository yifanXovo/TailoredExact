# Round98 reproduction

All30 formal runs are complete. Do not continue/replay their existing directories.
The original frozen source/helper/binary identities remain authoritative: v2
development and v3 revision/confirmation are separate panels. No new solver run
is needed for this delivery.

## Committed compact evidence: no solver needed

From repository root:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_verify_delivery.py
```

It verifies30 actual endpoint routes against original physics and input SHA,
qualified endpoints,75 receipts and194 recorded actual Optimize counts. No
Gurobi or local large matrix is needed. This is an executor-side entry point,
not a full independent solver reproduction. `compact_evidence01/runs/*.json`
contains actual routes/inventories, original audit/summary, source hashes,
native call scopes and Optimize ledger. Record14 retains original failed audit
and exact recovery separately; its normal result is not fabricated or replaced.
`local_artifacts.csv` binds401 retained local files. Large model/vector/binary
bytes remain local; do not recompress/rewrite them or their journal identities.
Native numerical certification is not a rational proof inferred from a SHA.

Record14 recovery: `recovered_models/C3_R1/qualified_recovery.json`, SHA256
`96edc767b6f971f295c28b0ebdeec15ff692a64d27ff92d22016327abf20f2cb`.
Only the replay copy's model paths changed; matrix bytes match original journal
SHA. Original audit=false and endpoint=null remain. Raw original evidence is
required for full journal/coverage replay; compact verification needs only Git.

## Clean build and tests

Use a new checkout at the delivered PR head (read `delivery.json`), for example
after fetching the Round98 branch:

```powershell
git worktree add --detach E:/codes/ExactEBRP-round98-repro origin/codex/round98-state-service-reformulation
Set-Location E:/codes/ExactEBRP-round98-repro
$env:PATH = 'D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;' + $env:PATH
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_build.py independent_build01
& './build/research/round98-state-service-v3/Round98StateServiceTests.exe' results/unified_exact_round98/repro_micro_models01
```

The build uses gcc14.2 UCRT, Gurobi13.0.2, bundled MSVC CMake/Ninja, blank build
type and no active solver. Default targets include ExactEBRP, R98 tests/exporter
and Round65ReferenceBuild. Labels are exclusive. Different checkout/compiler/link
paths may change binary SHA; bind the new binary and never mix its time with the
original panel. Original Gurobi DLL SHA:
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
Installation/licensing are local prerequisites; no license is delivered.

R98 tests use zero Optimize (36,125 projection points, three micro fixtures×four
modes, actual writer/mapping/decoder boundaries). Use a fresh output directory;
the original v3 passing log is `engineering/ctest_v3_pure02`. Do not describe all CTest as zero Optimize: the existing
Round68 native fixture performs3 actual calls each time; its earlier3 invocations
are charged in `qualification/ctest_native_cost_correction.json`.

## Actual models and diagnostic qualification

Zero-Optimize production-writer export to a fresh directory:

```powershell
& './build/research/round98-state-service-v3/Round98ModelExport.exe' reference/round98_confirmation/C2.txt 7200 60 60 0.15 0 1 1 results/unified_exact_round98/repro_C2_models01
```

Arguments: `input T pickup drop lambda gamma_L gamma_U cutoff directory`.
Exports off/aggregate/projected/vehicle-state with actual types, rows/columns,
nonzeros and LP SHA. For exact retained diagnostics use their precise
gamma/cutoff from `development_inputs.json`, not this illustrative broad interval.
Plain P: `Round65ReferenceBuild input T pickup drop lambda fresh_directory`,
also zero Optimize.

`round98_qualification.py destination micro_model_directory` runs a finite12-call
R0/R1/R2 batch with independent original-physics enumeration. Existing Gurobi
Python13.0.2 is `build/research/round88-ot/venv/Scripts/python.exe` in the original
workspace. `round98_lp_diagnostic.py role new_label strict` declares3 raw LPs
and1 common-coordinate completion, with durable call records. Strict1e-8/1e-9
is diagnostic-only; production tolerances stay unchanged. Retain all failures
and whole-process fees; integer03's earlier7 calls are reconstructed from output
and failure program flow, not a complete durable per-call ledger.

`round98_vehicle_qualification.py` is the recorded fixed-label vehicle01 batch,
not an idempotent replay. It declares7 calls and depends on retained old R2 root
exports/vector. Existing destinations must fail closed. Exact reproduction needs
a separate workspace with those artifacts and recorded bindings, following
`qualification/vehicle01/launch.json`, billing all7 calls. Its second completion
frees s/q but still fixes other shared auxiliaries; the historical label
`fixed_original_physical_coordinates` is not a pure physical projection claim.

`round98_start_audit.py completed_process fresh_label` checks actual full ordered
Start rows/bounds/readback, p/d physical integers and R3 theta0/1, zero Optimize.
Run after process exit. `revision_R2_starts.json`/`revision_R3_starts.json` each
record two submissions. Original R3 scope string also says R2; actual matrix/type
checks and source cover R3. Independent selected-Start text replay is described
in `root_final_review.md`.

## New matched performance reproduction

In the clean checkout, use the retained fixed inputs:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_campaign.py prepare reproduction01 results/unified_exact_round98/confirmation_protocol01.json
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_run_batch.py reproduction01 1 2 3 4 5 6 7 8 9
```

Preparation generates3 new plain P references in one finite zero-Optimize batch.
The9 whole-process caps are900/1800/3600s for each role's3 P/ENS/R3 arms. Bind
current source/helpers/runtime/binary/input; all launches are serial, Threads1,
Seed0, PresolveAuto, zero gaps, original tolerances, affinity mask4. Startup,
build, LP/MIP, Start, verification and normal close are paid. This rerun uses
already-observed confirmation data and is reproduction, not new independent
selection evidence. No algorithm-internal time/work slices or switches exist.

Archived development02 cannot resume with latest source: it used v2 before
immutable-path fixes/R3. Exact v2 replay requires its then-current file bindings
and `round98_common.BUILD` v2 path in a separate checkout. revision01 used v3
and prepaid reference from vehicle01; for a new reproduction remove
`prepaid_reference` from a new protocol and generate/bill a fresh reference,
rather than reuse different-binary or absent evidence. Do not edit old protocols
or replace their times. Helpers refuse duplicate or changed-binding prefixes.

## Original-workspace postprocessing

After every solver exits, these exclusive commands extract retained originals:

```powershell
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_results.py new_results_label development02 revision01 confirmation01
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_checkpoints.py confirmation01 new_checkpoint_label
& 'D:/msys64/ucrt64/bin/python.exe' scripts/round98_compact_evidence.py new_evidence_label
```

They need original raw files, retired-prefix/recovery evidence and local models.
The cost extractor encodes this Round98 historical cost contract; a new campaign
requires its own clearly separated full fee record. These scripts launch no
optimizer. Final originals are complete_results, compact_evidence01 and the two
long checkpoint CSVs. Checkpoints use the same committed journal prefixes/normal
endpoint, never spliced fresh extensions. See RESUME.md for completed state.
