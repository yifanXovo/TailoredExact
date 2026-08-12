# Round 37 focused diagnostic analysis

All run gates passed: **True**; false certificates: **0**; certificate regressions: **0**.

| Row | V/M | Exposure | Pilot LP gain | C6 common-UB gap | G1 common-UB gap | AUC improvement | Outcome |
|---|---:|---:|---:|---:|---:|---:|---|
| r36_08_tight_T_seed5102 | 20/3 | True | 0.00160882 | 0.201952 | 0.0927645 | 0.083344 | g1_improves |
| r36_09_round31_sealed_moderate_V50_seed1112848618 | 50/3 | True | 0.000476256 | 0.188285 | 0.183171 | 0.00148304 | g1_improves |
| r36_10_high_imbalance_seed6202 | 50/3 | True | 0.0545466 | 0.158054 | 0.187018 | -0.0249312 | g1_regresses |

## Decision

Advance only the stable positive and stable regression witnesses to a selected
900-second confirmation, without changing G1. The V20 tight-T row improved both
the final common-UB gap and common-window AUC at 180 and 480 seconds. The V50
high-imbalance row regressed on both measures at both caps despite having the
largest immediate selected-cell LP gain. The formerly censored V50 moderate
row is excluded: its 480-second improvement is small and has no replicated
exposed smoke result. This is a mechanism-boundary confirmation, not validation
or a promotion gate.
