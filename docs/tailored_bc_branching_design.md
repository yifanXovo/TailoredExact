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
- a one-shot custom Gini split callback is wired for branch context when `--tailored-bc-gini-branching callback` is requested, but the smoke row does not reach branch context and no hard-leaf validation has proven this path useful yet.

Any row with callback branching disabled must not claim callback branch-and-cut evidence.
