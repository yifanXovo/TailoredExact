# Low-Gini Interval Oracle Strengthening

The exact interval cutoff oracle now exposes generic strengthening flags:

- `--interval-oracle-low-gini-tightening`
- `--interval-oracle-objective-cutoff-row`
- `--interval-oracle-penalty-domain-tightening`
- `--interval-oracle-service-operation-tightening`
- `--interval-oracle-symmetry-breaking`

The `paper-exact-v20-certificate` preset enables these flags. The objective
cutoff row is kept as a mandatory part of the cutoff-feasibility oracle because
the oracle question is whether an original feasible solution exists with
`G + lambda * P <= UB - epsilon`.

Implemented tightening:

- penalty-budget domain constraints derived from
  `P <= (UB - epsilon - gamma_L) / lambda`;
- station residual upper bounds `e_i <= P_budget / weight_i` for positive
  station weights;
- existing original-model nonzero service-operation consistency is preserved;
- identical-vehicle symmetry breaking remains guarded by
  `--interval-oracle-symmetry-breaking`.

These constraints are necessary conditions for any solution that improves the
incumbent within the tested Gini interval. They do not use sampled routes,
archive incumbents, or instance-specific constants.

Ablation summary:

```text
results/oracle_closure_round/oracle_strengthening_ablation.csv
```

The strengthened/deeper `moderate_seed3301_oracle_deep` run did not certify the
row. It closed the same 4 root leaves as the 600s run but partitioned timeout
leaves more deeply and exposed the remaining exact-oracle bottleneck.
