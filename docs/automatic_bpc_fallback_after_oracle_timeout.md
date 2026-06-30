# Automatic BPC Fallback After Oracle Timeout

Automatic BPC fallback is now explicitly tracked after interval-oracle timeout:

- `--auto-interval-bpc-fallback true|false`
- `--auto-interval-bpc-time-limit <seconds>`
- `--auto-interval-bpc-max-leaves <N>`
- `--auto-interval-bpc-max-nodes <N>`
- `--auto-interval-bpc-pricing-time-per-call <seconds>`

BPC fallback can close a leaf only if exact pricing closure is proven for the
tree nodes used as lower-bound evidence. Otherwise it remains diagnostic and
the row stays noncertified.

This round:

- `moderate_seed3301_oracle_deep`: attempted 2 leaves, closed 0.
- `tight_T_seed3102_controlled`: attempted 2 leaves, closed 0.
- `high_imbalance_seed3201_controlled`: attempted 2 leaves, closed 0.

Summary:

```text
results/oracle_closure_round/bpc_fallback_after_oracle.csv
```

Conclusion: BPC fallback still did not provide exact leaf closure. The active
blocker remains interval cutoff MIP timeout and exact-pricing leaf closure, not
UB quality.
