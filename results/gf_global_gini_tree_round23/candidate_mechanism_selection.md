# Round 23 candidate mechanism selection

The official candidate is P2, the dispersion-coupled child lower-bound
estimate. P1 was audited first and rejected because supported explicit
open-node enumeration/selection exists only in the legacy node-control API,
not in the current generic callback. Mixing callbacks or performing a partial
migration would violate the preregistered safety conditions.

P2 is selected only because its mathematical proof, conservative numerical
implementation, hand cases, invalid-input gates, and exhaustive toy-optimum
tests pass. Selection does not use benchmark speed.

The one uniform option is `--global-gini-tree-child-estimate
dispersion-coupled`. It is off by default; corrected S0 uses `parent-copy`.
The option is identical for F0 and F3 and contains no V/M/capacity/name/seed/
path/family/time dispatcher. It changes only the proved estimate supplied when
creating a child. It does not change rows, bounds, split locations, objective,
incumbent semantics, candidate validation, or pruning rules. A detected
aggregate-domain contradiction retains the parent estimate and does not prune.

Official IBM API context and the retained bottleneck evidence are recorded in
`scheduler_api_feasibility.md` and `round23_bottleneck_synthesis.md`.
