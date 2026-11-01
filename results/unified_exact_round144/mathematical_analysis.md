# RN information in the original variables

The experimental question is whether one cheap root RN source can retain
useful normalized Gini information without retaining the RN columns in the
formal GI-TBC models. Stable R137, its own H, M-B/VD-P, pair-only support,
AM=.08, depth 8/minimum width 1e-4, AP off and R134 proof policy remain the
carrier. The research flag defaults off.

## Validity by finite-box projection

Let the matched continuous source be

\[
 \min\{c^Tx+c_0:x\in P,\ Ex+Fz\ge d,\ \ell\le z\le u\}.
\]

Only RN rows belong to this block; old routing rows, the objective cutoff and
the old objective remain in P. Equalities have unrestricted multipliers.
All new RN columns have objective coefficient zero. Production-redundant
finite caps are retained: \(t\in[L_t,U_t]\), \(w_{iy}\in[0,U_t]\), normalized inventory
\(\widehat Y_i\in[0,M_iU_t]\) (outward rounded) and normalized pair epigraph
\(\widehat h_{ij}\in[0,1]\).
The old diagnostic's infinite upper bounds are never interpreted as finite.

For any legal multiplier vector \(\beta\), set \(a=E^T\beta\), \(r=F^T\beta\)
and \(b=d^T\beta\). Then

\[
 a^Tx\ge b-\sigma_{[\ell,u]}(r),\qquad
 \sigma_{[\ell,u]}(r)=\sum_j\max(r_j\ell_j,r_ju_j).
\]

This validity argument needs no dual optimality and no exactly zero floating
residual. It applies to the actual RN row coefficients and actual finite
bounds. The resulting row contains only original selectors and G.

## Numerical transport

The implementation uses the equivalent \(\le\) convention. A \(\ge\) RN row is
negated and weighted by \(\max(\Pi,0)\); a \(\le\) row is weighted by \(\max(-\Pi,0)\);
an equality is oriented according to its unrestricted \(\Pi\) and weighted by
\(|\Pi|\). Wrong-sign inequality multipliers are clipped to the legal half-axis
and recorded. Thus the combination is \(A_x x+A_z z\le B\). Zero is submitted on
every extension column. The signed finite-box conversion bound produces

\[
 \widehat A x\le\widehat B,\quad
 \widehat B\ge B+\sum_j\max_{v\in[l_j,u_j]}
                 (\widehat A_j-A_j)v.
\]

For eliminated columns, this is precisely \(-\min_{\ell\le z\le u}A_z z\). For retained columns,
it compensates coefficient rounding, including deletion below 1e-12.
`projectObjectiveResources` encloses every product/addition with directed
binary64 intervals and rounds the final \(\le\) RHS upward. Existing R104 APIs
and behavior are preserved. Independent Fraction checks interpret every
binary64 row, multiplier, bound and submitted coefficient exactly. Actual
Native readback checks all terms and RHS; compact LP reoptimization measures
the remaining numerical loss.

## Matched-root value and its limits

Under exact optimal primal/dual solutions, the RN part of the optimal dual
attains the extension-box support at the optimal z. Replacing that dual
block by its single projected row retains the same dual lower bound; the
RN optimal x also satisfies the row. Hence the two matched root optima are
equal. These are the same-domain, same-objective assumptions of standard LP
duality and the earlier [R104 result](https://github.com/yifanXovo/TailoredExact/blob/aa1d0e5b268cf95442b3713b2af8fc505974f6c2/results/unified_exact_round104/mathematical_algorithm.md).
This is not a new duality theorem or the complete RN projection. A narrower
compatible descendant inherits validity; its optimum need not match RN.
Grouping before box support can lose cancellation, since
\(\sigma(r_1)+\sigma(r_2)\ge\sigma(r_1+r_2)\). No grouping grid is pursued.

R104's ACTIVE root preservation accompanied full-method regression; its
ACTIVE and SHADOW each used 4349 auxiliary LPs and 3644 DPs. Those negative
results remain. RN-P instead pays once for the newly established R143 RN
information and removes the extension columns from the formal model.
Neither the old result nor the compression theorem predicts search speed.

## Once-root integration and scope

The source runs after the current run's own H and initial root are known.
Its artifact, Native call, X/Pi/RC/basis, source cost and status have separate
identities. The source handle is discarded; its point and bound are not
installed as formal control or Start. The original model is rebuilt/embedded
with the PC and optimized normally. Future artifacts accept the PC only for
the same input and contained G/cutoff/support domains. An absent root selector
in a narrower support is exactly zero. New runs clear all source/cache state.
No instance identity, size, leaf-time threshold or hardware clock chooses the
representation. A zero RN dual aggregate gives an exact \(0\le0\); its outward
transported tautology \(0\le B\) with \(B\ge0\) is omitted as a mathematical redundancy.
A nonpositive proved denominator bound omits the RN
source uniformly. Failed/unknown sources retain their actual status.

## Original-space structure and scalar floors

A scalar objective floor can also match a single root value. Structural
information is distinguished here on an explicitly limited rational block.
For any rank support a of the pairwise absolute-difference sum, write the
normalized inventory as \(v_i=c_i\sum_y y w_{iy}\). With \(\sum_i v_i=1\),
\(\sum_y w_{iy}=t\), and \(L_t s_{iy}\le w_{iy}\le U_t s_{iy}\), any \(\eta\)
and station multipliers \(\lambda_i\) give

\[
 d_{iy}=(a_i-\eta)c_i y-\lambda_i,\qquad
 \kappa_{iy}=\min(L_t d_{iy},U_t d_{iy}),\quad
 \Lambda=\sum_i\lambda_i,
\]
\[
 ng\ge\sum_i a_i v_i
 =\eta+\Lambda t+\sum_{i,y}d_{iy}w_{iy}
 \ge\eta+\min(L_t\Lambda,U_t\Lambda)
       +\sum_{i,y}\kappa_{iy}s_{iy}.
\]

This Rank-PC family is valid independently of its strength at a chosen
point. The station coefficients are the minimum of two affine functions of
the inventory state. A rank vector has entries \(2\operatorname{rank}_i-n-1\), or a convex
combination of such permutations; this is the ordinary support function of
the absolute-difference sum.

Consider the continuous three-station block with \(c_i=1\), supports \(\{0,1\}\),
inventory sum in [1,2], and selector mass at inventory one fixed to
(1,1/2,0). This is a declared LP cross-section, not an integer routing domain.
The old R143 witness has \(g=1/3\) and old g-state products
\(q=((0,1/3),(0,1/3),(1/3,0))\). Each station's products sum to \(g\) and obey the
full unit-box product bounds. Here \(H=2\), \(J=2/3\) and \(\tau=3/2\);
\(H\le3J\), TC \(H\ge\tau\), TC2 \(H\ge2\) and the stock bounds

\[
 \max(g,\tau+2g-2)\le J\le\min(\tau+g-1,2g)
\]

all hold. Endpoint pair couplings attain the same absolute differences
because each pair has at least one fixed inventory marginal. With rank
\(a=(2,0,-2)\), \(\eta=1\) and station multipliers \((1,-1,0)\), the valid Rank-PC is

\[
 3g\ge1-s_{1,0}+\tfrac12s_{2,0}-3s_{3,1}.
\]

Its RHS at that point is \(5/4\), so \(g\) must be at least \(5/12\). The RN optimum in
this fixed-selector cross-section is exactly \(5/12\): normalization gives
\(v=(t,1-t,0)\), while the middle zero-state product is \(2t-1\ge1/4\). Thus
\(t\ge5/8\) and \(g\ge2t/3\ge5/12\). Equality is attained at \(t=5/8\) with
\(w=((0,5/8),(1/4,3/8),(5/8,0))\); choosing old \(q=((0,g),(0,g),(g,0))\) also
satisfies the retained old rows at \(g=5/12\).

Append an independent \(p\ge0\) and use the same objective \(g+p\) in both old and
RN blocks. The RN optimum is still \(5/12\) (attained with \(p=0\)), so this is a
valid matched scalar floor. At the old point, \(p=1/12\) gives \(g+p=5/12\): the
scalar floor is satisfied while the structural PC remains violated by 1/4.
This witness is confined to the declared old Gini/stock/count/endpoint-product
block with that independent epigraph. It is not a strict separation witness
for an entire routing P, and it proves no universal floor dominance.

## Saved-point witnesses and provenance

The six goal-supplied Rank-PC point violations have been finitely reconstructed
from saved R143 ranks, eta, supports, denominator bounds and old points, with
zero Optimize. Violations divided by n are .023855359195111166,
.005944242130579499 and .011385760529762846 for K35 BASE, stock and TC+stock;
they are .06850590621823809, .022542692207833517 and .022542692207833594 for
the corresponding RX20-T1 domains. The reconstructed legal station
subgradients give exact nonzero counts 15/15/40 and 14/14/14. These are their
own certificate identities, not the absent supplemental ZIP's exact rows
with counts 19/19/44 and 14/14/14. The point violations agree with the goal's
displayed decimals and are not newly optimized objective gains. R143's old
raw has no complete Pi/RC/basis; this round's paid sources genuinely obtain
those attributes. New source/compact LPs and compiled-row qualification are
reported separately from those point certificates and from full-method costs.
