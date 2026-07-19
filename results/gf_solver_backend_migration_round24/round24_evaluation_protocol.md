# Round 24 preregistered evaluation protocol

This protocol is frozen before any Round 24 candidate performance result. Round 24 is not a promotion round. Corrected CPLEX S0/F0 remains the stable paper mainline for every outcome.

## Uniform solver policy

Every native solve uses one thread. P-CPX is the complete original compact model with CPLEX presolve on and no HGA or known UB. P-GRB reads the identical canonical LP bytes, uses Gurobi Presolve `-1`, Seed `0`, MIPGap `0`, and MIPGapAbs `0`, and receives no HGA or known UB. Tailored arms use only a same-run independently verified HGA-TGBC incumbent and the same objective cutoff, Gini range, binary split hierarchy, F0 rows, interval-row factory, parent-bound inheritance, scheduler, and process deadline.

The external-tree Gurobi cold and warm arms both retain an unchanged model per leaf if the lifecycle gate passes. The warm arm alone explicitly submits a complete, independently verified same-run start to compatible newly created leaves. A start is never a bound, closure, or native-tree inheritance mechanism.

The CPLEX presolve-on single-tree arm is always labeled **known-unsafe presolve-on single-tree diagnostic**. Its native model configuration is invalid for original-problem certification and no status or bound is authoritative exact evidence.

## Fixed instances and budgets

- Correctness sentinel: `moderate_seed4301`, six arms, 120 seconds each.
- Resume/warm gate: `V12_M2`, fresh-cold, retained-cold, retained-warm, 120 seconds each.
- Safe architecture ablation: `V12_M1` and `V12_M2`, S0-SAFE versus external CPLEX presolve-off, 180 seconds each.
- Performance matrix: exactly `V12_M1`, `V12_M2`, `high_imbalance_seed3202`, and `tight_T_seed3101`, crossed with the seven frozen Stage 2 arms, 300 seconds each.

No instance or arm may be replaced after observing a result, and no selected run may be extended. All HGA, model construction, native solves, logging, and finalization count against process wall. Matched arms use the same finalization reserve. Runs are serial on this host.

## Blocking Stage 0 gates

Both clean build configurations, all C++ and Python tests, local Gurobi license smoke, canonical model equivalence, toy exact solves, exhaustive external-tree checks, status/certificate checks, lifecycle checks, and static dispatch scans must pass before official performance. A missing Gurobi license is a blocking failure, not a reason to substitute another solver or invent rows. If the license remains unavailable, every performance row is recorded as unavailable/excluded and no Stage 1/2 process is launched.

The local audit already observed Gurobi error 10009 with no standard license file or configured license environment. That observation occurred before implementation and contains no candidate performance information; the Stage 0 gate remains frozen as written.

## Comparison-only bounds

The common UBs in `round24_comparison_ub_manifest.csv` come from immutable retained evidence and are used only after a run to compute reporting gaps, AUC, and threshold crossings. They enter neither a plain nor a Tailored solve.

## Decision hierarchy

For correctness-valid arms: strict original-problem certificate; then process-wall time among strict rows; otherwise valid final LB, common-UB gap, AUC, and threshold crossings. The known-unsafe CPLEX diagnostic is excluded from that hierarchy. The permitted classifications and paired views are exactly those in the Round 24 request; no post-result rule or arm is added.
