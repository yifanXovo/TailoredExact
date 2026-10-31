# Reciprocal normalization of the Gini block

Round143 retains the stable R137 GI-TBC route, operation, inventory and selector
structure. The research question is whether a second, normalized use of the same
inventory selectors supplies useful information beyond the old shared-g
products. The objective remains the original \(g+\lambda P\). The penalty is
never multiplied by the reciprocal variable. RN is an intersection with the
old model, with its original integer constraints and stable cuts retained.

## Exact integer extension and compact implementation

Use the actual binary64 coefficient \(c_i\) loaded in the old row \(r_i=c_iY_i\).
Let \(S=\sum_i c_iY_i\) and \(A=\sum_{i<j}|c_iY_i-c_jY_j|\). On a full model
scope with \(0<S_L\le S\le S_U\), put \(L_t=1/S_U\) and \(U_t=1/S_L\), rounded
outward. For the existing station states, RN adds continuous
\(t,w,\widehat Y,\widehat h\):

\[
 L_t\le t\le U_t,\quad L_t s_{iy}\le w_{iy}\le U_t s_{iy},\quad
 \sum_y w_{iy}=t,\quad \widehat Y_i=\sum_y y w_{iy},
\]
\[
 \sum_i c_i\widehat Y_i=1,\quad
 \widehat h_{ij}\ge\pm(c_i\widehat Y_i-c_j\widehat Y_j),\quad
 \sum_{i<j}\widehat h_{ij}\le n g.
\]

All new columns are continuous and nonnegative. The product facets
\(w\ge t-U_t(1-s)\) and \(w\le t-L_t(1-s)\) follow from the station mass equality,
\(\sum_y s_{iy}=1\), and the other states' upper/lower bounds. Omitting them is therefore
an exact compact implementation of RN1. No old state_g, zprod or h column is
reused: they have different physical units.

At integer selectors, every unselected \(w\) is zero and the selected \(w=t\).
Hence \(\widehat Y=tY\) and normalization gives \(tS=1\). The new Gini row says
\(g\ge A/(nS)\). Conversely, any original integer feasible point with \(S>0\)
and any legal epigraph \(g\ge A/(nS)\) extends by \(t=1/S\), \(w=ts\),
\(\widehat Y=tY\), \(\widehat h_{ij}=t|c_iY_i-c_jY_j|\). The original
model \(g\) is retained even when it exceeds physical \(G\); its current g interval
must still be respected. This extension proof does not authorize a physical
MIP Start whose true G lies outside that interval.

Thus RN preserves the original integer problem and its old-space projection
is contained in the old continuous relaxation. Containment alone proves
neither a strict optimum gain nor faster complete search.

The production writer adds two finite caps with the same old-space projection.
\(\widehat Y_i\le M_iU_t\) follows from nonnegative \(w\) and \(\sum_yw_{iy}=t\).
Since \(v_i=c_i\widehat Y_i\ge0\) and \(\sum_i v_i=1\), the minimum necessary
\(\widehat h_{ij}=|v_i-v_j|\) is at most one. Any feasible RN extension can
reduce each \(\widehat h\) to that minimum without changing an old column or
violating the Gini upper row; \(\widehat h_{ij}\le1\) is therefore redundant in the
projection. These finite caps permit the established full-matrix/Start reader
to remain unchanged. They are not an extra integer-count strengthening.

## Full-scope denominator bounds and numerical transport

Empty departure, loaded return and conservation imply
\(B^-=\max(0,B-\sum_kQ_k)\le\tau=\sum_iY_i\le B\), with
\(B=\sum_i b_i\) excluding the depot.
Cumulative pickups are not bounded by fleet capacity. For actual supported
endpoints \(m_i,M_i\), set \(\tau_L=\max(B^-,\sum_i m_i)\) and
\(\tau_U=\min(B,\sum_i M_i)\).
An incompatible interval follows the existing infeasible-domain route and is
never inverted.

Start from \(Y=m\). The minimum \(S\) fills \(\tau_L-\sum_i m_i\) inventory units
in ascending \(c_i\) order; the maximum fills \(\tau_U-\sum_i m_i\) in descending
\(c_i\) order. Positive coefficients make those total-inventory endpoints optimal. This continuous box-budget
problem relaxes support holes and all routing constraints, so its bounds are
valid for the full original scope without another Optimize or enumerating S.
No observed S, incumbent inventory or heuristic sample supplies a bound.

The diagnostic oracle uses Fraction values of actual loaded binary64 c_i.
Production reuses checked common-dyadic __int128 arithmetic from R140 for the
complete coefficient/inventory sums. It converts S_L downward and S_U upward,
then rounds each reciprocal outward. This covers accumulated summation error
before inversion. Checked arithmetic fails closed outside its representable
range. New row coefficients bypass the legacy near-zero/near-one formatter;
an exact positive power-of-two row scale, if necessary, preserves coefficients
that a Native LP parser would otherwise omit. No feasibility/optimality
tolerance is loosened.

Every model uses its own actual supported interval and physical budget. A
parent-valid bound would remain valid on a child, but a local bound is never
exported to a larger scope. The single applicability rule is a proved positive
full-scope S_L. If its lower bound is zero, RN contributes no rows or columns
and the old exact model and S=0 convention remain. The optional zero/positive
disjunction in the goal is not implemented: no evidence currently requires
that second controller.

## Strict separation and an explicit limitation

The exact three-station fixture has \(c=(1,1,1)\), support \(\{0,1\}\),
\(\tau\in[1,2]\), inventory-one selector masses \((1,1/2,0)\), old \(g=1/3\)
and inventory-one old g-products \((1/3,1/3,0)\).
\(H=2\), \(J=2/3\), \(\tau=3/2\) satisfy the declared old Gini,
stock, TC and TC2 blocks. Endpoint pair transport gives the same absolute
differences, and the penalty on this support is linear. This is a specified
relaxation subblock witness, not a fabricated full BRP instance.

RN has \(t\in[1/2,1]\), \(v=(t,1-t,0)\). The middle site's zero-state product is
\(2t-1\ge1/4\), so \(t\ge5/8\) and \(g\ge2t/3\ge5/12\). Equality is attained
at \(t=5/8\) with \(w=((0,5/8),(1/4,3/8),(5/8,0))\).
The strict separation is exactly \(1/12\).

For four stations with \(c_i=1\), support \(\{0,1\}\), fixed \(\tau=3\) and all
inventory-one masses \(3/4\), RN admits \(t=1/3\), \(w_1=1/4,w_0=1/12\) and
\(v_i=1/4\), hence \(g=0\). Old TC gives \(H\ge3\), fixed-inventory stock
gives \(J=3g\), and \(H\le4J\) implies \(g\ge1/4\).
RN alone does not dominate the retained integer-count information and does
not close the full R133 integer-objective mixture gap. This directly supports
the additive design; no replacement-model comparison grid is warranted.

## Twelve fixed-point checks and their scope

The original R140 carrier is bound by SHA256
`2cb1ab936753ce9ac26ae1f970b070b2751190af79f6a80a8b0f5d254902bf5f`.
The separately named supplemental offline ZIP was not present locally. The
portable checker therefore reconstructs all twelve checks from that original
carrier, without loading Native or rerunning any old optimization. These are
newly reconstructed certificates, not an assertion that the missing ZIP was
received. Some reconstructed rank/eta supports are stronger than the rounded
lower bounds stated in the goal; their actual identities are retained.

With selectors fixed, each station's attainable \(v_i\) at \(t\) is an interval
\([\ell_i(t),u_i(t)]\) obtained by exact fractional knapsack. Their endpoint
functions are piecewise linear. The complete feasible t interval satisfies
\(\sum_i\ell_i(t)\le1\le\sum_i u_i(t)\), together with all station product/mass
bounds. For any permutation rank vector \(a_i=2\operatorname{rank}_i-n-1\),
or a convex average at ties, and \(\eta\),

\[
 ng\ge\eta+\sum_i\min\{(a_i-\eta)\ell_i(t),(a_i-\eta)u_i(t)\}.
\]

The checker minimizes this expression at every endpoint and knapsack/
normalization breakpoint of the complete t interval. Six K35/RX20-T1 saved
points are excluded. Rank supports may be selected using a finite search, but
the final lower bound covers the whole interval exactly; unsuccessful sample
search is never an exclusion proof. For K20/RX35-T2, a constructive t and
water-filled attainable v give six extensions with original columns and
objective unchanged. The new columns and binary64 linear residuals are saved.

These checks interpret binary64 c and selector masses as rationals. The old
complete LP points are still numerical feasible optima under the inherited
policy, not rational full-matrix optimality certificates. A separated saved
point need not raise the reoptimized LP optimum; an extendable saved optimum
does not make RN redundant throughout the old model. The four separately
optimized matching LPs test the former question directly.

## Historical and literature position

R88 already developed pair-CDF/endpoint transport; R138 already established
the continuous selected-resource shared-factor hull application. Neither is
renamed as RN. R133's integer objective mixture issue remains a distinct
limitation. Earlier rejection of coarse denominator buckets, approximate
reciprocals and unproved scaling of all integer variables is not an experiment
on this retained-integer finite-selector construction. The R142 count-proof
continuation is closed; its CP/ALL controls are not inherited into the RN
candidate. R137 AM/no-strict-child is also left unchanged.

Reciprocal normalization is standard. Charnes and Cooper (1962) introduce the
linear-fractional change of variables and normalized denominator. Yue,
Guillen-Gosalbez and You (2013) combine that transformation with Glover
linearization for MILFP reformulations; their publisher abstract explicitly
identifies those ingredients. Chen and Hooker (2023), section 4.2 and the
appendix's Gini formulation, already give a normalized linear formulation of
the Gini criterion. Their double-pair normalization is equivalent to A/(nS)
here. The project contribution being tested is the exact connection to its
existing integer inventory/route structure, complementarity with prior
expressions, and complete computational value. No new general fractional
programming principle, full integer hull, or journal-level improvement is
claimed.

Primary sources checked on 1 November 2026:

- [Charnes and Cooper, 1962, DOI](https://doi.org/10.1002/nav.3800090303),
  and the CMU library scan's displayed transformation on p.182.
- [Yue et al., 2013, publisher abstract](https://aiche.onlinelibrary.wiley.com/doi/abs/10.1002/aic.14185).
  Full-text access was not needed or claimed for the above attribution.
- [Chen and Hooker, 2023, author manuscript](https://johnhooker.tepper.cmu.edu/equityGuideAOR3post.pdf),
  section 4.2 and Gini appendix, displayed manuscript pp.13 and 36-37;
  [published article](https://doi.org/10.1007/s10479-023-05264-y).
