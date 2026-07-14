# Controlling-leaf scheduler: exactness and evidence boundary

## Scope

Round 18 changes the order and duration of exact fixed-interval solves. It does
not change the original objective, any fixed-interval feasible region, the
paper-safe static row set, the incumbent verifier, or the frontier coverage
rule. `legacy` and `controlling-leaf` are explicit modes in the same binary;
the paper preset continues to default to the legacy behavior.

For every non-replaced relevant final leaf (i), let (F_i) be its unchanged
fixed-interval feasible set, (U) the same-run verified incumbent cutoff, and
(b_i) its current accepted lower bound. A leaf is relevant when its lower
Gini endpoint is below (U), using the existing certificate tolerance.

## Bound operations

Every admitted source is independently valid for the same (F_i). Therefore

\[
b_i \leftarrow \max\{b_i,\widehat b_i\}
\]

is valid and monotone. Since the final leaves cover the complete improving
Gini range, the full-frontier bound

\[
B=\min_{i\in L} b_i
\]

is a valid original-problem lower bound. A closed no-improver leaf may use
(U) in this minimum. A timeout is not closure, and an unattempted leaf stays
in (L) with its inherited or base valid bound.

The controller selects only leaves attaining (B) within the existing
certificate tolerance. Changing that selection order cannot change any
(F_i), objective coefficient, row, incumbent, or accepted-bound rule, so it
cannot change certificate validity.

## Splits

The controller may invoke only the existing adaptive split operation and its
existing depth, width, factor, and eligibility conditions. Children inherit a
parent bound only because each child feasible set is a subset of the parent
feasible set. All children are validated for exact endpoint coverage and are
inserted before the parent is atomically marked replaced. Thus the parent and
children never contribute simultaneously and their union preserves the same
Gini range. Finite maximum split depth prevents endless refinement from
permanently replacing exact-leaf service.

## Persisted native CPLEX bounds

Callback-managed diagnostic workers can atomically persist native CPLEX
best-bound records. Acceptance requires a complete temporary-file/atomic-
rename record whose run ID and sequence, instance hash, interval endpoints,
cutoff, minimization sense, complete LP fingerprint, formulation profile,
single-thread policy, native time-limit parameter and return code, model type,
and bound source exactly match the parent expectation. Heartbeats, partial or
stale files, identity mismatches, non-native sources, and any record influenced
by benchmark, archive, external-incumbent, BPC, route-mask, focus-only,
historical, or diagnostic bounds are rejected.

Persistence does not alter the mathematical bound. An accepted checkpoint
below (U) improves (b_i) but leaves the leaf open. A bound reaching (U)
permits bound fathoming. A checkpoint alone never proves infeasibility or
optimality. When solver-final and checkpoint bounds both pass identity checks,
their maximum is valid. Official static rows register no callback and normally
use the solver-final CPLEX API bound; checkpoint engineering is evaluated
separately.

## Budget and fairness

The process has one parent wall deadline. The in-budget finalization reserve is

\[
r=\min(30,\max(5,0.02T)).
\]

No new solve starts once the reserve boundary is reached. A selected leaf's
attempt (k), starting at zero, requests

\[
q_i(k)=30\,2^k\text{ seconds},
\]

and the native limit is truncated only by remaining parent time less the
reserve. There is no configured maximum quantum.

New tied controlling sets are ordered by decreasing interval width, increasing
lower endpoint, increasing upper endpoint, then canonical leaf ID. Round-robin
water filling ensures every still-open member receives one quantum before a
member receives another at the same bound level. Consequently, under an
unlimited global horizon, finite split depth, and a persistently tied final
set, each persistent leaf receives infinitely many attempts and arbitrarily
long individual requested quanta. This is an asymptotic service property, not
a finite-budget closure guarantee and not exact CPLEX tree resume: every
attempt rebuilds the fixed-interval model/search.

## Claims kept separate

- Mathematical correctness follows from unchanged feasible sets, valid bound
  merging, exact leaf coverage, and exact-safe closure rules.
- Finite-budget performance is empirical; a finite run need not close.
- Asymptotic fairness follows from deterministic round robin and unbounded
  geometric quanta under the assumptions above.
- Eventual full convergence additionally assumes the underlying exact
  fixed-interval solver eventually terminates on a sufficiently long attempt.

No instance name, path, seed, size class, archived result, known objective, or
diagnostic/benchmark bound participates in scheduler decisions.
