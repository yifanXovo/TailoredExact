# GF Compact BC Round Final Report

Branch at run time: `codex/longrun-round17-local-results`. Base commit before this work: `653da7d46096b04dd7bb7cb999f8b76c0583df2d`.

## Scope

This round introduces `--algorithm-preset paper-gf-compact-bc`, the Gini-frontier compact branch-and-cut/certification framework. It keeps native HGA-TGBC incumbents as UB-only evidence, uses valid Gini-frontier relaxation bounds, and closes unresolved leaves with original fixed-interval compact MIP/BC evidence from CPLEX. Route-load BPC is disabled by default and did not contribute to any paper-row certificate in this round.

## Implemented Cut And Model Mechanisms

- Fixed handling-time audit: the aggregate global handling row now charges pickup quantity only under the current compact/verifier convention, replacing the invalid `cunit * (p + d)` aggregate row.
- Direct interval Gini cap/floor rows: `H <= V * gamma_U * S` and `H >= V * gamma_L * S`.
- Interval-tight McCormick rows for `G * bit` using `[gamma_L, gamma_U]`.
- Total station inventory conservation bounds for empty-start vehicles with possible depot return.
- Movement-reachability final-inventory domain tightening and visit-final-inventory linking rows.
- Objective lower-estimator cutoff row and penalty lower-bound cheap closure row.
- Low-Gini centering band, pair/triple route-duration support cuts, and pairwise transfer compatibility cuts.
- Conservative receiver-set source-cover cuts remain diagnostic/disabled by default.

## Paper Mini-Suite

| row | status | certified | LB | UB | gap | runtime_s | compact leaves closed/timed out | unresolved | BPC used |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| regen_candidate_V12_M1_average.txt | optimal | yes | 0.357200583208 | 0.357200583208 | 0 | 303.4084659 | 6/0 | 0 | no |
| regen_candidate_V12_M2_average.txt | optimal | yes | 0.718504070755 | 0.718504070755 | 0 | 290.781898 | 0/0 | 0 | no |
| high_imbalance_seed3202.txt | optimal | yes | 1.74931345205 | 1.74931345205 | 0 | 293.4988343 | 0/0 | 0 | no |
| tight_T_seed3101.txt | optimal | yes | 0.107252734134 | 0.107252734134 | 0 | 76.0123309 | 0/0 | 0 | no |
| moderate_seed3301.txt | gcap_frontier_not_closed | no | 0.047141 | 0.0491525526647 | 0.0409246835758 | 300.5755767 | 4/2 | 2 | no |

Result: V12 M1, V12 M2, high_imbalance_seed3202, and tight_T_seed3101 certify under `paper-gf-compact-bc`. moderate_seed3301 remains noncertified at this bounded run with two unresolved leaves and gap about 0.0409.

## Cut Ablation Snapshot

| row | variant | status | LB | UB | gap | runtime_s | closed/timed out |
|---|---:|---:|---:|---:|---:|---:|---:|
| regen_candidate_V12_M2_average.txt | no_new_cuts | gcap_frontier_not_closed | 0.681921 | 0.718504070755 | 0.0509156068059 | 60.4934203 | 1/1 |
| regen_candidate_V12_M2_average.txt | all_safe_60s | gcap_frontier_not_closed | 0.692512 | 0.718504070755 | 0.0361752588648 | 60.5712398 | 1/1 |
| high_imbalance_seed3202.txt | no_new_cuts | gcap_frontier_not_closed | 1.631997 | 1.74931345205 | 0.067064282798 | 78.8647021 | 3/1 |
| high_imbalance_seed3202.txt | all_safe_600s | optimal | 1.74931345205 | 1.74931345205 | 0 | 293.4988343 | 0/0 |

The ablation is intentionally small. It shows short-budget rows with the new compact-BC cuts disabled remain open, while the full safe configuration certifies V12 M2 and high_imbalance_seed3202 at longer budgets. A full per-family ablation remains future work.

## Plain CPLEX Benchmark-Only Rows

| row | status | LB | UB | gap | runtime_s | nodes | verifier |
|---|---:|---:|---:|---:|---:|---:|---:|
| regen_candidate_V12_M1_average.txt | optimal | 0.357200583208 | 0.357200583208 | 0 | 128.2411592 | 224191 | yes |
| regen_candidate_V12_M2_average.txt | not_certified | 0.64378396605 | 0.718504070755 | 0.103993989382 | 300.1644599 | 626569 | yes |
| high_imbalance_seed3202.txt | not_certified | 1.196041412 | 1.76951964364 | 0.324086954162 | 300.5128798 | 28597 | yes |

These CPLEX rows are benchmark-only. Their incumbents/bounds are not imported into the compact-BC exact pipeline.

## Audit Status

- `audit_bpc_certificate.py --self-test`: passed.
- Certificate audit over `results/gf_compact_bc_round/raw`: `audited_rows=37 failures=0`.
- `certificate-basis-test`: passed (`diagnostic_passed`).
- `option-consistency-test` for `paper-gf-compact-bc`: passed (`diagnostic_complete`).
- Handling convention model-generation test: passed; aggregate handling row charges pickup variables only.

## Evidence Files

- `gf_compact_bc_summary.csv`: audited raw-result summary.
- `interval_leaf_status.csv`: interval and compact-BC leaf statuses.
- `model_strengthening_audit.csv`: cut counts and domain tightening by compact-BC model.
- `cut_family_ablation.csv`: small diagnostic ablation snapshot.
- `plain_cplex_comparison.csv`: CPLEX benchmark-only comparison.
- `command_manifest.csv` and `instance_manifest.csv`: command template and input hashes.
- `certificate_audit.csv`: full audit results.

## Remaining Bottlenecks

- moderate_seed3301 still has two timeout leaves at the bounded 300s/30s-per-leaf setting. The best bound is much stronger than earlier core-BPC rows, but not yet enough to certify in this run.
- The support-duration and transfer cuts are static. Dynamic root separation is scaffolded by options but not implemented as a callback-level branch-and-cut loop yet.
- Receiver-set source-cover cuts remain disabled/diagnostic until compatibility assumptions and tests are complete.

## Recommendation

The new mainline should be described as a Gini-frontier compact branch-and-cut/certification framework, not BPC. It is ready for a focused compact-BC cut-strengthening round on moderate_seed3301 and additional V20 rows, but not yet for broad benchmark claims until the moderate/tight remaining stress rows are reproduced at longer budgets and the cut ablation is expanded.

Final commit SHA: pending until commit.
