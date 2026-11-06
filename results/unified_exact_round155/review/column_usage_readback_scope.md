# Column-use evidence and the final readback

The implemented loop writes the positive weights of every tracked
Round155-origin column after each qualified RMP solve, including the final
refresh when one is required. The observation threshold is strictly greater
than `1e-10`. The saved marginal contribution is the sum of those recorded
weights for each station/state coordinate. Tracking continues through the
actual source chain, without importing the competing matched-screen branch.

The general price/Q reader verifies prices, feedback, bounds and retained
full-Q primal witnesses. Its output does not independently reconcile every
column-use observation. The separate `scripts/round155_usage_readback.py`
therefore reads the original usage files, rebuilds cumulative usage metadata
from the actual feedback order, recomputes the recorded marginal sums, and
compares the resulting counts and weights with the per-step and final results.
Where a complete sparse primal was saved, it also checks the exact projection
onto every inventory-column variable and compares it with the usage record.
It performs no Optimize or Native model read; it is still a necessary check
and will receive its own outer fee after the experimental lane is idle.

The loop did not save a complete primal at every unchanged intermediate
objective. Consequently, a usage-only observation supports a claim about
the recorded weights, not an independent reconstruction of that complete
unrecorded primal. The reader reports those coverage counts separately.
Qualified saved stage-end and improved-upper witnesses remain subject to the
general full-Q primal readback. No recorded weight above `1e-10` is not a
proof of rationally zero weight or of the uselessness of every new column.

At creation of this note, the reader is prepared but unexecuted. No PASS is
claimed. Its actual result and closed fee must be inspected in the final
scientific review. This addition changes only the final evidence reader and
does not modify the running panel, any frozen research source, or the
post-panel continuation rules.

## Actual final readback: 2026-11-06T10:14:21.986052+00:00

column_usage_readback_v1 actually PASS, with closed fee 15.114310499979183s. It checks 1220 observations across 11 phases: 27 complete saved primal projections and 1193 tracking-only observations. K's main branch has 6689 added columns, with 48 ever recorded above 1e-10 (maximum 6.445603339705698e-10; 20 earlier-phase columns and 28 final-phase columns). NC's main branch has 1163 added columns and none recorded above 1e-10. All recorded marginal sums and cumulative usage reconcile. The scope limits above remain applicable; these are not rational-zero or unsaved-primal claims.
