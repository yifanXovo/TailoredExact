# Reproduce and verify Round76

Owned checkout: E:/codes/ExactEBRP-round66. The user's original dirty checkout
is untouched. Base is published R75 commit692cf9f0ef8852d4ee0d62c5ed206c081658d158.
The measured production source is4f6254c2639972ce3ac2b80906ce6d4ebd701f3e;
qualification_v1.json records every source hash and configure/build/test command.
Only documentation, evidence and experiment drivers change after that build.

Use the same Gurobi13.0.2, MinGW compiler and Windows machine settings for
paired timing claims. Build output is frozen at build/round76/v1. The actual
binary SHA256 is in qualification_v1_audit.json and startup/identity.json.
All ten startup commands, instance hashes, settings and prelaunch identity are
in startup/identity.json. They derive their own witness; no historical route
is supplied. The separate fixed-witness diagnostic identity records the old
R75 library and two archived witnesses; that is only mechanism diagnosis.

The drivers refuse to replace completed namespaces. To reproduce, use a fresh
checkout/output directory and replay the frozen commands, preserving the full
source identity and original physical/numerical contract. Do not rerun closed
driver mains in this checkout. Full performance requires a new admitted plan.

Portable byte verification, without extraction or Gurobi:

```
python scripts/round76_package.py --verify-only
```

It checks every member length/SHA256 in all three bundles, including fixed
diagnostic output, startup output, the new structural composition traces,
all qualification CLI model/log/witness trees, the standalone native Start
fixture, and build/test logs. Executables remain local with recorded hashes.
Stored repository-relative Windows paths are normalized by the verifier;
cross-OS execution itself has not been tested.

For offline mathematical replay see round76_startup.py::replay_closure and
the reused round73_seed_diagnostic.py::replay_joint. These rebuild operations
independently of C++ materializers, then invoke the original full Python
physical/objective check. round76_native_audit.py checks both actual submitted
vectors and original tiny certificates; round76_audit_qualification.py verifies
all actual Optimize counts/native versions. Restore raw bundles into a new
directory and adjust explicit roots for a new replay. Several inherited LP
audit helpers retain absolute Windows paths; full relocation is not tested.

Plan.md admits the completed fixed diagnosis; implementation_plan.md admits
the completed source qualification and startup screen. No complete-method,
long or independent-confirmation run belongs to this stage. Resource totals
and limits are in resource_summary.json. No reset credit or main merge.
