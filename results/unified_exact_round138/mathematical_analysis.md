# Shared Gini products and global inventory consistency

This study extends the accepted Round137 GI-TBC formulation. It retains empty
departure, loaded return with unloading time, unique nonzero one-way service,
prefix vehicle capacity, complete own H, pair-only support, AM .08 and AP off.
The new production switch is default-off and adds four rows with no variables.
The new information is global resource consistency of already shared products.
It is not a new general convexification principle.

## 1. Physical units and valid inventory bounds

All following sums exclude the depot, whose serialized stock may be 50000.
Let \(B=\sum_i b_i\), \(\tau=\sum_iY_i\) and let \(R_k\) be the load
returned by vehicle \(k\). Empty departures and conservation give

\[
\tau=B-\sum_kR_k,\qquad 0\le R_k\le Q_k,\qquad
B^-:=\max(0,B-\sum_kQ_k)\le\tau\le B.
\]

Deliveries free space for subsequent pickups, so cumulative pickups need not
be bounded by a vehicle's capacity. No such invalid bound is introduced.
Targets and objective weights may be heterogeneous. Write
\(r_i=Y_i/D_i\), \(S=\sum_i r_i\), \(A=\sum_{i<j}|r_i-r_j|\) and
\(P=\sum_i\omega_i|r_i-1|\). The physical objective is
\(F=G_{\rm true}+\lambda P\), with \(G_{\rm true}=A/(nS)\) when \(S>0\)
and zero otherwise. The model's \(g\) is an epigraph variable and need not equal
\(G_{\rm true}\) at every native integer completion.

On a model's actual interval \([\alpha,\beta]\), VD-P uses

\[
\sum_y s_{iy}=1,\quad Y_i=\sum_yys_{iy},\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
\sum_yq_{iy}=g,\quad Z_i=\sum_y yq_{iy}.
\]

Integer selectors imply \(Z_i=gY_i\). Relaxed station mixtures do not impose
all products of global budgets with \(g\). Crucially, \(Z_i\) is an inventory
product, not \(gY_i/D_i\). The existing Gini row is
\(H_\Sigma:=\sum_{i<j}H_{ij}\le n\sum_i Z_i/D_i\).

## 2. Four inventory RLT inequalities

For any valid row \(a^\top Y\le b\), multiply its slack by \(g-\alpha\)
and \(\beta-g\), both nonnegative, then substitute the existing products:

\[
a^\top Z\le\alpha a^\top Y+b(g-\alpha),\qquad
a^\top Z\ge\beta a^\top Y+b(g-\beta).
\]

With \(J=\sum_iZ_i\), the physical inventory bounds yield

\[
\begin{aligned}
J&\ge\alpha\tau+B^-g-\alpha B^-,\\
J&\ge\beta\tau+Bg-\beta B,\\
J&\le\beta\tau+B^-g-\beta B^-,\\
J&\le\alpha\tau+Bg-\alpha B.
\end{aligned}
\]

At \(\alpha=0\), the last row is \(J\le Bg\). These inequalities are valid
for every exact product completion, including a nonminimal epigraph \(g\),
heterogeneous targets/weights/capacities, loaded return, zero total inventory,
zero \(g\), and a collapsed interval. The implementation uses the current
writer's actual \(g\) bounds. It neither treats a cutoff as a global physical
fact nor silently substitutes a stronger local stock budget.

All variable coefficients are emitted at max_digits10, bypassing the legacy
near-zero and near-one coefficient filters. Only the new multiplied right
sides are rounded outward by one ULP: upward for upper rows, downward for lower
rows. Exact Fraction checks confirm their directions. No general tolerance or
native proof policy changes.

## 3. Continuous selected-resource product hull

Let \(\mathcal P=\{s\ge0:\sum_y s_{iy}=1,\ As\le b\}\), and let
\(\mathcal X=\{(s,g,q):s\in\mathcal P,\ \alpha\le g\le\beta,\ q=gs\}\).
Retain \(s\in\mathcal P\), the station VD-P inequalities, and impose for
**every row defining the selected resource block**

\[
Aq\le\alpha As+b(g-\alpha),\qquad
Aq\ge\beta As+b(g-\beta).
\]

The resulting formulation is \(\operatorname{conv}(\mathcal X)\). Necessity
follows from the slack products. For sufficiency, when \(\alpha<g<\beta\), set

\[
s^\beta=\frac{q-\alpha s}{g-\alpha},\qquad
s^\alpha=\frac{\beta s-q}{\beta-g},\qquad
t=\frac{g-\alpha}{\beta-\alpha}.
\]

The local bounds make the two vectors nonnegative; their station sums are one.
The resource product inequalities give \(As^\alpha\le b\) and
\(As^\beta\le b\). Direct substitution yields

\[
(s,g,q)=(1-t)(s^\alpha,\alpha,\alpha s^\alpha)
             +t(s^\beta,\beta,\beta s^\beta).
\]

At an endpoint, the nonnegative differences in each station sum to zero, giving
the exact endpoint product. If \(\alpha=\beta\), local bounds already enforce
\(q=\alpha s\). Additional equalities require their product equalities, or
both corresponding inequality products.

This is the standard RLT/two-endpoint disjunctive construction, consistent with
Adams and Sherali's linearization framework, the Sherali-Adams RLT monograph,
and Balas's disjunctive hull theory [@AdamsSherali1990R138; @SheraliAdams1999R138;
@Balas1998R138]. The four stock rows give this conclusion only for the
continuous block defined by station simplices and the selected stock budget.
They do not describe the full integer inventory, route or original-objective
epigraph hull. Omitting products of other resource rows does not preserve the
stronger all-row hull conclusion.

## 4. Strict complementarity with TC in the original J2/J3 reference

Keep the original joint fleet mixture, theta, event ranks, cutsets, old state
penalty and declared R88 CDF/product controls free. Here \(n=4\), \(B=3\),
\(D_i=\omega_i=1\), states are 0/1/2, and \(g\in[0,3/4]\). Let
\(a=\sum_i s_{i1}\), \(b_2=\sum_i s_{i2}\), so \(\tau=a+2b_2\le3\).
The inherited TC row is \(H_\Sigma\ge a+4b_2\ge\tau\). Thus

\[
\tau\le H_\Sigma\le4J\le12g,\qquad
F\ge\tau/12+\lambda(4-\tau)
\ge\min\{4\lambda,1/4+\lambda\}.
\]

The saved original binary64 coefficient is exactly
\(\widehat\lambda=5404319552844595/36028797018963968>1/12\). At this
coefficient and this reference only, the four optimal LP values are

| Original reference | Optimal objective |
|---|---|
| Reference | \(\widehat\lambda\) |
| Reference + stock RLT | \(\widehat\lambda\) |
| Reference + TC | \(\widehat\lambda+3/16\) |
| Reference + TC + stock RLT | \(\widehat\lambda+1/4=F^*_{IP}\) |

For the third cell, the old local product bound gives
\(J\le4g+(3/4)b_2\); TC then implies \(g\ge a/16\). The retained state
penalty gives \(P\ge4-a\). Since \(a\le3\) and
\(\widehat\lambda>1/16\), the lower bound is
\(\widehat\lambda+3/16\). Its old attaining point has \(g=3/16\),
\(J=3/4\), violating \(J\le3g=9/16\).

The zero-g old mixture still attains the first two cells. For the fourth cell,
use the existing equal mixture of four legal fleets whose final inventories
are permutations of (0,1,1,1). Each station has
\(s_0=1/4,s_1=3/4,s_2=0\). Set \(g=1/4\), \(q_0=1/16,q_1=3/16\),
\(Z_i=3/16\), \(H_{ij}=1/2\), \(e_i=1/4\). Full exact replay checks every
one of the original 583 matrix rows, all 284/298 variable bounds, the state
penalty, and R88 B1/B2 extensions. A saved matching integer fleet supplies the
upper bound. Existing zero-inventory loaded-return fleets also pass full
exact replay and the stock rows; the variable-inventory/zero case was not
removed. No unchanged historical enumeration was repeated and no solver was
needed for these proofs. See math/exact.json and independent review records.

The old zero-g point satisfies stock RLT and violates TC by 3; the old TC
attaining point satisfies TC and violates the stock upper row by 3/16. Thus
neither information family implies the other on this retained full reference.

The third cell is not claimed for arbitrary lambda. The result proves a
specific complementarity of count and resource products. It does not by itself
justify adding TC to the complete current algorithm.

## 5. GS, heterogeneous targets, AP and earlier station products

The historical structural-cut and structural-policy studies already implemented
independent aggregate \(W_{GS}\approx gS\), its four McCormick rows and
\(H_\Sigma\le nW_{GS}\), and tested fixed subproblems. With equal targets
and tight \(S\le B/D\), that construction also closes the tiny TC gap.
The tiny closure therefore does not show superiority over historical GS.

The new distinction is consistency of the same \(Z/q\) variables in the stock
normal \(\sum Y_i\), as distinct from the ratio normal \(\sum Y_i/D_i\).
For a pure product witness, take two stations with \(D=(1,2)\), states 0/1/2,
\(B=1\), \(g\in[0,1/2]\), \(g=1/4\), and

\[
s_1=(3/4,1/4,0),\quad q_1=(1/4,0,0),\qquad
s_2=(5/8,0,3/8),\quad q_2=(1/16,0,3/16).
\]

The local VD-P constraints hold, \(Y=(1/4,3/4)\), \(Z=(0,3/8)\),
\(S=5/8\), and shared \(W=\sum_iZ_i/D_i=3/16\). This satisfies all four
aggregate McCormick rows on \([0,1/2]\times[0,1]\), but violates
\(\sum Z_i\le Bg\) by \(1/8\). It is a product-block separation, not a
claimed complete BRP/TC extension. Real-root objective gains require the actual
same-domain reoptimizations reported separately.

The new GS controls use the same saved domain, a proved fractional-inventory
knapsack upper bound on S, no reverse-H inequality, no S buckets and no
controller change. Independent W and shared W controls are named separately.
R55 MC4 and VD-P concern station boxes/state hulls; they are not the missing
global budget products. R132-133 already distinguish service-coordinate
strictness from objective gains. R135 AP/IND addresses state-penalty
cancellation under its stated projection assumptions and retains its accepted
mixed/negative complete-method history. AP remains off here. None of these
historical results is relabelled as a new independent validation sample.

## 6. Extension boundary

A selected additional physical resource row can be treated by the same two
slack products, using its existing state expression in s and q. For example,
\(C(s)=\sum_{i,y}(b_i-y)_+s_{iy}\) equals total pickups at an integer shared
state completion. With unloading on return, handling time is
\((t_p+t_d)C\), so \((t_p+t_d)C\le mT\) is necessary. This does not cap
cumulative pickups by Q. Such a row is an optional separate exploration;
the primary full comparison changes only the four stated inventory rows.
