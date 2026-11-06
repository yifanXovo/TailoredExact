# Round155 evidence recovery and reproducibility

Start with `final_report.md`, `review/final_scientific_review.md`,
`candidate_decision.json` and `cost_report.json`. The delivered science
commit and Draft PR are recorded in `publication.json`; `RESUME.md` gives
the latest completed actions. Science is frozen separately from later
publication/recovery metadata to avoid self-referential commit hashes.

## Current-round recovery

`public_manifest.json` lists the exact bytes of thin files and new-only
archive parts. Each archive has its own SHA256/size and a compressed member
index with every member's SHA256/size. Parts are concatenated in listed
order before archive verification. All paths must be relative safe paths;
runtime binaries, licenses, Git internals and traversal paths are excluded.

With the verified existing Python/runtime environment and inherited helper
sources available, the following command performs anonymous byte recovery
into a new empty directory under ExactEBRP-work/restore:

```powershell
& 'E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe' scripts/round155_delivery.py restore <fixed-science-commit>
```

The helper downloads the manifest from raw.githubusercontent.com at the
literal 40-hex commit, checks its local identity, fetches and hashes all
listed thin files, parts and indexes, then verifies every assembled archive
and member before extracting it. It uses four I/O workers inside a single
delivery operation, with the experimental lane idle. No Optimize, Native
model work, compilation or old producer is invoked. The actual result is
`public_restore_receipt.json`; an attempted failure is retained separately.
Do not interpret this recovery as re-executing scientific computations.

The default destination ends in `attempt01` and is create-only. A repeat
must not overwrite or remove a prior recovery. Use a separately reviewed
new destination if another recovery is ever necessary.

## Inherited dependencies and executed sources

Old inputs, original Q, starting pools/supports and old source are references
in `reuse_index.json`, using fixed science commits and member/source hashes.
They are not copied into current-round carriers. Relevant fixed science:

| Source | Fixed commit |
|---|---|
| R154 | a1a3a8d1d88d0af35163e7f134bac09e1ad2077c |
| R153 | 7d64c14faac43c6f410d435dd73b5ba5e49f2f30 |
| Stable R137 | e735c3447eb1443713c700942d873de1783a4a26 |
| Measured production source | d834d62c7a1be599867db04a427f1d43dd3631cb |

`source_manifest.json` and launch-specific `engineering/source_snapshots`
identify current and actually executed R155 sources separately. The static
inherited Python dependency closure is not a dynamic import trace. For
23 inherited files, fixed Git LF/CRLF bytes are related to actual checkout
bytes by an explicit, exactly reconstructible newline conversion. Both
hashes and sizes are recorded. No other byte substitution is accepted.

The unchanged PE hash is
`0d3a94183285cc2794676c717a23dc75a47c872ad48c26d2237dd8634f1a5a01`;
the Gurobi DLL hash is
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
These installed runtime dependencies are retained in place and excluded
from public carriers. There is no R155 production rebuild.

## Scientific evidence and accounting

The new carriers retain raw Native outputs, all failures, source snapshots,
per-phase directions/certificates, actual new columns and coefficient/bound
deltas, sparse saved primals, endpoint models, complete-arm time chains,
launch/receipt pairs and independent reader results. Read the qualified
level-price correction bindings before interpreting historical raw lowers.
Reports are indexes into this evidence, not replacements for raw results.

All saved price/feedback records and support replays were actually checked.
Full-current-column recomputation and full-primal usage checks have the
limited coverage stated in the final report. Re-running a solver is not
necessary to verify public byte recovery and must not be smuggled into the
delivery operation. Any future scientific rerun needs its own paid outer,
fresh output path and unchanged identity/tolerance disclosures.

`cost_report.json` is the final closed scientific ledger. Packaging, Git
publication, anonymous recovery and metadata cleanup are separately timed
public I/O; pure writing is not claimed to be experimentally metered.
`cleanup_record.json` records the bounded current-round retention/deletion
decision and actual volume observations. The initial protected-byte table
was empty; only the actual later 47-path snapshot is used for final byte
checks, as explained in `review/workspace_snapshot_scope.md`.
