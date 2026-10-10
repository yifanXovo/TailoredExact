# Limited Round111 public recovery

The carrier reconstructs the current six Seed1 observations and imports the
fixed R110 main36 authority. It does not contain the complete old R110 main
raw archive, production PE, Gurobi DLL, license or credentials. Eight finite
old Seed/H100 fixtures are retained only for audit equivalence. Historical
claims use the explicitly pinned small sources and tables in the manifest.

`compact_evidence/manifest.json` identifies every exact archived byte, the
stdlib reader/restorer, any genuine oversized archive parts, the 205 production
source bindings and the explicit bootstrap dependency. Parts are used only if
the actual compressed stream exceeds the inherited 95 MiB single-blob limit.

Run from a checkout containing the proposed carrier and the new restorer:

```powershell
python -X utf8 scripts/round111_public.py export --root . --out E:/fresh-public-export
```

Run the next command with the **exported public directory as cwd**. Its new
destination must not exist; the restorer creates that fresh empty directory.

```powershell
python -X utf8 scripts/round111_public.py restore --public-root . --out E:/fresh-restored-root
```

Then use the **restored directory as cwd**, with that same directory supplied
as the explicit read root:

```powershell
python -X utf8 scripts/round111_reader.py --root . --out rebuilt --compare results/unified_exact_round111/reports_final
python -X utf8 results/unified_exact_round111/review/round111_independent_review.py --root . --mode public --label public_raw01
```

These are offline engineering reconstructions with zero Optimize. They do not
load a solver or repeat performance measurements. The primary comparison
requires identical CSV field values, row counts, file sets and all JSON fields.
The independent public mode separately recomputes current physical fleets,
model/type/scope/cover/return obligations, exact clocks, Seed pairs and the
layered decision; it imports the signed old main36 without reauditing its full
matrix archive. It checks the actual restore receipt and prevents original-root
or private-binary fallback.

The science carrier freezes the completed research evidence and local final
review. Actual export, restoration, rebuilt comparison, public independent
review and remote PR verification are later observations. Their launch/cwd,
source hashes, exits and fees are retained separately, so the frozen carrier
does not claim to contain receipts that were produced after it.

R110 remains BLOCKED and old arm42 remains over cap and UNEVALUABLE. The new
layer is `R110_MAIN_36_PLUS_R111_SEED_6`; it is not a new-wrapper measurement of
all42 and adds no independent geographic sample.
