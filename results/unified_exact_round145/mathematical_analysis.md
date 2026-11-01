# Connecting counts and physical inventory to reciprocal normalization

The carrier is the stable R137 BASE formulation. The research source adds the
production-capped R143 RN block and six rows, with no further columns. All
statements below use a positive proved denominator bound and the actual finite
selector support. Physical inventory, ratio total and the two product factors
g and t are distinguished throughout. Standard concave chords, RLT/endpoint
decomposition and dual aggregation are credited as such; this is a connection
of problem information, not a new general convexification method.

## Integer identities and the normalized count rows

Let r_i=c_iY_i, S=Σr_i>0, A=Σ_{i<j}|r_i−r_j| and G=A/(nS).
For finite supported ratio levels, let θ_j be increasing positive thresholds
with Δ_j=θ_j−θ_{j−1}>0 (θ_0=0) and K_j=Σ_{i,y:c_iy≥θ_j}s_iy.
At every integer selector point,

    A = Σ_j Δ_j K_j(n−K_j).

R140 obtains valid integer count bounds ell_j≤K_j≤u_j from actual supported
physical stocks and Bminus≤ΣY_i≤B. Its TC chord through0,u and TC2 chord
through ell,u give, respectively,

    K(n−K) ≥ (n−u)K,
    K(n−K) ≥ ell*u + (n−ell−u)K.

Each aggregate is A≥b+Σk_iy s_iy. In the integer RN extension t=1/S,
w_iy=t*s_iy and v_i=c_iΣy*w_iy. The RN abs epigraph has
Hhat=Σhhat_ij≥t*A and Hhat≤n*g. Multiplying the integer-valid count
aggregate by t>0 yields NC:

    Hhat − b*t − Σk_iy*w_iy ≥ 0.

Both NC1 and NC2 are retained. Their RHS difference is
ΣΔ_j*ell_j*(u_j*t−W_j), W_j=Σ_{c_iy≥θ_j}w_iy. Fractional w/t
need not satisfy integer K upper bounds. Hence NC2 cannot unconditionally
replace NC1. Negative k, the b*t term, actual dyadic threshold identities and
physical support ranges are essential. Old TC/TC2 rows on H do not themselves
constrain Hhat,w.

The production writer calls the unchanged exact-dyadic R140 generator.
Its downward signed coefficient/constant conversions remain safe because
w,t≥0. Diagnostic LPs instead aggregate exact Fraction coefficients and apply
a signed finite-box conversion correction to the whole row. These are separate
valid floating representations of the same ideal NC construction; neither is
relabeled as byte-identical to the other. Actual production rows are checked
independently against R140-down coefficients, including signed terms.

## Four reciprocal-stock endpoint rows

Put tau=ΣY_i and tauhat=Σrn_Y_i=Σy*w_iy. For proved physical bounds
Bminus≤tau≤B and RN bounds L≤t≤U, expanding the nonnegative products of
the two stock slacks and two factor slacks gives

    tauhat − L*tau − Bminus*t ≥ −L*Bminus,
    tauhat − U*tau − B*t      ≥ −U*B,
    tauhat − U*tau − Bminus*t ≤ −U*Bminus,
    tauhat − L*tau − B*t      ≤ −L*B.

These are TS1..TS4. They connect endpoint inventory of the *same t,w* used
by RN. R138 STOCK connects g,state_g,Z instead. Under heterogeneous c,
ΣY is not S=ΣcY. No substitution of ratio units for physical stock is made.
Intersecting the proved physical stock interval with the sum of support extrema
is valid and used by both NC and TS.

The production TS writer uses original Y and rn_Y, avoiding unnecessary
selector products in coefficients. L,U and integer stock endpoints are actual
binary64/exact integers; only −endpoint*slope needs outward RHS rounding.
All six new rows receive exact positive power-of-two scaling if necessary to
preserve Native coefficient support. No positive-denominator proof means the
source is uniformly omitted under the inherited convention, not that an
invalid lower bound may be returned.

## A strict complementary local family and its remaining integer gap

Fix any n≥4, c_i=1, supported Y_i∈{0,1}, Bminus=1, B=n−1 and
s_i0=s_i1=1/2. Thus tau=n/2 and the old g domain is[0,(n−1)/n].
Let O denote the declared local VD-P/stock/TC/TC2/Gini/RN block.
For the old variables take

    q_i1=(n−1)/n², q_i0=g−q_i1,
    J=(n−1)/n, H=n−1, h_ij=2/n.

The2n vectors with stock total1 or n−1, mixed equally, attain the fixed
selector marginals and ordinary pair differences. This is not asserted to
be a common convex combination of every g-product and integer objective
epigraph variable. Old TC2/Gini/stock imply n−1≤H≤nJ≤n(n−1)g, so
g≥1/n, attained by the displayed old variables.

RN has L=1/(n−1), U=1. Normalization gives Σw_i1=1, while product/mass
constraints imply Σw_i0=n*t−1≥n*L/2. Consequently

    t ≥ t_N=(3n−2)/(2n(n−1)).

NC2 requires n*g≥(n−1)t. TS4, using tauhat=1 and tau=n/2, gives

    1 ≤ n/(2(n−1)) + (n−1)t − 1,
    t ≥ t_S=(3n−4)/(2(n−1)²).

The four optima are therefore:

| Fixed-selector local block | min g |
| --- | --- |
| O | 1/n |
| O+TS | 1/n |
| O+NC | (3n−2)/(2n²) |
| O+NC+TS | (3n−4)/(2n(n−1)) |

Attainment: for each site set w_i1=1/n,w_i0=t−1/n. Use t_N without TS,
t_S with TS, retain the displayed old q construction, and use hhat=0 without
NC or hhat_ij=2t/n with NC. All product faces, mass, normalization, stock
rows and inherited finite caps hold. The two strict gains are
(n−2)/(2n²)>0 and(n−2)/(2n²(n−1))>0. For n=4 the values are
1/4,1/4,5/16,1/3. Fixed state penalty P=n/2 adds the same lambda*n/2
to all original-objective optima; strictness is not manufactured by changing
the objective.

At positive-stock integer binary points G=(n−tau)/n. Under the same fixed
marginals E[tau]=n/2, the complete integer Gini epigraph convex hull has
minimum g=1/2, attained by the same2n-point mixture. The joint relaxation
is only≈3/(2n). It strictly improves O yet leaves substantial integer-objective
consistency unexpressed. This is a fixed-selector local theorem, not a full
route/cutoff strictness witness or a dominance claim over every R141/R142
conditional disjunction. The supplied all-n algebra and prior finite Fraction
checks are reused; no new n-grid or binary-specialized algorithm is introduced.

The hhat≤1 caps are inherited integer-valid finite bounds. A pure-RN argument
that lowers each hhat to its pair absolute minimum cannot simply be reused
after NC requires larger Hhat. This report claims the actual capped source,
not unproved full-projection redundancy of those caps in the joint relaxation.

## Original-point separation is distinct from reoptimization

For arbitrary site multipliers lambda_i and Gamma=b+Σlambda_i, NC and
mass Σ_yw_iy=t imply n*g≥Gamma*t+Σ(k_iy−lambda_i)w_iy.
Using the shared t box and per-selector L*s≤w≤U*s gives the original row

    n*g ≥ min(L*Gamma,U*Gamma)
          + Σ min(L*(k_iy−lambda_i),U*(k_iy−lambda_i))*s_iy.

Thus a positive violation separates the original x from *every* NC extension,
not merely one saved z. Multiplier optimality is unnecessary for validity.
The task's supplied NC2-PC saved-source violations/n are K35 .0862352641105,
RX20 .0125145224432,K20 .1139059369152,RB35 .1340443111542. These are
zero-Optimize separation facts. Those x also violate old TC2, so the table
alone cannot establish cross-information gain. The new K35 strong-O solve
and nested O+NC+TS reoptimization answer that separate numerical question.
No historical point or separating row is injected into fresh full runs.

## Complete-block projection and its numerical realization

Let P be the formal stable BASE and every additional source row be
Ex+Fz≥d, with zero objective on the finite-box RN variables z. Any
sign-correct multiplier beta gives

    (Eᵀbeta)x ≥ dᵀbeta − Σ_j max((Fᵀbeta)_j*l_j,(Fᵀbeta)_j*u_j).

Both ideal and implementation blocks include *every* RN,NC and TS row.
The selected source excludes old stock/TC/TC2 because they gave no further
measured joint K35 objective increment; their strong-carrier diagnostic is
retained separately. If they were added to a future source, their dual rows
would also have to be projected, not silently assigned to P.

Validity requires only legal signs, actual row/box coefficients and safe
arithmetic. Same-root value preservation additionally requires exact optimal
primal/dual solutions, the same P/domain/objective and zero new-column costs.
This standard dual principle, including its R104 antecedent, is not new,
and does not imply all-tree equality or the complete RN+NC+TS projection.
The implementation clamps only wrong-signed numerical multipliers, aggregates
with outward intervals, eliminates *all* RN residual coefficients by finite-box
support, and compensates original-box rounding/tiny deletion. Original Y,
selectors and G may remain. The two transported compact LPs quantify the
actual loss instead of assuming exact cancellation.

Only the current run's complete own H and initial root determine the source.
One paid source LP is restored/discarded before rebuilding formal BASE+PC.
No source point,bound or handle becomes formal controller proof evidence.
Compatible narrower g/cutoff/support domains inherit the original-variable
row; absent root selectors become zero while Y remains an original variable.
All source calls remain in Native quality/lifecycle/cost audits. Default off,
zero projection, failed source and nonpositive denominator use the inherited
fail-closed proof policies. Actual production Native audit reconstructs and
checks RN+all six rows, while formal audits reject persistent RN columns and
NC/TS source rows.
