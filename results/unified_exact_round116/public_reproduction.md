# Round116 current evidence restoration

The scientific payload contains the frozen six inputs,24 fixed arm positions,
36 pair positions, actual qualification and raw evidence, source/license/
projection lineage,17 qualified formal endpoints, the one failed pending arm,
and six unstarted positions. Its execution stage is BLOCKED. The signed carrier
manifest lists every included byte; production executables, native DLLs,
licenses, credentials and full historical performance carriers are excluded.
The large cohort JSON and full native-claim CSV are carried losslessly inside
that bundle; the smaller endpoint, reliability and pair tables are also directly
available in the repository.

The standard-library reader works with Python3.12 without Gurobi. Join the
indexed32MiB parts in manifest order, verify their SHA256s and extract the gzip
tar into a new empty directory. Verify every file against the manifest. All
saved absolute native paths are translated to that root by the existing
portable reader. No original-worktree data fallback is allowed.

Use `scripts/read_round116_reporting.py --root <restored-root> --out <new-dir>`
to reconstruct the current raw core. The original admitted reader is retained
unchanged; the reporting copy only removes a duplicated `id` keyword in vector
construction. The failed formal return audit is not patched. The exact diff
and actual original reporting failure are in `engineering/reporting_reader.diff`
and `engineering/reconstruction01_failure.txt`.

`round116_report.py organize` separates formal and H100 qualification tables.
`round116_analysis.py` recomputes exact inventory/objective components from
sealed existing fleets; it neither constructs routes nor strengthens formal
certificates. `round116_source_check.py` regenerates all six input bytes from
the raw-mapped projected source table. Forward PROJ was exercised during source
preparation; portable restoration checks the saved transformation contract,
inverse checks and serialization rather than independently rerunning PROJ.

The actual one-export/one-empty-root restoration uses `round116_delivery.py`.
`round116_restore_check.py` then reconstructs and compares raw and organized
core, exact arithmetic, existing physical/Start summaries and source lineage.
New engineering durations/timestamps are excluded from equality explicitly;
measured producer/verification/total clocks and paid native fees are compared
unchanged. Original files are used only as equality references. Output-only
receipt routing preserves the archived receipts. No native optimization runs.

The public payload commit precedes actual export/restoration/review receipts.
Those receipts and remote head/base/draft/OID observations are later, separate
commits; they never claim to verify their own future commit. This is an
implementer-authored separate restoration and review, not a third-party native
reproduction. No next research round is automatically started.
