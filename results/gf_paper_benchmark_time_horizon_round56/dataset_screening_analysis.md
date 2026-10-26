# Round 56 paper-candidate dataset screening analysis

Round 56 is a matched **paper-candidate screening panel**, not a recovered historical benchmark and not a final replicated paper dataset. It uses one independently generated base landscape per V, so the observations below are structural screening evidence rather than population-level statistical generalizations.

All 50 mandatory scenarios are retained without filtering: 40 primary Q=30 factorial rows and 10 Q=20 capacity-transfer sentinels. Final strict certificates: 40; verified incumbents: 50; capped noncertified rows: 10.

## Exact-solution screening by V

| V | Rows | Certified by 3600 s | Certified final | Noncertified | Median wall s |
|---|---|---|---|---|---|
| 8 | 10 | 10 | 10 | 0 | 4.65192935 |
| 12 | 10 | 10 | 10 | 0 | 11.4683313 |
| 20 | 10 | 9 | 9 | 1 | 121.050723 |
| 30 | 10 | 6 | 6 | 4 | 365.186734 |
| 50 | 10 | 5 | 5 | 5 | 2082.09004 |

## Exact-solution screening by operational T

| T (s) | Rows | Certified by 3600 s | Certified final | Noncertified | Median wall s |
|---|---|---|---|---|---|
| 1800 | 10 | 7 | 7 | 3 | 332.626401 |
| 3600 | 15 | 8 | 8 | 7 | 1595.64221 |
| 10800 | 10 | 10 | 10 | 0 | 72.1312549 |
| 18000 | 15 | 15 | 15 | 0 | 90.2137009 |

All cross-V, cross-M, cross-Q, and cross-T proof-difficulty comparisons use the common 3600-second checkpoint. The nine predeclared 7200-second rows are used only to inventory additional exact solutions; they do not replace the common horizon.

## Native-witness utilization by T

| T (s) | Witnesses | Mean max utilization | Largest utilization | Mean used-vehicle utilization | Largest route duration s |
|---|---|---|---|---|---|
| 1800 | 10 | 0.990722918 | 0.999915668 | 0.975909004 | 1799.8482 |
| 3600 | 15 | 0.995467527 | 0.999222235 | 0.973553397 | 3597.20005 |
| 10800 | 10 | 0.78506814 | 0.981607352 | 0.674253832 | 10601.3594 |
| 18000 | 15 | 0.667994798 | 0.983051987 | 0.494152165 | 17694.9358 |

Every route statistic describes the single final native witness returned by the official run. No route was compacted, shortened, relabeled, repaired, or post-optimized. Route duration is therefore not the minimum duration compatible with its objective, and vehicle usage is not a minimum-vehicle claim.

## Structural interpretation

The direct 50-row instance, result, and route tables provide the auditable evidence for V, M, Q, and T effects. Exact monotonicity claims are restricted to pairs in which both endpoints strictly certified; capped witnesses remain descriptive and are never promoted to exact solutions. V30/V50 constitute the large-scale screening regime and are compared at the common 3600-second horizon, including honest capped outcomes.

The time-horizon screening classification is `mixed_t_sensitivity`. The panel remains unsuitable for final paper generalization because each structural cell ultimately inherits only one frozen base landscape for its V.
