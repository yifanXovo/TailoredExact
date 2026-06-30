# 04 Valid Relaxations And Cuts

Paper-core relaxations must contain every original feasible route-load solution
for the interval.  Valid examples include:

- inventory/route/Gini interval relaxation;
- non-enumerative vehicle-indexed operation and transfer-flow relaxations;
- station residual and penalty-domain tightening;
- compact-flow relaxation used as a lower-bound relaxation, not as a compact
  original oracle certificate;
- Gini spread, required movement, and aggregate handling capacity cuts when
  their assumptions are derived from interval and cutoff data only.

Complete route-mask enumeration remains a diagnostic/regression tool only.
