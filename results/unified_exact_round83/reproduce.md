# R83 reproduction and evidence boundaries

Read status.md and campaign/driver_completion.json before any action. The
original standalone diagnostic, qualification and ten startup commands are
closed. Their failures and recoveries must not be replaced. The complete
13-arm campaign uses its original driver, which refuses a duplicate namespace.
Never launch it again while active or after closure. See full_screen_plan.md
for exact roles, order, caps and frozen interpretation.

## Identities and environment

Owned checkout E:/codes/ExactEBRP-round66, base R82 final30996a5c023adc2257cf9f4581e3672cf9a644d1
and draft PR143. Qualified production source4496078f25c0cdad1cf7a5c39835fd23121e8978,
build/round83/v1/ExactEBRP.exe SHA256
25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e.
Release MinGW/UCRT compiler and core/source hashes are recorded by qualification.
Git stores LF in main.cpp, PaperExternalGiniTree.cpp and CMakeLists.txt while
this qualified Windows working copy uses CRLF. A literal blob-byte check
therefore fails; normalized source text agrees and every measured source hash
remains unchanged. production_commit_byte_check.json preserves that observation.
The measured_source_bytes bundle preserves exact qualified working source bytes;
use its hashes when reproducing the build, rather than assuming Git EOL policy.

The standalone prototype uses13bf7a5317220ea60a283e814aefbf77245de1fd and the
unchanged R78 core library; do not rebuild it against later integrated source.

Python D:/msys64/ucrt64/bin/python.exe; PATH starts D:/msys64/ucrt64/bin and
D:/gurobi1302/win64/bin. Gurobi13.0.2; every native run is serial, Threads1,
Seed0, PresolveAuto, zero requested gaps, original numeric tolerances. Diagnostic
and startup processes make zero Optimize calls. Affinity helpers bind logical2
(mask4) on the original mixed-core machine and record restoration. There is no
frequency lock. Full costs include every algorithm step and exit.

Protocol and campaign/identity.json bind four original inputs without new draws.
Startup uses five earlier input identities; diagnostic identity binds each
archived BDS-final witness used only for diagnosis. Formal algorithms acquire
their own witnesses. R82 U6 is exposed development for ENS-C, and all benchmark
inputs retain original T/Q/inventory/weights. No archived U/L is imported.

## Original command provenance, not a rerun instruction

scripts/round83_diagnostic.py v1 compiled and executed the one standalone tranche.
scripts/round83_qualify.py v1 ran configure/build/all62 tests once. The separate
qualification and actual Start audits used no additional Optimize. Source and
binary hashes are verified before any subsequent run.

scripts/round83_startup.py v1 ran original commands1-6, stopping on a reader
assertion after D7 ENS-C had already returned normally. Its original summary
and round83_audit.py remain. round83_audit_v2.py preserves untouched explicit
empty routes. scripts/round83_startup_resume.py re-audited original command6
without rerun and launched only the original commands7-10. Use
startup/completion_summary.json for the combined10-run view; reader_failure.json
and reader_v2_check.json record the defect and targeted representation checks.

scripts/round83_research.py owns the original complete13-arm queue and four
reference exports. Its launch commands, per-run receipts, timestamps, source,
binary, input and configuration hashes are in campaign. Only committed payloads
whose completed observer read is available by the checkpoint may contribute.
The sole whole deadline is distinct from the post-run independent audit cost.

The queue is closed; scripts/round83_analyze.py and round83_mechanism.py each
ran once and passed. They check physical/global coverage, all native calls and model
identity, fixed checkpoint comparisons, actual Start vectors and readback,
all25 current paths and the available same-build startup pairs. They guard
against replacing completed analysis outputs. Do not reinterpret acceptance
of a Start as causal performance benefit.

## Portable byte verification and replay limits

Delivery and its separate byte-only verification both passed. The review-only command is:

```powershell
$env:PYTHONUTF8='1'
& 'D:\msys64\ucrt64\bin\python.exe' scripts/round83_package.py --verify-only
```

The compact index binds a gzip JSON member manifest, which records every source,
archive path, length and SHA256. Verification checks all archived bytes without
extraction or a solver. Indexed bundles retain qualification native/CLI/structural
artifacts, startup and diagnostic outputs including failures, full logs/models/
observations/witnesses/Start vectors and reference exports. Compiler and solver
binaries and licenses stay local with hashes; no credential is distributed.

Live replay scripts include absolute Windows model/log paths in original
receipts. Moving archives to another OS is not a demonstrated drop-in replay.
Keep original receipts immutable and provide a separate path map or isolated
original-layout copy before adapting offline readers; verify member hashes
first. Checkpoint availability timestamps remain original, never reconstruction
time. Byte verification is portable and distinct from a fresh performance run.

For a new performance realization, use a new explicit stage/output namespace,
bind the qualified source/compiler/environment and unchanged protocol again,
declare a bounded plan and current controls, and preserve the new identity.
Do not remove guards or overwrite these original records. Recompilation on
different tools is not automatically the same binary or a matched timing test.

ENS-C is default-off and overall acceptance remains pending. Stage evidence review
and publication are complete: draft PR144, https://github.com/yifanXovo/TailoredExact/pull/144 .
publication.json binds the exact evidence head/base. Two HTTPS failures and the
successful exact-object API transport are retained.
No main merge. All producers are closed; see next_hypothesis.md for resource-paused
follow-up, not a command to restart this campaign.
