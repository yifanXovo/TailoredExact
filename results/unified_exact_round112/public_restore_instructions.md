# Public-only recovery contract

The measured production source is d0014a7163e3996fe120471420e56b089c9715ae.
Scientific payload and the later actual verification receipts use separate
commits. The carrier manifest binds every archived file, exact compressed stream
and any necessary contiguous parts. Only an actually oversized archive is split.
No PE, DLL, license, credential or old full evidence carrier is published.

Use the proposed public carrier, the public `scripts/publish_round112.py` and
its explicitly pinned `scripts/round110_public.py` dependency. Export and restore
must use new, nonexistent destination directories. The restore runs from the
exported public script, with no original-worktree fallback:

```powershell
python scripts/publish_round112.py export --root E:/codes/ExactEBRP-round112 --out F:/ExactEBRP-Round112-public01
python F:/ExactEBRP-Round112-public01/scripts/publish_round112.py restore --public-root F:/ExactEBRP-Round112-public01 --out F:/ExactEBRP-Round112-restored01
python F:/ExactEBRP-Round112-restored01/scripts/read_round112.py --root F:/ExactEBRP-Round112-restored01 --out F:/ExactEBRP-Round112-rebuilt01 --compare F:/ExactEBRP-Round112-restored01/results/unified_exact_round112/reports_final
```

The reader is pure Python and loads no solver. It reconstructs twelve qualified
formal endpoints, one interrupted partial record, seven unstarted fixed rows,
all thirty pair positions, complete-H eligibility and separate backend results.
Absolute measured paths are translated strictly to the supplied restored root.
Historical claim authorities are explicitly copied and bound, not replayed as
current performance. Compare every current core CSV/JSON field; missing/null/error
states remain missing/null/error. An independent restored-root review must then
inspect the actual restored bytes. Actual results of this one recovery and remote
PR verification are recorded later; this document makes no future success claim.
