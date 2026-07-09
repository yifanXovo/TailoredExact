# Alternative Formulation Final Report

The current binary-expansion compact MILP remains the runnable plain benchmark in this round and is labelled `tolerance_exact`.

Exact S enumeration, exact S selector, and exact S parametric cutoff are represented by complete-coverage audits and a direct-algebra toy equivalence test. The toy test passes, but V12 and V20 route-domain S sets exceed the configured cap, so route benchmark rows are `exact_but_too_large`.

No exact alternative formulation outperformed the current plain formulation at 300s/1200s because no route-level exact-S alternative was small enough to run. Approximate SOS2/coarse S-bucket/Dinkelbach-style formulations are rejected as exact benchmarks unless a later proof establishes exact finite certificate equivalence.

Future benchmark work should revisit exact-S formulations only after stronger domain reduction makes complete denominator coverage tractable.
