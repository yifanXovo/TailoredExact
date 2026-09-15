# Reproduce and verify Round78

Owned checkout E:/codes/ExactEBRP-round66; the original dirty checkout is
untouched. Production source is 4a0561e0f8193e3e874c1bd0bfa8bc381fb66f5e;
build/round78/v1/ExactEBRP.exe SHA256 is
3fae847a75c3c9d07d8f5f0444daeafb73559865e6bffb816746802b9e2f43ab.
qualification_v1.json preserves exact configure/build/test commands and source
hashes. The initial standalone diagnostic used prototype commit 53207cd20;
its five exact source files are preserved under diagnostic/v1/source_archive.
Production later moved the same controller into the shared core. Do not
rebuild the prototype from the final production tree and call it the original.

The unified candidate preset is research-round78-vds-balanced-descent. It uses
the current-run 25 JDS-X paths, physical insertion/quantity closure, and the
balanced-block duration descent in mathematics.md, before unchanged VD-S proof.
No archived witness is an input to a formal candidate run. Full commands,
input hashes, settings and fixed order are in campaign/identity.json; startup
and diagnostic identities have separate ledgers. Timings require the recorded
Windows machine, Gurobi 13.0.2, compiler, single-thread settings and affinity.

All producer mains refuse to overwrite their completed namespaces. Reproduce
experiments only in a fresh output namespace with an explicit new resource
plan. Repeating a command is a fresh run, not a continuation of a solver state.
Do not invoke the completed qualification/startup/campaign producers to inspect
existing evidence.

After delivery is closed, lossless byte verification needs no extraction or
Gurobi:

```
python scripts/round78_package.py --verify-only
```

The root bundle_manifest.json lists every source path, member, size and SHA256.
The bundles cover qualification CLI/native Start/structural artifacts, startup,
fixed diagnosis and its compile log, all three full runs, and original compact
reference export. Executables remain local with hashes.

For a new offline replay, restore bundles into a separate tree using manifest
paths. round78_audit.py independently enumerates every balanced placement and
replays strict physical changes; its adapter normalizes array-form snapshots
before using the inherited CLI-result hash. round78_analyze.py checks current-
run receipts, original witnesses, global bound scopes/coverage and checkpoint
availability. round78_mechanism.py checks actual submitted/readback Start
vectors against all model rows, native acceptance and the 25-path trace.
Audit mains are guarded against replacing completed outputs.

Some retained native model paths and inherited LP readers use absolute Windows
paths. Bundle byte verification is portable; full cross-OS relocation/execution
is untested. Numerical certification and strict rational proof remain distinct.
This stage's exposed D7 1200-second screen cannot substitute for the required
broader development, common 3600-second comparisons and independent confirmation.
