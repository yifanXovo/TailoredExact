# Round 30 frozen protocol

## Roles and non-promotion rule

S0/F0-CPLEX remains the stable accepted paper mainline and is not modified,
retuned, aliased, or replaced in Round 30. C0-DIAG is exact but uses historical
time quanta and an attempt-count split rule.
C0-DIAG is never promotion-eligible. C3-REPLICA remains the exact S0 decomposition
reference. C4-CANDIDATE remains the frozen Round 29 child-LP-benefit reference.
C5-CANDIDATE is one new algorithmically distinct experimental candidate.

Round 30 does not automatically promote C5, whatever its measurements.

## Pre-freeze evidence

The Phase A parser reads retained Round 25/26 evidence without modifying it.
It treats C0 and the rejected C1 label as the same frozen algorithm and
attributes independent differences to run variability. The audit and shadow
replay are completed before C5 selection. Round 29 C4 AUC rows without a
compatible observed trace are explicitly marked `auc_unavailable`; no
endpoint pseudo-trajectory is retained.

Exactly one C5 prototype is selected. No fallback is activated. The
development matrix contains the seven prescribed instances, C4 and C5, one
60-second run per pair. Moderate4301 receives an additional 75-second
correctness and native-event sentinel. These are nonofficial diagnostics.

## Frozen C5

Selector: `round30-dual-bound-target`.

Lifecycle: `round30-same-leaf-bound-target`.

The initial range is four exact intervals. Binary midpoint splitting retains
maximum depth 8 and minimum width `1e-4`. The certificate tolerance is `1e-7`.
The normalized split threshold is the single dimensionless value
`rho = 0.01`.

For an eligible parent with valid lower bound \(b\), complete child LP bounds
\(b_L,b_R\), and independently verified upper bound \(U\), define

\[
b_C=\min(b_L,b_R),\qquad
r=(b_C-b)/\max(U-b,10^{-7}).
\]

Child LP infeasibility causes an immediate exact atomic split. A finite strict
gain with \(r\ge 0.01\) also causes an immediate split. With no strict gain,
the child models are discarded and the complete parent MIP is solved. With
\(0<r<0.01\), the parent MIP runs until Gurobi's validity-gated
`GRB_CB_MIP_OBJBND` reaches \(b_C\), or until native exact closure,
infeasibility, or the overall process deadline. Reaching \(b_C\) requeues the
still-open parent with its valid bound; when the best-bound scheduler selects
it again, the parent is atomically replaced by its two children and both
inherit the strengthened parent bound.

No internal decision uses elapsed time, Work, nodes, solution count, attempts,
retries, family, dimensions, seed, instance identity, path, or a historical
optimum. The sole time control is the uniform 300-second overall process cap
with a fixed 5-second engineering shutdown margin.

## Trace contract

C0, C3, C4, and C5 emit
`external/global_bound_trace.csv` under the Round 30 schema. P-GRB uses its
native progress callback. AUC is a left-continuous step integral between
consecutive observations and stops at the final observed timestamp. It is
unavailable if validation fails. No interpolation and no extension after the
last event are permitted.

## Official serial matrix

Every solver uses one thread and a 300-second process-entry cap. Runs are
strictly serial.

- Stage 1: seven mechanistic instances by C0, C4, C5 = 21 rows.
- Stage 2: all 17 primary instances by P-GRB, C4, C5 = 51 materialized rows.
  The 14 overlapping C4/C5 rows are the byte-identical Stage 1 executions;
  Stage 2 launches the other 37 rows.
- Stage 3: five anchors by S0, C0, C3, C4, C5 = 25 materialized rows. The
  15 overlapping C0/C4/C5 rows are Stage 1 executions; Stage 3 launches S0
  and C3 only, ten rows.
- Stage 4: two additional C5 repetitions on each of five instances = 10 rows.

All commands, instance hashes, source commit, executable hashes, protocol
hash, parameter freeze, and forbidden-logic scan are frozen before Stage 1.
After Stage 1 begins, no C5 source, callback contract, threshold, geometry, or
command construction may change.

## Failure handling and classification

An interrupted leaf remains open with its last backend-certified bound.
Incomplete coverage cannot certify. Any false bound, vanished interval,
invalid closure, verifier failure, lifecycle asymmetry, incomplete trace used
for AUC, or forbidden C5 control makes C5 invalid. A general correctness fix
would stop the matrix, preserve affected evidence, rebuild and rehash, and
uniformly rerun affected rows; no best-of reruns are allowed.

Final classification uses the exact categories
`paper_exact_and_performance_promising`,
`exact_c0_mechanism_transfer_partial`,
`exact_but_no_transfer_gain`, or `invalid`. The stable-mainline decision is
independent: S0/F0-CPLEX remains the mainline.
