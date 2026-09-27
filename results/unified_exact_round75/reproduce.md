# Reproduce and verify Round75

Use the owned worktree E:/codes/ExactEBRP-round66. The original dirty checkout
was not modified. R74 base and R75 measured source/binary identities are in
prior_publication_verified.json, qualification_v2.json and final_report.md.

Publication uses the Git Data connector after four ordinary Git connection
failures. Its commit identity may differ, while the published tree is checked
against the local publication tree. measured_history.bundle preserves every
original R75 measured-source/evidence commit through0ea9781aba59fa629c48d48bea2f6df5d6c56ba6.
It requires the recorded R74 base, already on GitHub. The bundle passed
git bundle verify; publication_transport.json records its SHA256 and scope.
To inspect the original history after cloning/fetching R74, fetch this local
bundle into a new, unused archive ref. Do not overwrite an existing branch.

Portable bundle verification (Python standard library only):

```
python scripts/round75_package.py --verify-only
```

It reads each of three bundles and checks every member's exact length/SHA256
against bundle_manifest.json without extracting. Bundles retain original
relative member names and source paths. The reader normalizes stored Windows
separators in repository-relative paths. producer_scripts/round75_package_v1.py
retains the exact producer matching the manifest hash, before this read-only
path portability fix. Cross-OS execution has not itself been tested.
Do not overwrite existing raw or
qualified build namespaces. Executables remain local under build/round75/v1
and v2; their SHA256 values are in qualification audits. Build commands,
compiler/runtime and source-file hashes are recorded in qualification launches.

For a new reproduction use a fresh checkout/output namespace, the same Gurobi
13.0.2 and qualified compiler, and the frozen configure/build/test commands.
The qualification driver deliberately refuses to replace v1/v2. Failed V1 and
successful V2 identities are both essential; V1's missing proof whitelist is
not a passed certificate. Native tiny inputs, models, Starts, logs and original
witnesses are in the qualification bundles; tests.log records all56 tests.

The startup identity contains all ten exact commands and original input hashes.
The native program derives its own JDS-X start, then QDS-X quantities; no saved
witness is fed to it. A fresh performance experiment needs a separately admitted
plan/identity, not edits or reruns of this closed startup directory. The current
screen has no full-method performance, P-GRB control or confirmation claim.

Offline replay entry points are scripts/round75_startup.py (physical trace
functions), round75_endpoint_oracle.py (two full neighborhood oracles),
round75_audit_qualification.py and round75_native_audit.py. Their original main
functions are guarded against replacement. The raw trace initial/final snapshots
and every operation change permit independent reconstruction. Restore bundles
to a separate directory and adjust only explicit path roots for a fresh replay.
Several inherited model/witness tools use recorded absolute Windows paths;
cross-machine full path relocation has not been tested. Hash-only delivery
verification above is independent of those original paths.

See plan.md and qualification_repair_plan.md for bounded allocations, and
resource_summary.json for actual costs. No reset credit was used. The stage's
negative finding does not mark the sustained research goal complete.
