# Round 27 frozen evaluation protocol

This protocol was fixed before any Round 27 performance run. It evaluates one
uniform paper-compatible candidate and does not tune after seeing results.

## Arms

`P-GRB` is the complete original compact MILP, Gurobi 13.0.2, one thread,
Presolve automatic, Seed 0, exact-zero relative and absolute MIP gaps, and no
HGA, Tailored, cutoff, warm-start, or external information.

`C0-LEGACY` is the byte-identical frozen Round 26 cold external-Gurobi
executable. It uses a 10-second HGA, 30/60/120/... second leaf quanta, and
splits after two unresolved attempts. It is a historical efficiency reference
and is explicitly non-paper-compatible.

`C2-PAPER` changes only the two scheduling mechanisms required by Round 27.
It uses HGA Seed 20260626 and stops after exactly 2,000 consecutive completed
generations without strict global-best fitness improvement. Wall time is
telemetry only in the HGA loop. Its external tree uses four initial intervals,
midpoint binary splits, maximum depth 8, minimum width 0.0001, unchanged static
F0 interval models, parent-bound inheritance, verified cutoff, one Gurobi
thread, Presolve automatic, and Seed 0. It has no warm start.

For each selected C2 leaf, the complete LP relaxation is solved to LP
optimality. If structurally eligible, both midpoint-child LPs are solved to LP
optimality. The parent is atomically replaced exactly when a child LP is
infeasible or the minimum finite feasible child LP bound exceeds the parent LP
bound by more than the existing certificate tolerance. Otherwise the parent
is terminal and its complete interval MIP is optimized exactly once until
native optimality, native infeasibility, or the overall process deadline. A
global-deadline interruption stops the complete external algorithm and leaves
the interrupted leaf open. The next leaf after a completed terminal MIP is
chosen by the unchanged global best-bound ordering.

C2 has no per-leaf TimeLimit other than the remaining overall process deadline
used solely to stop the complete run; no WorkLimit, NodeLimit, SolutionLimit,
quantum, attempt, or retry rule; no same-leaf restart; no instance-, family-,
seed-, size-, path-, performance-, or known-optimum dispatch; no fallback or
portfolio; and no performance-tuned split tolerance.

## Correctness gate (Stage 0)

Performance is blocked unless clean isolated release builds succeed with and
without Gurobi, every registered C++ test and repository Python test succeeds,
new deterministic HGA and LP-event lifecycle tests succeed, the exact toy
comparison succeeds, interval coverage and bound inheritance succeed, the
terminal-leaf exactly-once and deadline-interruption tests succeed,
moderate_seed4301 passes its established correctness sentinel, and the static
no-dispatch/no-internal-budget audits pass.

## Official workload

Stage 1 runs generation-stagnation HGA standalone, without an HGA time budget,
on `V12_M2` twice and once each on `high_imbalance_seed3202` and the existing
V50 instance `moderate_seed6301`. Identity of V12_M2 generation count, final
fitness, and independently verified objective is mandatory.

Stage 2 is exactly 15 serial official rows: `V12_M1`, `V12_M2`,
`high_imbalance_seed3202`, `moderate_seed3302`, and `tight_T_seed3101`, each
with `P-GRB`, `C0-LEGACY`, and `C2-PAPER`, under a 300-second overall process
wall cap.

Stage 3 is exactly two serial V50 smoke rows on `moderate_seed6301`, with
`P-GRB` and `C2-PAPER`, under the same 300-second overall process wall cap.
The cap is an experiment budget only. On C2 it may terminate the whole process
but may never trigger an HGA phase switch, leaf switch, split, retry, or
restart.

## Measurements and decisions

Every row retains commands and hashes, native logs, result JSON, verifier and
certificate state, bound progress, HGA trajectories, LP/MIP status ledgers,
parent/child bounds and split decisions, lifecycle, Work, model/read counts,
and memory. Large text/model/trajectory files are gzip-compressed losslessly
with restoration hashes.

The analysis compares strict certification, certificate time, independently
verified UB, valid global LB, common-UB gap, bound-progress AUC, total and LP
Work, LP count, terminal-MIP leaf/count, split count, model reads/builds, peak
memory, stagnation, and HGA generation telemetry. C2 is classified as
`approximately_reproduced`, `paper_compatible_but_performance_risky`, or
`invalid` using the definitions in the Round 27 request. This round never
promotes C2 or changes the stable mainline.
