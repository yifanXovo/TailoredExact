# Tailored BC Branching Design

The target branch strategy is Gini-aware:

- branch first on variables that control final inventory and ratio dispersion;
- use interval selector variables for Gini or denominator buckets when the model is built with exact coverage;
- preserve CPLEX default branching for ordinary compact variables when no valid Gini branch candidate is available.

Current implementation status:

- branch-priority and Gini-branching options are parsed and reported;
- selector/outer-controller metadata is emitted;
- no true CPLEX branch callback is active in the current command-file CPLEX build.

Any row with callback branching disabled must not claim callback branch-and-cut evidence.
