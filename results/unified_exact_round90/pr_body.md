## Change

An interval midpoint can leave a parent LP point feasible in one child's state/product relaxation. This default-off research candidate instead proposes the current optimal parent LP's G value when it is finite and strictly inside the current interval, with the original midpoint as fallback. Both children share the identical stored endpoint, and their complete LPs still determine the original AM decision.

For a fixed feasible parent point in the complete one-hot product blocks, G balances the summed raw violations of the two renewed sets of product bounds and maximizes their smaller sum. This supports a point-selection hypothesis; it does not guarantee an objective-bound gain, exclude alternative optimal LP points, or imply faster convergence. The original depth-8 and minimum-width safeguards, terminal MIP, full coverage, startup, proof targets and whole-run deadline remain.

The candidate requires current parent LP/model identity and matching cached child geometry and epochs before evidence reuse. A dedicated split-choice ledger records the point and child evidence. The feature has its own research identity and rejects combinations with startup reduction or native B1. The ENS-C reference remains unchanged. This follows Round89's documented D3 stop and does not enable its parked cuts.

## Validation status

The implementation compiles in `build/research/round90-lp-g-split`: configuration takes 1.4680975s and the initial build 32.2208135s. Independent review found that a candidate with no eligible split could miss a failed ledger-header write. A narrow repair now fails explicitly on candidate header/row write errors; [final static review passes](results/unified_exact_round90/lp_g_split_independent_static_review.md). The repair build and necessary legacy relinks take 6.5924511s and 0.7807577s, for 41.0621198s total recorded compilation cost. Initial and revised hashes, original logs and the finding remain in the [compile handoff](results/unified_exact_round90/static_review_handoff.md) and [revision](results/unified_exact_round90/static_review_revision_001.md).

The frozen [zero-Optimize qualification](results/unified_exact_round90/lp_g_split_qualification_independent_review.md) passes: geometry/cache 3 groups, global-tree 9 groups, AM 28 checks, and three invalid CLI combinations rejected by their intended guards. All seven source and five binary hashes remain unchanged. The six-command batch takes 1.2274166s outer wall, including 1.1513118s summed command time; the full precheck/postcheck interval is about 130.5s and is not represented by that batch time. A separate cost receipt corrects an original null aggregation field without overwriting it.

No Round90 Optimize or actual-model performance run has been admitted yet. The bounded runner is under source review; actual controller paths and performance require separate observed evidence. No mainline promotion or broad long-time campaign is authorized by this change.

See the [round plan](results/unified_exact_round90/plan.md), [source handoff](results/unified_exact_round90/lp_g_split_implementation_handoff.md) and [reviewed fixed-point mathematics](results/unified_exact_round88/split_critical_band_proposal.md).
