# Heuristic / Relaxation / Dataset Round Final Report

Implementation commit SHA before report finalization: 2b3729bb1d1badf89e85748e136254a488f8b1aa

Final pushed branch-tip SHA: see final response or run `git rev-parse HEAD` after pull; a committed file cannot stably contain its own content hash.

## Code Changes

- Added a reproducible paper primal heuristic UB path (`--primal-heuristic none|greedy|hga-tgbc|best-of-all`) and a standalone `--method primal-heuristic` exporter.
- Changed `paper-bpc-core`, `paper-exact-portfolio`, and `paper-bpc-experimental` defaults so arbitrary incumbent archive scanning is disabled unless explicitly requested.
- Added UB provenance fields: `incumbent_source_category`, `incumbent_source_is_paper_reproducible`, and `incumbent_source_contributes_lower_bound`.
- Extended C++ and Python certificate guards so incumbent sources cannot be treated as lower-bound evidence.
- Added no-operation-budget-first relaxation ordering: if the valid no-budget relaxation cutoff-fathoms an interval, the harder operation-budget relaxation is skipped.
- Added deterministic capacity/inventory variant generator: `scripts/generate_capacity_inventory_variants.py`.

## Migrated / Implemented Heuristic Components

The implemented `hga-tgbc` mode is a clean paper-facing derivative: seeded randomized route construction, route-load decoding, and local improvement over complete verifier-checked route plans. Debug outputs, old benchmark loops, and unrelated HybridGA scaffolding were not migrated.

## UB Source Comparison

| instance | row | source | status | UB | LB | gap | certified |
|---|---|---|---|---:|---:|---:|---|
| V12 M2 | empty 120s | empty | gcap_frontier_not_closed | 1.00822320985 | 0.522037873005 | 0.482219941077 | False |
| V12 M2 | explicit heuristic 120s | explicit_incumbent_json | gcap_frontier_not_closed | 0.756165366387 | 0.476385670531 | 0.369998029918 | False |
| V12 M2 | diagnostic archive 120s | diagnostic_archive | gcap_frontier_not_closed | 0.719065249476 | 0.692627421486 | 0.036766938758 | False |
| V12 M2 | paper heuristic 300s | primal_heuristic | gcap_frontier_not_closed | 0.756165366387 | 0.68873937145 | 0.0891683194372 | False |
| V12 M1 | paper heuristic 300s | primal_heuristic | gcap_frontier_not_closed | 0.364375057616 | 0.354350322125 | 0.0275121342176 | False |

The diagnostic archive incumbent remains stronger on V12 M2 (`0.719065249476`) than the new heuristic incumbent (`0.756165366387`). Archive rows are not paper-core default evidence.

## Relaxation Optimization

The tested V12 paper-heuristic rows are bound-time dominated and have zero pricing time. The no-operation-budget-first ordering is certificate-safe and avoids harder operation-budget MIPs when the weaker valid relaxation already cutoff-fathoms an interval. Summary: `results/relaxation_optimization_round/summary.csv`.

## Generated Dataset Summary

- Generated variants: 12 under `reference/generated_variants/`.
- Paper-core 60s rows run: 10.
- Certified generated variant rows: 5.
- Noncertified generated variant rows: 5.
- Manifest: `reference/generated_variants/manifest.csv`.

## Audit Status

- `results/heuristic_relaxation_dataset_round/certificate_audit.csv`: 20 rows, 0 failures.
- `results/generated_variant_round/certificate_audit.csv`: 22 rows, 0 failures.
- V4 paper-core remains certified at objective `0`.

## CPLEX Benchmark Evidence

A V4 CPLEX/compact availability probe certified objective `0`. Full CPLEX rows for every generated variant were skipped to keep this round bounded; see `results/generated_variant_round/skipped_runs.csv`.

## Remaining Bottlenecks

- The paper heuristic UB is weaker than the best diagnostic archive incumbent on V12 M2, so the regenerated V12 rows do not close under the new paper-core default in the short reruns.
- The current bottleneck remains relaxation/cutoff proof time for V12 paper-heuristic runs; pricing time is zero in these rows.
- The next optimization should strengthen the reproducible HGA/TGBC-style primal heuristic toward the archived V12 M2 UB while preserving verifier-gated exports.

## Key Paths

- Commands: `results/heuristic_relaxation_dataset_round/commands.md`
- Heuristic round summary: `results/heuristic_relaxation_dataset_round/summary.csv`
- Incumbent dependence: `results/primal_heuristic_round/incumbent_dependence_summary.csv`
- Relaxation summary: `results/relaxation_optimization_round/summary.csv`
- Generated variant summary: `results/generated_variant_round/summary.csv`
- Variant performance by base: `results/generated_variant_round/variant_performance_by_base.csv`
