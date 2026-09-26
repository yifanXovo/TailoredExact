## Change

An interval midpoint can leave a parent LP point feasible in one child's state/product relaxation. This default-off research candidate instead proposes the current optimal parent LP's G value when it is finite and strictly inside the current interval, with the original midpoint as fallback. Both children share the identical stored endpoint, and their complete LPs still determine the original AM decision.

For a fixed feasible parent point in the complete one-hot product blocks, G balances the summed raw violations of the two renewed sets of product bounds and maximizes their smaller sum. This supports a point-selection hypothesis; it does not guarantee an objective-bound gain, exclude alternative optimal LP points, or imply faster convergence. The original depth-8 and minimum-width safeguards, terminal MIP, full coverage, startup, proof targets and whole-run deadline remain.

The candidate requires current parent LP/model identity and matching cached child geometry and epochs before evidence reuse. A dedicated split-choice ledger records the point and child evidence. The feature has its own research identity and rejects combinations with startup reduction or native B1. The ENS-C reference remains unchanged. This follows Round89's documented D3 stop and does not enable its parked cuts.

## Validation status

The implementation compiles in `build/research/round90-lp-g-split`: configuration takes 1.4680975s and the build takes 32.2208135s. The main executable and focused geometry/cache, global-tree, AM and exchange targets link successfully. Exact source/binary hashes and original compiler logs are preserved in the [compile handoff](results/unified_exact_round90/static_review_handoff.md). These targets have not been executed, and no Round90 Optimize has been admitted. Independent static review is pending before a frozen qualification batch; this draft will be updated with actual validation and all paid positive or negative results. No mainline promotion or broad long-time campaign is authorized by this change.

See the [round plan](results/unified_exact_round90/plan.md), [source handoff](results/unified_exact_round90/lp_g_split_implementation_handoff.md) and [reviewed fixed-point mathematics](results/unified_exact_round88/split_critical_band_proposal.md).
