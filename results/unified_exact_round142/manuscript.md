# Conditional count consistency in shared-factor proof sources

Round142 research increment: task dated 30 October 2026, scientific closeout
31 October 2026 (Asia/Shanghai). This note extends the retained
R138 resource-block theorem and R141 count disjunction. McCormick/RLT and
network-flow integrality are standard tools. The result below concerns a
declared selector/count block, not the integer hull of inventory routing.

## 1. What scalar floor injection can achieve

Let \(P\) be the parent relaxation, and let \(P_i\) be its two source relaxations,
with the **same complete linear objective**, optimal values \(\lambda_i\) and
qualified conservative floors \(\beta_i\le\lambda_i\). D0 installs the common
minimum floor; D1 has the same count links and conditional floor. If a weaker
source optimum can be extended by its corresponding **integer** b to all
of D1's links, then

\[
 \min_i\beta_i\le z_{D0}\le z_{D1}\le\min_i\lambda_i.
\]

The first inequality is the common floor, the second is inclusion, and the
last follows by extending that particular source optimum. This is the
mathematical floor-row statement. For serialized Native rows the actual
affine endpoints, including ObjCon and their existing outward-rounding
enclosures, are the authorities; ULP-scale serialization differences are not
new source information. Merely knowing a
dual bound does not construct this extension. A side modeled by only one
count inequality need not satisfy the parent's other endpoint; it must be
checked. Neither an infeasibility status without a qualified cutoff-complement
argument nor a different objective proves this upper inequality.

For R141 the three weaker saved source optima have respectively \(K=10.3033421624\)
in [9,33] (K35 high), 1.9808370142 in [0,5] (RB35-T2 low), and 5.4031520881
in [0,7] (K20 low). Their original objective and all other source rows are
retained in the source-to-parent extension. Thus, ideal floors \(\beta_i=\lambda_i\)
force equality of both root optima. When both floors are lowered by \(\varepsilon\)
and not truncated by cutoff, the possible difference is at most \(\varepsilon\),
apart from the separately guarded serialization margin. R141's equal root
objectives have a structural explanation. Round142 seeks stronger source
\(\lambda_i\) and cover, not a D1-over-D0 root objective gain.

## 2. Why reverse linear inventory bounds are not new information

At a threshold, write \(H\) for always-high stations and \(a_i\) for optional high
mass. Each optional station's actual support gives

\[
Y_i\le b_i^{<}+(M_i-b_i^{<})a_i,\qquad
Y_i\ge m_i+(h_i-m_i)a_i.
\]

With an integer cardinality bound on \(\sum_i a_i\), maximizing the first affine
sum selects the largest allowed inventory increments; minimizing the second
selects the smallest required threshold increments. The continuous unit
cardinality knapsack has an integral extreme optimum. The familiar sorted
reverse inventory formulas are therefore implied by the existing continuous
selectors plus count range, rather than a new linear strengthening.

The exact-support replay in `offline_screen.json` covers every one of the 24
plain/conditional positions (12 distinct threshold-side domains). Original
and reverse-implied intervals agree: K35 [251,326], RB35-T2 [161,236], K20
[148,208]. Stock/TC2 budgets do not change. No new reverse-inventory
production experiment is justified.

## 3. Four conditional product rows

VD-P already has nonnegative state selectors \(s_{iy}\) and products \(q_{iy}\)
in the existing `state_g` columns,

\[
\sum_y s_{iy}=1,\quad \sum_yq_{iy}=g,\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
Y_i=\sum_yys_{iy},\quad Z_i=\sum_yyq_{iy}.
\]

Use the **loaded** positive dyadic coefficient \(c_i=1/D_i\) and exact supported
threshold \(t\), not a rounded displayed ratio. Define the existing-column sums

\[
K_t=\sum_{i,y:c_iy\ge t}s_{iy},\qquad
W_t=\sum_{i,y:c_iy\ge t}q_{iy}.
\]

For physical integer selectors \(W_t=gK_t\). A valid conditional interval
\(\ell_t\le K_t\le u_t\) and the source's actual \([\alpha,\beta]\) yield

\[
\begin{aligned}
W_t&\ge\alpha K_t+\ell_t g-\alpha\ell_t,\\
W_t&\ge\beta K_t+u_t g-\beta u_t,\\
W_t&\le\beta K_t+\ell_t g-\beta\ell_t,\\
W_t&\le\alpha K_t+u_t g-\alpha u_t.
\end{aligned}
\]

These are standard RLT/McCormick inequalities. No \(W\) variable is needed. For
\(\alpha<\beta\), combining the two \(u\) inequalities implies \(K_t\le u_t\); combining
the two \(\ell\) inequalities implies \(K_t\ge\ell_t\). If \(\alpha=\beta\), VD-P fixes
\(q=\alpha s\) and the product inequalities degenerate: linear count ranges must
still be retained. Both implementations explicitly retain the count ranges.

All rows are normalized to \(\ge\). Variable coefficients are loaded endpoints,
integers and \(\pm1\). An outward downward ULP on each nonzero endpoint-times-
integer RHS contains the exact product; exact zero terms are deleted, small
nonzero terms are kept. An exact positive power-of-two scaling preserves
small coefficients through Native's reader. The expected row map is built
from these actual emitted coefficients and the already rounded/scaled RHS.

## 4. Endpoint meaning and the precise hull statement

For \(\alpha<g<\beta\) put \(\theta=(g-\alpha)/(\beta-\alpha)\) and

\[
s^\alpha=\frac{\beta s-q}{\beta-g},\qquad
s^\beta=\frac{q-\alpha s}{g-\alpha}.
\]

These are stationwise probability selectors. The original triple is

\[
(s,g,q)=(1-\theta)(s^\alpha,\alpha,\alpha s^\alpha)
             +\theta(s^\beta,\beta,\beta s^\beta).
\]

The ordinary count range constrains the average \(s\). CP constrains **both**
endpoint selectors to the same conditional range. Stock's four product rows
constrain endpoint *total inventory*, which does not enforce endpoint
threshold counts. At \(g\) endpoints use the unnormalized masses \(\beta K-W\) and
\(W-\alpha K\), without division. This also explains the numerical diagnostics.

Let \(P_C\) consist only of station one-hot simplices and a finite set of nested
threshold-count bounds with integer endpoints. It is an integral polytope:
give each station one unit of supply, create a unit-capacity selection arc
for every supported state to its ratio layer, and send all layers along one
descending chain to a sink. The chain arc crossing \(t\) carries exactly \(K_t\);
assign it integer lower/upper capacities \(\ell_t,u_t\). This is a network with
integer supplies and capacities. Its integral flow polytope projects to
\(P_C\) in the selection arcs. Missing intermediate thresholds need no bounds.
Infeasible capacity sets produce an empty polytope, not fractional exceptions.

Apply R138's selected continuous resource-block endpoint theorem to \(P_C\).
VD-P plus each defining count range and its CP rows is exactly
\(\operatorname{conv}\{(s,g,q):s\in P_C,\ \alpha\le g\le\beta,\ q=gs\}\).
Integrality of \(P_C\) also makes this the hull of the graph with integer selectors.
To see the latter point, on the **graph** at a fixed \(g\), decompose any fractional
\(s\in P_C\) into integer \(P_C\) selectors at that same \(g\); the products decompose with them.
This does **not** assert \(q=gs\) for every point in a fixed-\(g\) slice of the
overall convex hull: mixtures across different \(g\) endpoints remain possible.

The theorem omits weighted inventory budgets, routes, time, the full Gini
numerator and the original objective's remaining relationships. Adding these
constraints does not preserve an assertion of the complete BRP integer hull.
If all stock and count defining rows are lifted, the R138 endpoint theorem
still gives the corresponding **continuous selected resource-block** product
hull; integrality is not established for the weighted stock block.

## 5. Selected versus propagated families

For each threshold let \(A_t=\beta K_t-W_t\) and \(B_t=W_t-\alpha K_t\). VD-P makes
both nonnegative sums of nested per-state masses. CP is equivalent to

\[
\ell_t(\beta-g)\le A_t\le u_t(\beta-g),\qquad
\ell_t(g-\alpha)\le B_t\le u_t(g-\alpha).
\]

For \(t\ge t_{\mathrm{selected}}\) the two masses cannot exceed the selected masses; for
\(t\le t_{\mathrm{selected}}\) they cannot be smaller. A selected conditional upper bound
therefore propagates to every higher threshold, and a selected lower bound
to every lower threshold. Thus parent-family CP plus selected conditional
CP is equivalent to CP for all monotonically propagated ranges. The explicit
linear count ranges are retained, particularly for fixed g. ALL's possible
increment over selected-only comes from other **parent** product constraints;
it is not a separate new propagation principle or a network algorithm.

## 6. An exact strict witness

Four stations have support \(\{0,1,2\}\), \(c_i=1\), total inventory \([3,5]\), and \(g\in[0,3/4]\).
At each station take \(s=(1/4,1/2,1/4)\), \(q=(3/20,3/40,3/20)\), and \(g=3/8\).
Then \(\tau=4\), \(J=\sum_i Z_i=3/2=g\tau\), \(K_1=3\), \(K_2=1\), \(W_1=9/10\), \(W_2=3/5\).
Choose \(H_\Sigma=5\) and \(h_{ij}=5/6\). Local VD-P, stock rows, old TC (RHS 2),
parent TC2 (RHS 4), the child \(K_2\le1\) TC2 (RHS 5), the product-side bound
\(H_\Sigma\le4J=6\) and all parent count CP hold. But the child requires
\(W_2\le g=3/8\), violated by **9/40**.

The endpoint selectors are \((1/10,4/5,1/10)\) and \((2/5,1/5,2/5)\). Both have
total inventory 4; the latter has \(K_2=8/5>1\), although the average has \(K_2=1\).
This proves strictness of the stated relaxation block even with exact stock
product and all parent CP. It is neither a complete BRP feasible point nor
a positive objective/gap theorem. `math/tiny.json` and the independent review
check this with Fraction; the fixture also covers \(\alpha>0\), fixed \(g\) and tiny
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

The reoptimized selected points make the previously missing endpoint limits
active: K35 low has \(\beta\)-endpoint count 8 (formerly 10.4765), K35 high has
\(\alpha\)-endpoint count 9 (formerly 8.39817), RB35-T2 low has \(\beta\)-endpoint count 5
(formerly 12.0380), and K20 low has \(\beta\)-endpoint count 7 (formerly 10). The two
stronger-side optima remain extensible at the same objective. These endpoint
values are explanatory diagnostics of saved binary64 points; no division is
used by the writer, and its no-division mass residual is the correctness check.

## 8. Matched continuous source results

The table shows numerical optimal objectives. Every inherited source row, variable, objective constant, cutoff and domain remains. C uses complete saved primal and old qualified optimum, without another Optimize. S appends four selected CP facets plus the missing opposite count range. ALL explicitly adds every propagated range and four facets per threshold. All twelve new LPs pass the unchanged 1e-6 quality gates.

| Role / side | Old L | Selected L | ALL L | Selected floor |
| --- | --- | --- | --- | --- |
| K20 / low | 0.255556703 | 0.255628878 | 0.255628878 | 0.255628778 |
| K20 / high | 0.268192585 | 0.268192585 | 0.268192585 | 0.268192485 |
| K35 / low | 0.241539946 | 0.241586247 | 0.241586247 | 0.241586147 |
| K35 / high | 0.240140105 | 0.240163916 | 0.240163916 | 0.240163816 |
| RB35-T2 / low | 0.146301753 | 0.146558193 | 0.146558193 | 0.146558093 |
| RB35-T2 / high | 0.150566942 | 0.150566942 | 0.150566942 | 0.150566842 |

| Role | Old min cover | Selected min cover | Gain | ALL - selected |
| --- | --- | --- | --- | --- |
| K35 | 0.240140105 | 0.240163916 | 2.381078e-05 | 6.10622664e-16 |
| RB35-T2 | 0.146301753 | 0.146558193 | 0.000256440319 | 1.99840144e-15 |
| K20 | 0.255556703 | 0.255628878 | 7.21752899e-05 | 2.22044605e-16 |

ALL requires 384--548 CP rows per source, selected only four; its further optimized gains are at roundoff scale. It is not selected for online use. The three original weak points are separated by product residuals .414570726 (K35 high), .167523020 (RB low), .228635736 (K20 low), although their average physical counts already satisfy the source range. These violations and the exact strict witness do not predict the size of an objective gain. Per-side construction, Native solve, Work, rows/nonzeros and endpoint counts are in the full precision LP CSV/JSON.


## 9. Complete methods, clocks and adverse outcomes

The only candidate is selected CP in the two R141 D1 sources. Each method pays for its own H (separate fixed seed 20260626), ordinary root/lookahead, count-source construction and both proofs, validation and Native search. Primary Gurobi Seed 0, Threads 1 and affinity mask 4 apply. M-B/VD-P, pair-only, AM=.08, depth 8, minimum width 1e-4 and AP off remain fixed. There is no per-instance product set, timed switching rule, imported diagnostic floor or extra probe. Physical route horizon and experimental cap are separate.

| Role | Stations / vehicles | Physical T s | lambda | Cap s |
| --- | --- | --- | --- | --- |
| K35 | 35/3 | 10800 | 0.15 | 2400 |
| RB35-T2 | 35/3 | 7200 | 0.0551252752 | 2400 |
| K20 | 20/2 | 5400 | 0.15 | 1200 |
| K15 | 15/2 | 3600 | 0.15 | 600 |

| Role | Method | Verified U | Supported L | T cert s |
| --- | --- | --- | --- | --- |
| K35 | TC+stock | 0.650438712 | 0.568288526 | open |
| K35 | TC2+stock | 0.702148613 | 0.541970377 | open |
| K35 | GI-TBC | 0.692854359 | 0.565765681 | open |
| K35 | Stock | 0.669595569 | 0.556776898 | open |
| K35 | R141 D1 | 0.655549726 | 0.559530134 | open |
| K35 | Selected CP | 0.665418889 | 0.545040775 | open |
| RB35-T2 | TC+stock | 0.319080493 | 0.233927262 | open |
| RB35-T2 | TC2+stock | 0.324275718 | 0.229904209 | open |
| RB35-T2 | GI-TBC | 0.344642626 | 0.21898595 | open |
| RB35-T2 | Stock | 0.401200218 | 0.2291816 | open |
| RB35-T2 | R141 D1 | 0.413773275 | 0.227918419 | open |
| RB35-T2 | Selected CP | 0.357402102 | 0.229365547 | open |
| K20 | TC+stock | 0.716806546 | 0.716806546 | 135.696813 |
| K20 | TC2+stock | 0.716806546 | 0.716806546 | 115.019623 |
| K20 | GI-TBC | 0.716806546 | 0.705355793 | open |
| K20 | Stock | 0.716806546 | 0.716806546 | 101.635385 |
| K20 | R141 D1 | 0.716806546 | 0.716806546 | 93.5355741 |
| K20 | Selected CP | 0.716806546 | 0.716806546 | 86.671444 |
| K15 | TC+stock | 0.592264882 | 0.59226488 | 45.2425381 |
| K15 | TC2+stock | 0.592264882 | 0.592264882 | 36.1332107 |
| K15 | GI-TBC | 0.592264882 | 0.592264879 | 112.769303 |
| K15 | Stock | 0.592264882 | 0.592264882 | 33.8182265 |
| K15 | R141 D1 | 0.592264882 | 0.592264882 | 32.3593347 |
| K15 | Selected CP | 0.592264882 | 0.592264882 | 27.4882483 |

All four selected Seed0 roles complete their original protocols. K15 and K20 keep the same two qualified proofs as old D1 and stock, with production 27.488248 / 86.671444 s and total 32.645135 / 95.985987 s. Against historical R141 D1 their production gains are 4.871086 / 6.864130 s, below the inherited max(10 s,10% of the smaller clock) threshold. K20 versus historical stock improves production by 14.963941 s, which is substantive, but total by only 8.473685 s, below 10 s. This is a cross-version whole-method comparison, not an isolated CP timing claim. K35 ends at U/L=0.665418889072/0.545040775489; its old-D1 changes are U +0.009869163281 and L -0.014489358147. RB35-T2 ends at 0.357402102170/0.229365546910, a repair over historical old D1 but still a worse U/stronger L tradeoff against stable GI-TBC, and worse at both endpoints than old TC+stock and TC2+stock. K35 is also dominated by old TC+stock. All open certificate times stay null; no cap is called convergence.

| Role / method | Produce s | Verify s | Total s | Relative gap |
| --- | --- | --- | --- | --- |
| K15/Selected CP | 27.4882483 | 5.1568864 | 32.6451347 | 5.45490556e-14 |
| K20/Selected CP | 86.671444 | 9.3145433 | 95.9859873 | 7.74423051e-16 |
| K20/R141 D1 | 87.5457672 | 9.9311264 | 97.4768936 | 1.5488461e-16 |
| K35/Selected CP | 2371.17983 | 16.9936684 | 2388.1735 | 0.180905766 |
| RB35-T2/Selected CP | 2371.1611 | 15.4975585 | 2386.65866 | 0.358242312 |
| RB35-T2/R141 D1 | 2371.07304 | 13.6092377 | 2384.68228 | 0.449206938 |

Open T_cert stays null and is displayed as open. No cap is imputed as convergence time. Signed gap, returned Native ObjVal/ObjBoundC, externally merged L, all probe/target/terminal work and nodes remain separate fields. Nested H/LP/MIP/Work is descriptive and never charged twice. Historical rows retain their original source/PE/full clocks; missing roles are not inferred.

Two independently paid same-PE old-D1 bridges retain the identical source/PE, input, own H, root, selection/pivot, count links and complete window. The first integer matrices match after removing only the floor row; source CP is absent from those integer models. K20 old D1 produces its proof in 87.545767 s (97.476894 total); selected CP changes production by -0.874323 s and total by -1.490906 s, without a substantive incremental proof-clock gain. RB old D1 ends at U/L=0.413773275022/0.227903449004; CP improves both endpoints, with U delta -0.056371172852 and L delta 0.001462097906. This is the actual matched complete intervention: stronger source models and the returned two floor coefficients. It does not identify Native branching on b or attribute the result only to the weak-side raw objective increment. K35 has no new same-PE bridge; retain its adverse cross-version comparison without assigning causality solely to CP. Native returned bounds and the externally merged supported L remain separate full-table fields.

| Same-PE role | CP - old U | CP - old L | Produce delta s | Total delta s |
| --- | --- | --- | --- | --- |
| K20 | 0 | -4.4408921e-16 | -0.874323246 | -1.49090635 |
| RB35-T2 | -0.0563711729 | 0.00146209791 | 0.0880610833 | 1.97638188 |


## 10. Scope, decision and reproducibility

Retain the uniform selected-CP entry as research-only and close this count-proof continuation. Conditional count products fill a real shared-factor relaxation freedom and raise all three weaker sources/min-covers. They do not provide a sufficiently consistent complete-method increment for promotion: the small-role old-D1 proof benefit is not substantive under same-PE matching, K35 regresses at both endpoints against historical D1, and the hard roles remain behind old TC+stock at both endpoints. Stable R137 GI-TBC remains the default. Preserve the actual RB matched result and every adverse/failed result as finite research evidence; neither stronger LPs nor this panel proves general Native performance dominance.

The independently selected K20/RB same-PE bridges are complete. No remaining-four-role expansion, new D0 grid or Seed1 is entered: these would not change the adoption/stop decision given the completed hard-role boundary. No missing role is inferred. ALL has no useful extra source information, reverse inventory bounds are implied and unchanged, and further similar RLT, AM/Seed grids or H redesign are not opened. A future continuation needs genuinely different joint information or search evidence, under a new explicit task. Stopping is based on scientific and marginal decision value with ample unused budget, not the 8-hour ceiling.

Independent checks before the expensive pilot confirm CP directions/constants, loaded support and current g endpoints, full Native row readback under a single source SHA, absence from the parent/MIP and actual source-floor binding. The retained R141 physical-side, Start, cutoff-complement, source revocation and disposable-probe lifecycle checks are reused. Positive-alpha, fixed-g and tiny-coefficient fixtures avoid relying only on root alpha=0. The separate C++ switch defaults off; prior stable/research launchers and configurations retain their bytes.

The conservative new experimental charge is the complete measured outer including mandatory pure postverification: 7504.312010 seconds (2.084531 hours) of the 28800-second ceiling. The inherited online G1 submeter is 7420.265580 seconds and explicitly separates disjoint pure postverification; it is not added again. Qualifications, failed fixtures and all entered positive/adverse runs are included. Builds, offline analysis, documents and public I/O are separate; unmeasured interactive editing/review receives no invented timing precision.

The fixed diagnostic carrier and inherited members, actual source/PE/DLL and hybrid compile lineage, frozen input/parameter matrices, complete returned evidence and costs are bound by manifests. This appendix is a standalone research increment; the formal R137 manuscript remains available. Local scientific validation and finite anonymous public archive/member readability are different claims. Post-PR cleanup is bounded to this round and retains unique raw/failures and necessary runtime dependencies. No merge, historical deletion or unrelated production line follows.

The standard antecedents remain McCormick envelopes and reformulation-linearization [@mccormick1976; @AdamsSherali1990R138]; the continuous endpoint theorem is the retained R138 result, not a newly claimed general convexification principle.
