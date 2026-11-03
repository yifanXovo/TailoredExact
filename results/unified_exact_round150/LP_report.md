# Three complete matched PF to CPF LPs

The old R149 complete PF MPS/result/solution/arithmetic records are reused from
fixed science `3bb93fa2f4b8c267af8fae409864191e033c5bb2` and the archive pinned in
`reuse_index.json`. No D or PF baseline was reoptimized. Only fixed-dual CPF
rows were appended, preserving all old rows, objective, constant, variable
domains, supports and cutoff exactly. Every variable was free during the new
Optimize. Independent MPS parsing and actual Gurobi readback confirm this scope.

| Domain | Saved D value | Saved PF value | New CPF value | PF−D | CPF−PF |
|---|---:|---:|---:|---:|---:|
| K20 base | .236010302342365 | .237043344713575 | .237826346116704 | .001033042371211 | .000783001403129 |
| K35 base | .204187028163866 | .206104958905020 | .206603355168264 | .001917930741154 | .000498396263243 |
| RX20 base | .365004645621491 | .365603247853745 | .366724025832099 | .000598602232255 | .001120777978353 |

These are numerical optimization comparisons on three fixed domains, not
full-method endpoints or exact rational optimality certificates. The PF−D
column belongs to R149; it is not credited to CPF. All three new solves return
OPTIMAL at Seed0/Threads1 with the unchanged Native DLL, cap120s and the existing
1e-6 feasibility/optimality parameters. There are three new Optimize calls and
three returns, with zero repeated baseline and zero additional quality Optimize.

The old R149 K35 scalar-only control differs from its old D value by
−3.225086737e-7. That is compatible with the accepted numerical qualification
and the scalar bound's exact theoretical redundancy; it is not evidence of a
strict mathematical weakening. This historical control is reused without
Optimize and is not a new CPF position.

| Domain | Added rows / NZ | Old point violations / maximum | Fraction (s) | Construct incl. readback (s) | Readback (s) | Native Runtime (s) |
|---|---:|---:|---:|---:|---:|---:|
| K20 | 451 / 902 | 15 / .019306833244 | .011614 | .635329 | .196054 | .188000 |
| K35 | 539 / 1078 | 34 / .003655840423 | .012430 | 2.379407 | .766096 | 1.031000 |
| RX20 | 143 / 286 | 8 / .051858032938 | .003651 | .545276 | .174739 | .082000 |

The construction and Native times are nested observations; the metered outer
fees include them once. Native Runtime is not added to the outer a second time.
The fixed actual binary64 multipliers, exact station minima, prefix/suffix
leave-one-out sums, all transported beta coefficients, actual added rows and
their model SHA are preserved in each `LP/*_CPF/arithmetic.json` and
`construction.json`. Models and primal/dual solutions remain immutable in the
indexed diagnostic carrier. No state bound is promoted to a global g bound.

## Numerical quality and the K35 boundary

| New CPF domain | Direct row residual | Bound violation | DualVio | DualResidual | Numeric primal−dual |
|---|---:|---:|---:|---:|---:|
| K20 | 1.819e-12 | 0 | 3.730e-17 | 1.166e-15 | 2.776e-17 |
| K35 | 1.819e-12 | 0 | 3.469e-18 | 2.776e-16 | 1.138e-15 |
| RX20 | 9.095e-13 | 0 | 0 | 5.551e-16 | 5.551e-17 |

All new ConstrVio, BoundVio and ComplVio are zero, with ConstrResidual at most
7.276e-12. The diagnostic dual objective is the row multiplier/RHS sum plus
the reduced-cost contribution at its favorable bound. All new adverse reduced
costs at an infinite bound are zero. Complete quality attributes and both the
direct primal check and this numerical dual diagnostic are saved, rather than
inferring an objective-error bound from local solver tolerances alone.

The old K35 PF primal−dual diagnostic difference is .000619045711770 and its
DualVio is about8.92e-7. That remains a limitation of the old optimum record.
The new K35 CPF numerical dual is .206603355168262, above the old *saved primal*
.206104958905020 by about.000498396263242. Thus the present positive comparison
does not rely on treating the old weaker diagnostic dual as a precise optimum.
The new KKT diagnostics are much tighter, while neither record is claimed to
be an exact rational certificate. No old LP is repurchased and no extra
Optimize is needed to decide this finite numerical screen.

The old point violations alone could have been removed by moving to another
old optimum. Complete free reoptimization instead reports positive increments
on all three domains. CPF therefore passes the **matched numerical LP increment**
stage at low arithmetic cost. This is sufficient for a future unified production
candidate to be worth evaluating; it does not establish end-to-end benefit.
The next informative step would qualify one fixed-dual CPF implementation on
top of D+PF, including actual transport, Start and child scope, then compare
D+PF against D+PF+CPF with complete own H on the original RB35 objective,
where PF previously exposed an incumbent cost. This is a future study, with
the same candidate used uniformly and presolve, search and incumbent/bound tradeoffs as
risks. This round does not write production C++, build a PE or start CPF full.

RB35's old root separation is background only; there is no fourth LP, no
exact-conditional matrix, no multi-round propagation and no AP/STOCK/Shared-S/RN
combination panel. The CPF task ends independently of the B/D confirmation.
