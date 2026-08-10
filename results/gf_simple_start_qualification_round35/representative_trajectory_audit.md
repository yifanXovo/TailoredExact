# Representative trajectory audit

One observed row per populated diagnostic pattern is shown below. Selection is
deterministic: the largest absolute SIMPLE-versus-HGA final-gap difference in
that pattern. Full event sequences and hashes remain in
`incumbent_decomposition_interaction.csv`.

| pattern | stage | instance_id | V | M | full_startup_verified_ub | simple_startup_verified_ub | full_initial_global_lb | simple_initial_global_lb | full_actual_splits | simple_actual_splits | full_terminal_mip_calls | simple_terminal_mip_calls | full_final_gap | simple_final_gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1_simple_ub_not_weaker_simple_faster | matrix1800 | round32_multi_m_high_imbalance_V20_M2_seed1052706459 | 20 | 2 | 4.3569 | 4.3569 | 0.0000 | 0.0000 | 3 | 3 | 1 | 1 | 0.0000 | 0.0000 |
| 2_simple_ub_weaker_exact_phase_similar | matrix1800 | moderate_seed4302 | 20 | 3 | 0.0485 | 0.0661 | 0.0000 | 0.0000 | 0 | 0 | 3 | 2 | 0.0000 | 0.0000 |
| 3_simple_ub_weaker_exact_phase_faster | matrix1800 | moderate_seed5301 | 20 | 3 | 0.1689 | 0.2433 | 0.0000 | 0.0000 | 0 | 0 | 1 | 2 | 0.4906 | 0.1940 |
| 4_simple_ub_weaker_exact_phase_slower | matrix1800 | round32_multi_m_tight_T_V20_M2_seed89001413 | 20 | 2 | 0.3536 | 0.4219 | 0.0000 | 0.0000 | 1 | 0 | 3 | 2 | 0.0000 | 0.0000 |
| 5_simple_certification_or_final_gap_regression | matrix1800 | round32_multi_m_moderate_V50_M4_seed721910669 | 50 | 4 | 0.4067 | 0.6328 | 0.0000 | 0.0000 | 0 | 1 | 1 | 1 | 0.1946 | 0.4991 |
| 6_other | matrix1800 | round32_multi_m_high_imbalance_V50_M2_seed910922492 | 50 | 2 | 5.0520 | 4.8976 | 0.0000 | 0.0000 | 0 | 0 | 2 | 2 | 0.0000 | 0.0000 |

No timing interpolation, post-final trace extension, solver rerun, or causal
counterfactual is used in this audit.
