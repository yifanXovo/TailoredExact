# GF Tailored BC Bound Trajectory Round

This round keeps `paper-gf-tailored-bc` as the paper-facing line:

```text
Gini-frontier decomposition
+ valid interval relaxation/frontier bounds
+ CPLEX-managed tailored fixed-interval branch-and-cut
+ audited full-ledger aggregation
```

Plain CPLEX remains benchmark-only. Its bounds are not imported into the Tailored-BC ledger.

## Engineering Change

The callback CPLEX API now records valid solver-native bound information during callback execution:

- `CPXsetterminate` is loaded and armed as an additional worker termination guard.
- `CPXCALLBACKINFO_BEST_BND` is sampled from generic callback contexts.
- `CPXCALLBACKINFO_BEST_SOL` and `CPXCALLBACKINFO_NODECOUNT` are sampled when available.
- Progress CSV rows distinguish `cplex_native_callback_info` from heartbeat-only activity rows.

If `CPXmipopt` returns, the final JSON records the solver-final status and final best bound. If the worker must be externally stopped, the wrapper can preserve the best CPLEX-native checkpoint bound in a noncertified JSON.

## Current Evidence

The minimal bound-trajectory package is in:

```text
results/gf_tailored_bc_bound_trajectory_round/
```

The two moderate low-Gini fixed intervals now produce valid CPLEX-native checkpoint trajectories under callback Tailored-BC. They are classified as `valid_bound_progress`, not `no_valid_bound_bug`.

The corresponding plain/no-cut fixed-interval benchmark rows did not produce a valid bound before wrapper finalization in this minimal run and remain benchmark-only.

## Remaining Limitation

The worker boundary is improved but not fully solved: on hard callback leaves, `CPXmipopt` may still fail to return a solver-final JSON under the requested time limit. Checkpoint bounds are valid diagnostics but are not automatically paper-core certificate evidence.

The next implementation step is a production worker boundary for frontier integration, with explicit audited rules for when checkpoint-bound evidence may be merged.
