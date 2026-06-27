# Large Compact-Flow Relaxation

Date: 2026-06-27

## Purpose

The V20/M3 stress rows need a large-instance lower-bound family that does not
depend on complete all-subset route-mask enumeration. This round adds an
optional compact-flow relaxation to the interval relaxation portfolio.

This is not the compact exact MILP benchmark and not a CPLEX incumbent source.
It is a lower-bound relaxation used only inside the paper-core frontier.

## Model Sketch

For each vehicle `k`, station/depot arc variables `x[k,i,j]` are added over the
depot plus station graph. In LP mode they are continuous; in `mip-light` mode
they are binary for the compact-flow structure while the model remains a
relaxation of the original route-load problem.

The model links service variables to flow:

```text
sum_j x[k,i,j] = y[k,i]
sum_j x[k,j,i] = y[k,i]
sum_j x[k,depot,j] <= 1
sum_i x[k,i,depot] <= 1
```

It also adds a fractional route-duration row:

```text
sum_{i,j} travel[i,j] x[k,i,j]
  + pickup_time * total_pickup[k]
  + drop_time * (total_drop[k] + depot_unload[k])
  <= T_k
```

Every original feasible route-load solution induces a feasible compact-flow
solution by setting its used arcs to one and its station operations to the true
route operations. Therefore the relaxation lower bound is valid.

## CLI

```text
--large-compact-flow-relaxation off|lp|mip-light
--large-compact-flow-time-limit <seconds>
```

Reported fields include:

- `large_compact_flow_relaxation`;
- `large_compact_flow_arc_variables`;
- `large_compact_flow_constraints`;
- `large_compact_flow_time_seconds`.

## Round Result

`mip-light` is the first V20-safe relaxation component in this round that gives
material lower-bound improvement:

| row | previous gap | new gap | note |
|---|---:|---:|---|
| `high_imbalance_seed3201_miplight_300s` | 0.122744236967 | 0.0682096293371 | improved |
| `high_imbalance_seed3202_miplight_300s` | 0.100084871258 | 0.0544001976401 | improved |
| `tight_T_seed3101_miplight_300s` | 0.968587506517 | 0.333333333333 | improved |

It is not universally stronger: moderate rows and `tight_T_seed3102` have worse
short-run gaps with `mip-light` than with the LP relaxation. The current
recommendation is to keep `mip-light` as an explicit controlled variant and add
per-interval variant selection before making it a default.
