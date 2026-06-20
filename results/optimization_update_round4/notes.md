# Round 4 Notes

## Scope

This round implements exactness-preserving support-duration and incumbent
pipeline improvements. It does not claim new V12 optimal certificates.

## Local Inputs

Runnable source files found for this pass:

- `testdata/examples/gcap_smoke_V4_M1.txt`
- `reference/regen_candidate_V12_M1_average.txt`
- `reference/regen_candidate_V12_M2_average.txt`

V8/V10 source text files were not present in this checkout. The search found
historical logs and result JSON files for V8/V10 but no runnable source `.txt`
inputs, so those cases were not rerun.

## Incumbent Audit

Best verified local seeds:

- V12 M1 average: compact-CPLEX seed, UB `0.366157179488`, LB
  `0.276814435880`, gap `0.244001070067`. This is a verifier-accepted upper
  bound only and should be labeled seeded/hybrid.
- V12 M2 average: BPC-owned portfolio/strong seed, UB `0.759438494406`, LB
  `0.589679023540`, gap `0.223532876088`.

Historical route-bearing V12 result files did not verify against the regenerated
local V12 inputs because of route-duration and station-capacity mismatches. They
were discarded as incumbents.

## Support-Duration And Route-Mask Results

The strengthened `ceil(|S|/2)` support-duration mechanism is implemented and
covered by diagnostics, but the real V4/V12 rows in this pass generated zero
support-duration cuts and removed zero route masks. The synthetic diagnostics in
`smoke_support-pruning-test.json` and `smoke_route-mask-support-test.json`
demonstrate cases where the old one-operation rule cuts nothing while the
strengthened rule cuts infeasible supports.

## Certificates

- V4 smoke remains certified by full BPC with objective/LB/UB `0`, gap `0`,
  verifier passed, and closed frontier ledger.
- V12 M1 and V12 M2 ablation rows remain noncertified. They are lower-bound and
  incumbent-quality diagnostics only.

## Error Capture

All smoke, incumbent-audit, and ablation commands exited with code `0`. Captured
logs were scanned for address/access-violation, segmentation, `bad_alloc`, and
out-of-memory signatures; none were found in this pass.

## CPLEX Use

Plain CPLEX benchmarks were not rerun in round four. CPLEX-backed code may still
be used internally by compact/compact-CPLEX incumbent seeding and by the
inventory/route/Gini relaxation when available. Compact/CPLEX seeds are upper
bounds only and are not BPC lower-bound evidence.

## Remaining TODOs

- Add compatible V8/V10 source instances or regenerate them for the current
  parser before running a full target-instance ablation.
- Investigate stronger V12 lower bounds; support-duration pruning did not affect
  the real regenerated V12 masks.
- Implement an exact support-feasibility oracle only if it can prove support
  infeasibility without heuristic failure or timeout.
