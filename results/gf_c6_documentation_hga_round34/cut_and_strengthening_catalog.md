# C6 cut and strengthening catalog

## Notation and counting convention

The current C6 metadata names 15 active strengthening families: six global
and nine interval-local. Structural base-model constraints, the two bounds on
the interval's `G` variable, final-inventory domain bounds, and the verified
incumbent objective row are documented here but are not added to that count.

For station \(i\), vehicle \(k\), and station pair \(i<j\), use:

- \(Y_i\): final station inventory; \(s_i^0\): initial inventory;
  \(c_i\): station capacity; \(\widehat Y_i\): target;
- \(p_{ki},d_{ki}\): pickup and drop quantities;
- \(z_{ki}\): vehicle-visit indicator;
- \(r_i=Y_i/\widehat Y_i\), \(e_i\ge |r_i-1|\), and
  \(h_{ij}\ge|r_i-r_j|\);
- \(S=\sum_i r_i\), \(H=\sum_{i<j}h_{ij}\),
  \(P=\sum_i w_i e_i\), and \(G=H/(VS)\);
- \([\gamma_L,\gamma_U]\): the current Gini interval;
- \([S_L,S_U]\), \([P_L,P_U]\), and
  \([Y_i^L,Y_i^U]\): safe interval-local domains;
- \(U\): independently verified minimization upper bound,
  \(C=U-\varepsilon\): strict improving cutoff;
- \(Q_k\): vehicle capacity, \(T\): route-duration limit, and
  \(c_h=t_{pickup}+t_{drop}\): handling time per pickup/drop cycle.

All rows are written into the deterministic canonical fixed-interval model and
therefore affect both its LP relaxation and its native MIP unless the entry is
only a bound tightening. C6 uses static construction; these are not
dynamically separated Gurobi callback cuts.

## Summary

| Family | Scope | Precise type | LP | MIP | Construction authority |
|---|---|---|---:|---:|---|
| inventory conservation | global | aggregate valid inequalities | yes | yes | `writeCanonicalCompactModel` |
| movement reachability domains | global | domain tightening | yes | yes | canonical writer + `buildRound18StaticIntervalRows` |
| visit-inventory linking | global | valid linking inequalities | yes | yes | canonical writer |
| global handling capacity | global | aggregate valid inequality / infeasibility test | yes | yes | canonical writer |
| support duration | global | route-support cover and conditional duration inequalities | yes | yes | canonical writer |
| transfer compatibility | global | pairwise valid compatibility inequality | yes | yes | canonical writer |
| direct Gini cap/floor | interval | exact cross-multiplied interval constraints | yes | yes | `buildRound18StaticIntervalRows` |
| interval-tight McCormick | interval | convex-hull binary-product strengthening | yes | yes | row factory |
| objective-estimator cutoff | interval | cutoff-based valid estimator | yes | yes | row factory |
| penalty lower-bound closure | interval | domain-derived lower bound and no-improver closure | yes | yes | row factory |
| Gini spread | interval | valid inequality | yes | yes | row factory |
| required movement | interval | domain-derived valid inequality | yes | yes | row factory |
| low-Gini centering | interval | projected exact range valid inequalities | yes | yes | row factory |
| variable-\(S\) centering | interval | projected valid inequalities | yes | yes | row factory |
| \(SP\)-product estimator | interval | McCormick relaxation plus cutoff estimator | yes | yes | row factory |

## Global families

### 1. Inventory conservation

Let \(I_0=\sum_i s_i^0\) and \(Q_\Sigma=\sum_k Q_k\). The writer adds

\[
  I_0-Q_\Sigma\le\sum_iY_i\le I_0.
\]

The upper row states that vehicles cannot create station inventory; the lower
row uses the maximum total inventory that can remain loaded at route ends.
These aggregate inequalities are valid for the full root domain and are
constructed once per canonical interval model. They strengthen both LP and
MIP. Source: `writeCanonicalCompactModel` in `src/CplexBaseline.cpp`, enabled
by `compact_bc_inventory_conservation`; registered as
`inventory_conservation` by `buildRound18StaticIntervalRows`.

### 2. Movement reachability domains

For station \(i\), the code computes

\[
 a_{ki}=\max\left(0,\left\lfloor
 \frac{T-d_{0i}-d_{i0}}{c_h}\right\rfloor\right),
\]

then

\[
 R_i^p=\max_k\min\{s_i^0,Q_k,a_{ki}\},\qquad
 R_i^d=\max_k\min\{c_i-s_i^0,Q_k,a_{ki}\}.
\]

The safe final-inventory bounds are tightened to

\[
  s_i^0-R_i^p\le Y_i\le s_i^0+R_i^d.
\]

The bound assumes even the most favorable direct depot--station--depot route;
any real route has no more movement opportunity. It is a domain tightening,
not a cut. The shared row factory intersects it with any independently safe
incumbent/penalty domains before deriving interval rows. Sources:
`writeCanonicalCompactModel` and `buildRound18StaticIntervalRows`.

### 3. Visit-inventory linking

With \(v_i=\sum_k z_{ki}\) and the base constraint \(v_i\le1\), the two rows
are

\[
  Y_i\le s_i^0+(c_i-s_i^0)v_i,
  \qquad
  Y_i\ge s_i^0(1-v_i).
\]

If no vehicle visits \(i\), both force \(Y_i=s_i^0\); if one visits, they
reduce to station-capacity bounds. These are global valid linking
inequalities, constructed once and active in both LP and MIP. Source:
`writeCanonicalCompactModel`, option `compact_bc_visit_inventory_linking`.

### 4. Global handling capacity

The active row is pickup-only:

\[
  c_h\sum_{k,i}p_{ki}\le MT.
\]

Each vehicle's base duration constraint already charges \(c_h p_{ki}\), so
summing the \(M\) duration capacities yields this valid aggregate relaxation.
If separately derived mandatory pickup handling exceeds \(MT\), the writer
also emits an empty-row infeasibility constraint. This is a global valid
inequality plus a safe derived infeasibility test; it is not the exact route
duration model. Source: `writeCanonicalCompactModel`, option
`global_handling_capacity_cuts`.

### 5. Support duration

For vehicle \(k\) and a station subset \(A\) of the configured sizes two and
three, let \(\tau(A)\) be the implemented depot cycle lower bound and
\(m(A)=c_h\lceil |A|/2\rceil\).

If \(\tau(A)+m(A)>T\), the route-support cover is

\[
  \sum_{i\in A}z_{ki}\le |A|-1.
\]

Otherwise the writer adds a conditional duration row

\[
  c_h\sum_{i\in A}p_{ki}+B\sum_{i\in A}z_{ki}
  \le T-\tau(A)+B|A|,
\]

where the code chooses

\[
 B=T+\tau(A)+c_h\max\left(1,
   \sum_{i\in A}\min\{s_i^0,Q_k\}\right).
\]

When every station in \(A\) is visited, this enforces the cycle lower bound
plus actual handling; otherwise the conservative \(B\) deactivates the row.
These are static valid inequalities, not user cuts. Empirical counters retain
pair and triple rows separately. Source: `writeCanonicalCompactModel`, helper
cycle-lower-bound functions, options `compact_bc_support_duration_cuts` and
`compact_bc_support_cut_max_size`.

### 6. Transfer compatibility

For a potential receiving station \(j\), define the compatible sources

\[
  A_{kj}=\{i\ne j:
  d_{0i}+d_{ij}+d_{j0}+c_h\le T\}.
\]

The writer adds

\[
  d_{kj}\le\sum_{i\in A_{kj}}p_{ki}.
\]

A vehicle cannot drop inventory at \(j\) unless it can first collect that
amount from a distinct station on at least the optimistic two-station route.
This is a global pairwise compatibility valid inequality. Source:
`writeCanonicalCompactModel`, option
`compact_bc_pairwise_transfer_compatibility`.

## Interval-local families

### 7. Direct Gini cap and floor

The Gini identity \(G=H/(VS)\) and the interval imply

\[
  H-V\gamma_U S\le0,
  \qquad
  H-V\gamma_L S\ge0.
\]

These are exact cross-multiplied interval restrictions (the active domains
ensure the denominator interpretation used by the original formulation). They
are constructed for every interval and inherited/rebuilt for children. Source:
`buildRound18StaticIntervalRows`, option `compact_bc_direct_gini_rows`.

### 8. Interval-tight McCormick rows

The base formulation contains binary expansion bits \(b_{i\ell}\) for final
inventory and product variables \(q_{i\ell}=G b_{i\ell}\). With
\(G\in[g_L,g_U]\), the row factory adds the binary-product convex hull:

\[
\begin{aligned}
 q_{i\ell}&\ge g_L b_{i\ell}, &
 q_{i\ell}&\le g_U b_{i\ell},\\
 q_{i\ell}&\ge G+g_Ub_{i\ell}-g_U, &
 q_{i\ell}&\le G+g_Lb_{i\ell}-g_L.
\end{aligned}
\]

This is an interval-specific McCormick strengthening. It is exact for a binary
multiplier and is active in LP and MIP. Source: row factory, option
`compact_bc_tight_mccormick`.

### 9. Objective-estimator cutoff

Because \(H=VSG\), \(S\le S_U\), and an improving solution obeys
\(G+\lambda P\le C\), the safe relaxation

\[
  H+VS_U\lambda P\le VS_U C

\]

is added when a verified cutoff and positive \(S_U\) exist. This is a
cutoff-based lower-estimator row; it is not the objective definition. Source:
row factory, option `compact_bc_objective_estimator_cutoff`.

### 10. Penalty lower-bound closure

The local final-inventory domains imply

\[
 e_i\ge
 \operatorname{dist}\left(1,
 [Y_i^L/\widehat Y_i,Y_i^U/\widehat Y_i]\right),
\]

and hence a computed \(P_L\). The factory explicitly adds

\[
  P=\sum_iw_ie_i\ge P_L.
\]

If

\[
  \gamma_L+\lambda P_L\ge C-10^{-9},
\]

the interval contains no strict improver and the factory emits the
contradictory empty row \(0\le-1\). This is a domain-derived valid lower bound
and exact no-improver closure, not a heuristic prune. Source: row factory,
option `compact_bc_penalty_lb_closure`.

### 11. Gini spread

For every \(i<j\), the factory adds

\[
  (V-1)h_{ij}-V\gamma_U\sum_t r_t\le0.
\]

The total pairwise dispersion bounds any single pairwise deviation; the
coefficient \(V-1\) is the implemented projection. This is an interval-local
valid inequality driven by the upper Gini bound. Source: row factory, option
`gini_spread_cuts`.

### 12. Required movement

The inventory balance is

\[
  Y_i+\sum_kp_{ki}-\sum_kd_{ki}=s_i^0.
\]

Therefore the local domains yield

\[
 \sum_k(d_{ki}-p_{ki})\ge Y_i^L-s_i^0
 \quad\text{when }Y_i^L>s_i^0,
\]

and

\[
 \sum_k(p_{ki}-d_{ki})\ge s_i^0-Y_i^U
 \quad\text{when }Y_i^U<s_i^0.
\]

These are exact consequences of balance and interval-local domains. Source:
row factory, option `required_movement_cuts`.

### 13. Low-Gini centering

The row factory projects the ratio-extrema formulation into pairwise range
rows. With

\[
  \Delta_U=\frac{V\gamma_U S_U}{V-1},
\]

it adds, for every \(i<j\),

\[
  r_i-r_j\le\Delta_U,\qquad r_j-r_i\le\Delta_U.
\]

These are projected exact ratio-range upper bounds under the interval and
local \(S\) domain. Avoiding eliminable extrema variables also avoids a known
presolve interaction. Source: row factory, option
`low_gini_ratio_band_tightening` together with direct Gini rows.

### 14. Variable-\(S\) centering

Rather than substituting \(S_U\), the stronger variable-sum projection is

\[
  (V-1)(r_i-r_j)-V\gamma_U\sum_t r_t\le0,
\]

plus the reverse inequality for every pair. This is an interval-local valid
inequality using the actual \(S\). Source: row factory, option
`compact_bc_variable_s_centering`, active inside the low-centering block.

### 15. \(SP\)-product estimator

Let \(W_{SP}\) represent a relaxation of \(SP\), with
\(S\in[S_L,S_U]\) and \(P\in[P_L,P_U]\). The factory adds the four continuous
McCormick inequalities, written equivalently as

\[
\begin{aligned}
W&\ge S_LP+P_LS-S_LP_L,\\
W&\ge S_UP+P_US-S_U P_U,\\
W&\le S_UP+P_LS-S_U P_L,\\
W&\le S_LP+P_US-S_L P_U.
\end{aligned}
\]

It then adds the cross-multiplied cutoff estimator

\[
  H-VC S+V\lambda W_{SP}\le0.
\]

The McCormick system is a valid relaxation of the continuous bilinear product;
the final row is a cutoff-based estimator. Source: row factory, option
`compact_bc_sp_product_estimator=paper-safe` with tight local product bounds.

## Structural interval and cutoff rows outside the 15-family count

Each fixed-interval model also receives \(\gamma_L\le G\le\gamma_U\) and safe
final-inventory bounds. When the same-run incumbent is verified, the exact
improving row

\[
  G+\lambda\sum_iw_ie_i\le U-\varepsilon
\]

is added. It preserves at least one global optimum whenever the incumbent is
not already optimal, and makes each interval model a search for a strict
improver. These are essential structural/cutoff restrictions, but the Round 34
headline “15 active strengthening families” follows the explicit six-plus-nine
registry requested for the paper catalog.

## Construction, inheritance, and audit

`buildRound18StaticIntervalRows` emits canonical coefficient maps, senses,
right-hand sides, bound changes, family names, scopes, validity notes, and
stable signatures. `writeCanonicalCompactModel` combines those rows with the
base model. C6's frozen `full-inherited-pack`/`deferred` profile constructs the
complete static interval model before its LP or MIP is solved. Children receive
their own valid local domains and exact row signatures; atomic split requires
their inherited lower bounds, not merely row similarity.

Round 32--33 evidence shows that child lookahead and adaptive splitting are
active, but it does not establish that any one family always reduces runtime.
The current repository contains broad counters and row-signature ledgers, not
a clean 15-way causal ablation. Accordingly this catalog claims validity and
active construction, not unsupported family-specific speedups.
