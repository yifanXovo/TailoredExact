# Coupled integer objective epigraph: object and qualification

This study uses the user's complete Round153 goal and the fixed R152 science
at d489ec2948f079105e4532a2e06ae4eed9fcd500. The stable method remains the
R137 GI-TBC definition. Reference restoration and offline research do not
transfer paid data to a subsequent algorithm arm.

## Domain and information hierarchy

For each saved domain, R consists of all declared station states satisfying
the hard total inventory lower and upper bounds and the physical Gini cap.
The zero-total state, when legal, is handled separately with true Gini zero.
The completion cost is f(Y)=max(gamma_L,G(Y)), and the unary penalty is
h_i(y)=omega_i |c_i y-1|. With fixed state marginals s, every common
distribution has the same expected penalty H(s)=sum h_i(y)s_iy. Consequently
the minimum expected total objective is Theta(s)=H(s)+Gamma(s), where Gamma
minimizes expected f over common legal inventory distributions.

Q denotes the complete free routing LP, including its original load, time,
cutoff, objective and auxiliary variables. The selected historical reference
contains AP/GD/stock/count/common-factor/RN information, both R145 normalized
count rows, all four product rows, and the union of the old eight supports,
the final support and floor. Each comparison uses the same Q. Old row bytes,
derivations and source member hashes are recorded in reference/. Redundant
blocks and transported direct-g rows use zero-solve primal/dual sandwiches
when available; no old result is counted as a new experiment.

The coupled object minimizes F(x)=g+P_e over x in Q, with
s=sum_Y lambda_Y v(Y), sum lambda=1, lambda>=0 and
g>=sum_Y lambda_Y f(Y). The inventory subproblem generates a representation
of joint marginals; it neither replaces the physical route search nor uses
the R105--107 integer service master followed by a routing oracle.

When AP is present, g-completion implies the corresponding total-objective
completion. The converse need not hold because excess penalty epigraph slack
can pay for a total-objective row without raising g. This inclusion is an
object-level statement. Actual written coefficients and numerical witnesses
receive separate qualification. The three current-Q projection witnesses
are legal common distributions; their expected G is only a feasible value,
not Gamma(s). Compatible projection alone does not settle the completion gap.

## Restricted master upper and whole-domain lower

A finite legal column set K is an inner restriction, so a qualified RMP
primal supplies z_Gamma <= U_K. The stored original x can have fractional
routes. U_K is a strengthened LP-value upper and is never a BRP physical
incumbent or a lower bound for BRP. Artificial Phase-I objectives are not
normal RMP uppers. Restricted infeasibility is not full-hull infeasibility.

Each column's true f is recomputed with Fraction from the declared binary64
ratios. The RMP writes f upward and adds a 1e-8 completion safety margin.
Every admitted primal is checked against the complete original matrix,
lambda mass/nonnegativity, every marginal including the omitted redundant
station link, and the true Fraction expected f. Primal feasibility uses the
inherited numerical LP policy; it is not a rational primal certificate. The
artificial safety margin is excluded from the dual lower calculation.

With convexity multiplier a, marginal multipliers pi and beta>=0 for the
completion row, the full price is m=min_R [beta f(Y)-pi.v(Y)]. The written
link orientation is sum lambda v-s=0; its solver Pi therefore matches pi in
this expression. No extra h term is left in Gamma pricing. Beta=0 is a full
resource/Gini-constrained projection price; beta is never divided out.

The implementation computes an exact binary64 residual support C_Q from
the selected row multipliers and finite bounds implied by the original Q.
Bounds are derived before any inventory columns are added, so they cannot
borrow restricted-column information. Row multiplier signs are repaired,
and every adverse residual requires a finite original-Q bound. This proves
F(x)+pi.s-beta*g >= C_Q for all x in Q under the loaded matrix semantics.
Let a_K=min(a,min_K[beta*f-pi.v]) using true column costs. Then

    D_K = C_Q + a_K,
    delta = max(0,a_K-L_m),
    L_Gamma = D_K-delta <= z_Gamma <= U_K.

The correction is paid once because lambda has total mass one. A numerical
RMP ObjVal is not substituted for D_K. Existing qualified Q lower bounds
are retained by maximum. The exact C_Q certificate, a_K, price interval,
delta and cumulative interval are saved for every completed normal step.
Interrupted calls without returns provide no new bound.

Basic duals, near-optimal dual selection and midpoint-level selection are
candidate discovery methods. The latter two minimize absolute deviations
from an AP-based center without imposing a potential radius. The target
dual band is numerical and never itself a lower certificate. A level is
the midpoint of a known valid lower and primal upper; its candidates still
pass the same C_Q and full-domain price correction. No-column steps may
continue only if the qualified cumulative lower actually increases.

## Pricing and safe support rows

The reusable price is beta*f(Y)+sum d_i(Y_i), with d=-pi for the coupled
master and d=h,beta=1 for the independent total-objective floor. Hard-total
DP provides beta*gamma_L+min sum d even if its attaining stock violates the
Gini cap. Such an infeasible witness is never used as a column or upper.
For a legal zero stock the separate price is beta*gamma_L+sum d_i(0).

The positive branch uses binary inventory states and normalized products,
retaining every original support, both hard total bounds, physical Gupper
and the f epigraph. Optional NC1/NC2/TS1-4 rows are necessary consequences,
not a changed stock domain. Signed objectives use station anchors and a
power-of-two scale. Downward coefficient transport and the declared Native
objective guard are paid in the original price units. Native bounds retain
their numerical qualification policy; no claim of exact integer proof is
made solely from a binary64 solver status. Pool candidates are reevaluated
against true f and the complete domain, then supply only upper witnesses
and legal columns. Unexpected online Native statuses retain the exact DP
fallback; they do not remove the positive branch or manufacture a bound.

Every completed lower supplies beta*g-pi.s >= L_m. Written coefficient
errors are transported by the finite g interval and one-hot station
minima, downward at the RHS. Beta0 rows remain projection rows. Current
useful supports are reinserted in the same complete free Q for attribution;
point violation and fixed-marginal separation are not free optimum gains.

## Strict example and historical boundary

The independent reconstruction in review/exact_strict_example.json checks
the strengthened 169-row,68-variable finite block with Fraction. At its
specified marginals, H=3/32, Gamma=161/1080 and Theta=1049/4320. The restored
reference has g minimum1/9 and objective59/288, giving exact gap41/1080.
The displayed feasible extension and a nonnegative combination of the
normalized-count and absolute-difference inequalities establish equality.

This is a fixed-marginal inventory-block separation. It is not a complete
routing strict example or a claim against every historical disjunction.
The old117-row global-floor gap1/480 cannot be inherited: the new reference
fixed point already exceeds the domain's global integer minimum. The
independent verifier explicitly checks this distinction.

## Transfer boundary and attribution

The scalar floor is checked against pure B separately from its gain over
the diagnostic reference. An offline legal lower greater than the pure-B
root is a real opportunity; an inventory upper no greater than B rules out
that scalar opportunity on this domain. Neither establishes complete-method
benefit. Any online J must recompute from its own H/current source and pay
its full construction/pricing cost. Its formal row uses the total objective
G+sum omega e, which is valid without adding AP. Root reuse is limited to
verified descendants with the same data/coefficients, narrower supports,
Gini interval and cutoff. No historical floor, potential or cross-arm
incumbent enters its producer.

Restricted masters, full-domain pricing, dual correction and column
generation are classical tools, not new general theory here. See
[Dantzig and Wolfe (1960)](https://doi.org/10.1287/opre.8.1.101) and the
restricted-master/pricing discussion in
[Desrosiers et al., Branch-and-Price, section3.2](https://www.gerad.ca/papers/G-2024-36.pdf).
The contribution under evaluation is the finite value, scope, implementation
cost and algorithmic usefulness of this inventory objective information in
the unchanged routing relaxation.
