# Conditional counts and a shared Gini factor

Round142 research increment, 30 October 2026. This note extends the retained
R138 resource-block theorem and R141 count disjunction. McCormick/RLT and
network-flow integrality are standard tools. The result below concerns a
declared selector/count block, not the integer hull of inventory routing.

## 1. What scalar floor injection can achieve

Let P be the parent relaxation, and let P_i be its two source relaxations,
with the **same complete linear objective**, optimal values lambda_i and
qualified conservative floors beta_i <= lambda_i. D0 installs the common
minimum floor; D1 has the same count links and conditional floor. If a weaker
source optimum can be extended by its corresponding **integer** b to all
of D1's links, then

\[
 \min_i\beta_i\le z_{D0}\le z_{D1}\le\min_i\lambda_i.
\]

The first inequality is the common floor, the second is inclusion, and the
last follows by extending that particular source optimum. Merely knowing a
dual bound does not construct this extension. A side modeled by only one
count inequality need not satisfy the parent's other endpoint; it must be
checked. Neither an infeasibility status without a qualified cutoff-complement
argument nor a different objective proves this upper inequality.

For R141 the three weaker saved source optima have respectively K=10.3033421624
in [9,33] (K35 high), 1.9808370142 in [0,5] (RB35-T2 low), and 5.4031520881
in [0,7] (K20 low). Their original objective and all other source rows are
retained in the source-to-parent extension. Thus, ideal floors beta_i=lambda_i
force equality of both root optima. When both floors are lowered by epsilon
and not truncated by cutoff, the possible difference is at most epsilon,
apart from the separately guarded serialization margin. R141's equal root
objectives have a structural explanation. Round142 seeks stronger source
lambda_i and cover, not a D1-over-D0 root objective gain.

## 2. Why reverse linear inventory bounds are not new information

At a threshold, write H for always-high stations and a_i for optional high
mass. Each optional station's actual support gives

\[
Y_i\le b_i^{<}+(M_i-b_i^{<})a_i,\qquad
Y_i\ge m_i+(h_i-m_i)a_i.
\]

With an integer cardinality bound on sum a_i, maximizing the first affine
sum selects the largest allowed inventory increments; minimizing the second
selects the smallest required threshold increments. The continuous unit
cardinality knapsack has an integral extreme optimum. The familiar sorted
reverse inventory formulas are therefore implied by the existing continuous
selectors plus count range, rather than a new linear strengthening.

The exact-support replay in offline_screen.json covers every one of the 24
plain/conditional positions (12 distinct threshold-side domains). Original
and reverse-implied intervals agree: K35 [251,326], RB35-T2 [161,236], K20
[148,208]. Stock/TC2 budgets do not change. No new reverse-inventory
production experiment is justified.

## 3. Four conditional product rows

VD-P already has nonnegative state selectors s_iy and products q_iy=state_g_iy,

\[
\sum_y s_{iy}=1,\quad \sum_yq_{iy}=g,\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
Y_i=\sum_yys_{iy},\quad Z_i=\sum_yyq_{iy}.
\]

Use the **loaded** positive dyadic coefficient c_i=1/D_i and exact supported
threshold t, not a rounded displayed ratio. Define the existing-column sums

\[
K_t=\sum_{i,y:c_iy\ge t}s_{iy},\qquad
W_t=\sum_{i,y:c_iy\ge t}q_{iy}.
\]

For physical integer selectors W_t=gK_t. A valid conditional interval
ell_t <= K_t <= u_t and the source's actual [alpha,beta] yield

\[
\begin{aligned}
W_t&\ge\alpha K_t+\ell_t g-\alpha\ell_t,\\
W_t&\ge\beta K_t+u_t g-\beta u_t,\\
W_t&\le\beta K_t+\ell_t g-\beta\ell_t,\\
W_t&\le\alpha K_t+u_t g-\alpha u_t.
\end{aligned}
\]

These are standard RLT/McCormick inequalities. No W variable is needed. For
alpha<beta, combining the two u inequalities implies K_t<=u_t; combining
the two ell inequalities implies K_t>=ell_t. If alpha=beta, VD-P fixes
q=alpha s and the product inequalities degenerate: linear count ranges must
still be retained. Both implementations explicitly retain the count ranges.

All rows are normalized to >=. Variable coefficients are loaded endpoints,
integers and +/-1. An outward downward ULP on each nonzero endpoint-times-
integer RHS contains the exact product; exact zero terms are deleted, small
nonzero terms are kept. An exact positive power-of-two scaling preserves
small coefficients through Native's reader. The expected row map is built
from these actual emitted coefficients and the already rounded/scaled RHS.

## 4. Endpoint meaning and the precise hull statement

For alpha<g<beta put theta=(g-alpha)/(beta-alpha) and

\[
s^\alpha={\beta s-q\over\beta-g},\qquad
s^\beta={q-\alpha s\over g-\alpha}.
\]

These are stationwise probability selectors. The original triple is

\[
(s,g,q)=(1-\theta)(s^\alpha,\alpha,\alpha s^\alpha)
             +\theta(s^\beta,\beta,\beta s^\beta).
\]

The ordinary count range constrains the average s. CP constrains **both**
endpoint selectors to the same conditional range. Stock's four product rows
constrain endpoint *total inventory*, which does not enforce endpoint
threshold counts. At g endpoints use the unnormalized masses beta K-W and
W-alpha K, without division. This also explains the numerical diagnostics.

Let P_C consist only of station one-hot simplices and a finite set of nested
threshold-count bounds with integer endpoints. It is an integral polytope:
give each station one unit of supply, create a unit-capacity selection arc
for every supported state to its ratio layer, and send all layers along one
descending chain to a sink. The chain arc crossing t carries exactly K_t;
assign it integer lower/upper capacities ell_t,u_t. This is a network with
integer supplies and capacities. Its integral flow polytope projects to
P_C in the selection arcs. Missing intermediate thresholds need no bounds.
Infeasible capacity sets produce an empty polytope, not fractional exceptions.

Apply R138's selected continuous resource-block endpoint theorem to P_C.
VD-P plus each defining count range and its CP rows is exactly
conv{(s,g,q): s in P_C, alpha<=g<=beta, q=gs}. Integrality of P_C also makes
this the hull of the graph with integer selectors. To see the latter point,
on the **graph** at a fixed g, decompose any fractional s in P_C into
integer P_C selectors at that same g; the products decompose with them.
This does **not** assert q=gs for every point in a fixed-g slice of the
overall convex hull: mixtures across different g endpoints remain possible.

The theorem omits weighted inventory budgets, routes, time, the full Gini
numerator and the original objective's remaining relationships. Adding these
constraints does not preserve an assertion of the complete BRP integer hull.
If all stock and count defining rows are lifted, the R138 endpoint theorem
still gives the corresponding **continuous selected resource-block** product
hull; integrality is not established for the weighted stock block.

## 5. Selected versus propagated families

For each threshold let A_t=beta K_t-W_t and B_t=W_t-alpha K_t. VD-P makes
both nonnegative sums of nested per-state masses. CP is equivalent to

\[
\ell_t(\beta-g)\le A_t\le u_t(\beta-g),\qquad
\ell_t(g-\alpha)\le B_t\le u_t(g-\alpha).
\]

For t>=t_selected the two masses cannot exceed the selected masses; for
t<=t_selected they cannot be smaller. A selected conditional upper bound
therefore propagates to every higher threshold, and a selected lower bound
to every lower threshold. Thus parent-family CP plus selected conditional
CP is equivalent to CP for all monotonically propagated ranges. The explicit
linear count ranges are retained, particularly for fixed g. ALL's possible
increment over selected-only comes from other **parent** product constraints;
it is not a separate new propagation principle or a network algorithm.

## 6. An exact strict witness

Four stations have support {0,1,2}, c_i=1, total inventory [3,5], g in [0,3/4].
At each station take s=(1/4,1/2,1/4), q=(3/20,3/40,3/20), and g=3/8.
Then tau=4, J=sum Z_i=3/2=g tau, K_1=3, K_2=1, W_1=9/10, W_2=3/5.
Choose H_Sigma=5 and h_ij=5/6. Local VD-P, stock rows, old TC (RHS2),
parent TC2 (RHS4), the child K_2<=1 TC2 (RHS5), the product-side bound
H_Sigma<=4J=6 and all parent count CP hold. But the child requires
W_2<=g=3/8, violated by **9/40**.

The endpoint selectors are (1/10,4/5,1/10) and (2/5,1/5,2/5). Both have
total inventory4; the latter has K_2=8/5>1, although the average has K_2=1.
This proves strictness of the stated relaxation block even with exact stock
product and all parent CP. It is neither a complete BRP feasible point nor
a positive objective/gap theorem. math/tiny.json and the independent review
check this with Fraction; the fixture also covers alpha>0, fixed g and tiny
dyadic coefficients. No integer optimization is needed.

## 7. What the finite LP evidence establishes

All six saved sources retain the same objective, support, cutoff, g interval,
stock, old TC, parent TC2, count side and child TC2. Their saved optima satisfy
all selected and propagated linear ranges. Each C control therefore uses the
old qualified numerical optimum and the same-objective feasible saved point
without Optimize. Full original-matrix feasibility is checked again when
building the new LPs. This is a numerical LP-policy witness, not a rational
primal/dual certificate.

Selected CP increases both K35 sides and the weak RB35-T2/K20 sides; the two
already strong sides keep their objectives to numerical precision. The
min-cover gains are 0.000023810780, 0.000256440319 and 0.000072175290.
ALL adds no further optimized information (differences about 1e-15), despite
384--548 product rows per side versus selected's four. Consequently the one
uniform online candidate is selected CP in the two R141 D1 proof sources.
It adds no variable, probe, Start mapping or frontier type. The Native parent
MIP has the old structure; new information enters only through the two newly
qualified source floors. Complete search value is a separate empirical
question, answered by the full-method tables and final decision.

The exact source MPS/solution identities, native coefficient readback, row/NZ
and construction/solve costs, K/W endpoint diagnostics and conservative floors
are recorded by LP_plan.json, LP/* and the compact LP reports. Slight negative
changes near 1e-15 on unchanged sides are numerical equality, not a loss from
adding valid rows. No tolerance is changed to manufacture an improvement.
