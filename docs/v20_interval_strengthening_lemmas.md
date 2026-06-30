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

The required net movement from Lemma C gives a lower bound on handling time.
The oracle records this value and adds the valid aggregate capacity row
`sum cunit*(pickup+drop) <= M*T` with
`--global-handling-capacity-cuts true`.

### Lemma E: Transfer Compatibility Singleton Cuts

The current implemented transfer subset family is the safe singleton case.  If
vehicle `k` cannot travel `depot -> i -> depot` and perform one unit of
operation within `T`, then `z[k,i] = 0`.  This is a necessary condition for
every original route and is logged under transfer-subset capacity cuts.

### Lemma G: Service-Operation Linking

The compact oracle enforces `p[k,i] + d[k,i] >= z[k,i]`, matching the original
route convention that a visited station has nonzero operation.

## Not Yet Implemented

Full Hall-style multi-station transfer subset cuts and stronger low-Gini
centering bands remain future work.  They require additional proof and
separation logic before they can be used as certificate evidence.
