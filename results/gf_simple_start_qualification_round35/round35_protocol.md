# Round 35 frozen protocol

## New solver rows

The only executable arm is `C6-SIMPLE-START`: the existing deterministic
three-mode greedy constructor, independent candidate verification, and the
unchanged C6 exact framework. Stage `matrix1800` contains the 35 Round 32
primary instances at a 1,800-second process cap. Stage `v50_3600` contains 12
fresh independent V50 processes at 3,600 seconds. Stage `repeat` contains two
V20 rows at 1,800 seconds and one V50 row for each of M=2,3,4 at 3,600
seconds. There is no continuation or solver-state resume.

All commands use Gurobi 13.0.2, Seed 0, one thread, a 15-second orderly
shutdown margin, and a watchdog separated from the nominal process cap by 90
seconds. Startup, verification, model construction, exact search, and final
certification are included in process-entry wall time.

## Frozen exact contract

Four initial intervals, all 15 strengthening families, complete LPs,
best-bound scheduling, launch-frozen next-frontier targets, requeue, lazy
child lookahead, `rho=0.01`, midpoint splitting, depth 8, width `1e-4`, atomic
coverage replacement, exact closure, and strict original-problem
certification are unchanged. Round 35 adds no C7 and no algorithm mechanism.

## Historical comparison

The Round 32 C6-FROZEN and P-GRB rows are never rerun. Compatibility requires
instance hash and dimensions, nominal/process budget, Gurobi 13.0.2,
one-thread execution, compatible C6/plain contract, process-entry timing, and
strict-certificate semantics. Incompatible comparisons are reported as
unavailable rather than substituted.

The predeclared repeat set balances V20 high/tight and V50 M2/M3/M4 before
Round 35 performance is observed. Performance does not dispatch startup by
instance. Qualification is decided only after correctness, full-matrix,
long-V50, repeatability, and structural interaction audits.
