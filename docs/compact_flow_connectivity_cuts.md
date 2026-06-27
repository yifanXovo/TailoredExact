# Compact-Flow Connectivity Strengthening

Date: 2026-06-28

The large compact-flow relaxation can be strengthened with continuous
single-commodity connectivity flow:

```text
--large-compact-flow-connectivity true|false
```

For each vehicle, continuous arc-flow variables ship one unit from the depot to
each fractionally served station.  Arc flow is bounded by a large-M multiple of
the compact-flow arc variable.  Every original route induces a feasible
connectivity-flow solution by sending one unit along the route prefix to each
served station.  The constraints are therefore valid relaxation constraints.

## Round Finding

Connectivity constraints are proof-safe, but the first adaptive V20 rows did
not beat the prior fixed LP/mip-light baselines when connectivity was mixed
with service-operation and penalty-domain cuts.  Connectivity remains an
explicit ablation flag, not a paper-core default.

