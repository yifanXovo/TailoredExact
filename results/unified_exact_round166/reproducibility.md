# Reproducing the representation and the evidence

The measured C++ source is commit
`0298dd45fbc3645af927c4a4dd1d43ecbdb567a9`. The delivery adds paper, data,
readers and receipts on top. `candidate_manifest.json` binds complete actual
source bytes, compiler, CMake cache, own PE and external Gurobi DLL. B and
C166 were measured with the same new PE, SHA256
`27e71873536bcd8e6001aee0c2514a5cc8122763728c62e6d467cd528b48daba`.
Historical R163/R164 measurements retain source
`e920b92e199e825ec89a2932f701861ff158e0d4` and PE
`fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93`.

## Build and explicit candidate entry

The measured platform is Windows/GNU with Gurobi13.0.2. The compiler is
`D:/msys64/ucrt64/bin/g++.exe`, its SHA is in the candidate manifest. A fresh
Ninja CMake build uses `EXACT_EBRP_ENABLE_GUROBI=ON`,
`EXACT_EBRP_BUILD_ROUND166_QUALIFICATION=ON`,
`GUROBI_ROOT=D:/gurobi1302/win64`, empty `CMAKE_BUILD_TYPE`, and empty
`CMAKE_CXX_FLAGS`, matching the recorded build. Build targets are `ExactEBRP`
and `Round166Qualification`. Full configure/build logs are under `build/`.
The runtime carrier contains the project's own executables. Supply a locally
licensed Gurobi installation; its external DLL SHA is
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
The commercial DLL and license are external dependencies.

`--round166-breakpoint on` selects the explicitly named
`research-C166-breakpoint-bit` / `round166-breakpoint-bit` representation.
Its default is off. Full preset and all explicit research-off flags are in
`config/gi_tbc_c166_round166.json`. The entry reuses the pure existing
GI-TBC planner with that separate configuration. For example, this command
only displays a complete launch plan:

```powershell
python -B scripts/paper_c166_round166.py --input results/unified_exact_round163/inputs/R163-C20-S/first/instance.txt --out-dir E:/codes/ExactEBRP-work/reproduce-round166/C20-C166 --T 5400 --lambda 0.10787606377934943 --cap 1200 --seed 0 --json
```

The entry requires a new output directory. Its `--run` option is the explicit
execution request for a separately planned replication. The actual twelve
measured launch vectors, including the fresh B controls, are preserved in
`matrix_frozen.json` and each campaign `identity.json`. The candidate entry's
six normalized vectors were checked against that matrix with zero producer
launches (`reproduction_entry_check.json`). Stable B's existing entry remains
`scripts/paper_s2.py`; use the new same-build PE explicitly when reproducing
the paired controls. The literal frozen commands are authoritative for
performance replication. The legacy planner format name `paper-S2-launch-v1`
describes serialization; the separate config and actual result identify C166.
Embedded R163 `known=false`/`exposed=false` fields preserve the original
R163 selection metadata. Round166 explicitly treats every input as already
exposed (`panel_kind`, endpoint `not_holdout` and the final summary); those
inherited flags do not establish a new holdout cohort or enter the algorithm.

## Qualification and full-method measurements

`src/round166_qualification.cpp` implements all new optimization, exact tiny
enumeration and local/complete model drivers in C++. Local fixed objectives,
64 calls, eight root/child paired LPs, 16 calls, eight boundary/tiny native
calls, and eight nonzero-controller calls total96 Optimize. Zero-controller,
algebra, legacy-B export and independent readers add zero. The complete
diagnostic outer window is539.0807707s, including failures/waits/export.

The tiny instance has two stations, initial stock(3,0), targets(2,2),
capacities(4,4), one capacity3 vehicle, zero travel, 60s pickup/drop and
T=360s. Its independently enumerated optimum is stock(1,1), objective.15,
with one loaded unit returned and240s total handling. The donor stock1 is
an interior non-breakpoint. Stock(4,0),T=480 supplies the independent exact-zero
case. The retained zero-stock/loaded-return native fixture checks the other
boundary. `qualification/reader_fix.json` and controller failure files retain
two analysis-reader failures; healthy producers were kept and read again.

The twelve formal arms execute serially, six fixed exposed inputs, Seed0,
own H seed20260626, one thread, native default strategies, gaps0 and unlimited
NodeLimit. The nominal caps are1200s for n20 and2400s for n35; cap+300
reservation and cap+900 fault watchdog do not extend a producer's evaluation
window. The inherited native cap-6, process shutdown margin30 and outer
hard-stop cap-2 remain in the command contract. Each arm has a fresh process
and pays H/import/construction/native/online checks/close in T_produce;
required subsequent checks are T_verify. `fees/`, producer receipts and
`reports/summary.json` retain nonoverlapping actual costs. Native Runtime,
Work, nodes and H time explain the same work rather than adding extra fees.

Raw model matrices, complete semantic Starts, native journals/logs, complete
fleets, source/coverage trajectories and reader failures are in the new-only
carriers and member map named by `evidence_archives.json`. The map restores
relative paths and checks every member SHA. The earlier source carriers are
referenced by fixed identity; the selected old members are not republished
as an entire historical collection.

## Solver-free data and document reconstruction

From a recovered current source/evidence tree, these are read-only or document
actions with zero Optimize:

```powershell
python -B scripts/round166_analysis.py
python -B scripts/round166_results.py
python -B scripts/round166_csv.py
python -B scripts/round166_figures.py
python -B scripts/round166_documents.py assemble
python -B scripts/round166_documents.py pdf
python -B scripts/round166_documents.py qa
```

`review/data_physical_archive.json` contains all50 complete verified fleet
records and their owners. `data_recover.py` identifies fixed historical
members needed for an independent reconstruction; the original cover's
canonical full-content SHA and scoped summary avoid copying long old traces
into every record. `round166_analysis.py` uses rational arithmetic, all true
finite intersections, original source qualifications and explicit safe
margins. Its inputs enter no measured producer.

Only the five maintained R137 components and their referenced figures feed
the current document assembly. The R166 builder explicitly inherits R165's
working typography and binds actual date, template/header and toolchain in
the cache identity. `method_and_model_source.md` remains historical. Source,
assembly, PDF, page-text/bounds and actual visual checks are tied in
`source_manifest.json`, `document_build.json` and `document_qa.json`.

The separate six-row B-only increment preserves the original28-column
schema. The local103-row GB18030 copy and user files remain unchanged; the
requested106-row master was not found in the bounded entry search. Full
details and the three absent old N/A-P identities are in
`CSV_reconciliation.json`. C166 is recorded only in its variant/pair tables.
