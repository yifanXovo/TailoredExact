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

The old unqualified receiver-set source-cover form is unsafe when receiver-set
stations can exchange bikes internally.

## Singleton Receiver-Set Source Cover

The strengthening round implements only the conservative singleton row.  If
tightened inventory domain `L_j` proves station `j` needs net delivery
`R_j=max(0,L_j-initial_j)`, any original feasible fixed-interval solution must
drop at least `R_j` bikes at `j`.  The valid paper-safe row is therefore:

```text
sum_k d[k,j] >= R_j
```

This is a delivery requirement, not an outside-source-cover claim.  It does not
forbid internal transfers among a larger receiver set and does not assume a
sampled route.  Pair and larger receiver-cover rows remain diagnostic until a
full compatibility proof is added.

## Dynamic Root Cuts

The current implementation records root-cut-round options and can rerun static
valid families under a root-round configuration.  It does not yet implement a
true CPLEX callback or fractional root-solution separation loop.  Therefore
dynamic-root rows in the strengthening round are diagnostic for scheduling and
metadata, not evidence for a new dynamically separated cut family.
## Round 2 Receiver Cover Status

Singleton receiver-source-cover cuts remain valid under the current empty-start
vehicle and one-service-mode station convention. Pair/set receiver-cover cuts
are not paper-core evidence in this round. The old drop-cover form is unsafe
when receiver-set stations can exchange bikes internally. A net-delivery pair
form is documented in `docs/receiver_set_source_cover_pair_proof.md`, but it
remains diagnostic pending complete proof and projection tests.

Dynamic root separation in round 2 reuses only cut families already classified
as valid. The dynamic loop may add a cut only after reading a root LP solution
and verifying a positive violation; generated cuts are logged separately from
static rows.

## Effectiveness Attribution Rules

The effectiveness round does not add a new mathematical certificate source. It
adds attribution and finalization checks around the existing sources:

- relaxation/frontier bounds remain valid when the ledger records
  `interval_closure_source=relaxation_bound` and the row passes audit;
- Compact-BC interval evidence is valid only for original fixed-interval models
  with `compact_bc_bound_scope=original_fixed_interval` or proven infeasibility;
- wrapper checkpoints are never converted into optimal certificates;
- `--compact-bc-diagnostic-force-leaf-solve` is diagnostic-only unless a future
  full-ledger merge proves exact coverage under the same instance, lambda, T,
  incumbent UB, and Gini interval partition.

These rules allow correct attribution without requiring Compact-BC to dominate
rows already closed by relaxation.

## Effectiveness Round 2 Evidence Separation

Diagnostic forced-leaf solves and plain fixed-interval MIP comparisons are valid experiments but do not contribute lower-bound evidence to a full-frontier certificate.

## Effectiveness Round 3 Evidence Separation

Safe low-Gini mode reuses proved low-Gini centering, movement/domain, penalty lower-bound, and objective-estimator rows. Aggressive diagnostic modes and plain fixed-interval MIP comparisons do not contribute lower-bound evidence to full-frontier certificates.

## Low-Gini Variable-S Centering

For any original fixed-interval solution with
`S=sum_i r_i`, `H=sum_{i<j} h_ij`, and `G=H/(V S) <= gamma_U`, the max-spread
inequality gives `H >= (V-1)(r_max-r_min)`.  Combining both inequalities yields

```text
(V-1)(r_max-r_min) <= V gamma_U S.
```

The interval upper bound `gamma_U` is constant, so this is a linear valid row.
It is safe for paper-core Compact-BC when `r_min <= r_i <= r_max` rows are also
present.  Propagating `r_min/r_max` back into integer final-inventory domains is
not enabled as paper evidence in this round.

## S*P McCormick Objective Estimator

The no-improver cutoff condition can be written as:

```text
H + V lambda S P <= V (UB-epsilon) S.
```

The implementation introduces `W_SP` with McCormick bounds over valid
nonnegative bounds on `S` and `P`, then adds:

```text
H + V lambda W_SP <= V (UB-epsilon) S.
```

Every original feasible solution can set `W_SP=S P` and satisfy the McCormick
system, so the row cannot cut an original incumbent-improving solution.  The LP
relaxation may choose a smaller `W_SP`, making the row weaker than the nonlinear
cutoff but still valid.

## S-Range Bucket Refinement Status

Rows of the form `S_L^b <= S <= S_U^b` with bucket-specific objective
estimators are valid for the corresponding S subleaf.  They are not yet
paper-core full-leaf evidence because the full frontier ledger does not
partition each Gini leaf over S and check exact bucket coverage.  The current
implementation therefore labels S-range refinement as diagnostic unless a
single bucket covers the whole parent S domain.
