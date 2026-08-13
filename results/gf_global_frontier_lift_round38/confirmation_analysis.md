# Round 38 confirmation analysis

All run gates passed: **True**; false certificates: **0**; certificate regressions: **0**.

| Row | V/M | Initial bounds | b+ | t | Completes | Split | C6 gap | G2-A gap | Gap change | AUC change | Outcome |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| r36_08_tight_T_seed5102 | 20/3 | 0.20682410371683468;0.28917631309429254 | 0.208433 | 0.289176 | False | False | 0.201952 | 0.0897011 | 0.112251 | 0.0945276 | g2a_improves |
| r36_10_high_imbalance_seed6202 | 50/3 | 7.4070090034849541;7.5557176110501905 | 7.46156 | 7.55572 | False | False | 0.158065 | 0.158065 | 0 | -0.00078866 | tie |
| r36_11_tight_T_seed6102 | 50/3 | 0.48661597140378293;0.62305459378377903 | 0.540854 | 0.623055 | False | False | 0.0910562 | 0.100064 | -0.00900788 | -0.0108887 | g2a_regresses |

## Frozen-rule interpretation

Diagnostic admissible: **True**. Stable-witness gate: **True**. Confirmation eligible: **True**. Promotion mechanism gate (at least one accepted next-frontier completion): **False**.
