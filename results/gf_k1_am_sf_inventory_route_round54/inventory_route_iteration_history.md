# Inventory-route iteration history

## Iteration 1 — frozen before the offline census

The two predeclared variants are IR1 (full mixed closure) and IR2 (full mixed plus nondominated projected closure). Both use the same exact deterministic separator, tolerance, base model, and fresh-model closure machinery. The frozen census—not terminal-MIP runtime—decides whether either variant may enter live testing.

## Iteration 2 — conditionally closed

IR3 (one exact mixed-cut pass) is the only permitted second-iteration variant. It may open only if a valid full-closure variant passes the offline gate while closure overhead clearly dominates bound gain. Until that condition is observed, iteration 2 is formally not opened. No instance-, size-, time-, or result-dependent policy is permitted.

Implementation debugging before the census corrected only generic construction, validation, and telemetry. It did not change the predeclared mathematical variants or use live MIP performance.

The first census launch exposed an accounting defect on the moderate V50 state: each fresh LP solve inherited the full process allowance rather than its remaining allowance. That partial census was invalidated. The sole correction subtracts elapsed closure time before every fresh solve and before closure begins; the variants, inequalities, tolerance, and gate are unchanged. The corrected census is rerun in full with the ordinary 3600-second cap for V50 and a 120-second engineering envelope for smaller LP states.
