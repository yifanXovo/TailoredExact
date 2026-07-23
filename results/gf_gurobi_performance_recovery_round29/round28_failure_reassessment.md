# Round 28 C3 failure reassessment

This reassessment is computed from the immutable Round 28 result JSON files,
tree ledgers, optimize ledgers, and global-bound traces. It does not modify or
reinterpret the Round 28 package.

## What the retained evidence proves

- 30 completed official C3 rows were reconstructed.
- They launched 5764 complete native optimizations: 4107 LP events
  and 1657 terminal MIPs.
- Every optimization created/read a fresh model (5764 reads) and
  the native logs observed 5764 presolve executions. Thus the
  measured build/read share (median 7.0%) is only file and
  parse overhead; it excludes repeated presolve, repeated root work, lost LP
  bases, lost cuts, and terminal-MIP startup.
- Terminal MIPs consumed 80.4% of recorded Gurobi Work.
- C3 made 2366 unconditional structural splits and achieved
  0 LP-bound prunes.
- Of 2027 splits whose two immediate child LPs were both observed,
  723 (35.7%) did not strictly
  improve the one-level controlling lower bound.

## Moderate6301 boundary

All three retained Moderate6301 C3 attempts contain a complete HGA generation
trajectory (3,326 recorded generations in each retained attempt), but no result
JSON and no external-tree directory. In the Round 28 implementation the
trajectory is written after `ga.run()` and before best-solution extraction,
the full compact route decoder, and independent verification. Therefore the
old evidence rules out an external C3 tree failure and bounds the loss to the
post-generation/pre-exact transition. It cannot distinguish extraction from
route decoding or verification; Round 29 flushed phase instrumentation is
required for that distinction.

## Mechanism classification before C4

The dominant observed mechanisms are excessive structural refinement and
terminal-MIP creation, followed by repeated cold optimization startup.
File/model construction is measurable but is not the complete repeated cost.
Weak LP pruning is direct evidence: the retained completed aggregate has zero
LP-bound-pruned leaves. Incumbent weakness is not the principal explanation on
the reconstructed rows because the HGA incumbent is independently verified
before the tree. Exact presolve/root seconds are unavailable from the Gurobi C
API and are not fabricated; execution counts and per-event native logs are
reported instead.
