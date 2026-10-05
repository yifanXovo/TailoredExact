# Reproduction and evidence entry points

Stacked base: R102/PR164 delivery
`0b5640f0de5a29abf6545962dd776a2fab198f90`. The R103 measured source freeze
is `317579b974336233472acd6db80f9f5a4478c880`; measured PE SHA is
`836b2ee3f7e373c8be0a1f2bdf5b6e06ac67a95ea7ef65374972288acdc862ea`.
`production_freeze.json` binds source, helpers, rules and actual runtime.
The final documentation commit is not a new measured build.

Run from the repository root in Windows PowerShell. Management Python is
`D:/msys64/ucrt64/bin/python.exe`; numerical readers use
`build/research/round88-ot/venv/Scripts/python.exe`. The actual DLL is
`D:/gurobi1302/win64/bin/gurobi130.dll`, Gurobi13.0.2, SHA
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
Build receipts record the exact CMake/Ninja/GCC environment. No binaries,
DLL or license are committed. A rebuilt executable with another SHA is
a reproduction build, not an additional strict pair on the measured PE.

Every label is exclusive. Never rerun an existing label, extend a finished
short trajectory, concatenate different runs, or launch while a real
performance/reader/build process is still alive. Check PID, launch, receipt,
completion and runtime_status before resuming a lost tool session. Importing
the Python modules never launches Optimize. Performance is serial and does
not overlap builds, compression or numerical review. Native Threads1,
Seed0, PresolveAuto, zero gaps and certificate tolerances stay unchanged.

## Mathematical and native qualification

`round103_build.py FRESH_LABEL ExactEBRP Round103HullOracle Round103HullTests Round102ServiceTests Round65ReferenceBuild Round98ModelExport`
builds the implementation, persistent support oracle, witness enumerations
and injected-master hull tests. Its default target list is smaller, so
use the explicit targets for full reproduction.
These are engineering receipts. The successful witness tests cover1728
base/552 anchor signed supports plus edge cases; the hull tests cover
seven certificate/UNKNOWN/failure fixtures. Actual persistence faults in
`round103_root_faults.py` are separately charged research, not unit fixtures.

The common launcher charges a finite reader/diagnostic batch, for example:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round103_common.py FRESH_FEE 600 research build/research/round88-ot/venv/Scripts/python.exe scripts/round103_points.py FRESH_POINTS F2 raw 590
```

`round103_points.py` retains the actual complete vector, original typed
matrix, service point, full support plans and exact residual combinations.
`round103_capacity.py FRESH_LABEL ROLE CAP [ANCHOR_SELECTION]` uses the
same old full objective LP plus certified outer rows. Closure requires an
optimal outer LP and every vehicle's explicit within-tolerance member at
that very point. `round103_primal_capacity.py` constructs a finite-column
restriction and saves a numerical full-matrix upper witness; its objective
is not an original BRP lower bound or route upper bound. `round103_anchor_analysis.py`
selects only the investigated at-most-three-anchor structure from actual
mixture resource deficits. `round103_same_domain.py` reprices literal R102
directions on the actual C++ floating domain. The older immutable C2 logs
contain return records without begins; no begin records are reconstructed.

The diagnostic tolerance1e-8 describes numerical membership only. Support
RHS and row scaling use exact dyadic values. Exact rational normalized
combination weights need not be dyadic. Historical nearest-rounded display
upper fields remain preserved; authoritative exact combination residuals
are rechecked, and the future writer emits strict outward floats plus the
exact rational residual. F5 duplicate/numerical UNKNOWN remains UNKNOWN.

`native01` is the F2 SHADOW/SUBMIT120s production qualification, using the
same self-paid pass, with SHADOW writing no rows. It does not isolate the
complete-certification time difference of longer runs. `root_faults01`
exercises two actual preparation persistence failures; both streams are
rejected by the original reader before MIP Optimize. Do not relabel the
intentional child failures as successful native solves.

## Full original-problem campaigns

These are reproduction patterns; create fresh protocols/campaign names:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round103_campaign.py prepare FRESH_CAMPAIGN FRESH_PROTOCOL.json
& D:/msys64/ucrt64/bin/python.exe scripts/round103_campaign.py run FRESH_CAMPAIGN 1
```

Preparation builds fresh unchanged P references without Optimize and pins
source/PE/DLL/input/helper identities. `run` admits only the never-started
next arm after a valid audited prefix. `round103_run_batch.py CAMPAIGN N...`
is finite and serial, with no retries. H uses the base necessary domain,
one self-paid standard LP and normalized certified separation per new
qualified canonical MIP, at most one reliable row per vehicle. It preserves
the original Start policy and pays all setup/auxiliary calls. Cache reuse
is bound to the paid canonical/input/scope identities. P has no new rows
or external Start. Original quantity types and original objective/evaluator
remain unchanged in every arm.

`protection01_protocol.json` preregisters F2 H/ENS/P/J1200s, including the
single contemporary R102-J attribution reference. `development01_protocol.json`
preregisters C2 and N2 three-arm1800s development. `protection_C3_protocol.json`
retains the known R98-C3 regression role, ENS/H/P1800s, not an independent
confirmation input. `round103_development_batch.py` orchestrates only these
nine fixed development/protection arms and their three reference children;
it never revises the candidate or chooses confirmation by outcomes.

`confirmation_freeze.json` binds once-only synthetic H1 V30 and H2 V50,
fixed seeds/bytes, geometry, positive weights, nonzero shortage construction,
orders and the unchanged production freeze. No confirmation search occurs
at input creation. The frozen conditional H1/H2/F5 protocols require a
worthwhile candidate after completed development/protection; explicit
negative cancellation may stop unstarted groups. Cancelled groups have
no reference builder or solve receipt and never count as completed tests.
Immutable stage_decision.json records experimental admission; final_decision.json
records not_promote after all three groups completed. No group was cancelled.
round103_confirmation_batch.py ran those fixed groups serially without retry,
redraw or revision; its final wrapper exit was0.

## Reporting, review and fees

After all performance is idle, charge `round103_verify_evidence.py` as a
reader batch. It reprices retained production directions with the C++
oracle, verifies full standard-LP points and exact original/new model data,
and checks signed rows against the independently audited physical routes.
It never Optimize or reruns native B&B; repeated production pricing is
execution-team validation, not independent alternative recurrence.

`round103_results.py FRESH_REPORT CAMPAIGN...` reuses the original scope
and clock readers without recovery overlays. It retains per-arm/paired
CSV, actual native stages, cost, Start, physical witnesses, signed gaps
and common covered checkpoints. Both certified arms may have real time
ratios; a one-sided certificate has no invented exact speed ratio; both
unproved arms have unknown eventual certification order. Publication and
observation milestones do not identify exact engine discovery/proof times.

`round103_fees.py FRESH_FEES` reconciles all closed research receipts,
performance plus recorded postexit audit costs, failures and conservative
allowances, with actual auxiliary Optimize/DP counts. Nested seconds are
not added twice. Reporting/independent numerical readers are charged;
pure builds, unit fixtures, receipt reconciliation and byte packaging are
separate engineering. Reference children are conservatively counted.

The independent read-only review retains its own different level-DP code,
actual support/plan/matrix checks, paid failure and scoped conclusion under
`review/`. It did not independently rerun native B&B or price all827 F2
capacity rows. Its legacy begin-log assertion failure and precision
representation findings are disclosed in `independent_review.md`.

`round103_package.py FRESH_PACKAGE REPORT FEES CAMPAIGN...` compresses
exact original bytes only while idle. Its manifest maps compact points,
plans, proofs, full LP/typed matrices, canonical data, physical report
witnesses, failures and receipts to SHA-indexed larger local artifacts.
Hashes are provenance, not substitute mathematical certificates. Existing
user files and unrelated historical data are never added or overwritten.

Final completion/admission state is recorded in `final_report.md` and
`RESUME.md`. ENS-C stays default. H is explicit research opt-in through
`--round103-resource-hull submit`; M-B/R101/R102-J are not automatically
combined or promoted, and this branch is neither merged nor deployed.

## Completed final entry points

All research is closed at72 charged starts. Do not run another research
reader in this completed round. For a separately budgeted reproduction,
use fresh exclusive fee/output labels and the recorded environment:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round103_common.py FRESH_EVIDENCE 600 research build/research/round88-ot/venv/Scripts/python.exe scripts/round103_verify_evidence.py FRESH_EVIDENCE_OUTPUT confirmation01 confirmation_long01 long_tail01
& D:/msys64/ucrt64/bin/python.exe scripts/round103_common.py FRESH_REPORT_FEE 600 research D:/msys64/ucrt64/bin/python.exe scripts/round103_results.py FRESH_REPORT native01 protection01 development01 protection_C3 confirmation01 confirmation_long01 long_tail01
```

The actual closed runs use evidence_final01/diagnostic final_evidence01 and
reports_final01. Final independent metadata interface is:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round103_common.py FRESH_REVIEW_FEE 300 research D:/msys64/ucrt64/bin/python.exe results/unified_exact_round103/review/round103_final_review.py --reports reports_final01 --clocks reports_final01_clocks --fees fees_prefinal02 --decision stage_decision.json --final-decision final_decision.json --receipt-label FRESH_REVIEW_FEE --output FRESH_REVIEW_OUTPUT --campaigns native01 protection01 development01 protection_C3 confirmation01 confirmation_long01 long_tail01
```

review02 verifies the corrected J cost subset and all final run metadata;
review01 and both prefinal snapshots remain historical. Final complete
fees_final01:72 starts/44907.45178329994s,102 native/19675 auxiliary Optimize,
18624 DP. The J reference contributes52 inherited DP calls; the original
report whole_run_costs.csv DP column is explicitly R103-only. fees.csv,
failures.csv and fee_reconciliation.json are the complete accounting.
Pure receipt reconciliation and byte packaging use engineering receipts:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round103_common.py FRESH_FEES_ENGINEERING 300 engineering D:/msys64/ucrt64/bin/python.exe scripts/round103_fees.py FRESH_FEES
& D:/msys64/ucrt64/bin/python.exe scripts/round103_common.py FRESH_PACKAGE_ENGINEERING 1200 engineering D:/msys64/ucrt64/bin/python.exe scripts/round103_package.py FRESH_PACKAGE reports_final01 fees_final01 native01 protection01 development01 protection_C3 confirmation01 confirmation_long01 long_tail01
```

compact_evidence03 contains exact original bytes, gzip-compressed when large.
Verify both compressed SHA and decompressed source SHA from manifest.json.
The SHA-indexed LP pool deduplicates identical bytes; contracts/points bind
their actual source/canonical paths. A fresh checkout contains the compact
package, not every local raw directory. Restore selected original paths from
the manifest and matching LP digests before replaying saved evidence. The
original paths are Windows E:/codes/ExactEBRP; another root/runtime/build
requires a fresh identity and cannot claim the original strict paired PE.
Larger closure iterations are indexed locally; they are not all committed.
The package is selected evidence, not an independently repriced proof for
all827 F2 capability rows. engineering_final.json lists the engineering
receipts after byte packaging closes; it is outside the package's own cutoff.

`round103_verify_bytes.py PACKAGE FRESH_OUTPUT` is pure engineering: it verifies
compressed and original byte SHA, all explicit frozen source/runner bytes,
measured PE/DLL and protected user files. byte_check02/byte_verification02
passed for1119 source records/1004 unique files. It does not audit mathematics.
Round103 attributes preserve frozen driver/input/evidence bytes across checkout.
