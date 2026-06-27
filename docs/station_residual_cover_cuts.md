# Station Residual Cover Cuts

Date: 2026-06-27

## Purpose

Station residual cuts use only incumbent cutoff, interval gamma range, station
capacity, target inventory, and penalty weights. They are lower-bound-domain
cuts and do not depend on sampled routes or route pools.

## Validity

For an improving solution with incumbent cutoff `UB`, interval lower Gini bound
`gamma_L`, and objective `G + lambda * P`, the penalty must satisfy:

```text
P <= (UB - gamma_L) / lambda
```

Station penalty terms are nonnegative. Therefore each station final inventory
domain can be safely tightened by excluding values whose own weighted target
deviation already exceeds the available penalty budget. This is a necessary
condition for any solution that can improve or match the incumbent cutoff within
the current interval.

This round also adds a projection penalty floor for large-instance relaxation
rows:

```text
sum_i w_i * |Y_i / T_i - 1| >= projection_penalty_lower_bound
```

where the right-hand side is computed from independent station-capacity domain
minimums. This cannot remove a feasible original solution because every
original final inventory vector has penalty at least the sum of per-station
domain minima.

## CLI

```text
--station-residual-cover-cuts true|false
--station-residual-cover-max-cuts <int>
```

Reported fields include:

- `station_residual_domains_tightened_count`;
- `station_residual_domain_width_before`;
- `station_residual_domain_width_after`;
- `station_residual_cover_cuts_added`;
- `station_residual_cover_time_seconds`.

## Round Result

The residual-domain cuts add valid bookkeeping and small lower-bound tightening
on V20 rows, but they are not the main improvement. Example:

- `high_imbalance_seed3202_miplight_1200s` adds 21 residual cuts and ends with
  LB `1.69375051373`, UB `1.74931345205`, gap `0.0317627113992`.

For V12 and smaller instances these residual projection cuts are disabled by
default in this round because the complete small-instance route-mask and
vehicle-indexed relaxation stack is already stronger and the residual floor
adds solve time without improving the 300s certificate path.
