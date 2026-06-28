# Exhaustive Interval Relaxation Portfolio

Date: 2026-06-28

The option:

```text
--relaxation-portfolio-mode exhaustive
--relaxation-exhaustive-stop-on-fathom true|false
```

runs all selected valid relaxation variants for an interval, or stops early
when one variant already fathoms the interval.  The solver keeps only the
maximum valid lower bound.  Timed-out or incompatible artifacts cannot be used
as certificate evidence.

In the V20 certificate round, exhaustive mode was tested on
`high_imbalance_seed3202`.  It did not improve the previous best mip-light
1200s gap.  The full 300s exhaustive row ended with gap `0.0755243654678`, worse
than the previous mip-light 1200s gap `0.0317627113992`.

Trace:

```text
results/v20_certificate_round/exhaustive_variant_trace.csv
```

