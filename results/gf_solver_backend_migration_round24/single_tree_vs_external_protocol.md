# Persistent single tree versus external multi-optimize protocol

The architecture comparison freezes the original compact objective, F0 rows, verified same-run HGA-TGBC incumbent semantics, improving Gini range, deterministic initial partition and split hierarchy, interval-row factory, parent-copy bound inheritance, one thread, exact-zero gaps, scheduler, finalization reserve, process-wall budget, and P1/P2/F3 off.

S0-SAFE is one CPLEX environment, problem, model read, presolve-off root, and `CPXmipopt` with continuous native Gini children. T-CPX-EXT-PON uses the same solver-neutral Gini geometry but creates static presolve-on interval models and may execute multiple independent `CPXmipopt` calls. Stage 1C preregistered T-CPX-EXT-POFF to isolate architecture under the same safe presolve-off settings. The known-unsafe presolve-on single-tree diagnostic can measure only speed/work and is never authoritative exact evidence.

For every matched row, reporting would compare optimize calls, distinct roots/presolve executions, cumulative root/presolve/model-build time, nodes/work, valid final LB under a frozen reporting-only common UB, common gap, normalized AUC, and threshold crossings. The Stage 0 Gurobi license failure blocked these official paired rows, so no performance effect is estimated in Round 24.
