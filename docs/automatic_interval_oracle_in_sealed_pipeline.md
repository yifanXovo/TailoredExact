# Automatic Interval Oracle in the Sealed Pipeline

The sealed completion pipeline attempts interval-local exact cutoff MIP
diagnostics after a row exits without a certified full frontier. This stage is
strictly conservative.

## Trigger

The wrapper and solver expose:

- `--auto-interval-oracle true|false`;
- `--auto-interval-oracle-time-limit <seconds>`;
- `--auto-interval-oracle-max-leaves <N>`;
- `--auto-interval-oracle-order low-gini|min-gap|min-lb|all`;
- `--auto-interval-oracle-restart-on-improved-ub true|false`.

In the sealed completion round, checkpoint oracle postprocessing selected the
current controlling checkpoint leaf for each interrupted V20 row and ran:

```text
interval_exact_cutoff_mip
```

No instance-specific interval id or gamma range was supplied by the algorithm.

## Certificate Rule

An interval oracle can close an interval only when the exact cutoff MIP proves
infeasibility for the original fixed-interval cutoff model. A timeout is
unresolved. A feasible improving solution would be UB-only until independently
verified and followed by a full frontier restart.

Focused oracle diagnostics do not certify the whole row unless all final leaves
are covered exactly by a safe full-ledger merge.

## Current Round

The checkpoint oracle attempted one leaf for each interrupted V20 row:

- `high_imbalance_seed3201`: timeout;
- `tight_T_seed3102`: timeout;
- `moderate_seed3301`: one leaf proven infeasible;
- `moderate_seed3302`: timeout.

Because the full frontier still had other open leaves or no complete merge, all
four rows remained noncertified.
