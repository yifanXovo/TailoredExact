# Tailored BC Cut Proof Notes

## Gini Subset Envelope

For a subset `A` of stations with size `a`, let `R_A = sum_{i in A} r_i` and `S = sum_i r_i`. In a fixed interval with `G <= gamma_U`, `H <= V gamma_U S`. The average deviation of a subset from the global mean is bounded by the total pairwise spread, giving safe linear envelope rows:

`V R_A - a S <= V gamma_U S`

and

`a S - V R_A <= V gamma_U S`.

These rows are enabled only for bounded small subsets in static fallback.

## Low-Gini L1 Centering

Introduce `q_i >= |r_i - S/V|`. The Gini cap implies a valid loose centering condition `sum_i q_i <= 2 gamma_U S`. This is a relaxation of pairwise dispersion and cannot cut original feasible solutions in the interval.

## Vehicle Transfer Cutset

Under the empty-start vehicle convention, the net number of bikes delivered by a vehicle into a receiver subset cannot exceed pickups by that same vehicle outside the subset. The implemented static row is conservative and restricted to singleton/pair subsets.

## S-Bucket Refinement

S-bucket denominator refinement is certificate-safe only when child buckets exactly cover the parent feasible `S` domain and every bucket is closed. The current callback round keeps this as a coverage test rather than a paper certificate mechanism.
