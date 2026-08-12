# Round 37 focused diagnostic predeclaration

The medium-cap diagnostic is frozen after the exploratory smoke audit and
before any medium-cap result. It retains G1 byte-for-byte and selects exactly
three smoke witnesses under the protocol's permitted criteria:

| Ordinal | Panel row | V/M | Scenario | Smoke-defined role |
|---:|---|---:|---|---|
| 8 | r36_08_tight_T_seed5102 | 20/3 | tight_T | exposed material common-UB gap improvement |
| 9 | r36_09_round31_sealed_moderate_V50_seed1112848618 | 50/3 | moderate | cap-censored before the four-cell census completed |
| 10 | r36_10_high_imbalance_seed6202 | 50/3 | high_imbalance | exposed common-UB gap regression |

Each C6/G1 pair receives a 480-second overall process cap. This is a focused
mechanism diagnostic, not validation. It covers the observed positive signal,
the only censored policy exposure, and the only smoke regression, while adding
no instance based on a label-specific favorable outcome outside smoke.

G1, K=4, rho=0.01, HGA-FULL startup, proof normalization, one thread, seed 0,
coverage rules, lifecycle rules, comparison metrics, and certificate gates are
unchanged. No candidate alteration is permitted after this freeze.
