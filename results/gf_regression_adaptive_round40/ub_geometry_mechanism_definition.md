# Part 2 nested-dyadic UB geometry

Let the stable root be the mathematical Gini maximum `(V-1)/V`, independent of the incumbent. For dyadic level `d`, the hierarchy has `2^d` equal anchor cells on that root. Select the finest level whose proof-relevant prefix intersects at most the frozen target `K=4` cells. Intersect those cells with `[0, U_proof]`; only the last active cell may be truncated.

A stronger verified UB either keeps the same level or selects a finer dyadic level. Every coarser boundary is also a boundary in the finer hierarchy, so every old internal boundary still below the stronger cutoff is preserved. Suffix cells deactivate and the last endpoint may contract. The proof cutoff, LP/MIP semantics, C6 scheduler, `rho` split rule, atomic coverage, lower-bound ledger, and exact closures remain unchanged.

The policy is explicit (`--round40-c6-ub-geometry nested-dyadic-k4`), default-off, HGA-FULL-only, mutually exclusive with Round 36/37 geometry and K1 arms, and requires the frozen Auto-presolve contract.

The Round 36 projection uses 14 preexisting verified HGA/simple UB pairs. Ten pairs have different cutoffs: legacy UB-rescaled quartiles redraw relevant boundaries in all ten; nested dyadic preserves them in all ten. This is a geometry theorem/audit, not a monotonic-runtime claim.
