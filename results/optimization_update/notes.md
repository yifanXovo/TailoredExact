# Optimization Update Notes

Date: 2026-06-20.

## Implemented

- `ColumnPool` closed route-load projection dominance.
- `--column-dominance` and `--column-dominance-mode`.
- Dominance-filtered multi-column pricing insertion for `gcap-cg`, `gcap-tree`, and `gcap-frontier`.
- Dominance compression for verified route-column incumbent pools.
- Inventory-ratio projection lower bound.
- Incumbent penalty-budget inventory-domain tightening.
- JSON and comparison CSV statistics for dominance, projection bound, penalty tightening, and filtered pricing.
- Proof documentation in `docs/optimization_proofs.md`.

## Certificate Status

- V4 smoke frontier with full options certified the original problem: `results/optimization_update/raw/ablation_v4_full.json`, objective `0`, gap `0`, verifier passed.
- The V12 M1 average 60s stress smoke did not certify: `results/optimization_update/raw/stress_v12_m1_average_full_60s.json`, UB `0.393080018005`, LB `0`, gap `1`, verifier passed. This is correctly reported as noncertified.

No new V10/V12 paper target certificate was claimed in this update pass.

## Skipped Or Limited

- CMake build was skipped because `cmake` is not installed; the fallback `g++` build succeeded.
- Plain CPLEX benchmark comparisons were not rerun in this update pass. Existing CPLEX result artifacts remain unchanged.
- `--frontier-column-cache` is accepted and logged, but the cache is not enabled for certificate-producing runs. It remains a TODO.
- Exact route-support infeasibility cuts and HGA/TGBC incumbent import are documented future work and were not implemented in this pass.

## Summary Tables

- `results/optimization_update/ablation_summary.csv`
- `results/optimization_update/before_after_summary.csv`

