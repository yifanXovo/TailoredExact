# BPC Fallback Retest After Relaxation

Date: 2026-06-27

## Purpose

Previous rows ended with `tree_not_started_before_time_limit_or_reserve`, so the
round retested controlled BPC fallback after the new relaxation variants.

CLI pattern:

```text
--frontier-bpc-fallback-mode controlling-intervals
--frontier-bpc-fallback-max-intervals 1
--frontier-bpc-fallback-min-seconds 60
--frontier-bpc-fallback-reserve-fraction 0.20
```

## Results

| row | LB | UB | gap | nodes | pricing calls | result |
|---|---:|---:|---:|---:|---:|---|
| `v12_m1_bpc_fallback_300s` | 0.331296710948 | 0.357200583208 | 0.0725191208467 | 1 | 1 | worse than relaxation-only |
| `high_imbalance_seed3202_miplight_fallback_300s` | 1.65415045452 | 1.74931345205 | 0.0544001976401 | 0 | 0 | same as relaxation-only |
| `tight_T_seed3102_lp_fallback_300s` | 0.469176890001 | 0.600704436685 | 0.21895551065 | 0 | 0 | same as relaxation-only |
| `moderate_seed3302_lp_fallback_300s` | 0.131033733249 | 0.195636206549 | 0.33021736845 | 0 | 0 | same as relaxation-only |

## Conclusion

BPC fallback should remain diagnostic, not a paper-core default. On V12 M1 it
starts but does not close exact pricing and displaces useful relaxation time. On
V20/M3 the fallback reserve is not reached before relaxation consumes the row
budget. The current active bottleneck is still valid relaxation lower-bound
strength and scheduling.
