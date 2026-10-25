# Finite Round133 reproduction

The fixed science commit is recorded by the later `delivery_receipt.json`.
Pass that full 40-character commit to the recovery entry. It is separate from
the later metadata head, which records the actual recovery, cleanup and remote
readback. The science payload does not claim those future actions have passed.

The entry is `scripts/round133_public_restore.py`. Obtain that script from the
same public fixed science commit and check its published SHA. Run it with an
existing Python 3.12+ standard-library runtime and curl:

```text
python -I -B round133_public_restore.py --commit SCIENCE_COMMIT --destination E:/codes/ExactEBRP-work/restore/round133-public --receipt E:/codes/ExactEBRP-work/worktrees/round133/results/unified_exact_round133/public_restore_receipt.json
```

The destination must be one owned, initially empty directory under the declared
restore parent. A completed root cannot be rerun. A real failed attempt preserves
its cause and can resume in that same root with `--resume`; do not start another
empty root to discard a failure. Transport uses anonymous fixed-commit HTTPS,
with no HEAD/branch resolution, Git checkout, local historical raw fallback,
native assets, solver invocation or compilation.

`export_manifest.json` names each exact loose file and the one small inherited
tiny carrier. `raw_archive_manifest.json` and its compressed member indices bind
the new carriers to all current raw, failures and closed process receipts. The
old 34 carriers are unchanged. Only the explicitly indexed historical snippets
in `dependencies/historical_snippets.json` are reused. Execution source bytes,
the two reused main-source/binding pairs and the old bridge source dependencies
are separately published through `source_publication.json`. PE/DLL/object/library
identities remain historical execution attestations; recovery does not remeasure
assets that are deliberately absent.

After SHA/CRC/member verification and exact source materialization, recovery
must pass all three independent pure-Python checks:

1. `round133_portable_check.py`: all 22 fixed formal positions and the separate
   nonperformance correctness unit; actual frozen reader plus explicit effective
   post-seal H adapter, complete physical/model/H/Start/source/return/cover audits,
   original producer and verification clocks, and derived endpoint consistency.
2. `round133_joint_check.py`: exact J2/J3 full-universe service and objective
   arguments from the one declared inherited tiny carrier, without a new study.
3. `round133_d24_point_check.py`: all 22,996 serialized rows and 9,391 variables
   for the D24 own-zero extension, physical fleet, three refuted observations and
   saved loaded-coefficient comparison. This does not qualify the rejected source
   or validate the hidden native tree.

Derived replay writes remain in memory or external attempt receipts. The restored
scientific bytes and original measured clocks are not overwritten. Recovery
reports its own actual cost separately, with zero Optimize and zero compilation.
The finite delivery plan and space check record the bounded scope. Later delivery
receipts are appended without recursively repacking or recovering the science.
