# Round 23 artifact retention policy

The policy is conservative: immutable Round 22 evidence, all Round 23 official
evidence, forensic diagnostics, excluded attempts, commands, manifests, native
logs, result JSONs, canonical checkpoints, and uncertain historical artifacts
are retained. Tracked historical files default to retention. Pre-existing
untracked content is user-owned and retained.

Only the Round 23 runner's deterministic gzip operation was applied to new
streams exceeding 1 MiB. It records original/stored paths, sizes, hashes, and
`mtime=0`; canonical checkpoints remain directly readable. Exact duplicates
are inventoried but not removed because ownership and all inbound references
cannot be proved expendable. Reproducible builds are classified but retained
for final executable verification. No broad ignore rule was added.

`artifact_inventory.csv` hashes every tracked file, every immutable Round 22
and current Round 23 evidence file, and every non-result/non-build workspace
file. The remaining 288k-file/72GB scratch-result and build trees are recorded
as directory summaries with file counts, aggregate bytes, and largest-file
sizes; this avoids manufacturing an oversized inventory. `.git` internals and
the inventory/duplicate/evidence-manifest files themselves are excluded because
their changing self-hashes prevent a closed manifest. Those generated artifacts
are included in `evidence_package_manifest.csv` where applicable.
