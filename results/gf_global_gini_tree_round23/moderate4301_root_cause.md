# moderate4301 root cause

## Classification

The primary cause is category 20: a presolve-induced incompatibility in the
continuous-variable generic-callback branching configuration. The secondary
cause is category 18: status-scope semantics allowed native status 103 to be
described without an explicit native-model scope.

The first failing invariant is: every successfully created custom child whose
closed interval contains a feasible root witness must remain represented until
it is either processed or validly fathomed. At the root split, the valid HGA
witness has G = 0.015302186003961113 and lies in upper child UID 2. CPLEX
accepted both `makeBranch` calls, but with presolve enabled UID 2 disappeared
before its first relaxation. Only UID 1 was touched; CPLEX then returned status
103 after five nodes.

## Exclusions and causal controls

- Plain, S0, and S1 use the same instance bytes and core semantics.
- Both retained route witnesses independently satisfy the original problem.
- A canonical complete HGA extension satisfies every root LP row, bound, and
  integrality condition.
- Partial semantic fixation has a feasible auxiliary extension.
- Eager child rows reproduce status 103, excluding deferred-row timing as the
  first cause.
- Disabling dual and linear reductions (`Reduce=1, Linear=0`, then
  `Reduce=0, Linear=0`) still reproduces status 103.
- Disabling presolve changes the outcome to status 108 at the native deadline,
  with 94/114 created Gini children in corrected S0/S1, many sibling first
  touches, valid lower bounds, and no callback failures.

This controlled one-parameter ablation identifies presolve as the causal
condition for the witness-containing child loss in the current C API generic
callback architecture. It is not an instance, row-family, flow, inheritance,
or objective-boundary special case.

## General correction

Every production global-Gini solve now requires presolve off. The code also
sets `Preprocessing.Reduce=0` and `Preprocessing.Linear=0`, reads both back,
and fails before `CPXmipopt` if the complete parameter contract is not met.
Traditional search, best-bound selection, branch disjunctions, row timing,
row families, objective, cutoff, and one-tree lifecycle are unchanged.

Native infeasibility is now explicitly scoped. A verified witness that
satisfies the native model forces `certificate_rejected` with reason
`verified_feasible_witness_contradicts_native_infeasibility`; it can never be
serialized as original-problem infeasibility.

## Blast radius

The correction changes a CPLEX parameter on every Tailored global-tree solve.
Immutable Round 22 artifacts are not rewritten, but prior presolve-on Tailored
status 103 rows are excluded and prior Tailored strict certificates are not
silently treated as corrected-S0 evidence. Round 23 revalidates the fixed
six-instance subset, including both former V12 strict controls, with one frozen
corrected executable. Plain CPLEX is unaffected because it does not use the
continuous generic-callback branch operation.
