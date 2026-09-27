# Inventory-route iteration history

## Iteration 1 — frozen before the offline census

The two predeclared variants are IR1 (full mixed closure) and IR2 (full mixed plus nondominated projected closure). Both use the same exact deterministic separator, tolerance, base model, and fresh-model closure machinery. The frozen census—not terminal-MIP runtime—decides whether either variant may enter live testing.

## Iteration 2 — conditionally closed

IR3 (one exact mixed-cut pass) is the only permitted second-iteration variant. It may open only if a valid full-closure variant passes the offline gate while closure overhead clearly dominates bound gain. Until that condition is observed, iteration 2 is formally not opened. No instance-, size-, time-, or result-dependent policy is permitted.

Implementation debugging before the census corrected only generic construction, validation, and telemetry. It did not change the predeclared mathematical variants or use live MIP performance.

The first census launch exposed an accounting defect on the moderate V50 state: each fresh LP solve inherited the full process allowance rather than its remaining allowance. That partial census was invalidated. The sole correction subtracts elapsed closure time before every fresh solve and before closure begins; the variants, inequalities, tolerance, and gate are unchanged. The corrected census is rerun in full with the ordinary 3600-second cap for V50 and a 120-second engineering envelope for smaller LP states.

## Corrected offline outcome

The corrected census completed 68 rows (34 states for each of IR1 and IR2). Both variants were valid on every state, had strict violations in 33 recorded structural roles, and produced a strict final LP-bound gain on 25 states. IR2 produced no strict final-closure improvement over IR1, so the frozen least-expansive rule selected IR1. The IR3 entry condition did not occur and iteration 2 remains formally not opened.

## Live Stage A outcome

IR1 entered the mandatory paired 300-second development stage. All 28 physical rows were engineering-valid and produced zero false certificates. F0-CLEAN certified 11/14 states; IR1 certified 9/14 and lost the D1 and D13 baseline certificates. Those losses are two severe regressions. The shifted Work geometric-mean ratio was 1.089432 and aggregate normalized GI was 0.623423 for IR1 versus 0.498349 for F0-CLEAN. D4 supplied one material hard-state Work improvement, but the candidate failed the no-loss, no-severe-regression, and aggregate-nonworse gates. The 1200-second stage, confirmation, long checks, K1 integration, and sealed generalization panel therefore did not open.
