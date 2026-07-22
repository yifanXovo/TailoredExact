# Round 28 frozen protocol

## Scope and arms

Round 28 qualifies C3-REPLICA as an algorithm-level external-Gurobi migration
of corrected S0/F0. It does not alter or promote the default stable mainline.

- P-GRB: frozen one-thread complete compact Gurobi MIP, seed 0, automatic
  presolve, exact zero gaps, no HGA, decomposition, or tailored information.
- S0-CPLEX: frozen corrected stable CPLEX paper mainline.
- C2-PAPER: frozen Round 27 child-LP-lookahead external Gurobi arm.
- C3-REPLICA: this branch's distinct
  `--external-gini-scheduling cplex-algorithm-replica` arm.

C0 remains immutable historical evidence and is not run in the official Round
28 matrices.

## Frozen C3 parameters

- One solver thread; Gurobi seed 0; Gurobi presolve automatic/default.
- Exact relative and absolute MIP gaps zero.
- HGA seed 20260626; generation-stagnation stop after 2,000 consecutive
  completed generations without strict global-best fitness improvement; no
  active HGA wall-time stop.
- Complete improving range; 4 equal initial intervals represented by recursive
  root breakpoint branching; binary splits; adaptive maximum depth 8 after
  initial partition; minimum width `1e-4`.
- F0 `round20-current`; six accepted global and nine accepted interval-local
  row families; verified-incumbent cutoff epsilon zero.
- Best-bound leaf selection with tie order: lower bound, smaller width, greater
  depth, lower endpoint, upper endpoint, leaf ID.
- Unconditional eligible structural split; child LPs are deferred ordinary
  best-bound leaves; no child-benefit gate.
- At most one complete LP event per leaf and one exact terminal MIP event per
  terminal leaf. No per-leaf time, Work, node, solution, attempt, or retry
  control; no warm start or incremental optimization.
- The remaining overall process deadline is the only native interruption
  limit. Official process-wall cap: 300 seconds.

These parameters, command construction, instance membership, and tie rule are
frozen before the first official Stage 2 result. No performance-driven changes
are permitted afterward.

## Frozen instances

The primary matrix contains 17 non-sentinel instances: V12_M1, V12_M2;
high_imbalance_seed3202, moderate_seed3302, tight_T_seed3101;
high_imbalance_seed4201, moderate_seed4302, tight_T_seed4101;
high_imbalance_seed5202, high_imbalance_seed5203, moderate_seed5301,
moderate_seed5302, tight_T_seed5102, tight_T_seed5103;
high_imbalance_seed6202, moderate_seed6301, tight_T_seed6102.
moderate_seed4301 is correctness-only.

Every runner verifies path, byte count, and SHA-256 against the frozen Round 28
manifest and the retained authoritative hash before launching a solver.

## Serial stages

- Stage 0: clean CPLEX-only and Gurobi-enabled release builds; all C++ and
  Python regressions; static forbidden-logic/equivalence audits; 54 direct C3
  checks; exact toy P/S0/C3; moderate4301 P/S0/C2/C3 sentinel.
- Stage 1: toy, V12_M1, V12_M2, high_imbalance_seed3202, and the sentinel with
  S0 and C3 for mechanical equivalence.
- Stage 2: every one of the 17 non-sentinel instances with P-GRB and C3,
  producing 34 official rows.
- Stage 3: V12_M1, V12_M2, high_imbalance_seed3202, moderate_seed3302, and
  tight_T_seed3101 with S0, C2, and C3. Exact-identical Stage 2 P rows may be
  referenced but are not substitutes for the requested three arms.
- Stage 4: two additional C3 repetitions each on V12_M2,
  moderate_seed3302, and moderate_seed6301.

All runs are serial. Failed, interrupted, or emergency-terminated rows remain
in place and are never silently replaced. Diagnostics, if any, receive a
separate non-official label.

## Comparison and classification

Comparisons use a common independently verified UB, valid global lower-bound
trajectories, common-gap AUC, and threshold crossing. Relative gaps computed
from different incumbents are not the primary metric. The final classification
is exactly one of the five labels authorized by the Round 28 request. A
positive result does not promote C3; it only supports later long validation
and possible incremental-optimization research.
