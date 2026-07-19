# Round 24 solver capability matrix

| Capability | CPLEX 22.1.1 | Gurobi 13.0.2 | Round 24 consequence |
|---|---|---|---|
| Complete canonical LP import | available | adapter implemented; runtime import blocked by license | LP bytes are cross-solver identical; native Gurobi fingerprint is unavailable |
| Plain one-thread MIP | available and licensed | implemented, unlicensed locally | P-CPX toy executes; P-GRB fails closed before optimize |
| Exact-zero relative/absolute gap set/get | available | implemented | both certificate adapters require exact readbacks |
| Read-only MIP progress | available | implemented | no callback changes search state |
| Continuous native custom children | available, but unsafe with presolve in this architecture | not available in the required form | S0 uses safe CPLEX presolve-off; both solvers can use the external controller |
| Static fixed-interval solves | available | implemented | common solver-neutral external-tree interface |
| Same unchanged model continuation | not claimed by the fresh CPLEX adapter | supported by retained Gurobi model objects | continuation requires cumulative Runtime/Work/Node evidence and no reset |
| New-child native-tree inheritance | unavailable | unavailable | each child is a new model; only proved parent LB is inherited |
| Complete MIP start on a new model | not used in Round 24 external CPLEX | implemented and independently gated | a start is primal information only, never native-tree reuse or LB evidence |
| Native model fingerprint | canonical SHA-256/lifecycle bindings | `Fingerprint` adapter implemented | Gurobi value unavailable because environment creation stops at error 10009 |
| Local license | available | unavailable | preregistered Stage 1/2 performance matrix is blocked |

No backend is selected from instance metadata. Missing Gurobi capability or license is an explicit failure, never a fallback to CPLEX.
