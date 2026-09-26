# Refinement-score ablation

The frozen mechanism-6 panel compares the required causal arms at K0=1. The no-adaptive arm is the selected single-pass affine envelope with exact parent closure; the D-score arm is A(1,2,0.10).

| Arm | Exact | Censored | Work geometric mean | Terminal MIPs | Splits |
|---|---:|---:|---:|---:|---:|
| old-score-no-envelope | 5/6 | 1 | 125.909 | 28 | 24 |
| envelope-no-adaptive | 6/6 | 0 | 67.5474 | 6 | 0 |
| envelope-old-score | 6/6 | 0 | 90.5135 | 12 | 7 |
| envelope-D-score | 6/6 | 0 | 85.6248 | 26 | 41 |
| C6 | 5/6 | 1 | 67.2469 | 20 | 10 |
| K1-single | 5/6 | 1 | 69.799 | 6 | 0 |
| P-GRB | 6/6 | 0 | 327.213 | 0 | 0 |

The comparison is causal only at the frozen arm level. Differences in Work are not inferred from root-bound strength alone, and timing or hardware outcomes are excluded from every refinement decision.
