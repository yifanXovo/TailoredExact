# V20 Interval Strengthening Lemmas

This round adds certificate-safe strengthening to the exact interval oracle used by
`paper-exact-v20-certificate`.  The cuts are generic and do not branch on
instance names, known optima, or manually selected intervals.

## Implemented Lemmas

### Lemma A: Gini Max-Spread Bound

Let `r_i = Y_i / target_i` and `H = sum_{i<j} |r_i-r_j|`.  For any vector
`r`, `H >= (V-1)(max_i r_i - min_i r_i)`.  Since the interval enforces
`G <= gamma_U` and the compact model represents `G * sum_i r_i >= H / V`,
every pairwise spread satisfies

`(V-1) h_ij <= V * gamma_U * sum_t r_t`.

The implementation adds this row for every pair when `--gini-spread-cuts true`.

### Lemma B: Station Final-Inventory Domain Tightening

For incumbent cutoff `UB`, interval lower endpoint `gamma_L`, and `lambda > 0`,
any incumbent-improving solution must satisfy

`P <= (UB - gamma_L) / lambda`.

Because each penalty term is nonnegative,
`w_i |Y_i / target_i - 1| <= P_budget`.  The compact oracle uses this to tighten
integer bounds on each `Y_i`.  The row is safe for no-improver certificates
because solutions outside this domain already cannot beat the incumbent cutoff.

### Lemma C: Required Station Movement

If the tightened domain is `Y_i in [L_i,U_i]`, then:

- `L_i > initial_i` implies net delivery at station `i` is at least
  `L_i - initial_i`;
- `U_i < initial_i` implies net pickup at station `i` is at least
  `initial_i - U_i`.

The oracle adds the corresponding aggregate pickup/drop rows with
`--required-movement-cuts true`.

### Lemma D: Global Handling Capacity

The current verifier and compact model use the route-duration convention

`travel_k + cunit * sum_i p[k,i] <= T`,

where `cunit = pickup_time + drop_time`.  Drop quantities are not charged
separately in this convention; the handling cost for moving one bike is
accounted when the bike is picked up.  Therefore the only certificate-safe
aggregate handling row under this convention is

`cunit * sum_{k,i} p[k,i] <= M*T`.

The previous row `cunit * sum_{k,i} (p[k,i] + d[k,i]) <= M*T` is not
paper-core safe and must not be used as lower-bound evidence unless the entire
verifier/model duration convention is changed.  The implementation records
`global_handling_capacity_lb = cunit * required_pick_min`.

### Lemma E: Transfer Compatibility Singleton Cuts

The current implemented transfer subset family is the safe singleton case.  If
vehicle `k` cannot travel `depot -> i -> depot` and perform one unit of
operation within `T`, then `z[k,i] = 0`.  This is a necessary condition for
every original route and is logged under transfer-subset capacity cuts.

### Lemma G: Service-Operation Linking

The compact oracle enforces `p[k,i] + d[k,i] >= z[k,i]`, matching the original
route convention that a visited station has nonzero operation.

## Not Yet Implemented Or Diagnostic

Full Hall-style multi-station transfer subset cuts remain future work.  The
old direct form `sum drops in D <= sum compatible outside pickups` is not used
as paper-core evidence because it can be invalid when transfers occur inside
`D`.  Only conservative singleton/pair compatibility rows with documented
empty-start and one-mode-per-station assumptions may be enabled by default.
