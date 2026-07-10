# Structural Policy Scope

- Source commit for fresh solver rows: `940449b880c06d3199a5608e1849b97a33b8a259`.
- Mainline: `paper-gf-tailored-bc`.
- Official benchmark: current binary-expansion compact MILP with CPLEX.
- Callback/root vectors and auto-selection are diagnostic only.
- No fixed-interval incumbent is imported as a global UB.
- No full-frontier run uses an imported UB.
- BPC, route-mask, archive, known-UB, external-incumbent, and focus-only evidence are excluded.
