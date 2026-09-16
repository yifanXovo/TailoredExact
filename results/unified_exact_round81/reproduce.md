# Reproduce and verify Round81

Read `status.md` first: while the original campaign is active, do not run the
offline producers or packaging commands. This document describes the closed
stage entrypoints; audit/delivery receipts establish whether they have passed.

The production source is R78 commit
`4a0561e0f8193e3e874c1bd0bfa8bc381fb66f5e`; executable
`build/round78/v1/ExactEBRP.exe` has SHA256
`3fae847a75c3c9d07d8f5f0444daeafb73559865e6bffb816746802b9e2f43ab`.
R78 `qualification_v1.json` records its configure/build/test commands and its
bundles retain the qualification, structural and startup evidence. R81 adds no
production change, build, test or qualification solve. See `unified_method.md`
for the consolidated method, source map, parameters and correctness scope.

`plan.md` and `campaign/identity.json` freeze five roles, fourteen serial arms,
input/source/binary/driver hashes, commands and caps. S12/C2/D4 each have fresh
P-GRB/BDS-C/K1-R controls, D6 has only fresh P/BDS, and D7 has a fresh full trio.
No R80 K1 endpoint belongs in the fresh D6 matched table. Every arm acquires
its own information; five original compact exports bind P without adding any
Start, cut or imported bound. Matched timing requires the recorded Windows
machine, Gurobi13.0.2 and logical2/mask4 affinity. All raw launch arguments,
whole-deadline precedence and restoration records remain part of the evidence.

Never invoke completed producer mains merely to inspect evidence. Their
namespaces are immutable. A repeated or longer solve is a fresh experiment,
not continuation of an existing search. After the original driver closes, the
single intended offline sequence is analyze, mechanism, replication, package.
Each producer refuses to overwrite its completed output. Inspect the stored
audit rather than rerun it in place. Offline costs are separate from paid
complete-run wall times; none of these steps optimizes another model.

After delivery, verify every retained byte without extraction or Gurobi:

```
python scripts/round81_package.py --verify-only
```

`bundle_manifest.json` is the compact index. Its hash-bound
`bundle_members.json.gz` contains every original member path, length and
SHA256 as ordinary gzip JSON. The verifier checks agreement between index and
member manifest and reads every archived byte. Fourteen complete raw trees and
five original compact reference trees produce fifteen bundles. Restore to a
separate namespace before a new offline replay; preserve the recorded originals.

`round81_analyze.py` rechecks durable receipts, original physical endpoints,
bound scope/coverage, observed availability and the frozen comparison rules.
`round81_mechanism.py` checks actual Start vectors, model rows, readback/native
logs, all25 startup paths, every balanced/strict transition and outer handoff.
It reuses the unchanged R78 physical replay. `round81_replication.py` binds prior
stage bytes and retains all eleven same-cap original/repeated endpoints and
their own within-stage matched comparisons. Its separate D7 table compares
300/600/1200 checkpoints from the earlier1200 and new3600 caps; native defaults
can respond to that changed deadline, so these are consistency observations,
not same-cap repetitions or independent checkpoint samples.

Some model/native-log paths and inherited readers use absolute Windows paths.
Byte verification normalizes repository bundle paths; full cross-OS execution
and relocated raw replay are untested. Executables stay local with hashes.
Normal numerical certificates are not strict rational proofs. All five roles
are exposed development data. This stage cannot replace diverse unadapted
confirmation, regardless of its observed performance.
