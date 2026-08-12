# Round 36 representative trajectory report

This report selects one HH-versus-BW-P row per populated frozen Round-35
pattern by the largest absolute common-window proof-AUC difference.  It is a
derived view; the full event table and deterministic hashes are retained in
the companion CSV files.

| round35_pattern | instance_id | V | M | left_actual_splits | right_actual_splits | pre_first_split_sequence_changed | causal_outcome | right_minus_left_proof_auc |
|---|---|---|---|---|---|---|---|---|
| 1_simple_ub_not_weaker_simple_faster | round32_multi_m_high_imbalance_V20_M2_seed1052706459 | 20 | 2 | 3 | 3 | False | right_win | 0.04627 |
| 2_simple_ub_weaker_exact_phase_similar | moderate_seed4302 | 20 | 3 | 0 | 0 | True | left_win | -0.01279 |
| 3_simple_ub_weaker_exact_phase_faster | moderate_seed5301 | 20 | 3 | 0 | 0 | True | right_win | 0.1758 |
| 4_simple_ub_weaker_exact_phase_slower | round32_multi_m_tight_T_V20_M2_seed89001413 | 20 | 2 | 1 | 0 | True | left_win | -0.1269 |
| 5_simple_certification_or_final_gap_regression | round31_sealed_moderate_V50_seed1112848618 | 50 | 3 | 0 | 1 | True | left_win | -0.06117 |

There are 3
geometry comparisons whose downstream trajectory differs while both arms make
zero actual splits, and 11
whose first structural difference is already present before a split.  Such
rows cannot be attributed to rho.

All AUC values use the common observed window, left-continuous bound values,
no interpolation, and no post-last-event extension.
