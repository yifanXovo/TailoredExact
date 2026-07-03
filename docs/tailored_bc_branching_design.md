# Tailored BC Branching Design

The target branch strategy is Gini-aware:

- branch first on variables that control final inventory and ratio dispersion;
- use interval selector variables for Gini or denominator buckets when the model is built with exact coverage;
- preserve CPLEX default branching for ordinary compact variables when no valid Gini branch candidate is available.

Current implementation status:

- branch-priority and Gini-branching options are parsed and reported;
- the in-process CPLEX API path applies branch-order priorities with `CPXcopyorder` to binary `bit_*`, `z_*`, and `mode_*` compact-model variables;
- selector/outer-controller metadata is emitted;
- a generic CPLEX callback is registered and branch-context events are counted when CPLEX enters that context;
- a one-shot custom Gini split callback is wired for branch context when `--tailored-bc-gini-branching callback` is requested;
- `tailored-bc-branch-callback-smoke-test` now solves a diagnostic-only multidimensional binary knapsack through the same dynamic CPLEX C API with traditional search, presolve disabled, and branch priorities applied.  The current evidence row reports callback availability, relaxation and candidate callbacks, and 30 branch priorities applied, but CPLEX still solves before entering branch context (`tailored_bc_branch_callback_calls=0`, `tailored_bc_gini_branches_created=0`).

Any row with callback branching disabled must not claim callback branch-and-cut evidence.

Current paper status: Gini branch callbacks are implemented at the API boundary but not performance- or branch-context validated on ExactEBRP hard leaves.  Branch priorities are the only observed branching control mechanism in the callback round.
