# Inventory-route iteration history

## Iteration 1 — frozen before the offline census

The two predeclared variants are IR1 (full mixed closure) and IR2 (full mixed plus nondominated projected closure). Both use the same exact deterministic separator, tolerance, base model, and fresh-model closure machinery. The frozen census—not terminal-MIP runtime—decides whether either variant may enter live testing.

## Iteration 2 — conditionally closed

IR3 (one exact mixed-cut pass) is the only permitted second-iteration variant. It may open only if a valid full-closure variant passes the offline gate while closure overhead clearly dominates bound gain. Until that condition is observed, iteration 2 is formally not opened. No instance-, size-, time-, or result-dependent policy is permitted.

Implementation debugging before the census corrected only generic construction, validation, and telemetry. It did not change the predeclared mathematical variants or use live MIP performance.
