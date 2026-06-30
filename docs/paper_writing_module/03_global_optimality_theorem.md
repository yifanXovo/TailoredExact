# 03 Global Optimality Theorem

An incumbent is globally optimal for the original problem when:

- the incumbent route-load plan is verifier-passed;
- the frontier covers the full improving Gini range;
- every final interval is empty, relaxation-bound fathomed, or closed by an
  exact BPC tree;
- every BPC-closed interval has exact pricing closure;
- no interval has invalid lower-bound evidence, unresolved coverage, open nodes,
  or stale incumbent assumptions.

This theorem does not rely on heuristic incumbents, archive scans, compact CPLEX
benchmark bounds, or interval-oracle diagnostics.
