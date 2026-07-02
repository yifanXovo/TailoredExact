# Full Cut-Family Ablation Report

This round fixed the ablation flag semantics: compact cut flags are preserved after preset normalization, so `no_new_cuts` rows now actually disable the new compact-BC families. The CSV `results/gf_compact_bc_strengthening_round/full_cut_family_ablation.csv` records the executed smoke ablations.

Executed variants include `no_new_cuts` for V12 M2, high_imbalance_seed3202, tight_T_seed3101, and moderate_seed3301; all-safe static paper rows; one root-round diagnostic row; and a singleton receiver-cover diagnostic row. The full one-family-at-a-time and leave-one-family-out matrix is scaffolded by truthful CLI flags but was not exhaustively run in this round.
