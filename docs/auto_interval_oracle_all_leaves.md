# Automatic All-Leaf Interval Oracle

This round extends the sealed paper pipeline so the automatic interval oracle is
not limited to a single unresolved frontier leaf.

## Behavior

With:

```text
--auto-interval-oracle true
--auto-interval-oracle-order all
--auto-interval-oracle-max-leaves all
```

the solver collects every final unresolved Gini-frontier leaf after the
relaxation phase and attempts the exact interval cutoff oracle on each leaf. A
leaf is closed only when the oracle proves the original fixed-interval cutoff
MIP infeasible. If the oracle finds a verified improving original solution, the
incumbent is UB-only evidence and the full frontier must be restarted.

The option:

```text
--auto-interval-oracle-split-on-timeout true
```

splits a timed-out leaf into equal child gamma intervals up to
`--auto-interval-oracle-max-depth`. A parent leaf can be merged as closed only
when all child intervals close and the child intervals exactly partition the
parent without gaps or overlaps.

## Audit Fields

Each final JSON now records:

- `auto_interval_oracle_total_final_leaves`;
- `auto_interval_oracle_leaves_attempted`;
- `auto_interval_oracle_leaves_closed`;
- `auto_interval_oracle_leaves_timed_out`;
- `auto_interval_oracle_leaves_split`;
- `auto_interval_oracle_remaining_open_leaves`;
- `auto_interval_oracle_coverage_complete`;
- `full_ledger_merge_status`;
- `full_ledger_merge_audit_passed`.

The fields distinguish a complete oracle closure from a partial diagnostic
attempt. Timeout evidence does not certify a leaf.

## Round Outcome

In `results/sealed_closure_round/`, all nine sealed rows produced final JSON.
The all-leaf oracle closed four of six final leaves for `moderate_seed3301` and
one of four final leaves for `moderate_seed3302`. It did not close
`tight_T_seed3102` or `high_imbalance_seed3201`; those rows remain honestly
noncertified with timed-out leaves recorded in the oracle summary.
