# Round 56 frozen research contract

Round 56 is a **paper-candidate screening panel**, not a recovered benchmark and
not the final replicated paper dataset. It is stacked on `06b4c0634cbb85d3440be88511c736dd3282fdc9` /
`412de9e5c5e5e2c90d18634abe83ebf72b0abc1a` and draft PR #113. The sole evaluated algorithm is corrected
K1-AM-SF through `paper-k1-am-sf`: K0=1, midpoint splitting, balanced normalized
closure score, tau=0.08, F0-CLEAN, Gurobi native branching, one thread, seed 0,
Presolve Auto, exact-zero gaps, default PreCrush, and no dynamic user cuts.

The complete 50-row V/M/Q/T matrix, deterministic base seeds, process caps, and
three repeatability rows are frozen before runtime evidence. Every row is kept.
No external incumbent, archive scan, result-derived bound, post-certificate
route solve, objective-equivalent route search, route compaction, or mechanism
other than the stable mainline is permitted.
