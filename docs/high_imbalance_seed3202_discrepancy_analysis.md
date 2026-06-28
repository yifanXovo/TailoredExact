# high_imbalance_seed3202 Discrepancy Analysis

Earlier V20 rows for `high_imbalance_seed3202` included a noncertified
mip-light 1200s result and an exhaustive 300s row with a positive gap.  The
current replication round certifies the same instance repeatedly.

The option comparison is recorded in:

`results/v20_replication_round/high_imbalance_seed3202_option_diff.csv`.

Key differences:

| row | status | gap | portfolio mode | certificate mode | compact-flow | connectivity |
|---|---|---:|---|---|---|---|
| previous certified full run | optimal | 0 | fixed | bound | mip-light | true |
| previous exhaustive 300s | not closed | 0.0755243654678 | exhaustive | both | mip-light | false |
| current rep1 | optimal | 0 | fixed | bound | mip-light | true |

The certified rows use the fixed mip-light compact-flow relaxation with
connectivity enabled and keep the strongest valid lower bound per interval.
The weaker exhaustive row spent budget on additional variants and did not use
the same connectivity setting.  It therefore failed to close the full frontier
within its budget.  The evidence does not show stale ledger dependence:
replication rows are fresh full-frontier runs, with clean raw JSON, interval
CSV, progress CSV, UB event logs, and audit output.

The canonical setting for future V20 certificate attempts is therefore:

- native HGA-TGBC UB, verified and UB-only;
- full Gini-frontier ledger;
- fixed V20 relaxation portfolio with `large_compact_flow_relaxation=mip-light`;
- compact-flow connectivity enabled;
- V20-safe cuts and station residual domain cuts enabled;
- archive scanning disabled;
- BPC fallback off unless a focused diagnostic is explicitly requested.

This setting is now captured as `--algorithm-preset paper-exact-v20-certificate`.
The preset is a paper-candidate exact portfolio, not a replacement claim that
BPC pricing/tree is the active certificate path.
