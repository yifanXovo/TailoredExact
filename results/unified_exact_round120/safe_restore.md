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

The restored root runs this command with a regular Python installation:

```text
python <restored-root>/scripts/round120_release.py restored-check --root <restored-root>
```

The reader rebuilds each completed current four-arm group and all six pairs
from that root's raw files, then repeats the fixed N40 admission decision. It
imports only the restored scripts and reads only the restored evidence; there
is no original-worktree fallback, reference re-export, solver invocation,
network access or input generation. Comparison normalizes only the measured
and restored absolute root prefixes. It removes no numeric, timing, model,
Start, proof or logical field. It preserves unrun cancellations as unrun.

`round120_release.py restore` performs the actual Git export and hash-checked
safe unpacking when given the committed carrier and a new empty destination.
It deliberately refuses an existing destination. Its `restored-check` also
refuses an already populated `restored_reconstruction` output, so use a fresh
restore for a new independent reconstruction. Pure recovery is engineering
work, not another native performance trial or an independent solver repeat.

Actual staged bytes and every complete decompressed carrier member are checked
by the inherited Round117 publication scanner. This is the bounded publication
gate described in Round117, not a claim that every historical Git object is
secret-free. Old contaminated carriers are not dependencies of this recovery.
