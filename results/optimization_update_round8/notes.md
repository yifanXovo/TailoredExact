# Round 8 Notes

## Implemented

- Vehicle-indexed operation relaxation in the inventory/route-mask/Gini bound:
  service variables `y_{k,i}`, vehicle pickup/drop variables, station
  disjointness, vehicle balance, depot-return capacity, and mask operation
  budgets.
- Vehicle-indexed pickup-drop transfer flow linked to route masks with safe
  duration/capacity transfer caps.
- Focus-only interval diagnostic mode with explicit
  `diagnostic_interval_only` certificate scope.
- Deterministic generator for missing V8/V10 parser-compatible engineering
  benchmarks.
- Reporting predicate fix for bound-fathomed frontier certificates: branch-price
  exact-pricing closure is required only when a branch-price tree contributes to
  the certificate; bound-fathomed certificates remain subject to full frontier,
  gap, verifier, unresolved-interval, invalid-interval, and open-node checks.

## Main Results

| Instance | Row | UB | LB | Gap | Runtime (s) | Certified? |
|---|---|---:|---:|---:|---:|---|
| V12 M1 average | improved_full_300s | 0.368581603155 | 0.284563809518 | 0.227948961416 | 305.53 | no |
| V12 M2 average | improved_full_300s | 0.719065249476 | 0.689651961258 | 0.040904894569 | 295.71 | no |
| V12 M2 average | improved_full_1200s | 0.719065249476 | 0.689651961258 | 0.040904894569 | 1119.94 | no |

The V12 M2 1200s run did not improve beyond the 300s row. It is useful
convergence evidence but remains noncertified due to a positive gap and
unresolved frontier interval.

## Focus-Only Diagnostics

| Instance | Focus interval | Interval range | LB before | LB after | Closed? | Scope |
|---|---:|---|---:|---:|---|---|
| V12 M1 average | 0 | [0,0.184291] | 0.00515451203429 | 0.368581603155 | true | diagnostic_interval_only |
| V12 M2 average | 0 | [0,0.372737] | 0.0655870045173 | 0.745474506024 | true | diagnostic_interval_only |

Closing the selected interval does not certify the original problem because the
complete frontier is not closed.

## Generated V8/V10 Engineering Benchmarks

Historical runnable V8/V10 text files were not found. The generated cases are
deterministic engineering benchmarks only.

| Generated instance | Status | Objective | LB | UB | Gap | Time (s) | Certified? |
|---|---|---:|---:|---:|---:|---:|---|
| regen_V8_M2_average.txt | gcap_frontier_not_closed | 0.083892899793 | 0.083198612140 | 0.083892899793 | 0.008275880968 | 58.10 | no |
| regen_V10_M1_average.txt | gcap_frontier_not_closed | 0.718440682126 | 0.689582781094 | 0.718440682126 | 0.040167409433 | 56.87 | no |
| regen_V10_M2_average.txt | optimal | 0.060127095731 | 0.060127095731 | 0.060127095731 | 0 | 23.21 | yes |
| regen_V10_M2_low.txt | optimal | 0.163171713361 | 0.163171713361 | 0.163171713361 | 0 | 23.54 | yes |

## Safety

- V4 `gcap-frontier` remained certified with objective `0`, gap `0`, and
  `certified_original_problem=true`.
- No positive-gap run is labeled optimal.
- CPLEX plain benchmark was skipped, so no CPLEX speedup is claimed.
- Logs under `logs/optimization_update_round8/` were scanned for
  AddressSanitizer, access violation, segmentation, `bad_alloc`, out-of-memory,
  `-1073741819`, `3221225477`, and STATUS_ACCESS_VIOLATION signatures; no
  matches were found.

## Files

- Raw JSON: `results/optimization_update_round8/raw/`
- Logs: `logs/optimization_update_round8/` and committed copies under
  `results/optimization_update_round8/logs/`
- Summaries: `results/optimization_update_round8/*.csv`
- Generated inputs: `reference/generated/`
- Generator manifest: `reference/generated/manifest.csv`

## TODO

- Run V12 M1 improved_full_1200s during a longer local slot.
- Diagnose the V12 M2 bound plateau between 300s and 1200s.
- Compare generated V8/V10 files against historical inputs if those source
  files are recovered.
- Implement exact small-support feasibility cuts only if the oracle proves
  infeasibility; heuristic failures remain unusable.
