# Round120 current scientific evidence

`compact_evidence/manifest.json` and its numbered parts contain the finite safe
Round120 scientific payload. They include the current raw runs, all failed
qualification files and charged fees, production source, frozen helpers, input
files and the small named historical authorities required by the current
reader. They contain no native executable, solver DLL, license, credential,
runtime HTML or earlier campaign/carrier.

The delivery receipts describe one actual Git export and one restore into an
initially empty root. Their scope is the published scientific commit, not all
Git history or future commits. Later export/recovery, separate review and
remote publication receipts are outside the payload they examine.

The scientific carrier is fixed at commit
`75c4839f3b85f67f8eeb6c4700e0452d5204dd51`. Its original release runner
completed group01 and then compared an in-memory H operation tuple with its
stored JSON array. This representation mismatch stopped the first comparison;
an independent comparison of the complete stored group01 JSON found zero
field differences after root-prefix normalization. The failure is retained in
`delivery/recovery_attempt01.json`; the original release runner and every
frozen reader/helper remain unchanged.

The later, separately published `scripts/round120_recovery_completion.py` is
a receipt-generation recipe, outside the scientific payload. Copy that one
public source file into the restored root's `scripts` directory. Run it with
a regular Python installation:

```text
python <restored-root>/scripts/round120_recovery_completion.py
```

The recipe invokes the carrier's unchanged reader to rebuild each completed
current four-arm group and all six pairs
from that root's raw files, then repeats the fixed N40 admission decision. It
imports only the restored scripts and reads only the restored evidence; there
is no original-worktree fallback, reference re-export, solver invocation,
network access or input generation. Comparison normalizes only the measured
and restored absolute root prefixes. It removes no numeric, timing, model,
Start, proof or logical field. It compares the reader's stored JSON format,
including arrays serialized from Python tuples. It preserves unrun
cancellations as unrun. The receipt identifies the separately supplied recipe
by SHA and distinguishes it from the unchanged scientific reader dependencies.

`round120_release.py restore` performs the actual Git export and hash-checked
safe unpacking when given the committed carrier and a new empty destination.
It deliberately refuses an existing destination. The one actual export and
empty-root restore are reused for the documented continuation: the recipe's
explicit `--resume-first-attempt` option checks the already completed group01
JSON and rebuilds only groups02/03. No existing output is overwritten, no
second Git export is performed, and the first failed comparison is not erased.
Without that option the recipe requires new reconstruction outputs. Pure
recovery is engineering
work, not another native performance trial or an independent solver repeat.

The no-overwrite statement concerns completed reconstruction group outputs.
The unchanged reader refreshes six derived `round120_event_contract.json`
sidecars inside the expanded raw directories. A different-executor follow-up
checked that their changes are only restored-root paths, while 132 compared
sidecars, including all 12 `call_log_views.json`, remain byte-identical.
Initial unpack hash equality does not claim every expanded member remains
byte-identical after reconstruction. The executed receipt and recipe are
retained unchanged; `delivery/restored_check_scope.json` explicitly qualifies
its broad `frozen_reader_source_helpers_and_evidence_unchanged` field.
`review/extra_review_recovery.json` records the separate typed comparison of
every current-core field and the file-access-check limits. Python open/module
checks use the runtime installation prefix; they are not an OS sandbox.

Actual staged bytes and every complete decompressed carrier member are checked
by the inherited Round117 publication scanner. This is the bounded publication
gate described in Round117, not a claim that every historical Git object is
secret-free. Old contaminated carriers are not dependencies of this recovery.
