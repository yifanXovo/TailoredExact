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

The relaxation callback may separate the aggregate row `sum_i q_i - 2 gamma_U sum_i r_i <= 0` when the `q_l1_i` variables are present. The callback row is identical to the static aggregate cap, so its certificate role is the same paper-safe row family.

## Subset Inventory Imbalance

For a station subset `A`, let `Y_A = sum_{i in A} Y_i`, `I_A = sum_{i in A} initial_i`, `room(A) = sum_{i in A} (capacity_i - initial_i)`, and `bikes(A) = sum_{i in A} initial_i`. A vehicle can increase `Y_A` only by carrying bikes into `A`, and can decrease `Y_A` only by removing bikes from `A`. For every vehicle `k`, the conservative movement bounds

`DeltaPlus_k(A) <= min(Q_k, room(A), floor(T_k / cunit))`

and

`DeltaMinus_k(A) <= min(Q_k, bikes(A), floor(T_k / cunit))`

are safe under the current duration convention because they ignore travel time and compatibility and therefore overestimate what the vehicle can move. Summing over vehicles gives:

`Y_A <= I_A + sum_k DeltaPlus_k(A)`

and

`Y_A >= I_A - sum_k DeltaMinus_k(A)`.

The callback implementation separates the equivalent `<=` forms for singleton, pair, and triple station subsets from relaxation points. These rows are intentionally weak but paper-safe; stronger route-duration or compatibility-filtered subset inventory rows require separate proof before paper-core use.

## Vehicle Transfer Cutset

Under the empty-start vehicle convention, the net number of bikes delivered by a vehicle into a receiver subset cannot exceed pickups by that same vehicle outside the subset:

`sum_{j in D} d[k,j] - sum_{j in D} p[k,j] <= sum_{i notin D} p[k,i]`.

Equivalently, the basic unfiltered row can be written as:

`sum_{j in D} d[k,j] <= sum_i p[k,i]`.

This latter form is weaker but paper-safe for every receiver subset `D`: a vehicle starts with zero load, so total drops into any subset cannot exceed the total number of bikes picked up by that vehicle. The callback implementation separates this basic row for singleton, pair, and triple receiver subsets at relaxation points. Compatibility-filtered variants remain diagnostic/future work unless their source sets are proved supersets of all feasible external pickup sources.

## Support-Duration Cover Cuts

For vehicle `k` and a station subset `A`, let `cycle_lb_k(A)` be the exact depot-cycle lower bound used by the static compact-BC model for visiting all stations in `A`. Under the current compact duration convention, handling time is charged as `cunit * sum_i p[k,i]`. If a route visits every station in `A`, at least `ceil(|A|/2)` pickup units are required by the support-duration cover rule used in the static model, so any such route requires at least:

`cycle_lb_k(A) + cunit * ceil(|A|/2)`.

When this value exceeds `T_k`, no feasible original route for vehicle `k` can visit all stations in `A`. The cover row

`sum_{i in A} z[k,i] <= |A| - 1`

is therefore valid. The callback implementation currently separates only the violated pair and triple cover rows from high-support relaxation points. It does not add the static model's conditional big-M duration rows in callback form. Quad and lifted support-duration cuts remain future work.

## S-Bucket Refinement

S-bucket denominator refinement is certificate-safe only when child buckets exactly cover the parent feasible `S` domain and every bucket is closed. The current callback round keeps this as a coverage test rather than a paper certificate mechanism.
