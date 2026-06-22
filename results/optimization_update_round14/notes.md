# Round 14 Notes

Scope:

- This pass is stacked on the unmerged `production-hybrid-pricing-bpc` branch.
- It adds two-track column metadata and reporting:
  `elementary_feasible` for original feasible columns, and
  `ng_relaxed_lower_bound` for lower-bound-only relaxed columns.
- Relaxed columns are excluded from route-pool incumbent insertion, route-pool
  DFS selection, route export, and BPC leaf route reconstruction.
- Current relaxed columns are a conservative safe partial implementation:
  they are generated only from verified elementary projections. Non-elementary
  relaxed route projections are still rejected until projection feasibility is
  fully certified.

Build:

- `cmake` was unavailable.
- Fallback `g++` builds succeeded for `build/ExactEBRP.exe` and
  `build/ExactEBRPCompare.exe`.

Safety checks:

- V4 `gcap-frontier` remains certified with objective `0` for both
  exact-label and two-track hybrid.
- No positive-gap V12 or large-instance row is marked optimal.
- `relaxed-column-incumbent-safety-test` passed after confirming that a
  synthetic relaxed column is excluded from the route-pool incumbent master.
- The round-fourteen logs were scanned for access violation, segmentation
  fault, AddressSanitizer, out-of-memory, `bad_alloc`, and fatal
  `ExactEBRP error` signatures; none were found.

Main observations:

- V12 M2 full 300s improved its reported lower bound from exact-label
  `0.684003547210` to two-track hybrid `0.710571053706`, but the frontier
  remains open and noncertified.
- V12 M2 focus `[0.489218,0.512514]` matched exact-label and two-track
  lower bounds at `0.712948394993`; both remain noncertified.
- V12 M1 full 300s changed slightly from exact-label `0.337454471060` to
  two-track `0.337666891430`; both remain noncertified.
- V20 generated two-track frontier 300s ran and remained nonclosed.
- V50/V100 relaxed-RMP diagnostics ran without crashes. The movement-projection
  fallback produced values above the verified empty-route UB on these generated
  instances, so those bounds were rejected and the rows remain diagnostic with
  LB `0`.

Certificate notes:

- `relaxed_rmp_certificate_valid=false` for all large and V12 round-fourteen
  relaxed rows because ng-relaxed pricing did not close.
- Relaxed RMP rows are useful diagnostics but are not original-problem
  certificates unless the relaxed pricing problem closes and the full frontier
  ledger satisfies the standard certificate protocol.
- Plain CPLEX was skipped; no CPLEX speedup or certificate comparison is made.

Raw data:

- JSON: `results/optimization_update_round14/raw/`
- Logs: `logs/optimization_update_round14/`
- Summaries: `results/optimization_update_round14/*.csv`
