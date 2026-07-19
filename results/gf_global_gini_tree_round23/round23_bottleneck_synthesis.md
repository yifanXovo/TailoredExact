# Round 23 retained search-bottleneck synthesis

This synthesis uses only Round 22 dense trajectories, node/topology/sibling
traces, post-row traces, native JSONs, and logs. It excludes the anomalous
moderate4301 performance row.

The dominant per-run classifications are {'sibling_starvation': 40, 'equal_child_estimates': 6}. Sibling delay is
present in both wall time and processed-node count: the maximum retained
per-run wall delay is 2940.0933433999999 seconds and
the maximum processed-node delay is 45220.
Parent-copy creates no proved estimate lift, so equal estimates and native
best-bound tie behavior can compound starvation. Ordinary B&B growth,
simplex work, and late stagnation remain secondary or mixed signals.

Mechanism ranking under the preregistered criteria:

1. P1 would directly target starvation, but the CPLEX 22.1.1 generic callback
   exposes high-level branch/prune operations, not supported open-node
   enumeration and next-node selection. The documented selector is a legacy
   NodeCallback, so P1 requires an incomplete and forbidden callback migration.
2. P2 is a uniform, model-size-free child estimate derived from a proved
   dispersion/deviation inequality. It changes neither rows, bounds,
   objective, branching, nor pruning and is therefore the lower-risk supported
   candidate if its proof and exhaustive tests pass.
