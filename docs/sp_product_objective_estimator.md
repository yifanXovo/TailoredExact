# S-P Product Objective Estimator

The exact no-improver condition is `H + V lambda S P <= V (UB-epsilon) S`. The implementation introduces `W_SP` with McCormick bounds over valid `S` and `P` domains and adds `H + V lambda W_SP <= V(UB-epsilon)S`. For every original feasible solution, `W_SP=S P` satisfies the McCormick system, so the row cannot remove an original incumbent-improving solution. The relaxation may under-estimate `SP`, making the row weaker but still certificate-safe.
