# Round-Five Notes

## Scope

Implemented and tested:

- Executed focused min-LB frontier retry.
- Frontier route-column pool with a true-objective restricted incumbent master.
- Interval candidate audit under the original objective.
- Pickup-drop compatibility flow relaxation.
- New JSON/CSV fields for focused retry, route-pool incumbents, interval candidates, and compatibility-flow statistics.

Not implemented in this pass:

- Full HGA/TGBC metaheuristic import.
- Exact support-feasibility oracle cuts beyond the existing disabled switch.
- Frontier column cache.

## Build

CMake was not available. Both executables were rebuilt with the fallback `g++`
commands in `commands.md`.

## Available Inputs

Runnable local source text inputs found for this pass:

- `testdata/examples/gcap_smoke_V4_M1.txt`
- `reference/regen_candidate_V12_M1_average.txt`
- `reference/regen_candidate_V12_M2_average.txt`

V8/V10 source text files were not present in the checkout. Historical V8/V10
logs and result JSON files exist, but they were not rerun for round five.

## Safety Checks

All smoke, V12 ablation, and V12 incumbent-audit commands exited with code `0`.
Captured logs were scanned for memory/address signatures and none were found.
The exit-code files are:

- `logs/smoke_exit_codes.txt`
- `logs/ablation_v12_exit_codes.txt`
- `logs/incumbent_exit_codes.txt`

V4 `gcap-frontier` remains an original-problem BPC certificate with
`status=optimal`, objective/LB/UB `0`, `gap=0`, `unresolved_intervals=0`,
`open_nodes=0`, and `verifier_passed=true`.

## V12 Summary

Round-five V12 ablations remain noncertified.

| Instance | Best short ablation UB | Best short ablation LB | Gap | Notes |
|---|---:|---:|---:|---|
| V12 M1 average | 0.382683045935 | 0.258804234390 | 0.323711261476 | Focused retry executed in focused rows but made no valid LB progress. |
| V12 M2 average | 0.759438494406 | 0.587614408090 | 0.226251483934 | Focused retry executed in focused rows; the 120s row produced a weaker final ledger LB. |

Best incumbent-audit rows:

- V12 M1 average: BPC-owned `local`, `pool`, `portfolio`, and `strong` modes reached UB `0.369698924539`.
- V12 M2 average: BPC-owned `strong` and `portfolio` modes reached UB `0.759438494406`.

The route-pool incumbent master found verified restricted-pool incumbents but did
not improve the best V12 incumbent seeds. It is reported as UB-only diagnostic
evidence.

The pickup-drop compatibility flow found zero incompatible station pairs on both
regenerated V12 instances. Therefore it added audit structure but did not
strengthen the lower bound on these rows.

Plain CPLEX benchmarks were skipped in this pass. CPLEX-style compact seeds are
only labeled upper-bound sources and not BPC certificates.
