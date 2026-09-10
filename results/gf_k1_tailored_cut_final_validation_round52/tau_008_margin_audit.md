# Tau 0.08 complete replay and margin audit

The replay evaluated 334 available K1-AM decision records from
147 non-duplicated native ledgers plus the authoritative Round 47
offline replay. Exact-parent closure is reconstructed first from child/parent
bounds at certificate tolerance 1e-7; otherwise the frozen rule compares
`S_AM + score_tolerance` with tau. External mirror ledgers are excluded to avoid
byte-for-byte duplicate records; every retained row includes its source hash and
row number.

Records by evidence root: {"gf_c6_adaptive_mass_contraction_round47": 244, "gf_k1_amf_formulation_rescue_round48": 22, "gf_k1_interval_mip_vnext_round50": 33, "gf_k1_lp_primal_dual_rescue_round49": 35}.
Changed actions between 0.07915 and 0.08: 0.

## Anchor audit

- major_root: RETAIN (pass)
- strong_control_root: RETAIN (pass)
- tight3102_L0.0: RETAIN (pass)
- high_imbalance_root: MIDPOINT (pass)

## Twenty closest non-closure margins to 0.08

- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate_seed3301` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `external` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate3301_root` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `moderate3301_root` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `external` `L0`: S_AM=0.086467735592102801, adjusted margin to 0.08=0.0064728393396801948
- `tight_T_seed3102` `L0.0`: S_AM=0.051820587972674186, adjusted margin to 0.08=-0.028178894898541945
- `tight_T_seed3102` `L0.0`: S_AM=0.051820587972674186, adjusted margin to 0.08=-0.028178894898541945

The complete row-level evidence, including both raw and tolerance-adjusted
margins, is in `tau_008_complete_replay.csv`.
