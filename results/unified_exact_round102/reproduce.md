# Reproduction and evidence entry points

This branch stacks on R101/PR163 at `6a505855dc539f0d35a983c13ab22258480b79de`. Production C++ was frozen at commit `2b65d483e` before complete development. `production_freeze.json` contains every source binding, binary and runtime SHA and all four input identities. Results belong to that common build; the final documentation commit is not a newly measured executable.

## Environment and immutable labels

The measured Windows environment uses GCC14.2, Gurobi13.0.2 and exactly `D:/gurobi1302/win64/bin/gurobi130.dll`. Management Python is `D:/msys64/ucrt64/bin/python.exe`; NumPy/gurobipy diagnostics use `build/research/round88-ot/venv/Scripts/python.exe`. Run from the repository root. The existing diagnostic environment received NumPy; historical data was not modified. No executable, DLL or license is committed.

Each launcher uses exclusive creation. **Do not rerun existing labels**, concatenate fresh runs as extensions, or continue a batch while its real solver process remains alive. A new reproduction must use fresh labels and freshly prepared identities; exact binary/helper/input identities are checked before every arm. Every native solve remains serial, Threads1/Seed0/PresolveAuto, zero relative/absolute MIP gap, and the inherited tolerances. A different rebuilt PE is a reproduction build, not the original strict performance pair.

## Engineering and mathematical qualification

`scripts/round102_build.py FRESH_LABEL` configures/builds the core, diagnostic, DP tests and callback fault tests. Its receipt is pure engineering. The DP test independently enumerates1728 signed cases plus edge fixtures; the private callback test covers100 checks and ten failure streams. `round102_fault_reader.py STREAM_DIRECTORY FRESH_LABEL` uses the inherited interrupted-prefix reader and exclusively creates a fresh engineering record.

Use `round102_run.py` to preregister and charge a finite diagnostic batch, for example:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round102_run.py --cap 300 --calls 0 FRESH_FEE -- build/research/round88-ot/venv/Scripts/python.exe scripts/round102_native_points.py FRESH_POINTS development01
```

The saved LP screen and24 Optimize calls are in `diagnostics/screen01` and `diagnostics/lp01`. `round102_screen.py`, `round102_lp.py` and `round102_support.py` define the actual finite families, original service mapping and exact-dyadic integer support. These operate on traceable inherited LPs; they are retrospective qualification, not free historical rows injected into production. The exact F5 exported-duration proof is in `diagnostics/F5_actual_export_redundancy.json`.

After performance is idle, `round102_verify_certificates.py FRESH_LABEL CAMPAIGN...` checks complete saved supports, signed actual coefficient maps/RHS/activity and physical witnesses without Optimize. `round102_simple_budget.py FRESH_LABEL` checks cheap explanations for literal F2 supports. `round102_native_points.py` checks the full first original-column vector against **that call's canonical model before R102 rows**. Claim equality to a historical entire old LP only after separately matching its SHA. Later rows retain their service slice, not an invented complete later vector.

## Complete original-problem runs

The preregistered `native01_protocol.json` and `native02_protocol.json` are120s engineering-to-native qualifications on different successive binaries. They are not strict full-method performance comparisons across those binaries. `protection01_protocol.json` runs F2 ENS/J/P at1200s, `isolation03_protocol.json` adds one F2 SHADOW control, and `development01_protocol.json` runs C2/N2 P/ENS/J at1800s in the explicitly recorded orders. `round102_campaign.py prepare FRESH_CAMPAIGN FRESH_PROTOCOL` builds unchanged P references without Optimize; `round102_campaign.py run FRESH_CAMPAIGN NUMBER` runs only a never-started next arm after the valid audited prefix.

`isolation04_protocol.json` adds the complete1800s N2 SHADOW control. `round102_freeze_confirmation.py` exclusively saved confirmation_freeze.json and all three subsequent protocols before C3: confirmation01 C3 P/ENS/J1800s, confirmation_long01 N3 J/P/ENS3600s, and conditional long_tail01 F5 ENS/J/P3600s. C3/N3 are traceable larger R98/R99 roles unused for R102 design. All planned arms completed; N3's material budget gain admitted the already frozen F5 second long group, without source/direction/parameter changes. No fresh extension or stitched trajectory was used. Native/full results are immutable local data, not commands to rerun these labels.

`round102_results.py FRESH_REPORT CAMPAIGN...` reuses the inherited original-domain and clock readers with no R101 recovery overlay. Normal endpoints, whole-process costs, actual native calls, physical witnesses, root-table data, proof costs and signed gaps are retained separately. Shared checkpoints require that each arm's same-run verified prefix covers the checkpoint; a reliable certified endpoint can carry, an unproved early exit cannot. No interpolation, borrowed certificate or native Runtime substitution is used. Log publication/observation is an availability milestone, not an exact engine discovery time.

`round102_budget.py` reconciles billed starts and observed outer seconds plus explicitly labeled conservative allowances; engineering is separate and internal Optimize is not double billed. `round102_package.py FRESH_PACKAGE REPORT CAMPAIGN...` creates exact-byte compact evidence and a SHA index for larger local files. Compression and heavy readers/review must run only after all performance is idle. Hash indices support provenance; actual compact matrices, vectors, rows and routes carry the main mathematical evidence.

Final local outputs are reports_final01 and reports_final01_clocks, with all nine campaigns listed below. Their checked-in exact copies are under `compact_evidence/report/reports_final01/` and `compact_evidence/report/reports_final01_clocks/`; the large local raw directories are indexed rather than duplicated in Git. service_native_calls.csv records actual DP/cache/API/nonzeros and the native User bucket, leaving missing counts unknown. service_distinct_rows.csv compares exact coefficient/RHS values in physical car/station/p,d,z coordinates across native MIPs, separately by arm/input. checkpoint_pairs.csv and isolation_pairs.csv preserve matching-build/common-cap scope; clock tables include common1797/3597s coverage without pretending the normal early exit reached1800/3600. Whole-round fee_reconciliation.json is56 starts/43126.28325889993s; campaign-only33 starts/100 Optimize is a subset, and the finite LP batch adds24 actual Optimize calls. Conservative independent allowances are explicit; engineering source/fixture reads are separate. Initial missing-NumPy and two later diagnostic launcher failures are charged/preserved; fresh labels completed their checks without changing production.

These are reproduction **patterns**, with fresh report/package/receipt labels required:

```powershell
& D:/msys64/ucrt64/bin/python.exe scripts/round102_run.py --engineering --cap 300 --calls 0 FRESH_REPORT_RECEIPT -- D:/msys64/ucrt64/bin/python.exe scripts/round102_results.py FRESH_REPORT native01 native02 protection01 isolation03 development01 isolation04 confirmation01 confirmation_long01 long_tail01
& D:/msys64/ucrt64/bin/python.exe scripts/round102_run.py --engineering --cap 300 --calls 0 FRESH_PACKAGE_RECEIPT -- D:/msys64/ucrt64/bin/python.exe scripts/round102_package.py FRESH_PACKAGE FRESH_REPORT native01 native02 protection01 isolation03 development01 isolation04 confirmation01 confirmation_long01 long_tail01
```

The reporter/package reads existing immutable campaigns without solving. For NumPy/support/canonical-model readers, always use the round88 venv Python in the diagnostic example above; the management Python has no NumPy. Put wrapper options **before** its receipt label. Build04, faults02 and engineering/fault_reader_final01.json qualify the unchanged production build. Final signed support/physical replay is diagnostics/final_certificates02; first complete points are final_native_points02, prelong_C3_points01, prelong_N3_points01 and final_F5_points01. final_simple_budget02 corrects the coarser immutable final_simple_budget01 calculation. Compact evidence retains real rows/contracts/first vectors, LP witness vectors, typed old F2 matrix, physical routes and receipts; manifest.json indexes exact large local models, logs and binaries. No hash is substituted for a mathematical witness.

The final decision and completion state are recorded in `final_report.md` and `RESUME.md`. Both confirmation roles and both long groups completed normally/audited. No M-B combination or further performance grid was admitted after the mixed standalone results. ENS-C stays default; `--round102-service-cuts submit` is explicit research opt-in. R101 cuts and M-B remain OFF; P remains unchanged and receives no external Start. Independent review recomputed signed supports and actual-matrix points, then read final fees/clocks, with no independent native search or LP Optimize.
