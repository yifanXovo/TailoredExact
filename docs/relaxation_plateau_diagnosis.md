# Relaxation Plateau Diagnosis

The new V20/M3 stress rows and the V12 M1 300-second row are not primal-quality
failures. They have verified incumbents but positive gaps because the valid
relaxation portfolio does not yet fathom all final intervals.

Observed pattern:

- bound time dominates pricing/master time;
- route-pool and local re-decode repair do not improve the already strong UB;
- open intervals remain with lower bounds below the cutoff;
- no diagnostic or archive incumbent is used as lower-bound evidence.

Next target:

- stronger vehicle-indexed capacity/flow cuts;
- better interval-specific relaxation variant ordering;
- relaxation cache reuse across compatible child intervals;
- station residual cover cuts for high-imbalance V20 intervals.
