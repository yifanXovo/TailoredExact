# Round 36 evidence package

- Final classification: `decomposition_geometry_dominant`.
- Official rows: 56 checksum-complete.
- Separately frozen Stage C rows: 47 checksum-complete.
- Stage C historical-comparator gate:
  `False`; no automatic
  promotion was performed.
- Representative patterns: 5.
- Representative four-arm rows: 20.
- Compressed raw artifacts: 280.
- Raw bytes before/after lossless gzip: 6869623 /
  1115175.
- The all-row trajectory CSV is retained locally and packaged as deterministic
  `trajectory_events.csv.gz` for repository synchronization.
- License-sensitive material: none.
- Model dumps: excluded.

Representatives are selected deterministically within each frozen Round-35
pattern by the largest absolute HH-versus-BW-P common-window proof-AUC delta.
All four arms are packaged for each selected instance. Original raw paths,
uncompressed hashes, compressed paths, and compressed hashes are recorded in
`representative_raw_manifest.csv`. All 56 complete raw directories remain
local and are independently checksum-addressed by their completion markers.
All 47 Stage C completion markers and artifact manifests are independently
revalidated and checksum-indexed by `stage_c_completion_manifest.csv`; the
full Stage C raw directories also remain local.
