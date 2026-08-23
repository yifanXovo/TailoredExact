# Historical single-tree and API audit

## Scope and conclusion

The historical CPLEX global-Gini tree is a reference for lifecycle, local-domain provenance, and fail-closed callback engineering. It is not a validated target algorithm and its historical performance was mixed. A direct callback migration is not available in the current Gurobi C API. Round 41 therefore uses deterministic static model construction before optimize.

Relevant history is anchored by commits `5c2b1efc3` (Round 19 persistent global tree), `421b3cb4b` (Round 20 regression diagnosis), and `c05e59f6e` (Round 28 CPLEX-equivalent external Gurobi replica). The detailed historical contracts are in `docs/global_gini_tree_cplex_capability.md`, `docs/global_gini_tree_exactness.md`, `results/gf_global_gini_tree_regression_round/final_report.md`, and `results/gf_cplex_equivalent_gurobi_replica_round28/final_report.md`.

## Feasibility matrix

| Operation | Historical CPLEX implementation | Current Gurobi 13.0.2 C API | Round 41 decision |
|---|---|---|---|
| Read current node-local continuous `G` bounds | `CPXcallbackgetlocallb/ub` in branching/relaxation contexts | Callback query APIs expose prescribed callback data, but no application API for creating a pair of arbitrary continuous-bound children | Do not emulate dynamically |
| Create two child nodes with continuous-`G` bound changes | `CPXcallbackmakebranch` | No counterpart to callback-created child nodes in `gurobi_c.h` or the callback API | Unsupported; no migration claim |
| Attach rows local to a child subtree | `CPXcallbackaddusercuts(..., local=1)` at the first child relaxation | `GRBcbcut` adds callback cuts and `GRBcblazy` adds lazy constraints under their documented callback scopes; neither creates a named child or a child-local inherited row pack | Unsupported as the CPLEX mechanism |
| Submit an incumbent | CPLEX callback incumbent facilities | `GRBcbsolution` | Available but unrelated to segmented child creation; not required here |
| Add variables/linear rows before optimize | Callable-library model API | `GRBaddvars`, `GRBaddconstr` | Supported; canonical LP writer used |
| Add indicators before optimize | Static CPLEX model facilities | `GRBaddgenconstrIndicator`; Gurobi LP reader also accepts indicator syntax | Supported; ST-K2-I uses static native indicators |
| Add a deterministic perspective/disaggregated formulation | Static model construction | Static variables and linear constraints | Supported; Core/Extended use this path |
| Modify model structure inside `MIPNODE`/`MIPSOL` | Not the accepted CPLEX design; it used the dedicated branching and local-cut contexts | General model mutation is not a callback operation; only the documented callback functions are allowed at documented `where` values | Forbidden |
| Split into independent interval models | External fixed-interval solvers | Existing Gurobi backend and C6 scheduler | Supported, but it is the multi-tree behavior under study |

Official Gurobi references: [Callback Codes](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html), [C callback API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html), [C model modification API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/model.html), and [Callbacks feature guide](https://docs.gurobi.com/projects/optimizer/en/current/features/callbacks.html). The installed `D:/gurobi1302/win64/include/gurobi_c.h` independently confirms `GRBcbcut`, `GRBcblazy`, `GRBcbsolution`, and `GRBaddgenconstrIndicator`, and contains no callback child-creation function.

## Reusable lessons

- Require a valid optimal relaxation before treating its objective as a bound. An early CPLEX version omitted the relaxation-status check and pruned a branch containing the known optimum.
- Preserve original-space provenance and fail closed on incomplete column mapping, coverage, or row-family migration.
- Treat solver search modes as engineering contracts. The CPLEX implementation reproduced sibling loss under dynamic search and accepted only traditional search.
- Do not attach presolve-sensitive local rows prematurely. The accepted CPLEX path created child bounds first and attached forced local rows at the child's first relaxation.
- Keep one native finalization source and verify the decoded solution independently.
- Do not infer performance superiority from the one-tree lifecycle. Round 20 retained an instance regression, and Round 28's external replica showed that thousands of fresh optimizes can dominate some cases while helping others.

## Operations deliberately not reused

Round 41 does not call CPLEX, request Gurobi custom child creation, add node-local constraints, stop/restart a MIP while calling it one tree, or use callback timing/Work/nodes as a formulation choice. Every new object is in a hashed canonical model before the sole optimize call.
