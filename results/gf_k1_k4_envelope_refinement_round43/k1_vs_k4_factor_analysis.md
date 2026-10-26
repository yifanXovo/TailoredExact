# K1 versus K4 factor analysis

| Initial K0 | Old mechanism | New mechanism |
|---|---|---|
| 1 | K1-old (1.357 gmean Work) | A(1,2,0.1) (1.557 gmean Work) |
| 4 | C6 (1.329 gmean Work) | A(4,2,0.1) (1.681 gmean Work) |

The complete 2x2 comparison separates initial granularity from the shared new
operator. K4-new is better than K1-new on the major witness
(1346.050 versus 1545.849
Work) and on the strongest K4 control (203.525
versus 230.938 Work), confirming retained local
K4 strength. Neither new arm preserves the control against C6: their Work
ratios are 1.727 and
1.522, both above 1.20.

## Mandatory mechanism ablations

| Arm | Exact | Censored | Work gmean | Terminal MIPs | Splits |
|---|---|---|---|---|---|
| old-score-no-envelope | 5/6 | 1 | 125.909 | 28 | 24 |
| envelope-no-adaptive | 6/6 | 0 | 67.547 | 6 | 0 |
| envelope-old-score | 6/6 | 0 | 90.514 | 12 | 7 |
| envelope-D-score | 6/6 | 0 | 85.625 | 26 | 41 |
| C6 | 5/6 | 1 | 67.247 | 20 | 10 |
| K1-single | 5/6 | 1 | 69.799 | 6 | 0 |
| P-GRB | 6/6 | 0 | 327.213 | 0 | 0 |

The envelope, score, and recursion effects are reported as complete arm-level
outcomes. They are not attributed to changed Gurobi search merely because a
root LP is stronger. The strongest-control K1 and K4 complete-global-root LP
bounds are equal, so the zero chi numerator/denominator case is vacuous rather
than evidence of missing transferable root strength.
