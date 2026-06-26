# Exact-Phase UB Improvement Audit

UB event tracing was added through `--ub-event-log`. Every accepted verified
incumbent writes:

- event time;
- source;
- objective, G, and P;
- improvement over previous UB;
- route/operation totals;
- verifier status;
- paper-reproducibility flag;
- lower-bound contribution flag, always `false`.

The controlled weak-UB V12 M2 run started from greedy UB
`0.789342396801`. The newly added local re-decode repair found and verified
UB `0.718504070755`; the full frontier then certified the same value. This
demonstrates that the exact run can improve a deliberately weak initial UB
without using arbitrary archive scanning.

For V12 M1 and the V20/M3 stress set, UB did not improve after the strong native
HGA-TGBC initial incumbent. The evidence points to lower-bound closure rather
than missing short primal moves.
