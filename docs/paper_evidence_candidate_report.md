# Paper Evidence Candidate Report

Latest evidence package update: `results/bpc_pricing_optimization_round` copied key manifests and audits into `results/paper_evidence_candidate` with the `bpc_pricing_optimization_round_` prefix.

Classification:

- `paper-gf-bpc-core`: sealed core rows, no interval-oracle certificate and no CPLEX contamination.
- `large_v_diagnostic`: V50/V100 short-budget diagnostics with honest noncertified final JSON.
- `BPC diagnostic`: focused leaf validation CSVs and dominance ablation rows.
- `CPLEX benchmark`: preserved same-budget comparison table from the realignment round; not used as exact-pipeline lower-bound evidence.

Current evidence is not sufficient for broad paper benchmarking of BPC effectiveness. The strongest current conclusion is that the unified core is certificate-safe, while BPC pricing needs a deeper exact decomposition before it can serve as an empirically useful fallback.
