# Round146 independent mathematical pre-review

Reviewer: `gd_independent_review`, separate from the primary implementer.
Scope: the supplied Round146 goal, R140 exact dyadic utilities, R143 denominator
water-filling, R144 append/scope conventions, R145 mathematical analysis and
four selected saved points. No production GD implementation was available at
this review stage. No Optimize, compilation, or commercial Native loading was
performed. The mathematical plan passes; production admission remains subject
to the focused checks below.

## Derivation and scope

For any set J, every cross-set pair occurs once in A, and
`|r_j-r_i| >= r_j-r_i`. All non-cross terms are nonnegative. Therefore
`A >= |J| S - n sum_{i in J} r_i`. At S>0, choose exactly the stations with
`r_i/S < 1/n`. This proves

    G >= sum_i (1/n-r_i/S)_+
      = sum_i (r_i/S-1/n)_+.

The equality follows from the zero sum of the signed deviations. This is the
classical Gini/Hoover comparison, not a new general inequality. The original
objective stays `g + lambda P`, and g is an epigraph variable: every argument
requires only `g >= G`, so it also covers valid starts with nonminimal g.

For `r=c_i*y >= 0`, the function `(1/n-r/D)_+` is nondecreasing in D, whereas
`(r/D-1/n)_+` is nonincreasing in D. Thus a lower bound on the actual S gives
the low-deviation coefficient, and an upper bound gives the high-deviation
coefficient, with precisely the directions in the goal. At one integer point,
the bound corresponding to every site's selected state holds simultaneously.
The row sums lower bounds on different Hoover summands; it does not sum n
independent lower bounds on the complete Gini value. One-hot selector integrality
therefore proves both rows, and their linearity proves validity for the convex
hull of the integer epigraph.

The condition `S>0` is essential. If the necessary whole-domain lower bound is
not positive, uniformly omitting GD is safe and preserves the existing all-zero
convention. In particular the tempting zero-count row is not valid at the
all-zero point when its Gini is defined as zero. Nonnegative c values preserve
the water-filling argument, including c=0, provided the whole-domain positive
S proof still succeeds. The production project uses positive `1/target_i`;
negative or nonfinite ratios must never be accepted as this construction's
domain.

## State-conditioned denominators

After fixing `Y_i=y`, start at the lower inventory vector l. Positivity (or
nonnegativity) of c implies that an S minimizer can use the minimum feasible
physical inventory total `max(Bminus,sum(l))`; an S maximizer can use
`min(B,sum(u))`. An exchange of fill from a larger c to a smaller c decreases
S, proving the ascending greedy fill for the minimum; the reverse exchange
proves descending fill for the maximum. Since fixed and global domains are
nested, `S_L <= D_L <= D_U <= S_U` for each feasible conditional box.

The boxes are continuous relaxations of supported inventory values. Holes in
the support cannot make their lower bound too large or their upper bound too
small. These are exact extrema of the declared continuous box/total interval,
not necessarily of the discrete support. Infeasible conditional boxes may
receive zero coefficients because the corresponding state is absent at every
integer feasible point. No state deletion is required.

Physical inventory units are essential: `Bminus <= sum Y_i <= B`, not bounds
on `sum c_i Y_i`. The actual binary64 c values must be interpreted as their
dyadic rationals; replacing them by ideal reciprocals changes the claimed
model. The R140 checked integer arithmetic and R143 ordered fill supply a
suitable existing mechanism. Check overflow before arithmetic; do not silently
fall back to approximate extrema.

Conditional coefficients dominate the global coefficients in exact arithmetic
for feasible states. Separately rounded safe rows can differ by tiny rounding
amounts, so production bitwise dominance need not be an admission condition.

## Conversion and row transport

Write `n G >= sum a_iy s_iy`, with low coefficients
`a=(1-n*c_i*y/D_L)_+` and high coefficients `a=(n*c_i*y/D_U-1)_+`.
The G coefficient n and the low coefficient for y=0 are exactly representable
at project sizes; preserve the latter as exactly 1 on applicable feasible
states. Every other emitted selector coefficient must be no greater than its
exact ideal value and nonnegative. Because selectors are nonnegative, dropping
a tiny positive selector coefficient also only relaxes the row.

For the low coefficient, enclose `n*c_i*y` upward, D_L downward, the quotient
upward, and the subtraction downward. For the high coefficient, use numerator
downward, D_U upward, quotient downward, and subtraction downward. Alternatively
an existing exact ratio/interval helper may certify the same result. A single
`nextafter` on the final expression is insufficient unless all earlier
operations' error is already enclosed. Cancellation around coefficient zero
requires the same care; outward division alone does not enclose an earlier
rounded multiplication. No solver tolerance change is justified.

Native transport must check the emitted coefficients and signs, including
any intentionally omitted tiny terms. With `sum a*s - n*G <= 0`, removing tiny
positive state terms is safe, and does not require aggressive row scaling.
If scaling is used, apply the same exact positive power of two to the entire
row and check finite values and actual readback.

## Local family and information interpretation

At S>0, z zero stations contribute exactly zS from zero/positive pairs, so
`nG >= z`. GD's low row includes this inequality and adds nonnegative terms.
For the R145 binary unit-ratio family, the nonzero-state low coefficient is
zero under the stated bounds and the zero-state coefficient is one. With
half-half selectors this is `g >= 1/2`. At binary integer points
`G=(n-tau)/n`; any mixture with those marginals has expected tau=n/2 and hence
expected G=1/2. The old 2n-point mixture attains this. Thus the local integer
epigraph value is closed by the general GD rule. This leaves R145's strict
complementarity theorem intact and is not a full BRP hull result.

The exact, zero-Optimize recheck in `independent_saved_point_check.py/json`
uses unchanged saved binary64 selectors, g and c, with no renormalization:

| Saved point | State low violation | State high violation |
| --- | ---: | ---: |
| K20 joint | 0.0258580381333251 | 0.04955721355694184 |
| K35 joint | -0.0396648917457642 | -0.0471952123683414 |
| RX20 joint | -0.0226543590926077 | -0.0970665075006670 |
| RX20 compact | 0.2352605176653413 | 0.0186545799038493 |

The recheck also confirms the inherited exact global denominator bounds,
conditional-bound nesting, and exact state-versus-global coefficient dominance
at every feasible checked state. K20's zero-selector weight is exactly zero.
Its global-row violations are 0.0246166049720767 and 0.0446632389102343.
These are original-variable point separations, stronger than merely excluding
one extension, but they do not establish a reoptimized objective increment.
K35/RX20's qualified saved joint optima remain feasible after these rows are
added and hence give same-value numerical witnesses; do not buy those two
continuous solves again. This statement inherits the previous numerical
optimality qualification and is not an exact rational optimality certificate.

The optional state-Hoover formulation is also integer-valid: a chosen subset
of states selects a station subset at each integer point, reducing to the same
set inequality. Its extension-point violation alone does not rule out another
extension of the same original x. The ordinary site-mean Hoover relation is
weaker because summation over states can cancel signs before taking absolute
values. This justifies a finite information question, not a second algorithm
panel.

## Focused production admission checks

1. Compare actual emitted coefficients with an independent exact oracle for
   heterogeneous ratios, sparse/fixed supports, a conditional infeasible state,
   and a whole-domain zero denominator. Check both bound directions and exact
   zero-state coefficients, and include nonminimal-g feasible integer starts.
2. Prove root-scope caching uses the actual canonical support and physical
   stock interval. Compatible sub-supports may delete only absent selector
   terms. Changed input, expanded support, or weaker resource bounds must not
   reuse incompatible rows. A narrower g interval/cutoff does not invalidate
   GD but is not a substitute for inventory support checks.
3. Read actual Native row names, senses, RHS, scale and NZ. Confirm at most
   two rows, no new variables, no RN/source optimization or hidden callback,
   and unchanged old matrix/objective when the independent flag is off.
4. Confirm the formal initial LP, target/terminal MIPs and proof reconstruction
   receive applicable rows, not only standalone diagnostic LPs. Retain full
   physical Start and R134 proof/lifecycle verification; separate returned
   Native bounds from external supported L.
5. Bind every affected translation unit to the measured source/PE, then run
   the one short complete health qualification. Authoring-only changes do not
   justify re-running that health solve. Full K20 admission additionally needs
   the finite actual-model LP decision and same-PE strong reference design.

No mathematical blocker was found. This report is not a production-code pass
and does not infer complete performance, promotion, or a mandatory four-role
expansion from the point separations.
