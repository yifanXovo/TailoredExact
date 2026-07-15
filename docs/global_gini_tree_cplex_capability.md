# CPLEX 22.1.1 global-tree capability boundary

## Verified installation

The implementation was developed and tested against IBM ILOG CPLEX 22.1.1.0 (`cplex2211.dll`). Symbols are loaded dynamically with the callable-library signatures and Windows calling convention from the installed headers. The installed HTML reference was used for constants, parameter IDs, original-space rules, and context restrictions.

| Need | Verified API or setting | Engineering use |
|---|---|---|
| Branch callback | `CPX_CALLBACKCONTEXT_BRANCHING` (`0x0080`) | Decide a recursive Gini split or let CPLEX branch |
| Local bounds | `CPXcallbackgetlocallb`, `CPXcallbackgetlocalub` | Recover the current original-space G interval |
| Relaxation status | `CPXcallbackgetrelaxationstatus` | Require an optimal parent relaxation before using its objective as a child estimate |
| Relaxation point/bound | `CPXcallbackgetrelaxationpoint` | Obtain the valid parent relaxation objective |
| Node identity | `CPXcallbackgetinfolong`, info 9 and 10 | Node UID and depth |
| Global progress | `CPXcallbackgetinfodbl`, best-bound info 4 | Diagnostic bound trajectory |
| Child creation | `CPXcallbackmakebranch` | Original-space child bounds and child IDs |
| Local rows | `CPXcallbackaddusercuts` | Forced rows with `local=1` at the child's first relaxation |
| Native deadline | `CPXPARAM_TimeLimit` (1039) | One solver-native deadline |
| Native final LB | `CPXgetbestobjval` | Solver-final global lower bound |
| Best-bound nodes | `CPXPARAM_MIP_Strategy_NodeSelect` (2018) = 1 | Native best-bound selection |
| Presolve | `CPXPARAM_Preprocessing_Presolve` (1030) | Explicit on/off diagnostic switch |
| Search | `CPXPARAM_MIP_Strategy_Search` (2109) | Traditional = 1; dynamic = 2 |

`CPXcallbackmakebranch` and `CPXcallbackaddusercuts` both accept original-space columns. Requesting the branching context disables the nonlinear presolve reductions that CPLEX cannot crush safely. The local-user-cut API is valid only in the relaxation context; `local=1` scopes a row to that node and its descendants.

## Relaxation-status boundary

The branching context can be invoked when the node relaxation is not optimal. The installed documentation explicitly requires callers to inspect `CPXcallbackgetrelaxationstatus`. An early implementation omitted this check and used a transient restart objective as a child estimate. The final restart then pruned the branch containing the independently known optimum. The production callback now custom-branches only for statuses `CPX_STAT_OPTIMAL` and `CPX_STAT_OPTIMAL_INFEAS`; every other status is recorded and falls back to CPLEX branching.

## Presolve-safe local rows

Attaching the complete child row pack directly in `CPXcallbackmakebranch` reproduced a second CPLEX boundary: after presolve eliminated `r_min/r_max`, stronger child centering rows referencing those columns were incorrectly crushed. Presolve-off and standalone fixed-interval solves were correct.

Two exact changes preserve presolve:

1. child creation carries only original-space interval/domain bounds;
2. interval-local linear rows are forced with `local=1` at the child's first relaxation.

The extrema formulation is represented by the exact pairwise projection so the relaxation callback does not reference presolve-eliminated auxiliary columns. Matched presolve-on and presolve-off V8 solves then returned the same native optimum and verified incumbent with zero local-row failures. The official gate retains presolve on.

## Dynamic versus traditional search

Generic callbacks are documented as generally compatible with dynamic search. This particular recursive continuous-bound disjunction nevertheless reproduced sibling loss under CPLEX 22.1.1 dynamic search:

- the exported root LP solved to `0.160763515679` with plain CPLEX;
- traditional custom search, with presolve on and off, returned the same value;
- dynamic custom search returned higher false-optimal objectives or, in a bounds-only diagnostic, the seed incumbent;
- return codes from both child creations were zero and local pair coverage passed;
- the trace ended after following one child while an improving sibling should have remained.

This is treated as a reproduced engineering restriction, not as a claim that all generic callbacks are incompatible with dynamic search. `global-gini-tree` defaults to traditional search and fails closed if `dynamic` or `auto` is requested. It never silently changes the requested mode and can never issue a certificate from the unsafe path.

## Native features

The accepted configuration keeps these features:

- presolve on;
- CPLEX default primal heuristics;
- CPLEX default probing;
- CPLEX default native cuts; and
- one thread.

Traditional search is the only disabled alternative. It is disabled for reproduced correctness, not convenience. Root cuts and Tailored callback-only/bucket families are outside the Round 18 static-no-callback official profile; the family registry records them as excluded and blocks a global run if any is active.

## Finalization boundary

The native time limit is set once before `CPXmipopt`. At return, status, objective, best bound, and node count are read from the same problem object before it is freed. The lifecycle manifest counts exactly one environment, problem, model read, `CPXmipopt`, free, and close. Wrapper synthesis, nested interval solvers, leaf restarts, and child processes are certificate failures.

## Round 19 observed capability result

Presolve-on and presolve-off 30-second gates passed on V12_M1, V12_M2,
moderate_seed3301, and tight_T_seed3102. The official mode therefore uses
presolve on. All eight 300-second and all eight 900-second global-tree rows
returned through the native finalization path with one environment, one
problem, one model read, one `CPXmipopt`, one free, and one close. None used an
interval oracle or child process.

In CPLEX parameter reporting, heuristic frequency `0` and probing `0` mean the
CPLEX automatic/default policies; Round 19 does not set either feature to an
off value. Native cut parameters likewise remain at their defaults. Traditional
search is the sole explicit restriction, and the implementation rejects both
`dynamic` and `auto` rather than silently changing them.

The official global-tree traces contain zero callback failures, local-bound API
failures, column-mapping failures, nonoptimal-relaxation custom branches,
child-estimate failures, coverage failures, or local-row attachment failures.
Traditional best-bound search is consequently mechanically stable for this
implementation. This does not remove the documented dynamic-search boundary
and does not claim that every other generic callback requires traditional
search.
