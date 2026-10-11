# Evidence-only public reconstruction

Scientific terminal state is BLOCKED. The carrier stores current Round113 evidence and the explicitly limited signed R112 authority needed for12 old measurements/18 old pairs. It excludes PE, DLL, license, credentials and older full carriers. Restoration executes no Optimize and does not reproduce solver performance. Old matrix/scope authority is inherited from its original signed review, with current byte/clock checks, not newly re-audited from old LP files.

The manifest binds every restored file by exact bytes/SHA and binds the current offline reader, its admitted predecessor and delta. Single-blob evidence.tar.gz is used below95MiB; only an actually larger compressed stream is split into90MiB exact contiguous parts. No artificial split is allowed. Each destination must be a new nonexistent directory.

From a fresh public export containing scripts/publish_round113.py, scripts/round110_public.py and the manifest/carrier:

```powershell
python PUBLIC_ROOT/scripts/publish_round113.py restore --public-root PUBLIC_ROOT --out RESTORED_ROOT
python RESTORED_ROOT/scripts/read_round113.py --root RESTORED_ROOT --out RESTORED_ROOT/rebuilt --compare RESTORED_ROOT/results/unified_exact_round113/reports_final
```

Use actual absolute paths for PUBLIC_ROOT and RESTORED_ROOT. The restorer has only standard-library imports; the reader receives its restored root explicitly. CSV field size is64MiB. Core CSVs compare every field and core JSONs compare exact parsed values. Full physical_completion.json is supplemental organization evidence; its original raw fleet/input are independently revalidated by the reader. No file is fetched from an original worktree to fill a missing dependency.

Scientific payload, including raw authority/admission/reports/independent scientific review, is committed before later export/restore/remote receipts. Later receipts describe only operations actually completed and identify their observed scientific payload; no receipt verifies a future commit containing itself. The actual publication receipt records measured size, export, empty-root restore, reconstruction comparison and independent restored-root review.
