# BPC Pricing Optimization Round Final Report

Branch: `codex/longrun-round17-local-results`  
Final commit: recorded in final response after push. The commit SHA is self-referential and changes when this report is amended.

## Summary

This round realigned the implementation toward the unified `paper-gf-bpc-core` algorithm and focused on exact BPC pricing. The core certificate rules remain intact: no archive scanning, no known UB injection, no external incumbent, no V/M special-casing, no route-mask enumeration certificate, no interval-oracle certificate, and no CPLEX benchmark contamination.

No nontrivial BPC leaf closed in the tested budgets. The useful stage improvement is diagnostic and implementation-oriented: exact-safe pricing dominance is now active and visible, pricing-state counters are exported, BPC leaf validation produces state/depth/operation profiles, and paper-core scheduling now enters BPC instead of indefinitely deferring behind split-first logic.

## What Changed

- Added pricing controls and JSON fields for `pricing_dominance_mode`, completion-bound mode, load-DP cache flags, route-skeleton mode, operation-DP dominance, label counters, duplicate-state counters, and profile arrays.
- Added round-level BPC validation outputs:
  - `pricing_state_audit.csv`
  - `pricing_depth_profile.csv`
  - `operation_dp_profile.csv`
  - `bpc_leaf_validation_after_all.csv`
- Updated `paper-gf-bpc-core` scheduling:
  - disables split-before-tree for this core preset;
  - uses a smaller BPC reserve minimum for diagnostic runs;
  - still accepts only exact pricing closure as BPC evidence.
- Preserved separation between paper-core, diagnostics, exact portfolio, and CPLEX benchmark rows.

## Pricing Questions

1. Did pricing dominance begin pruning labels?

Yes. V12 M2 leaf 7 pruned about 193M labels with safe dominance in the 30s diagnostic. V12 M1 leaf 12 pruned about 222M labels. V20 leaves still show weak or zero route-label dominance, which points to a state representation/decomposition problem.

2. Did route skeleton + loading DP reduce states?

No full route-skeleton/loading-DP rewrite was completed. The controls and logging hooks exist, and operation-DP dominance is active, but this round did not deliver a separate skeleton/DP decomposition that closes leaves.

3. Did completion bounds prune pricing?

Completion-bound pruning is logged and active where the existing exact-safe bound applies, but it did not close any tested BPC leaf.

4. Did leaf-domain transfer improve pricing/RMP?

No decisive improvement was observed. The diagnostics indicate that the BPC leaf still solves a large exact pricing space.

5. Did RMP seeding improve convergence?

Not enough to close a leaf. Seeding remains UB/RMP-start support only and is not lower-bound evidence.

6. Did BPC cuts improve RMP bounds?

No. Cut counts stayed effectively inactive in the tested leaves, so cut separation remains a next implementation target.

7. Did any BPC leaf close with exact pricing?

No. This is the main negative result of the round.

8. Did paper-gf-bpc-core certify V12 M1 or V12 M2?

No. V12 M1 remained noncertified in the short paper-core row. The V12 M2 BPC-focused full-row attempt entered the expensive BPC path and was stopped by the wrapper; it is recorded as `interrupted_noncertified`, with no certificate claim.

9. How does large-V diagnostic behave?

V50/V100 diagnostics remain noncertified and wrapper-finalized under short budgets. They are audit-safe, but they do not yet produce useful valid LB progress in paper-core mode.

10. Should BPC remain in the main paper algorithm?

BPC should remain in the theorem as a valid exact fallback, but it should not be claimed as empirically effective yet. Current experiments rely on relaxation/portfolio certificates outside BPC-core for many successes. The next targeted round should implement a deeper exact route-skeleton/loading-DP decomposition and stronger exact completion bounds.

## Key Tables

- `bpc_leaf_validation_after_all.csv`: focused leaf outcomes.
- `bpc_pricing_profile.csv`: aggregate label and pruning counters.
- `dominance_ablation.csv`: V12 M2 safe vs dominance-off diagnostic.
- `unified_core_after_bpc_summary.csv`: paper-core full rows.
- `large_v_summary.csv`: V50/V100 diagnostics.
- `certificate_audit.csv`: all final raw JSONs audited, zero failures.

## Audit

Audit results:

- `audit_bpc_certificate.py --self-test`: passed.
- `audit_bpc_certificate.py results\bpc_pricing_optimization_round\raw --fail-on-error`: 7 rows, 0 failures.
- `certificate-basis-test`: passed.
- `option-consistency-test`: passed.
- `audit_no_instance_special_cases.py`: passed.
- `audit_no_v_threshold_paper_core.py`: passed.
- `audit_proof_coverage.py`: completed.

## Recommendation

Do not promote BPC empirical claims yet. Keep `paper-gf-bpc-core` as the unified exact framework, but state that the current BPC implementation is bottlenecked by exact pricing state explosion. The next round should target the exact pricing decomposition itself rather than frontier scheduling or interval-oracle certificates.
