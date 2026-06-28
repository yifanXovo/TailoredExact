# high_imbalance_seed3202 Reproducibility Audit

Round directory: `results/v20_replication_round/`.

The V20/M3 stress instance `reference/hard_stress/V20_M3/high_imbalance_seed3202.txt`
was rerun three times from a clean result directory using the same
paper-reproducible native HGA-TGBC incumbent path and fixed V20 relaxation
settings. Archive scanning was disabled in every row.

| replicate | status | objective | LB | UB | gap | runtime | certified |
|---|---|---:|---:|---:|---:|---:|---|
| rep1 | optimal | 1.74931345205 | 1.74931345205 | 1.74931345205 | 0 | 301.031s | true |
| rep2 | optimal | 1.74931345205 | 1.74931345205 | 1.74931345205 | 0 | 405.994s | true |
| rep3 | optimal | 1.74931345205 | 1.74931345205 | 1.74931345205 | 0 | 344.974s | true |

All three rows pass `scripts/audit_bpc_certificate.py --fail-on-error`.
The objective, lower bound, upper bound, incumbent source, instance scope, and
certificate basis are stable.  The second run split one final Gini band into
two bound-fathomed leaves where the first and third runs kept it as one leaf.
That means the ledger is not structurally identical line-for-line, but it is
certificate-equivalent: every final leaf is bound-fathomed, there are no
unresolved intervals, no open nodes, no invalid intervals, and the full
improving Gini range is covered.

No row uses result-directory archive scanning.  The incumbent source category
is `primal_heuristic`, with `incumbent_source_contributes_lower_bound=false`.
For V20 the route-mask all-subset enumeration flag remains noncertifying.

Machine-readable evidence:

- `results/v20_replication_round/high_imbalance_seed3202_repro_summary.csv`;
- `results/v20_replication_round/certificate_audit.csv`;
- raw rows under `results/v20_replication_round/raw/high_imbalance_seed3202_rep*.json`.
