# Paper Evidence Candidate Report

Latest evidence package update: `results/gf_compact_bc_strengthening_round`
contains the current paper-facing compact-BC evidence.

Classification:

- `paper-gf-compact-bc`: sealed Gini-frontier compact branch-and-cut rows;
  one-thread fair rows have `thread_fairness_class=one_thread_fair`.
- `CPLEX benchmark`: `method=cplex` / plain compact CPLEX rows; benchmark-only
  and not imported into exact-pipeline certificates.
- `diagnostic`: dynamic-root scheduling probes, receiver-cover diagnostics, and
  wrapper error JSONs for large-V memory failures.
- `BPC diagnostic`: historical route-load BPC validation artifacts only; BPC is
  not enabled in `paper-gf-compact-bc`.

Current controlled evidence:

| Row | Classification | Status |
|---|---|---|
| V12 M1 average | paper-gf-compact-bc | certified |
| V12 M2 average | paper-gf-compact-bc | certified |
| tight_T_seed3101 | paper-gf-compact-bc | certified |
| high_imbalance_seed3202 | paper-gf-compact-bc | noncertified in 300s one-thread run |
| moderate_seed3301 | paper-gf-compact-bc | noncertified, LB 0.046285 / UB 0.0491525526647 |
| V50/V100 diagnostics | diagnostic | noncertified wrapper error JSONs after memory failure |

Paper-readiness decision: not ready for broader benchmark claims.  The
compact-BC framework is certificate-safe and stronger than plain CPLEX on the
same one-thread 300s V20 comparisons, but the fair mini-suite certifies only
one of six V20 rows in this short controlled run and large-V model generation
needs memory reduction.

Latest evidence package update: `results/bpc_pricing_optimization_round` copied key manifests and audits into `results/paper_evidence_candidate` with the `bpc_pricing_optimization_round_` prefix.

Classification:

- `paper-gf-bpc-core`: sealed core rows, no interval-oracle certificate and no CPLEX contamination.
- `large_v_diagnostic`: V50/V100 short-budget diagnostics with honest noncertified final JSON.
- `BPC diagnostic`: focused leaf validation CSVs and dominance ablation rows.
- `CPLEX benchmark`: preserved same-budget comparison table from the realignment round; not used as exact-pipeline lower-bound evidence.

Current evidence is not sufficient for broad paper benchmarking of BPC effectiveness. The strongest current conclusion is that the unified core is certificate-safe, while BPC pricing needs a deeper exact decomposition before it can serve as an empirically useful fallback.
