# Balanced normalized closure rule

K1-AM-SF starts from one complete strict-improver Gini interval and considers
only its exact midpoint children.  For a parent interval (I), let (B_I) be
its valid LP lower bound, (B_-) and (B_+) the valid lower bounds of the two
midpoint children, (U) an independently verified incumbent, and
\(\varepsilon\) the existing certificate tolerance.  Define

\[
\Delta_I=\max\{U-B_I,\varepsilon\},\qquad
r_\pm=\operatorname{clip}_{[0,1]}\frac{B_\pm-B_I}{\Delta_I},
\]

\[
\beta_I=\min\{r_-,r_+\},\qquad
\alpha_I=\frac{r_-+r_+}{2},\qquad
M_I=\alpha_I\beta_I.
\]

When both child LP bounds are finite and valid, K1-AM-SF splits exactly when
\(M_I\ge\tau\), with the empirically frozen threshold \(\tau=0.08\).

## Exceptional evidence

- If both children are proved infeasible, their union proves the parent
  infeasible and the parent is closed exactly.
- If exactly one child is proved infeasible, exact coverage retains the other
  child; the finite-child score is not substituted for this logical action.
- Invalid or unavailable child LP evidence cannot authorize a score-based
  split or closure.  The valid parent remains open.
- If neither finite child strictly improves on (B_I), then at least one
  normalized improvement is zero and the score cannot justify a split.
- Native-target continuation and exact-parent closure remain the existing
  K1-AM-SF lifecycle actions.  The score does not convert a restricted-range
  result into an original-problem certificate.

## Properties

1. **Left/right symmetry.** Swapping the children swaps (r_-) and (r_+)
   and leaves their mean, minimum, and product unchanged.
2. **Bounds.** Clipping gives (r_\pm\in[0,1]), hence
   \(\alpha_I,\beta_I,M_I\in[0,1]\).
3. **Positive-affine scale invariance.** Under (x\mapsto ax+b), (a>0),
   both each bound improvement and the un-clipped denominator scale by (a).
   With the certificate tolerance transformed in the same objective units,
   each ratio and therefore (M_I) is unchanged.
4. **Two-sided requirement.** If either child gives no normalized improvement,
   its (r) is zero, so \(\beta_I=M_I=0\).
5. **Union interpretation.** The lower bound of the child union is
   \(\min\{B_-,B_+\}\); after the common normalization and clipping, its
   improvement is \(\min\{r_-,r_+\}=\beta_I\).
6. **Total tightening.** At fixed \(\beta_I\), increasing the other child's
   normalized gain raises \(\alpha_I\), so the score rewards additional
   two-sided tightening without accepting a zero-gain child.
7. **Midpoint minimax.** If a point (s\) splits \([L,U]\), the largest child
   width is \(\max\{s-L,U-s\}\).  It is at least \((U-L)/2\), with equality
   only at (s=(L+U)/2\).
8. **Status of \(\tau\).** The value 0.08 is a frozen empirical controller
   parameter, not a universally optimal theoretical constant.

The implementation uses first-class controller fields.  Historical Round/C6
fields remain compatibility adapters and do not define the paper algorithm.
