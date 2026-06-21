# Round 7 Notes

Implemented and tested:

- True progress checkpoint logging with an initial empty-incumbent row, interval relaxation/tree rows, adaptive split rows, focused-intensification rows, route-pool rows, and final summary rows.
- Adaptive Gini-frontier splitting of unresolved global-min-LB leaf intervals.
- Mask-specific route operation-budget cuts in the route-mask relaxation using non-overestimating depot-cycle lower bounds.
- Focused intensification integration with adaptive child split processing and operation-budget metadata.
- CSV/JSON reporting for adaptive split, operation-budget, focused split, and progress fields.

Safety observations:

- V4 gcap-frontier remains certified with objective 0 and gap 0.
- V12 M1 and V12 M2 remain noncertified; all positive-gap rows are reported as `gcap_frontier_not_closed` and `certified_original_problem=false`.
- No tested log contained address-sanitizer, access-violation, segmentation, `bad_alloc`, out-of-memory, or Windows STATUS_ACCESS_VIOLATION signatures.
- CPLEX plain benchmark was skipped in this pass; no CPLEX speedup claims are made.

Main V12 observations:

- V12 M1 300s improved_full final: UB 0.366563817616, LB 0.27908220858, gap 0.238653148053. Adaptive splitting created child intervals but did not close the frontier.
- V12 M2 300s improved_full final: UB 0.719065249476, LB 0.59572506958, gap 0.171528494787. Operation-budget cuts and adaptive splitting improved the valid lower bound relative to the 60s baseline.
- 1200s rows were not run locally because smoke plus V12 60s/300s runs consumed about 31 minutes; reproduction commands are in `commands.md`.

Remaining TODOs:

- Run the prepared 1200s commands on a longer unattended machine slot.
- Investigate why V12 M1 operation-budget cuts slightly weaken the solved time-limited relaxation bound in short runs; the result keeps valid lower bounds only and does not certify.
- Strengthen the route-mask relaxation beyond operation budgets, likely with vehicle-indexed operation/linking rows or exact support feasibility cuts.
- Add a deterministic benchmark for adaptive split depth/factor sensitivity.
