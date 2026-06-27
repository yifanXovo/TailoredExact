# Parallel Relaxation And Cache

Date: 2026-06-27

## Scope

The solver already caches relaxation evidence by interval and option signature.
This round extends the cache key with the new V20 relaxation settings:

- V20 cover-cut flags and limits;
- station residual cover-cut flags;
- large compact-flow relaxation mode and budget;
- frontier pre-split controls.

The CLI now also accepts explicit aliases:

```text
--frontier-relaxation-parallel true|false
--frontier-relaxation-workers <int>
```

These map to the existing deterministic frontier worker controls.

## Determinism Rule

Parallel interval processing may only change runtime. The final ledger is still
aggregated through stable interval ids and certificate guards. A row cannot be
certified unless the final JSON ledger fields pass the same audit as a
single-worker run.

## Round Result

The V12 M1 2-worker 300s row did not improve lower bound:

| row | LB | UB | gap | runtime |
|---|---:|---:|---:|---:|
| `v12_m1_current_300s` | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 300.828s |
| `v12_m1_parallel2_300s` | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 304.279s |

For this instance, the bottleneck remains relaxation strength and focused split
depth, not worker scheduling.
