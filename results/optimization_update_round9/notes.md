# Round 9 Notes

Scope: inventory branching, operation-mode branching, focus-range targeting, compatible focus-bound import, and V12 critical-interval diagnostics.

No positive-gap result is reported as optimal. Focus-only interval rows have diagnostic scope only. Imported focus bounds are lower-bound ledger evidence only and do not certify the original problem by themselves.

## Main Outcomes

- V4 `gcap-frontier` remains certified with objective `0` and gap `0`.
- V12 M2 focus-only `[0.465922,0.512514]` improved the interval LB from `0.496993274667` to `0.689652394993` but did not close the interval.
- V12 M1 focus-only `[0.230364,0.276436]` improved the interval LB from `0.234802392857` to `0.330637007941` but did not close the interval.
- V12 M2 full frontier with imported focus bound accepted one imported interval bound and ended at UB `0.719065249476`, LB `0.712948394993`, gap `0.00850667514168`, one unresolved interval, and no certificate.
- V12 M1 full 300s ended at UB `0.369698924539`, LB `0.282149235152`, gap `0.236813481393`, two unresolved intervals, and no certificate.

## Branching

Final-inventory branching created nodes on the V12 focus runs and generated V8 engineering run. Operation-mode branching is implemented and smoke-tested; it did not become the selected branch in the V12 focus rows. The `strong` mode is currently a bounded scoring selector, not full child-LP strong branching.

## Generated V8/V10

Generated V8/V10 inputs under `reference/generated/` were rerun for 60s. All four completed without process errors and remained positive-gap diagnostics under this short budget. They are deterministic engineering benchmarks, not historical paper targets.

## Error/Memory Scan

All round-nine logs were scanned for address/access-violation, segmentation, `bad_alloc`, out-of-memory, `fatal`, and related patterns. No matches were found.

## CPLEX

Plain CPLEX benchmarks were skipped in this pass. No CPLEX speedup claims are made. Compact/seed behavior remains UB-only when used by incumbent selection.

## Limitations And TODOs

- Run V12 M2 focus-only and imported full-frontier 1200s commands during a longer unattended slot.
- Replace the bounded `strong` branch selector with true child-LP/CG strong branching if runtime permits.
- Add stricter compatibility hashing for imported interval-bound reuse across independent runs.
- Investigate the post-import V12 M2 leaf `[0.489218,0.512514]`, which controls the remaining full-frontier gap.
- Operation-mode pruning counters currently report zero label/column pruning; the restrictions are enforced, but detailed pruning attribution remains a TODO.
