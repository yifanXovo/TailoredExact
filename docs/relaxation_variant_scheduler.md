# Relaxation Variant Scheduler

The frontier relaxation call now includes `--v20-safe-relaxation-cuts` in its
cache key. This prevents reusing a lower-bound artifact computed under a
different relaxation option signature.

The existing valid variant portfolio is retained:

- no-operation-budget first when it can cutoff-fathom an interval;
- operation-budget variant when it improves the valid lower bound;
- no-compatibility audit fallback when compatibility flow is not needed or the
  short relaxation budget would be better spent on the cheaper model;
- compatibility and vehicle transfer flow when they improve the selected bound.

For V20/M3 rows, the added continuous vehicle-indexed layer provides
vehicle-specific operation and transfer evidence without all-subset masks.
Variant notes are recorded in the result JSON notes and summarized in
`results/relaxation_bound_round/relaxation_variant_summary.csv`.

The scheduler remains certificate-safe because it selects the maximum available
valid lower bound for an interval and never treats a timed-out or incompatible
diagnostic artifact as a certificate.
