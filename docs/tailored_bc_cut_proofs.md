# Tailored BC Cut Proof Notes

## Gini Subset Envelope

For a subset `A` of stations with size `a`, let `R_A = sum_{i in A} r_i` and `S = sum_i r_i`. In a fixed interval with `G <= gamma_U`, `H <= V gamma_U S`. The average deviation of a subset from the global mean is bounded by the total pairwise spread, giving safe linear envelope rows:

`V R_A - a S <= V gamma_U S`

and

`a S - V R_A <= V gamma_U S`.

These rows are enabled only for bounded small subsets. They may be generated statically or separated inside the CPLEX relaxation callback from the current LP relaxation point. Callback separation does not change the proof: every added row is one of the same fixed-interval subset-envelope inequalities.

## Visit-Final-Inventory Linking

For station `i`, if no vehicle visits the station, the final inventory must remain at the initial inventory. With visit variables `z[k,i]`, the standard linking rows are:

`Y_i - initial_i <= (capacity_i - initial_i) sum_k z[k,i]`

and

`initial_i - Y_i <= initial_i sum_k z[k,i]`.

They are valid under the station-disjoint compact model because any station inventory increase or decrease requires a serving vehicle. The CPLEX relaxation callback separates these same rows when they are violated by an LP relaxation point.

## Low-Gini L1 Centering

Introduce `q_i >= |r_i - S/V|`. The Gini cap implies a valid loose centering condition `sum_i q_i <= 2 gamma_U S`. This is a relaxation of pairwise dispersion and cannot cut original feasible solutions in the interval.

## Vehicle Transfer Cutset

Under the empty-start vehicle convention, the net number of bikes delivered by a vehicle into a receiver subset cannot exceed pickups by that same vehicle outside the subset. The implemented static row is conservative and restricted to singleton/pair subsets.

## S-Bucket Refinement

S-bucket denominator refinement is certificate-safe only when child buckets exactly cover the parent feasible `S` domain and every bucket is closed. The current callback round keeps this as a coverage test rather than a paper certificate mechanism.
