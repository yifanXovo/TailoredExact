# P1 scheduler API feasibility

P1 is rejected for Round 23.

The current architecture uses the CPLEX 22.1.1 Callable Library generic
callback. Its documented branching context supports querying the current
relaxation, making children, and pruning the current node, but it does not
provide a supported operation to enumerate all open nodes and select a
particular next node. IBM describes generic callbacks as higher-level and as
offering less low-level branch-and-cut control than legacy callbacks.

Explicit remaining-node enumeration and `selectNode` are documented on the
legacy `NodeCallback`. Migrating only node selection would mix generic and
legacy control paths; a complete migration would also have to preserve custom
branching, local rows, candidate validation, node data, dense progress,
canonical inheritance, and lifecycle evidence. That migration is neither
implemented nor validated in this round. Branch creation order, child UID
order, and equal-estimate tie behavior are undocumented substitutes and are
forbidden by the protocol.

Relevant IBM CPLEX 22.1.1 documentation:

- https://www.ibm.com/docs/en/icos/22.1.1?topic=techniques-generic-callbacks
- https://www.ibm.com/docs/en/icos/22.1.1?topic=classes-ilocplexnodecallbacki
- https://www.ibm.com/docs/en/icos/22.1.1?topic=legacy-branch-selection-callback

Conclusion: supported paired-first-touch debt cannot be implemented completely
inside the current exact generic-callback single-tree architecture. P1 fails
the preregistered API gate independent of benchmark performance.
