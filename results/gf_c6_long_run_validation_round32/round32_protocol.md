# Round 32 frozen protocol

Round 32 validates the mathematically frozen Round 31 C6 algorithm. It does
not develop C7 and does not change leaf selection, native targets, requeue,
lazy child lookahead, split decisions, exact closure, interval geometry,
strengthening rows, rho, HGA, or exactness semantics.

## Frozen arms

- `P-GRB`: compact original MILP, Gurobi 13.0.2, one thread, Seed 0,
  automatic presolve, zero relative and absolute MIP gaps, no HGA.
- `C6-FROZEN`: selector `round31-nonblocking-native-bound`, lifecycle
  `round31-open-native-bounded`, one-thread Gurobi, four initial intervals,
  parent-native-first scheduling, one launch-frozen strictly higher
  next-leaf target with ties ignored, valid partial-bound requeue, lazy child
  LPs, current normalized child-gain rho 0.01, no mandatory target split,
  exact closure after no unused milestone, depth 8, width 1e-4, unchanged
  six global and nine interval-local row families, unchanged HGA.
- `C5-REFERENCE`: frozen Round 30 C5, limited diagnostic only.
- `S0-CPLEX`: unchanged accepted CPLEX S0/F0 mainline, contextual only.

## Timing and runner

Every official row is serial and independent. The nominal and process caps
are 1,800 or 3,600 seconds. The fixed shutdown margin is 15 seconds. The
runner watchdog is separated from the process cap by 90 seconds. Completion
is an atomic checksum-bearing marker written only after process exit, result
JSON parse and flush verification, required trace checks, and artifact
inventory. Resume skips only checksum-valid complete rows. Incomplete or
invalid rows are preserved under `invalidated_rows/` with an explicit
invalidation record before a fresh uniform rerun. This is experiment-row
resume, never native solve-state resume.

## Frozen matrices

Stage 1 is 23 retained authoritative instances by P-GRB and C6 at 1,800s
(46 rows). Stage 2 is 12 deterministic V20/V50, M2/M4, Q30 qualification
instances by both arms at 1,800s (24 rows). Stage 3 is the predeclared 12
V50 instances by both arms in independent 3,600s runs (24 rows). Stage 4 is
eight predeclared instances by C5 and C6 at 1,800s (16 rows). Stage 5 is
seven predeclared S0 anchors at 1,800s. Repeatability independently repeats
both primary arms on eight predeclared instances at 1,800s (16 rows).

All primary comparisons require the same instance, nominal budget, solver
version, executable, machine, and independently verified common UB. Metrics
are strict certification/time/work, valid LB, verified UB, common-UB gap,
observed proof AUC without interpolation or endpoint extension, time and work
to fixed common-gap thresholds, final-gap and AUC wins/losses/ties at stated
tolerance, and family/V/M/VxM summaries. Time-limited valid rows are retained.

Historical Round 31 rows are derived context only and never official Round 32
rows. No instance, comparison rule, or algorithm setting may change after
official execution begins. A general bug requires retaining and invalidating
all affected rows, rebuilding and rehashing, and uniform rerun.
