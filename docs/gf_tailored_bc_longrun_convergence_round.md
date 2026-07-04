# GF Tailored BC Long-Run Convergence Round

This round keeps the paper-facing algorithm on `paper-gf-tailored-bc`: Gini-frontier decomposition, valid interval bounds, CPLEX-managed tailored fixed-interval branch-and-cut, and audited full-frontier ledger aggregation. Plain CPLEX and plain fixed-interval MIP rows remain benchmark-only.

## Worker Boundary

Fixed-interval callback solves are executed as child worker processes by `scripts/run_tailored_bc_longrun_convergence_round.py`. The parent process enforces a hard wall-clock cap, reads the worker progress CSV, and preserves only CPLEX-native `CPXCALLBACKINFO_BEST_BND` rows as valid diagnostic lower-bound trajectory points. Heartbeat-only checkpoints remain invalid as bounds. Wrapper-synthesized rows are noncertifying diagnostics and are not merged into paper-core evidence.

## Targeted Optimization

The callback backend now supports:

```text
--tailored-bc-callback-separation-pacing off|bound-aware
--tailored-bc-callback-separation-min-calls <N>
```

`bound-aware` pacing keeps cheap valid cuts active on every relaxation callback, but delays expensive subset/support/transfer separation until either the native best bound improves or enough relaxation callbacks have elapsed. This is exact-safe because it only skips optional valid cuts; it never removes or rejects feasible original solutions.

## Evidence Summary

The round output is:

```text
results/gf_tailored_bc_longrun_convergence_round/
```

Moderate low-Gini leaf 2 closes at the 1200s paced callback setting. Moderate low-Gini leaf 1 improves from the 60s checkpoint bound to the 300s checkpoint bound, then plateaus through 1200s and 3600s at the same valid lower bound. The remaining bottleneck is therefore weak low-Gini bound progress, not absence of CPLEX-native checkpoint finalization.

The additional hard leaves `high_imbalance_seed3201_hard`, `tight_T_seed3102_hard`, and `moderate_seed3302_hard` close in the short fixed-interval tests; they do not expose the same long-run bottleneck as `moderate_seed3301_low_gini_1`.

Control rows in this package are diagnostic 60s reruns. They are not claimed as replacement certificates because the worker cap produced wrapper checkpoint rows rather than audited full-frontier final certificates.
