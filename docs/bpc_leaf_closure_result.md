# BPC Leaf Closure Result

This document summarizes whether any frozen target leaf closed by exact BPC
pricing in the repair round.  The final source of truth is
`results/bpc_core_repair_round/bpc_leaf_ablation_matrix.csv` and
`results/bpc_core_repair_round/final_report.md`.

Closure criteria:

- the run must use `paper-gf-bpc-core`;
- interval-oracle certificate fields must be false;
- exact pricing closure must be true for the BPC node/leaf used as lower-bound
  evidence;
- if branch nodes are used, every node contributing to the lower-bound proof
  must also have exact pricing closure;
- audit must pass.

Preliminary 300s and 1200s observations:

- No target leaf closed in 300s or 1200s.
- V12 M1 and V12 M2 still had negative reduced-cost columns near the time
  limit.
- moderate_seed3301 had positive best reduced cost but pricing enumeration did
  not complete, so closure was not certified.
- cuts remained inactive in baseline rows.

The 3600s rows determine whether longer exact pricing changes this conclusion.
