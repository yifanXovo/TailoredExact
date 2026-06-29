# Oracle Leaf Partitioning Strategy

Leaf partitioning is a certificate-safe response to an exact interval oracle
timeout. It is generic and does not depend on instance names, leaf ids, known
optima, or hard-coded gamma values.

## Rule

When a final unresolved leaf `[gamma_L, gamma_U]` times out and
`--auto-interval-oracle-split-on-timeout true` is enabled, the leaf is split
into `N` equal child intervals, where `N` is set by
`--auto-interval-oracle-child-split-count`. Children inherit only valid metadata
from the parent: instance hash, lambda, T, incumbent cutoff, and sealed-run
provenance.

The parent can be marked closed only if every child interval closes by a valid
certificate basis, currently `interval_exact_cutoff_mip_infeasible`. If any
child times out or remains unresolved, the parent remains unresolved.

## Merge Safety

The merge rule checks exact coverage:

- child intervals must be contiguous;
- no child intervals may overlap;
- the union of child intervals must exactly match the parent leaf within
  numeric tolerance;
- all child results must use the same instance hash, objective convention,
  incumbent cutoff, lambda, and T.

Timeouts and feasible relaxed artifacts are diagnostic only. They do not
contribute lower-bound certificate evidence.

## Observed Use

In `results/sealed_closure_round/`, partitioning was useful diagnostically but
did not create a new V20 certificate. It identified remaining timeout children
for `moderate_seed3301`, `tight_T_seed3102`, `high_imbalance_seed3201`, and
`moderate_seed3302`.
