# Round 35 incumbent-decomposition interaction audit

This audit compares the frozen C6-SIMPLE-START rows with compatible, read-only
Round 32 C6-HGA-FULL evidence. It identifies associations, not causality, and
does not introduce a mechanism or an instance-dependent startup policy.

## Coverage

- Compatible paired rows: 47 (35 at 1,800 seconds and 12
  independent V50 rows at 3,600 seconds).
- Rows whose target, split, or closure sequence hash changed:
  39.
- Rows where exact search recorded a native incumbent after startup:
  43
  for SIMPLE and
  27
  for HGA-FULL.

## Diagnostic pattern counts

| pattern | rows |
|---|---|
| 1_simple_ub_not_weaker_simple_faster | 3 |
| 2_simple_ub_weaker_exact_phase_similar | 1 |
| 3_simple_ub_weaker_exact_phase_faster | 16 |
| 4_simple_ub_weaker_exact_phase_slower | 3 |
| 5_simple_certification_or_final_gap_regression | 20 |
| 6_other | 4 |

## Interpretation boundary

The companion CSV records verified startup UBs, improving-range endpoints,
the four initial intervals, parent LP bounds, controlling leaves, targets,
requeues, lookahead gains, splits, depths, terminal work, closure ordering,
native-incumbent timing, bound AUC, and final certificate/gap. Sequence hashes
make structural differences auditable. Differences may be caused by cutoff
geometry and solver state, but this round does not claim a counterfactual or
causal mechanism.
