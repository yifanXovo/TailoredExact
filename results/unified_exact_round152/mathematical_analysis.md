# Hard-resource integer objective epigraphs: scope, structure and qualification

This study addresses the original Gini-plus-penalty objective over a necessary
integer inventory domain. It does not replace GI-TBC, decompose routes, or
claim that a small inventory model is the full physical BRP. The original
goal, preanalysis, independent reviews and actual model identities accompany
this note. All station weights below already include lambda.

## 1. Historical exclusions

AP is the known state-weighted penalty inequality, already related to VD-J
in R55 and tested as an aggregate in R135. The R55 penalty-cover prerequisite
failed before live confirmation, so that branch was not empirically refuted.
R135 had K35 benefits and certification slowdowns and was not adopted; neither
fact invalidates its mathematics. Consequently every new real-domain claim
here first confronts an AP-enhanced full free model.

R138 stock/common-G products, R140 complete threshold count ranges and TC2,
R141 count disjunctions, R142 conditional common-factor products, and R146
conditional GD are retained as historical results. The targeted strong
reference used here includes AP, GD, all four stock rows, TC and TC2, every
supported-threshold count range, and four common-factor count rows at every
threshold. It is explicitly a finite expression reference. It is not the
union of all possible count disjunctions, RN/source projections or route
hulls. Threshold identities and the equal-target balancing lemma are not
new results of this round.

R143--145 normalization/source-LP compression and R104 single-vehicle hull
dual compression show why a strong source or few transported rows do not
ensure complete algorithm gains. R105--107 inventory/service masters followed
by route oracles had waiting and physical-U regressions. This study uses
inventory optimization only to price valid lower-support inequalities; it
does not generate a route master or replace the physical incumbent search.
Historical inventory objective probes also precede this study: a newly
qualified scalar inventory floor is new evidence for its domain, not the
invention of inventory lower bounds. R133 remains the motivation and known
control, not this round's strictness proof.

## 2. Objective completion and a useful exact decomposition

Let R be the actual supported integer inventories satisfying the hard total
budget Bminus <= sum Y_i <= B and physical G(Y) <= gamma_U. Supports and c_i
are read from the saved complete model, with c_i interpreted as its loaded
binary64 rational. Route, loading and time restrictions are relaxed. The
oracle does not add the original objective cutoff; supports inherited from
that cutoff still bind the scope. Define

    h_i(y) = omega_i |c_i y - 1|,
    phi(Y) = max(gamma_L, G(Y)) + sum_i h_i(Y_i).

The lower endpoint gamma_L is a bound on the epigraph variable, not a lower
bound on physical Gini. Thus stocks with G(Y) < gamma_L remain valid. When
Y=0 is in R its price includes gamma_L. A legal nonminimal integer completion
has g >= max(gamma_L,G(Y)), e_i >= |c_iY_i-1|, so g+P_e >= phi(Y).

For fixed one-hot marginals s, write H(s)=sum h_i(y)s_iy. If a common
distribution over R exists, linearity of expectation gives exactly

    Theta_R(s) = H(s) + Gamma_R(s),
    Gamma_R(s) = min E[max(gamma_L,G(Y))], with the same marginals and R.

If there is no common distribution, both hull questions are infeasible.
This separates projection compatibility from objective information. AP has
already fixed the expected minimum penalty; remaining objective information
comes from the common distribution's Gini completion. Searching residual
potentials pi=h+psi avoids spending the potential range merely relearning AP.

For arbitrary finite pi, any qualified lower bound L on

    alpha_R(pi) = min_(Y in R) [phi(Y)-sum_i pi_i,Y_i]

gives g+P_e >= L+sum pi_iy s_iy. This is a pointwise integer-completion proof
and includes legal slack in g and e. A restricted-column master only proposes
pi. Its intercept is never installed. A feasible inventory is a pricing UB,
never a pricing LB or a full BRP physical incumbent. Negative potentials and
negative pricing bounds are retained. Statewise coefficient changes use the
exact one-hot correction Lhat <= L-sum_i max_y(pihat_iy-pi_iy).

## 3. New exact strict example and its limits

The independently audited theorem is in review/exact_small_theorem.md, with
a standalone standard-library checker and consumed-file hashes. Take

    n=3, c=(1,1/2,1/4), omega=(1/8,1/8,1/8),
    Y_i in {0,1,2,3,4}, 2 <= sum Y_i <= 5, [gamma_L,gamma_U]=[0,3/4].

The complete declared inventory reference has 117 rows and 46 variables,
including every old expression listed in section 1. It admits the exact
selector marginals

    Y_1=1 surely; P(Y_2=1)=3/4, P(Y_2=2)=1/4;
    P(Y_3=2)=P(Y_3=3)=1/2.

An exact complete reference extension has g=1/10, AP=3/32 and objective
31/160. Its nonzero state/G products are q_11=q_22=q_32=1/10; the full
rational extension, rather than selected scalar inequalities, is verified.
Every active selector has ideal conditional GD coefficient zero. The eight
count ranges match exhaustive feasible-inventory minima and maxima, so
tighter individual threshold counts cannot explain the remaining gap.

The hard total excludes (1,2,3), forcing a unique common distribution:

| Stock | Probability | Gini | Penalty | Original objective |
|---|---:|---:|---:|---:|
| (1,1,2) | 1/4 | 1/6 | 1/8 | 7/24 |
| (1,1,3) | 1/2 | 4/27 | 3/32 | 209/864 |
| (1,2,2) | 1/4 | 2/15 | 1/16 | 47/240 |

Hence Theta(s)=1049/4320 and Gamma(s)=161/1080. The exact same-marginal
objective gap is 53/1080. This is objective information at compatible
marginals, not an empty resource projection. Separately, exhaustive exact
evaluation of all 125 supported vectors and 49 resource-feasible vectors
gives the unique global inventory optimum 47/240. Its difference from the
feasible reference point is 1/480. These two gaps answer different questions.

The R133 equal-target control is closed by this reference. A heterogeneous
tight-budget control and a positive-gamma_L control show no reported scalar
gap. No routing extension is claimed for the new example; neither does it
establish strictness over every historical normalized or disjunctive hull.

## 4. Reference pricing and complete denominator coverage

Safe S bounds come from continuous inventory boxes intersected with the hard
total. If their lower bound is zero, the smallest positive supported c_i y
is a safe positive-state lower bound. Every positive S is covered by adjacent
geometric bins. No least-common-multiple grid of rational denominators is used.
For a bin [ell,u], the MILP keeps one-hot binary choices, integer inventory
totals, S in the bin, pairwise absolute-difference epigraphs and

    q >= gamma_L, A' <= n u q, A' <= n gamma_U S.

It minimizes q+sum(h-pi)x. The original ratio equalities use c_i directly;
there is no pre-rounded c_i*y coefficient. The two n*u and n*gamma_U
coefficients are rounded upward, which relaxes constraints with nonnegative
q and S. Objective coefficients are rounded downward; any Native readback
increase receives a finite one-hot correction. The full serialized matrix,
objective, bounds and variable types are compared after MPS readback.

The surrogate error at a feasible inventory is at most
min(gamma_U,(n-1)/n)(1-ell/u). This denominator error is reported separately
from the MIP gap. Only finite Native bounds from OPTIMAL or TIME_LIMIT are
accepted, with the recorded objective guard 1e-6*(1+sum_i max_y |h-pi|).
This is an R134-style qualified floating bound, not a rational proof of a
MIP tree. Abnormal statuses retain the independent fallback instead. Proven
empty bins are recorded, not silently omitted. Exact unary hard-total DP
supplies a lower bound to every unsolved bin. Refinement inherits its parent's
valid lower bound; the global lower bound is the minimum over all active
bins and the exact zero-stock component when applicable.

Every inventory incumbent is reevaluated with Fraction arithmetic on the
original phi and actual domain conditions before it supplies a UB. A
surrogate point failing real G <= gamma_U is rejected as a UB. Separation,
direction nonseparation and undecided pricing are recorded separately.
The four purposeful small universes exhaustively check these formulas.
Review-driven checks additionally exercise unprocessed bins, partial covers,
refinement inheritance, zero-stock merging and actual full-matrix readback.

## 5. Sparse marginal faces with a qualified complement lift

At exact nonnegative marginals, any state of zero mass is unused by every
common distribution. This motivates pricing on active state sets A_i, but
an active-face row alone cannot be lifted to the original parent domain.
Partition the original R into R_A (all Y_i in A_i) and its complement
(at least one inactive choice). On R_A use the bin MILP. For the complement,
an exact DP tracks (total inventory, has_inactive_choice) with unary costs
h_i(y)-pi_iy and adds gamma_L. It retains the full original supports and
hard budget and relaxes only G/bin restrictions. Thus

    alpha_R(pi) >= min(L_active, L_complement_DP).

An empty complement is accepted only when that exact flagged DP proves it.
No restricted-domain bound is used alone as a parent-domain bound. Inactive
residual potentials initially equal -M. A deterministic twelve-step scalar
bisection reduces M while the actual complement bound remains at least the
active bound. This is a modest coefficient lift, not optimal sequential
lifting or a full global dual solution. The potential normalization is one
constant per station and is accounted for in the actual price.

For floating saved marginals, truncation at 1e-10 is only a discovery choice.
All original variables remain free in the follow-up LP, and the qualified
row covers every original integer state. The raw-point activity and the
potential-weighted discarded/negative mass are recorded. Claimed separation
must exceed that uncertainty plus 1e-6. This prevents tiny negative selector
values multiplied by negative potentials from manufacturing a finding.

## 6. What a free LP comparison does and does not establish

A valid row can cut a saved optimum while another optimum with different
marginals has the same objective. N-B35's first residual row demonstrates
this directly. The finite eight-row loops address that uncertainty with
successive free reoptimization, retaining original objective, cutoff,
route/loading/time rows and all prior auxiliary freedom. A scalar floor
can independently raise an LP without validating the residual-row expression.
Conversely, a limited row collection with zero root gain does not prove that
the whole integer objective epigraph is redundant.

Actual numerical endpoints, time, sizes and direction classifications are
reported in the final evidence table. The original complete algorithms are
not reclassified using initial LP values. If production is not entered,
physical U, terminal support L and T_cert are unobserved for a new method.

## 7. Equivalent normalized integer oracle and its separate old reference

Later bin-pricing costs motivate an exact positive-denominator formulation
using the already known RN lift. With safe positive S bounds, let
tL <= 1/S <= tU. Binary one-hot x, tL*x_iy <= w_iy <= tU*x_iy and
sum_y w_iy=t force the single selected w to equal t. Define
Znorm_i=sum_y y*w_iy and rnorm_i=c_i Znorm_i. The normalization
sum_i rnorm_i=1 then implies t*S(Y)=1. Pairwise absolute differences of
rnorm sum to A(Y)/S(Y), so q>=gamma_L, sum a<=n*q and
sum a<=n*gamma_U express the exact minimum Gini completion and physical
upper condition. The hard integer total is retained on x; the old scaled
stock rows Bminus*t<=sum Znorm<=B*t also strengthen the continuous relaxation.

The objective remains q+sum(h-pi)x. Thus this is exactly the positive-S
pricing problem in ideal arithmetic, with zero handled separately. It is
not a new normalization theorem and it is not a bare continuous RN oracle.
The Native numerical guard, status whitelist, complete matrix readback and
exact original-stock UB checks remain; eliminating bin error does not
eliminate MIP gap. Three exhaustive qualification domains check equivalence,
signed prices, nonminimal completion and zero stock. The relative-gap tiny
case is correctly left UNDECIDED by the stricter price-resolution criterion.

The related continuous RN+scaled-stock block is appended to each complete
CP reference before the final full-state residual experiment. It increases
K35's old reference more than the earlier eight new rows did, which rules
out attributing that earlier small root gain to information beyond RN.
The normalized integer-price directions are generated on all original states
with |psi|<=.05; there is no inactive-state complement penalty in this last
contrast. Every direction's installed intercept still comes from the global
qualified price, and all complete LP variables remain free.

Native status names follow the [Gurobi status-code reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html).
The accepted-status and numerical-guard rules here are this study's explicit
qualification policy. No callback stop rule was implemented in this round.
