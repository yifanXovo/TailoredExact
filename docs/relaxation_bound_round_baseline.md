# Relaxation Bound Round Baseline

This round starts from branch `codex/longrun-round17-local-results` at remote
head `ef4cb62edf3081ffcfd06976d18705bf861b4edc`.

Baseline artifacts were read from `results/exact_primal_stress_round/` and
summarized in `results/relaxation_bound_round/baseline_plateau_table.csv`.

## Baseline Diagnosis

The current plateau is lower-bound closure in the interval relaxation ledger.
For regenerated V12 M1 and all V20/M3 hard stress instances, pricing time and
master time were zero or near zero and the BPC tree was not entered in the
baseline rows. The controlling intervals had valid relaxation lower bounds below
the verified incumbent, with unresolved intervals and open interval placeholders
remaining.

V12 M1 baseline:

- UB: `0.357200583208`
- LB: `0.332675660948`
- gap: `0.0686586848205`
- unresolved intervals: `2` in the previous stress summary, with the active
  lowest intervals recorded in the interval CSV.
- pricing time: `0`

V20/M3 baseline rows were also relaxation-bound plateaus. They were previously
mislabelled as `historical_target` in summary CSVs despite coming from
`reference/hard_stress/V20_M3`. This round fixes new result metadata to
`hard_generated_v20_m3`.

## Bottleneck

The bottleneck is relaxation lower-bound closure, not primal UB quality or route
pricing. Native HGA-TGBC and exact-phase local re-decode already provide strong
verified UBs on the regenerated V12 rows. The remaining work is to strengthen
certificate-safe lower bounds and schedule exact BPC fallback only where it can
add valid closed-node evidence.
