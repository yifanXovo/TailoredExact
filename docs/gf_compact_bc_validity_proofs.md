# GF Compact BC Validity Proofs

All paper-core cuts are necessary conditions for original feasible route-load
solutions in the fixed Gini interval.

## Handling Convention

The verifier and compact model use
`travel_k + cunit * sum_i p[k,i] <= T`, where
`cunit = pickup_time + drop_time`.  The aggregate handling row is therefore
`cunit * sum_{k,i} p[k,i] <= M*T`.  The old row
`cunit * sum_{k,i}(p[k,i]+d[k,i]) <= M*T` is not valid under this convention
and is excluded from paper-core evidence.  `scripts/test_compact_handling_convention.py`
checks the generated LP for this regression.

## Direct Gini Cap And Floor

For `H=sum_{i<j} h_ij` and `S=sum_i r_i`, interval membership implies
`gamma_L <= H/(V*S) <= gamma_U`.  Multiplying by the positive quantity `V*S`
gives `H <= V*gamma_U*S` and `H >= V*gamma_L*S`.

## Interval McCormick Rows

For binary `b`, continuous `G in [gamma_L,gamma_U]`, and `w=G*b`, the four
standard McCormick hull rows over the interval are valid and dominate the old
generic `[0,1]` product rows.

## Inventory Conservation

Vehicles start empty and may return residual pickups to the depot, so total
station inventory cannot increase and can decrease by at most total truck
capacity: `B0 - sum_k Q_k <= sum_i Y_i <= B0`.

## Movement-Reachability Domains

A station is served by at most one vehicle.  If vehicle `k` cannot reach station
`i`, perform `q` movement units, and return within `T`, then that vehicle cannot
change `Y_i` by `q`.  Taking the maximum reachable pickup/drop amount over
vehicles safely tightens `Y_i`.

## Visit/Inventory Linking

If no vehicle visits station `i`, station inventory cannot change.  The rows
`Y_i-initial_i <= (capacity_i-initial_i) sum_k z[k,i]` and
`initial_i-Y_i <= initial_i sum_k z[k,i]` encode this implication.

## Objective Lower Estimator

With a valid upper bound `S_U >= S`, the cutoff condition
`G + lambda P <= UB-epsilon` and `G=H/(V*S)` imply the necessary row
`H + V*S_U*lambda*P <= V*S_U*(UB-epsilon)`.

## Penalty Lower Bound

For each tightened domain `[L_i,U_i]`, the minimum possible
`|Y_i/target_i-1|` yields a lower bound on each penalty term.  Summing gives
`P_LB`; if `gamma_L + lambda*P_LB >= UB-epsilon`, the leaf has no improving
solution.

## Support-Duration Cuts

For pairs/triples, exact depot cycle lower bounds give a valid travel lower
bound for any route visiting the support.  If this plus a conservative minimum
handling count exceeds `T`, the support is incompatible.  Conditional duration
rows use a conservative big-M and are inactive unless every station in the
support is assigned to the vehicle.

## Transfer Compatibility

Under empty-start and one-mode-per-station conventions, a positive drop at `j`
by vehicle `k` requires compatible pickup quantity at some station that can be
visited before `j` within a conservative travel/handling lower bound.  If no
such pickup station exists, `d[k,j]=0`.

## Diagnostic Only

Receiver-set source-cover cuts are not default paper-core evidence.  The old
unqualified form is unsafe when receiver-set stations can exchange bikes
internally.
