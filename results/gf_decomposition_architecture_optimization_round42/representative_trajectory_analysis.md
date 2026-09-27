# Representative trajectory analysis

The two prespecified architecture witnesses and the fail-closed numerical
endpoint are recorded in `representative_trajectory_analysis.csv`. Ratios use
the frozen contemporary C6-HGA-FULL-K4 development row.

## Major fragmentation witness

| Arm | Work ratio | Shifted-time ratio | Exact s | Work | Nodes | Proof jobs | Strict |
|---|---:|---:|---:|---:|---:|---:|---|
| C6-HGA-FULL-K4 | 1.000 | 1.000 | 1777.84 | 3898.99 | 31176 | 8 | True |
| C6-K1-SINGLE | 0.783 | 0.758 | 1348.00 | 3052.42 | 37107 | 1 | True |
| EXTERNAL-K2-FIXED | 0.985 | 0.950 | 1689.48 | 3842.40 | 44067 | 2 | True |
| ST-K2-P-CORE | 0.446 | 0.429 | 761.64 | 1738.41 | 17047 | 1 | True |
| ST-K4-P-CORE | 0.781 | 0.750 | 1333.24 | 3044.52 | 31581 | 1 | True |
| ST-K4-P-CORE-HIERARCHICAL | 0.426 | 0.410 | 728.04 | 1661.91 | 17906 | 1 | True |
| PAIRED-K4 | 1.060 | 1.051 | 1868.01 | 4132.98 | 38523 | 2 | True |
| PAIRED-K4-FACTORED | 1.134 | 1.115 | 1982.38 | 4421.22 | 41418 | 2 | True |
| C6-SIBLING-CORE | 1.032 | 1.000 | 1777.86 | 4023.49 | 35070 | 4 | False |
| C6-SIBLING-CORE-FACTORED | 0.963 | 1.000 | 1777.89 | 3754.73 | 33743 | 4 | False |

The root-LP audit gives the same `0.028210692227...` lower bound for C6 and all
K4 static/paired formulations. Hierarchical ST-K4 reduces the independent
integer jobs from 8 to 1 and cuts Work to 0.426x C6, but the gain is not stable
on the positive control. Terminal sibling coalescing accepts two exact sibling
pairs and replaces four leaves, reducing the counted integer proof jobs from 8
to 4. Its union remains unresolved at the shared process cap, so coverage is
retained and strict certification is correctly refused.

## Strongest K4 positive control

| Arm | Work ratio | Shifted-time ratio | Exact s | Work | Nodes | Proof jobs | Strict |
|---|---:|---:|---:|---:|---:|---:|---|
| C6-HGA-FULL-K4 | 1.000 | 1.000 | 74.90 | 133.73 | 7878 | 7 | True |
| C6-K1-SINGLE | 5.532 | 5.361 | 405.93 | 739.78 | 24652 | 1 | True |
| EXTERNAL-K2-FIXED | 1.029 | 1.014 | 75.96 | 137.63 | 12265 | 2 | True |
| ST-K2-P-CORE | 1.371 | 1.315 | 98.82 | 183.30 | 11378 | 1 | True |
| ST-K4-P-CORE | 1.330 | 1.299 | 97.60 | 177.85 | 7628 | 1 | True |
| ST-K4-P-CORE-HIERARCHICAL | 1.570 | 1.570 | 118.19 | 209.98 | 8209 | 1 | True |
| PAIRED-K4 | 1.411 | 1.459 | 109.78 | 188.73 | 9030 | 2 | True |
| PAIRED-K4-FACTORED | 1.342 | 1.332 | 100.07 | 179.50 | 10450 | 2 | True |
| C6-SIBLING-CORE | 1.489 | 1.468 | 110.46 | 199.17 | 9144 | 5 | True |
| C6-SIBLING-CORE-FACTORED | 1.422 | 1.508 | 113.48 | 190.15 | 10570 | 5 | True |

Every candidate is slower than C6 here. K1 demonstrates the interval-strength
loss most sharply at 5.532x Work. The best Round 42 family ratio on this control
is 1.330x for flat ST-K4, still above the frozen 1.10 limit. Factored sibling
coalescing removes two counted proof jobs but uses 1.422x Work and 1.508x shifted
time.

## Numerical fail-closed endpoint

The CSV retains all ten arms. Baseline C6 and contemporary K1 remain honest
noncertificates. Several static covers certify because their native complete
cover and original-space verifier close the endpoint; none is treated as a
false certificate. The endpoint contributes catastrophic regressions exactly
where both frozen Work and shifted-time ratios exceed 1.25.
