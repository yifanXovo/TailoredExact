# Reproduce and verify Round79

The campaign reuses the exact qualified R78 production source
4a0561e0f8193e3e874c1bd0bfa8bc381fb66f5e and
build/round78/v1/ExactEBRP.exe, SHA256
3fae847a75c3c9d07d8f5f0444daeafb73559865e6bffb816746802b9e2f43ab.
R78 qualification_v1.json records configure/build/test commands; its eight
verified evidence bundles retain the qualification, structural and startup
evidence. This stage adds no C++ or parameter change, build, test or native
qualification fixture. Inherited costs are not charged as new work.

Read plan.md and campaign/identity.json for the frozen six roles, input/source/
binary/driver hashes, settings, exact commands, caps and fixed serial order.
Each arm obtains its own information. Original compact reference exports bind
P-GRB without adding a Start, cut or imported bound. Matched timing requires the
recorded Windows machine, Gurobi13.0.2, compiler and logical2/mask4 affinity.

Never invoke completed producer mains to inspect evidence. Their namespaces
are immutable. A repeated solve or longer budget is a fresh run requiring a
separate plan, not continuation of an existing solver state. All observed
checkpoints belong to their original complete run; availability is not backdated.

Once delivery is closed, verify every retained byte without extraction or Gurobi:

```
python scripts/round79_package.py --verify-only
```

bundle_manifest.json records per-member source paths, lengths and SHA256.
The stage bundles cover every full-run raw tree and all six compact references.
Restore them into a separate namespace before any new offline replay; do not
overwrite the retained originals. round79_analyze.py validates receipts,
physical endpoints, bound scopes/coverage and the frozen comparison rules.
round79_mechanism.py checks actual Start vectors against actual model rows and
readback/native logs, plus all25 startup paths and physical descent handoff.
round78_audit.py supplies the unchanged balanced/strict physical replay.

Some model/native-log paths and inherited LP readers use absolute Windows
paths. Hash verification normalizes repository bundle paths; full cross-OS
execution/relocation is untested. Executables remain local with hashes.
Normal numerical certificates are not strict rational proofs. This exposed
small/nonzero panel does not replace the required common3600 medium/large
comparisons or sufficiently diverse unadapted confirmation.
