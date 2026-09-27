
# Mathematical-model construction audit

All K1-AM-SF paths use the single deterministic canonical writer. The objective
is `G + 0.15 sum_i w_i e_i`; `Y_i` remains a bounded general integer; routing,
operation, load, inventory-conservation, ratio, absolute-deviation, Gini,
connectivity, interval, incumbent, penalty-bound, objective-estimator, SP,
pair-duration, and triple-duration rows were traced from construction through
the Gurobi reader. F0 omits only the historical exhaustive subset-duration
block.

The original bit representation enforces `Y_i=sum_b 2^b bit_i_b` and
`zprod_i=sum_b 2^b prod_i_b`, where every product row uses the active interval
endpoints. VD-P replaces only those product bits with exact station selectors
and perspectives; VD-J adds exact ratio and minimal-penalty state equalities.
The original `Y_i`, ratio, absolute-value, routing, and inventory equations are
retained. Selector domains are the propagated contiguous integer interval
`[L_i,U_i]`; values above capacity and below the proved lower bound are absent.

The audit found one material lifecycle defect: canonical artifacts and the
ordinary parent LP used the launch incumbent even after an independently
verified improvement. The row was weaker, so exact certificates were not
false, but runtime trajectories could use stale cutoff state. It is fixed by
an explicit incumbent epoch, current-cutoff construction, retained-model
discard, and LP-evidence invalidation. The corrected stable baseline therefore
requires the full D1-D14 rerun.

## Path audit

| Path | Construction/solve site | Cutoff | Result |
|---|---|---|---|
| initial root interval | `ensureArtifact` | current verified_ub | fresh epoch artifact |
| parent LP | `solveLp` | current verified_ub | epoch-keyed LP |
| midpoint child LP | `solveSpeculativeLp/manual child LP` | current verified_ub | complete before atomic split |
| partial native-target MIP | `runC6NativeTarget` | current verified_ub | same-formulation retained model |
| exact parent MIP | `PaperTerminalMip` | current verified_ub | integer domain restored |
| exact child MIP | `PaperTerminalMip after split` | current verified_ub | integer domain restored |
| cutoff tightening | `incumbent_epoch increment` | new verified_ub | lazy invalidation/rebuild |
| interrupted open leaf | `stopAtDeadline` | last valid bound | coverage retained |
| infeasible child | `complete LP infeasibility` | current epoch | atomic exact handling |
| strict certificate | `GurobiCertificate` | final verified_ub | full coverage and lifecycle gates |
