# Service-Operation Minimum Handling Cuts

Date: 2026-06-28

The option:

```text
--service-operation-min-handling true|false
--service-operation-min-handling-cuts true|false
```

adds the valid relaxation row:

```text
p[k,i] + d[k,i] >= y[k,i]
```

under the model convention that a visited station in an original route has a
nonzero pickup/drop operation.  For continuous relaxations this is weaker than
the original integer convention and therefore relaxation-safe.

The cuts are not enabled by canonical `paper-bpc-core`.  They are available for
V20 ablation and focused interval diagnostics.  In the current round, enabling
them inside focused exhaustive attempts did not close the priority V20
intervals.

