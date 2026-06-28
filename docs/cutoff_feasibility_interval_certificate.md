# Cutoff-Feasibility Interval Certificate

Date: 2026-06-28

This round adds result fields and command-line controls for cutoff feasibility:

```text
--relaxation-certificate-mode bound|cutoff-feasibility|both
--cutoff-feasibility-epsilon <double>
--cutoff-feasibility-time-limit <seconds>
```

The implementation currently records a certificate-safe wrapper around valid
lower-bound solves: if a valid relaxation lower bound for the full reported
scope reaches `incumbent_UB - epsilon`, the cutoff-feasibility status is
reported as infeasible by valid global lower bound.  If the valid lower bound is
below cutoff, the row remains unresolved.

This is not yet a separate standalone feasibility MIP.  It cannot certify an
interval unless the underlying lower-bound evidence already reaches the cutoff.

Round result: `high_imbalance_seed3202_exhaustive_300s` reports
`best_valid_bound_below_cutoff`, so no cutoff-feasibility certificate was
obtained.

