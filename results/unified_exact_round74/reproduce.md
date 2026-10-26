# Reproduction and evidence entry points

The completed campaign will retain exact inputs, executable/source hashes,
all four argv lists, settings and limits in campaign/identity.json. Live or
unfinished status is authoritative in status.md and campaign/summary.json;
the presence of this guide does not imply completion.

After delivery, the portable read-only integrity check is:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts/round74_package.py --verify-only
```

Use the available Python executable on another machine. This command reuses
R73's tar member verifier, checks bundle hashes and every member's length and
SHA256, extracts no files and starts no optimizer. It verifies byte identity;
it does not rerun Gurobi or manufacture a new certificate.

campaign/bundle_manifest.json maps every raw source path to a bundle member.
The run bundles retain result, physical routes, all journal payloads/receipts,
actual observation timestamps, native logs/models, phase and controller
ledgers, Start metadata and submitted/readback vectors. The reference bundle
contains the fresh original P model and fingerprint. Endpoint, checkpoint,
comparison, mechanism and resource JSON records provide compact review entry
points. Inputs are already versioned at the paths and hashes in identity.json.

The original local raw tree is campaign/local_raw under the owned
E:/codes/ExactEBRP-round66 checkout; its absolute model paths appear in journal
records. The frozen independent reader is scripts/round73_native_evidence.py,
and original route recomputation is reused from scripts/analyze_round61.py.
R74 analysis adds common-time comparisons and final-witness consistency;
R74 mechanism audit reuses the R67/R68 row and actual-Start vector mapper.
Their output records identify scripts and costs. Do not rerun completed
analysis/packaging in place: those namespaces are guarded against replacement.
Moving raw evidence to a different machine requires explicit relocation of
recorded model paths before local replay, while preserving original bytes and
mapping that relocation. Such a relocated full replay is not claimed tested
by the portable hash check.

A fresh performance reproduction is a new experiment. Use a clean checkout
of the measured source4ba09609cf3fb92ef29598dce8201231668324f9 or verify all
its recorded source hashes in the R74 checkout. The retained executable is
build/round73/v6/ExactEBRP.exe with SHA256
90d7bd2f84744b87958ff19a6e35bed76722cf680964a04ad6331135f5ff9029.
The inherited configure/build/CTest commands and passing54-test evidence
are in R73 qualification_v6.json and its retained qualification outputs.
A rebuild needs a new binary identity and qualification; do not claim it is
the retained binary merely because the source matches.

Use the frozen launch argv and a new empty output namespace, remapping only
executable/output/artifact locations as necessary. Preserve original inputs,
T/handling/lambda, presets, Threads1/Seed0/PresolveAuto, gaps/tolerances and
whole-run limits. Reuse the owned launcher/child affinity helper and the
supervised journal observation loop in scripts/round74_research.py. Record
the fresh identity before dispatch and serialize all optimizer calls. The
historical driver intentionally refuses its already occupied campaign path;
never delete evidence to make it run. No extra reproduction is launched or
included in this stage's measured outcomes by these instructions.
