# Relaxation Portfolio Optimization

## Change

The frontier relaxation stack now tries the no-operation-budget vehicle-indexed
inventory/route/Gini relaxation first when a finite incumbent cutoff is
available. If that valid relaxation already cutoff-fathoms the interval, the
harder operation-budget MIP variant is skipped. Otherwise the operation-budget
variant is solved and the solver keeps the stronger valid lower bound.

## Safety

Both variants are relaxations of the original problem. Selecting the maximum of
valid lower bounds cannot overstate the original optimum. Skipping the harder
variant after the weaker no-budget model has already fathomed the interval only
saves time; it does not change the certificate basis.

## Logging

Interval notes record the relaxation source, cutoff-fathoming status, and
selected lower-bound source. Summary evidence is in:

```text
results/relaxation_optimization_round/summary.csv
```

The current V12 short reruns remain bound-time dominated. Pricing time is zero
for the tested rows, confirming that the present regenerated V12 bottleneck is
relaxation/cutoff proof time rather than BPC tree pricing.

## Result

The optimization is certificate-neutral and reduces repeated equivalent MIPs on
intervals that can already be fathomed by the no-budget relaxation. It does not
recover the stronger archive-dependent V12 UB; that is a primal heuristic
quality issue, not a lower-bound certificate issue.
