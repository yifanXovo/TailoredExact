# Mechanism atlas

The structural atlas was frozen before exact candidate outcomes. It used only
interval endpoints, verified U, complete LP bounds/statuses, model geometry,
and the global K0/d/rho parameters.

## Depth screen

| d | Rows | D min | D median | D max | tau median |
|---|---|---|---|---|---|
| 1 | 6 | 0.1121 | 0.1359 | 0.2203 | 0.5190 |
| 2 | 6 | 0.0822 | 0.1041 | 0.2098 | 0.7473 |

Depth 1 has a nonzero but weaker deficit signal. Depth 2 has the stronger
median envelope-capture fraction and retains meaningful D variation, so d=2
was frozen. C_d was exactly 0.5 for d=1 and 0.75 for d=2 on every row; this is
a construction constant, not an admissible adaptive signal.

## Exact mechanism screen

| K0 | rho | Exact | Censored | Major Work | Control Work | Work gmean |
|---|---|---|---|---|---|---|
| 1 | 0.05 | 6 | 0 | 10493.025 | 402.251 | 285.978 |
| 1 | 0.1 | 6 | 0 | 1545.849 | 230.938 | 85.625 |
| 4 | 0.05 | 6 | 0 | 10778.649 | 394.569 | 284.976 |
| 4 | 0.1 | 6 | 0 | 1346.050 | 203.525 | 75.695 |

The symmetric 7,200-second extensions are used wherever present. Both K0
values select rho=0.10 under the frozen tail-first order.
