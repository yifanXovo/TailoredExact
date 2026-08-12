# Round 36 Stage C broader validation

The separately frozen candidate is `C6-BEST-PROOF-WIDE-ANCHOR-PROOF-NORM` (BW-P): the best verified startup incumbent controls proof, the wider verified value fixes decomposition geometry, and split normalization uses the proof incumbent. K=4 and rho=0.01 remain fixed.

Completed rows: 47/47; strict certificates: 18; valid noncertificates: 29; false certificates: 0.

## Historical-comparator endpoint summary

| Comparator | Candidate wins | Comparator wins | Ties | Certificate regressions | Median candidate-minus-comparator gap |
|---|---:|---:|---:|---:|---:|
| C6-HGA-FULL | 11 | 15 | 21 | 0 | 0 |
| C6-SIMPLE-START | 14 | 14 | 19 | 1 | -2.02503542e-16 |
| P-GRB | 45 | 0 | 2 | 0 | -0.129034326 |

Historical comparisons are used only where the Round 35 compatibility audit marks them compatible. Wall-clock monotonicity is not claimed; the frozen gate prioritizes certificate state and common-UB proof gaps.

## Decision

Keep C6-HGA-FULL unchanged; the geometry mechanism remains scientifically identified, but the candidate does not pass the frozen broad performance gate and should not be promoted.

No automatic promotion, rho tuning, K change, or instance-dependent dispatch was performed.
