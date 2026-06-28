# Cache And Parallel Determinism Audit

Date: 2026-06-28

Parallel interval relaxation was not the main solution path in this round.
Previous two-worker V12 M1 evidence did not improve the 300s lower bound over
the one-worker baseline.  The new cache key includes the adaptive portfolio and
new V20 cut flags so incompatible lower-bound evidence is not reused.

Round summary:

```text
results/paper_candidate_relaxation_round/cache_parallel_ablation.csv
```

Current recommendation: keep deterministic single-worker relaxation as the
default until the variant selector reliably improves bounds.  Parallel workers
can be used as a diagnostic acceleration option once selector decisions are
stable.

