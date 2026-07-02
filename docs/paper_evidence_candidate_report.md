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
## Round 2 Evidence Classification

`results/gf_compact_bc_strengthening_round2/` is the current one-thread
compact-BC evidence package.

Certified exact compact-BC rows:

- V12 M1 average
- V12 M2 average
- `high_imbalance_seed3202`
- `tight_T_seed3101`

Noncertified compact-BC rows include `moderate_seed3301`, the remaining V20/M3
stress rows, and all V50/V100 diagnostics. Plain CPLEX rows in this package are
single-thread benchmark-only comparisons.

## Time-Profile Evidence Classification

`results/gf_compact_bc_timeprofile_round/` is the current audited time-profile
package.

Certified exact compact-BC rows in this package:

- V12 M1 average;
- V12 M2 average;
- `tight_T_seed3101`;
- `high_imbalance_seed3202` in the 1200s static recovery row.

Noncertified compact-BC rows include `moderate_seed3301`,
`high_imbalance_seed3201`, `tight_T_seed3102`, `moderate_seed3302`, and all
large-V diagnostics. Plain CPLEX rows are one-thread benchmark-only rows.

Paper-readiness decision: not ready for broad benchmark claims. The package is
useful for controlled time-profile and same-budget CPLEX comparison, but
moderate low-Gini leaves and large-V model-size behavior still need targeted
compact-BC strengthening.

## Effectiveness Attribution Evidence

`results/gf_compact_bc_effectiveness_round/` is the current package for
certificate-source attribution and repaired time-profile finalization.

Classification in that package:

- `relaxation_only`: valid framework certificates closed before Compact-BC was
  needed;
- `relaxation_plus_compact_bc`: rows or leaves where Compact-BC contributes
  interval evidence;
- `wrapper_checkpoint_only`: noncertified interrupted artifacts repaired from
  the best valid progress checkpoint;
- `benchmark_only`: plain CPLEX rows, never imported into certificate evidence;
- `compact_bc_leaf_diagnostic`: interval-local subsolver rows used to diagnose
  Compact-BC behavior.

The correct paper claim is not that Compact-BC is always the dominant closure
source. The claim is a Gini-frontier compact certification framework with strong
relaxation/domain cuts and Compact-BC subproblems for unresolved intervals.
Current evidence keeps `moderate_seed3301` noncertified and identifies its
remaining low-Gini leaves as the next hard-leaf strengthening target.

## Effectiveness Round 2 Evidence

The candidate evidence now reports whether certificates are relaxation-only, Compact-BC-assisted, mixed, or diagnostic. Compact-BC dominance is not required for a valid framework certificate.

## Effectiveness Round 3 Evidence

The candidate evidence distinguishes relaxation-only certificates, Compact-BC-assisted certificates, diagnostic fixed-interval probes, and benchmark-only CPLEX rows. Compact-BC dominance is not required for a valid framework certificate.
