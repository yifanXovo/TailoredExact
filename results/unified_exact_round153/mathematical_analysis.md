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
candidate discovery methods. Selected duals minimize absolute deviations
from either an AP-based center or zero without imposing a potential radius. The target
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

### Exhaustive denominator partition and saved-direction refinement

For positive inventory sum S=sum c_i Y_i, exact hard-total DP supplies a
finite enclosing interval [Smin,Smax]. Partition this entire interval into
closed rational subintervals [l_j,u_j]. Shared endpoints are harmless:
the union covers every legal positive stock. Each price model retains the
original state supports, hard resources and Gini cap, and restricts
1/u_j <= t <= 1/l_j using outward bounds. The normalized state-product
bounds and their four total-stock product consequences are updated with
the same one-hot coefficient transport. These restrictions are necessary
for stocks in that subinterval, not global constraints on Q or R.

Let L_j be a qualified price lower for the conditional domain. An unrun,
unexpected-status or infeasible-report slice retains the global hard-total
DP lower rather than disappearing from the cover. With legal zero handled
separately, min_j L_j (and the zero value, when present) is a lower on the
full price. It can be strengthened by taking its maximum with the global
DP lower. A conditional upper must come from a true legal stock whose exact
S belongs to that slice; the parent may also reuse any global legal stock
as an upper. Empty or unresolved slices can leave a wide interval, which
is reported honestly. This construction was checked by full enumeration
on the targeted small domains before its large-domain use.

For a previously saved (beta,d), changing the pricing implementation does
not require a new RMP solve. If Q, R, beta and every d coefficient match,
reuse its exact C_Q and a_K, take the maximum of same-direction valid
price lowers, and apply C_Q+min(a_K,L_m) once. New legal stocks can enlarge
the next restricted master. This does not retroactively alter the old
certificate, old price interval or its paid cost.

### Reusing the historical CDF/OT epigraph inside pricing

The R88 B1 construction already represents pairwise absolute differences
by cumulative inventory distributions. This study reuses that mathematics
with the existing common reciprocal variable; it is not a new general
Gini theorem. For a pair i,j, form the increasing exact union of their
ratio levels (including zero), q_0<...<q_K, and let

    W_i(k) = sum_{c_i*y>q_k} w_iy,     delta_k=q_{k+1}-q_k,
    a_ij,k >= W_i(k)-W_j(k), a_ij,k >= W_j(k)-W_i(k).

For a true positive integer stock, W_i(k) is either zero or t. Choosing
the minimal auxiliary extension a_ij,k=abs(W_i(k)-W_j(k)) gives

    sum_{i<j,k} delta_k*a_ij,k = t*sum_{i<j}|c_iY_i-c_jY_j| = n*G(Y).

Arbitrary larger auxiliaries need not give equality. The minimal extension
shows that the additional upper rows D<=n*q and D<=n*gamma_U preserve every
legal integer stock and every q>=max(gamma_L,G). The bound 0<=a_ij,k<=t_U
is safe. Actual ratio levels use the original binary64 c_i as Fractions;
threshold widths are written downward and the Gini-cap RHS upward. These
roundings weaken necessary rows. All original mean-absolute, resource,
NC and TS rows are retained, and the objective/price guard is unchanged.
New auxiliaries occur only in the inventory price model, never in Q or
the frozen complete candidate.

In the exact continuous relaxation, the triangle inequality for the
integral gives integral|W_i-W_j| >= |integral(W_i-W_j)|, so the cumulative
block can strengthen the old difference of means. It does not subsume
hard-resource NC information. The independent
[design review](review/normalized_cdf_pricing_review.md) gives the precise
scope and counterexamples to overbroad redundancy claims. The new interface
qualification checks all actual rows and variable bounds on the existing
49-stock and mixed-zero small domains, including forced Native beta-zero
pricing. It does not reopen inherited numerical-boundary qualifications.

Historical outcomes remain separate. R88's
[fixed-LP decision](https://github.com/yifanXovo/TailoredExact/blob/247cf16b89e4a6c47b157d6eee1f981c7e8c9b98/results/unified_exact_round88/ot_epigraph_decision.md)
found no B2 increment over B1 on F2; four D7 arms were unfinished at their
300-second limits, so their family ordering was unknown. R89's
[complete-method decision](https://github.com/yifanXovo/TailoredExact/blob/fe19ca9d519d5c60e4b7bf37085645b41ae44723/results/unified_exact_round89/native_b1_decision.md)
parked its native-callback candidate after D3 certified the same objective
in 155.391 seconds for ENS-C versus 299.828 seconds for B1. Search work also
increased, while PreCrush and search-path effects were not isolated. That
finite adverse complete result is retained; the ten unrun arms are not
reopened. The present normalized pricing experiment neither revives that
candidate nor establishes complete-method benefit from a stronger LP.

### Exact integer-flow lower bounds for denominator slices

The larger CDF MIP probes motivate a separate lower-bound implementation.
This uses the same threshold identity without making its continuous
auxiliaries part of a mixed-integer search. Write
A(Y)=sum_{i<j}|c_iY_i-c_jY_j|, S(Y)=sum c_iY_i and T(Y)=sum Y_i.
On a positive denominator slice l<=S<=h, for any p,r in R and eta>=0,

    beta*f(Y)+sum d_i(Y_i) >=
      (beta/(n*h)+eta)*A(Y)
      + sum_i [d_i(Y_i)+p*Y_i+(r-eta*n*gamma_U)*c_iY_i]
      - max(p*Bminus,p*B) - max(r*l,r*h).

Indeed, beta*f>=beta*A/(n*h), and each of
p*T-max(p*Bminus,p*B), r*S-max(r*l,r*h), and
eta*(A-n*gamma_U*S) is nonpositive on the original feasible slice.
Minimizing the right side over the full Cartesian station state sets
therefore gives a valid slice lower. This is an explicit Lagrangian
relaxation for a lower bound; its minimizing label vector need not satisfy
resources, the slice or Gupper. It cannot be an inventory upper until all
original constraints are independently checked. The original full pricing
domain is unchanged. The beta*gamma_L plus hard-total DP lower is retained
separately, so a nonzero completion floor and beta-zero directions remain
valid even when this particular surrogate is weak.

For each station's ordered labels y_0<...<y_k, introduce threshold bits
z_j=1{Y>y_j}. Their order z_j>=z_{j+1} is enforced by arcs from the higher
threshold to the lower. Arbitrary signed unary costs have the telescoping
representation D(y_0)+sum_j[D(y_{j+1})-D(y_j)]z_j. For every pair of
stations, the exact merged ratio breakpoints express its absolute difference
as a positive sum of |z_i-z_j| terms, with constant zero/one tails folded
into unary terms and a constant. Because beta/(n*h)+eta>=0, every pair
coefficient is nonnegative and has an s-t cut representation. All declared
states, including holes and singleton supports, remain represented.

The implementation uses Python integers at scale2^40. The aggregate
constant, each signed unary coefficient and each nonnegative pair coefficient
are rounded with mathematical floor. This makes every label's rounded
energy no greater than its exact Fraction energy. Negative unary terms
use a source arc and retain their negative constant offset. Chain arcs have
capacity1+sum(all nonchain capacities); a cut assigning every threshold
zero shows that no minimum cut needs to violate a chain. Integer arithmetic
has no fixed-width overflow or residual-flow tolerance.

A feasible integer flow is checked independently for every arc capacity,
node balance and source/sink value. Flow=cut establishes the rounded
minimum, and (integer constant+flow value)/2^40 is a certified slice lower.
A cut alone would give an upper on the minimum cut and is insufficient
for this purpose. This is classical flow/cut duality, not new general
theory; see [Ford and Fulkerson (1956)](https://doi.org/10.4153/CJM-1956-045-5).
The original paper and theorem were checked through its Cambridge-hosted
primary text. The explicit inventory inequality and rounding argument
above establish this application's bound direction.

A small Native LP may choose p,r,eta from a finite candidate-search box.
Each generated label supplies its true linear energy constraint to that
LP; a rounded-cut minimizer is not assumed to be an exact supergradient
of the unrounded dual. The LP's objective is neither a full-price lower
nor an inventory-price upper. Every accepted lower comes from the separate
exact integer flow at the selected parameters. The finite box limits this
auxiliary search only, not the inventory states, original Q or valid-bound
scope. Candidate LP calls, exact-flow calls and costs are recorded separately.

Positive-S slices cover the entire exact denominator range with overlapping
endpoints. Take their minimum, include the separate legal-zero price,
then maximize with the original full-domain DP lower. Unvisited slices
retain that DP lower. Same-direction refinement also retains the old
qualified full-price lower. Small interface qualification must enumerate
every Cartesian label to check graph energy, downward rounding and flow
optimality, then check the original feasible slice stocks and full minimum.
Signed multipliers, beta zero, singleton/holed supports and altered-flow
rejection are explicit controls. The independent
[design gate](review/cut_pricing_design_review.md) precedes execution.

This is not the repository's first min-cut use. R54 InventoryRouteCuts and
R63 Round63TimeResource already use maximum-closure/min-cut separation via
DeterministicDinic.hpp, whose double-capacity tolerance does not supply
the integer certificate required here. R88 supplies the CDF identity.
The present application is a different offline price lower, not a novelty
claim for these ingredients or an admission to the complete production
candidate. The current adverse CDF MIP probes remain part of its motivation.

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

The structural mechanism can be stated without additional experiments.
Suppose two station marginals each have two states, all other stations
are fixed, and the hard upper resource bound excludes only the joint
high/high corner of these four combinations. Write p and q for the two
high-state marginal probabilities. Compatibility requires p+q<=1.
The joint probabilities are then forced to be (1-p-q,p,q,0), ordered as
(low/low,high/low,low/high,high/high). Consequently Gamma is exactly the
same weighted average of the three true f values. This follows directly
from the two marginal equations and the excluded corner; it does not
require a new convex-analysis theorem. In the present fixture the omitted
stock is (1,2,3), whose total 6 exceeds B=5. The three remaining Gini values
are 1/6,2/15,4/27, with weights 1/4,1/4,1/2, giving 161/1080. The normalized
old reference still admits g=1/9. Thus it is the joint resource exclusion
and nonlinear completion, not merely separate marginal realizability,
that explains this fixed-marginal separation.

## Feasible-column discovery and marginal-preserving pairs

An additional legal stock column expands the finite master toward the same
full hull; it cannot invalidate an already qualified lower. A heuristic
may therefore search for useful columns without solving a full price,
provided it claims only a qualified primal upper after free-Q reoptimization.
Floating candidate scores, sampled prices and a failure to find a selected
negative column give no complete-domain lower or convergence certificate.

There is a simple complementary-column mechanism. In an ideal feasible
distribution, let Y and Z have positive weights. Exchange their states at
one or two stations to produce Y' and Z'. Their stationwise multisets agree,
so for every state indicator,

    v(Y) + v(Z) = v(Y') + v(Z').

If both children belong to the original full R, replacing epsilon of each
parent by epsilon of each child preserves all marginals and total mass for
0 <= epsilon <= min(lambda_Y,lambda_Z). The expected completion changes by

    epsilon * [f(Y') + f(Z') - f(Y) - f(Z)].

A negative bracket improves the completion at those marginals. Unary price
terms cancel for the pair, but either child's individual reduced cost may
be nonnegative, so both children must be available together. A child already
in K needs no new copy. Exchanges sharing parent weights cannot have their
estimated gains summed as a simultaneous attainable improvement. Nor does
the completion change alone prove a lower full objective: Q may constrain
G through additional rows. The implementation adds true-checked children
and lets the unchanged complete master select a new distribution and x.
Its upper remains governed by the declared numerical primal policy.

Single-site and equal-and-opposite two-site quantity neighborhoods are
ordinary local search. Historical `src/Round75QuantityDescent.cpp`, retained
in the fixed R152 base, already enumerates these changes for verified
physical-route incumbents; `src/Round76PhysicalClosure.cpp` reuses that
operator in physical closure. The present use is for inventory-distribution
columns, with a different feasibility carrier. Neither these neighborhoods
nor the elementary marginal exchange is claimed as new general theory.
The finite selection limits and conditional experiment are recorded in
[primal_pool_plan.md](primal_pool_plan.md). The actual probes accumulated
33882 K35 and 54187 NC20 legal stocks without a material numerical-upper
improvement. These finite heuristic outcomes do not establish local
exhaustion or complete-price convergence. The fixed-direction screen
found useful new negative-price NC20 stocks, so upper stagnation is also
not evidence that every retained direction is already fully priced.

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
[Desrosiers et al., Branch-and-Price](https://www.gerad.ca/en/papers/G-2024-36).
The GERAD record was checked on 2026-11-04; it identifies the January 2026
revision and the 2026 Springer publication. The goal's section 3.2 refers
to the supplied working-paper version. The dual correction above is
derived here explicitly rather than relying on a version-dependent section number.
The contribution under evaluation is the finite value, scope, implementation
cost and algorithmic usefulness of this inventory objective information in
the unchanged routing relaxation.
