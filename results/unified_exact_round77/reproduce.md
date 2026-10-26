# Reproduce and verify Round77

Owned checkout E:/codes/ExactEBRP-round66; original dirty checkout untouched.
R77 changes no C++. Source 4f6254c2639972ce3ac2b80906ce6d4ebd701f3e and executable
build/round76/v1/ExactEBRP.exe are bound by campaign/identity.json, including
source, binary, input, driver and reader hashes. R76 qualification_v1.json
contains configure/build/test commands. Paired timings require the recorded
Windows machine, compiler, Gurobi 13.0.2 and settings.

The three exact commands/order are in campaign/identity.json. Replay only in
a fresh output namespace; never invoke the completed producer mains here.
Each formal arm derives its own information, without an archived witness.

Original campaign/summary.json and driver_completion.json intentionally retain
the failed post-solve adapter and two records. supervisor_scope_correction.json
preserves the failed audit, reproduces TypeError and validates the normalized
wrapper. continuation_identity/summary/completion record the original third
launch. round77_analyze.py::campaign_summary verifies linkage and constructs
the reviewed view without overwriting originals.

Portable lossless byte verification, no extraction or Gurobi:

```
python scripts/round77_package.py --verify-only
```

This checks all 834 members in four bundles against campaign/bundle_manifest.
For a new offline replay, restore bundles separately using manifest source
paths. round77_analyze.py checks receipts, physical U, bound scopes/coverage
and checkpoint availability. round77_mechanism.py checks closure, actual Start,
models and native logs. Inherited reader/verifier hashes are recorded. Normalize
array-form snapshots before using them as the dict-form CLI endpoint argument
to replay_closure; that is the retained wrapper defect, not a numerical repair.

Some native paths and inherited LP readers retain absolute Windows paths.
Byte verification normalizes repository paths; full cross-OS relocation and
execution are untested. Executables remain local with hashes. Guarded producer
and audit mains refuse to replace completed outputs. A fresh run or longer
panel requires a new plan, and cannot be represented as continuation of these
closed solver states.
