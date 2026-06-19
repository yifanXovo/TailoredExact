# Station-Operation Cut Proof

Date: 2026-06-14.

## Scope

This proof covers the station-operation rows added to the final-inventory/Gini interval relaxation in `src/Bounds.cpp`.

The project's certified model defines a served station as a station with a positive pickup or a positive drop operation. This is consistent with:

- `src/Evaluator.cpp`, which rejects a visited station with `pickup=0` and `drop=0`.
- `src/CplexBaseline.cpp`, which writes `p[k,i] + d[k,i] - z[k,i] >= 0`.
- Route-load columns, where a station belongs to a column support only when its signed operation `q_i` is nonzero.

Thus the relaxation variable `v_i` is not a free sightseeing/waypoint indicator. It is the projection-level indicator that station `i` has a positive operation and is assigned to a route support in the route-mask relaxation.

## Definitions

For station `i`:

- `p_i >= 0` is the aggregate number of bikes picked up at station `i`.
- `d_i >= 0` is the aggregate number of bikes dropped at station `i`.
- `v_i in {0,1}` in the integer relaxation indicates station `i` has a positive operation.
- `Y_i^0` is initial inventory.
- `C_i` is station capacity.
- `Qmax = max_k Q_k`.

The implementation defines

```text
U_i = max(min(Y_i^0, Qmax), min(C_i - Y_i^0, Qmax)).
```

and adds

```text
p_i + d_i <= U_i v_i
p_i + d_i >= v_i.
```

## Upper Row

In any feasible original route-load solution, a served station is operated by at most one vehicle because station visits are disjoint. At that station the operation mode is either pickup or drop, not both.

If station `i` is a pickup station, then

```text
p_i <= Y_i^0
p_i <= Q_k <= Qmax
d_i = 0.
```

Therefore `p_i+d_i <= min(Y_i^0,Qmax) <= U_i`.

If station `i` is a drop station, then

```text
d_i <= C_i - Y_i^0
d_i <= Q_k <= Qmax
p_i = 0.
```

Therefore `p_i+d_i <= min(C_i-Y_i^0,Qmax) <= U_i`.

If station `i` is not served, `v_i=0` and the existing linking rows imply `p_i=d_i=0`. Hence `p_i+d_i <= U_i v_i` is globally valid for every `M`, every vehicle-capacity vector `Q`, every `lambda`, and every route time limit `T`.

## Lower Row

For the project's certified route-load model, `v_i=1` means station `i` has a positive operation. Since pickup/drop quantities are integer,

```text
v_i=1  =>  p_i+d_i >= 1.
```

If `v_i=0`, the row is `p_i+d_i>=0`, already implied by nonnegativity. Therefore `p_i+d_i >= v_i` is valid for the solved model.

## Zero-Operation Visits

The high-level BRP wording can be read as allowing a route to pass through a station with zero pickup and zero drop. Such a zero-operation waypoint is not part of this project's certified model: the verifier rejects it and the compact MILP forbids it.

If a broader model allowed zero-operation station waypoints, the lower row would still be safe under the standard metric-distance assumption because a zero-operation waypoint can be removed from the route without changing final inventories, load, objective, or station operation time, and triangle inequality prevents travel time from increasing.

If zero-operation waypoints were allowed and the raw travel matrix were nonmetric and not interpreted as shortest-path travel times, the lower row would not be valid for that broader model because a zero-operation waypoint might act as a travel shortcut. That is not the model currently certified by ExactEBRP. The current benchmark instances parsed from `Hybrid GA/testdata/Smallnetwork2` rebuild distances from coordinates, and the bound code uses metric closure for route lower bounds.

## Implementation Audit

The rows are implemented in `src/Bounds.cpp` in `computeGiniIntervalInventoryRelaxationBound`:

```text
p_i + d_i - U_i v_i <= 0
p_i + d_i - v_i >= 0
```

where `U_i` is exactly `max(min(initial_i,Qmax), min(capacity_i-initial_i,Qmax))`.

The JSON notes for bound-producing runs include:

```text
station_operation_mode_cuts=true
nonzero_visit_operation_cuts=true
```

## Decision

The cuts are valid for certificate-producing runs of this project because the exact model being certified treats station service as a positive pickup or positive drop operation. They should remain enabled.
