# Round 10 Notes

Implemented:

- Strict pricing-closure semantics: incomplete pricing or remaining negative reduced cost now reports `pricing_closure_certified_exact=false`.
- Frontier interval state export/resume metadata with compatibility checks. Open nodes are not serialized in this build; resume rebuilds the interval tree from compatible metadata and generated column counts.
- Exact-CG continuation controls for unresolved focus intervals.
- Dual-stabilization CLI/reporting. For certificate safety, this pass records smoothing requests but uses true-dual pricing; stabilization remains a documented acceleration TODO.
- V12 M1 focus-bound import accounting.

Safety checks:

- All smoke commands exited 0.
- V4 gcap-frontier remains certified with objective 0.
- No logs in `results/optimization_update_round10/logs` matched memory/address failure patterns: access violation, segmentation fault, address, memory, bad_alloc, fatal, or Windows access-violation codes.
- No positive-gap V12 run is marked optimal.

Main outcomes:

- V12 M2 exact-CG focus `[0.489218,0.512514]` reached LB `0.712948394993`, UB `0.719065249476`, gap `0.00850667514168`, but pricing closure remained `pricing_time_limit`.
- V12 M2 resume from exported state loaded the compatible interval state and reproduced the same LB/UB/gap; no additional closure occurred.
- V12 M2 full frontier with imported focus bound accepted the import but remained noncertified, with remaining negative reduced cost reported.
- V12 M1 full frontier accepted the round-nine focus bound. The imported interval bound is present, but other intervals still control the global minimum lower bound.

CPLEX:

- Plain CPLEX benchmarks were skipped in round ten. This pass focused on BPC pricing-closure semantics and interval continuation.

TODO:

- Serialize true open BPC node state, not just compatible interval metadata and generated-column counts.
- Implement actual dual stabilization for column discovery, with exact true-dual final pricing verification.
- Run 1200s V12 M2 exact-CG and full-frontier import/resume rows when local wall-clock budget allows.
- Continue closure work on the remaining V12 M2 unresolved interval; current blocker is exact pricing/tree closure, not incumbent availability.
