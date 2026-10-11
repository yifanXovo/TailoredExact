# Restore and inspect the public evidence

The scientific carrier is fixed at commit `fcf9aa4881a76bbbb26f5ec409a74ea384672886`. One omitted 394-byte signed R113 authority is committed separately at `70fd7c6fc3c3dbbb3ad218a52ebfd8ac173c42eb`. There is one compressed carrier and one actual carrier Git archive. The supplemental leaf is restored from its exact committed Git blob, without making another carrier or archive. Its digest is bound by the already signed inherited dependency manifest.

From a checkout of this PR, use the provided Python3.12 scripts and a genuinely nonexistent destination:

```powershell
python scripts/round115_delivery.py restore fcf9aa4881a76bbbb26f5ec409a74ea384672886 E:/your/new-empty-root
python scripts/round115_dependency_repair.py restore 70fd7c6fc3c3dbbb3ad218a52ebfd8ac173c42eb E:/your/new-empty-root
python E:/your/new-empty-root/scripts/read_round115.py --root E:/your/new-empty-root --out E:/your/new-empty-root/reconstructed --compare results/unified_exact_round115/reports_final
```

The delivery helper uses a once-only export destination for the recorded execution; a new independent reproduction should choose its own checkout/output directory rather than reuse an existing recorded destination. It checks every compressed part and restored manifest SHA. The inherited receipt supplement checks both its Git blob hash and the signed inherited manifest hash. Current reconstruction reads the restored root's sources/input/raw/authorities only. The original finalized reports are used solely as the expected comparison, never as a missing-file fallback. CSV field capacity is fixed at64MiB before parsing.

In this execution, `E:/codes/ExactEBRP-round115-restore01` began empty. All6393 carrier files initially passed hash checks; the first reconstruction failed on the excluded small inherited receipt and is preserved. After the committed blob supplement,35 current core tables/JSON reproduced exactly, excluding only the fresh cohort observation timestamp from the comparison. The reader SHA also matches the admitted identity. No native solver or route-generation replay occurs.

`public_export_receipt.json`, `public_restore_receipt.json`, `public_dependency_incident.json`, `public_dependency_supplement_receipt.json`, `public_reconstruction_receipt.json` and `review/whole_goal01/signed_review.json` record actual sequential execution. They were created after their corresponding action and are not included in their own earlier science export. The seven-question review is implementer-authored; no independent third-party person/agent or native performance rerun is claimed. PE/DLL/license/credentials and full old carriers are excluded.
