# Independent exact theorem for the heterogeneous three-station example

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).
This proof concerns the complete declared **inventory objective block**.
It does not assert a feasible extension through a full routing model or
strictness over every historical source/disjunction or normalized hull.

## 1. Domain, strong reference and source fields

The domain is n=3, c=(1,1/2,1/4), Y_i in {0,1,2,3,4},
2<=Y_1+Y_2+Y_3<=5, gamma_L=0, gamma_U=3/4, and omega_i=1/8.
The upper Gini constraint is nonbinding for these nonnegative three-station
ratios because G<=2/3. The physical objective on this necessary inventory
domain is phi(Y)=G(Y)+(1/8) sum_i |c_i Y_i-1|.

The declared continuous reference has the inventory/ratio equalities,
one-hot selectors, local absolute deviations, all VD-P state/G products,
the original pairwise Gini numerator inequalities, and hard total bounds.
It additionally retains AP, both conditional GD rows, all four stock
product rows, old TC, TC2, every supported-threshold lower/upper count row,
and all four count/G product rows at every threshold. This is a precise
finite reference, not an assertion that every old algorithm has been
combined or that routes have been convexified.

Authoritative main-study inputs are:

- `small/v2/heterogeneous_wide/result.json`: `scope`,
  `exact_reference_objective`, `exact_integer_minimum`, and `mixture`.
- `small/v2/heterogeneous_wide/exact_extension.json.gz`: the complete
  rational extension, in particular each `state_i_y`, `state_g_i_y`, `G`,
  `Y_i`, `r_i`, `e_i`, `zprod_i`, and `h_i_j` field.
- `small/v2/heterogeneous_wide/reference.mps`: all 117 reference rows and
  46 variable bounds/objective coefficients.

The independent checker and result are `independent_exact_small.py` and
`independent_exact_small.json` in this review directory. It imports no main
implementation helper, uses no solver or Native API, reads MPS with an
independent small parser, and interprets its coefficients as the loaded
binary64 numbers. All consumed file hashes and the checker hash are in the
result. Its separately measured process outer fee is in
`independent_exact_small_fee.json`; the nested script time is not added.

## 2. A complete exact feasible reference extension

The nonzero selector masses are

    s_11 = 1,
    s_21 = 3/4, s_22 = 1/4,
    s_32 = 1/2, s_33 = 1/2.

All other selector masses are zero. Set g=1/10. The only nonzero state/G
products are q_11=q_22=q_32=1/10. The inventory, ratio, deviation and product
coordinates are

| i | Y_i | r_i | e_i | Z_i |
|---|---:|---:|---:|---:|
| 1 | 1 | 1 | 0 | 1/10 |
| 2 | 5/4 | 5/8 | 3/8 | 1/5 |
| 3 | 5/2 | 5/8 | 3/8 | 1/5 |

Take h_12=h_13=3/8 and h_23=0. Thus the numerator total is 3/4 and
3 sum_i c_i Z_i=3/4. AP is tight at 3/32. The original linear objective is

    f_ref = 1/10 + 3/32 = 31/160.

Independent exact arithmetic verifies all 117 rows and 46 variable bounds,
not only selected scalar formulas. Every state with positive selector mass
has zero low/high ideal conditional GD coefficient; these rows are satisfied
even before downward coefficient rounding. All other active reference
coefficients in this example are dyadic, so the strict gap is not an artifact
of weakening GD by a tiny serialization margin.

The independently enumerated exact count intervals, which match the saved
reference, are:

| Threshold | Minimum K | Maximum K |
|---|---:|---:|
| 1/4 | 1 | 3 |
| 1/2 | 1 | 3 |
| 3/4 | 0 | 2 |
| 1 | 0 | 2 |
| 3/2 | 0 | 2 |
| 2 | 0 | 1 |
| 3 | 0 | 1 |
| 4 | 0 | 1 |

Thus this example is not merely exploiting omission of a tighter individual
count range on one supported threshold.

## 3. Unique common distribution and exact same-marginal epigraph gap

At the stated marginals, nonnegative common-distribution weights force
Y_1=1, Y_2 in {1,2}, and Y_3 in {2,3}. The combination (1,2,3) has total 6
and violates the hard resource upper bound. Exactly three combinations
remain. The event Y_2=2 occurs only in (1,2,2), fixing its mass to 1/4.
The event Y_3=3 occurs only in (1,1,3), fixing its mass to 1/2. The remaining
mass 1/4 belongs to (1,1,2). Consequently the feasible common distribution
is unique; this conclusion needs no dual optimality claim.

| Y | Forced probability | G(Y) | Penalty | phi(Y) |
|---|---:|---:|---:|---:|
| (1,1,2) | 1/4 | 1/6 | 1/8 | 7/24 |
| (1,1,3) | 1/2 | 4/27 | 3/32 | 209/864 |
| (1,2,2) | 1/4 | 2/15 | 1/16 | 47/240 |

The saved exact mixture is independently checked against every marginal,
including all zero states, and against the hard resource/Gini conditions.
It proves compatibility, so the remaining gap is objective information,
not an empty common-distribution projection.

Because the distribution is unique,

    Theta(s) = (1/4)(7/24) + (1/2)(209/864) + (1/4)(47/240)
             = 1049/4320,
    H_AP(s)  = 3/32,
    Gamma(s) = Theta(s)-H_AP(s) = 161/1080.

Therefore

    Theta(s)-f_ref = Gamma(s)-g = 53/1080 > 0.

This is an exact fixed-marginal epigraph separation beyond the declared
AP/GD/stock/TC/TC2/all-count/CP block. The common distribution has inventory
totals 4 or 5, so it uses hard inventory feasibility rather than only a
constraint on the average total. No route, load or travel feasibility is
needed for this declared inventory-domain statement.

## 4. A separate full-domain strictness statement

The independent checker enumerates all 125 supported inventory triples,
retains the 49 satisfying the hard total bounds, and evaluates every
objective with Fraction arithmetic. The unique integer minimum occurs at
(1,2,2) and equals 47/240. Hence

    min_(Y in R) phi(Y) - f_ref = 47/240 - 31/160 = 1/480 > 0.

This proves that the reference admits a point below even the global
inventory objective floor. It does not need a proof that 31/160 is the
exact optimal reference LP value: a feasible point below the exact integer
minimum already proves strictness. The observed numerical reference LP
optimum is reported separately. The 1/480 global-floor gap and the
53/1080 same-marginal epigraph gap answer different questions and must not
be interchanged.

The R133 equal-target control is closed by the declared strong reference,
as expected from earlier count/stock/GD results. The other two finite
generated controls show no reported scalar gap. They remain controls,
not omitted adverse observations. The heterogeneous example demonstrates
a remaining structural distinction; usefulness and cost on complete real
models require the separate free-LP/oracle evidence.
