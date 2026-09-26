# Product-state critical band for a split: coordinator proposal

Status: both the critical-band theorem and the additional mass-weighted lemma have been independently reviewed in `split_critical_band_independent_review.md`. No code change, performance result, or admission of a different split strategy. This refines the full-primal-vector feasibility criterion in `split_mathematics.md`.

## The state/product block

Fix an optimal parent LP point x with G in [a,b] and selectors s_j in [0,1]. For each lifted product q_j = G s_j, the relaxation has

    a s_j <= q_j <= b s_j,
    G - b(1-s_j) <= q_j <= G - a(1-s_j).

Include in a multiset T the ratio q_j/s_j when s_j>0 and the ratio (G-q_j)/(1-s_j) when s_j<1. Include G itself. Define ell=min T and u=max T. Exact parent feasibility gives [ell,u] contained in [a,b]. For 0<s_j<1, G is the convex combination of the two ratios with weights s_j and 1-s_j. At s_j=0 or 1 the corresponding fixed-point identities q_j=0 or G must hold; they must be verified, not approximated by dividing through a numerical zero.

For any subinterval [a',b'] of [a,b], the unchanged point satisfies the renewed G bounds and all four renewed product-envelope inequalities **if and only if** a'<=ell and b'>=u. Proof: division of the first and fourth inequalities gives a' no larger than each present ratio; division of the second and third gives b' no smaller than each ratio. Zero/one selector identities and the explicit G entry handle the boundaries. This theorem concerns the specified product block. To transfer it to a complete child LP, verify every additional changed row, support/domain restriction, bound and cut, plus the unchanged objective and all other columns.

For a covering split [a,p] union [p,b], with a<p<b:

- the unchanged point remains feasible in the left product block iff p>=u;
- it remains feasible in the right product block iff p<=ell;
- neither block keeps the point iff ell<p<u.

Consequently, if all other child changes preserve this point, any p outside the open critical band (ell,u) leaves one child optimum equal to the parent optimum: that child contains the parent minimizer and is a restriction of the parent. The lower bound of the two-child union therefore cannot increase immediately. This is a sufficient zero-gain certificate for the complete LP only after full-point child feasibility is established. It is not a reason to discard an unresolved child or change coverage.

When ell=u=G, every lifted product at x is exact (q_j=G s_j), and conversely. No covering split of G alone can eliminate this point through these product envelopes. Other strengthening or integer branching may still matter; this does not certify the original routing problem.

## A candidate point and its limits

If ell<u, p=(ell+u)/2 excludes this particular parent point from both renewed product blocks. It maximizes min(p-ell,u-p) over p in [ell,u], a precisely defined margin in G units. It does **not** maximize LP-bound gain, establish strict gain in the presence of alternative parent minimizers, or imply a faster MIP.

This critical-band midpoint must not silently replace the existing interval midpoint. It may lie arbitrarily close to a parent endpoint. The current geometric depth proof for interval midpoints then fails; even a minimum leaf width alone does not prove that a sequence of highly unbalanced splits terminates. A full proposal would need a justified global progress rule or a new termination proof, as well as complete child-model checks. Introducing an unexplained balance parameter is not admitted here.

The immediate research use is diagnostic: compute the band from preserved LP points, classify whether the current interval midpoint can preserve that point, and compare with the full child-feasibility check. Small exact-rational fixtures must cover s=0/1, a=b, exact products, wide and narrow bands, boundary splits, alternative optima, and extra child constraints. No production action may rely on a merely approximate ratio near zero without an interval/numerical certificate.

## Additional mass-weighted exclusion lemma

For the actual complete onehot blocks, sum_j s_ij=1 and sum_j q_ij=G. The complementary ratio (G-q_ij)/(1-s_ij), when defined, is a convex combination of the other positive-mass ratios q_ik/s_ik. G is their overall convex combination. Hence the same critical-band endpoints can be obtained from the positive-mass q/s ratios alone. The complement inequalities used above are implied by summing the other state bounds; they need not be explicit model rows.

There is a second, mass-weighted splitting criterion that avoids dividing by small masses. For a fixed parent point and proposed p, define the total violations of the renewed upper/lower product rows:

    Phi_left(p)  = sum_(i,y) max(q_iy - p s_iy, 0),
    Phi_right(p) = sum_(i,y) max(p s_iy - q_iy, 0).

Phi_left is nonincreasing and Phi_right nondecreasing in p, and their difference is n(G-p). Thus p=G balances them and maximizes min(Phi_left(p),Phi_right(p)) over [a,b]. At this point both equal one half of sum |q_iy-G s_iy|. If at least one product is inexact, this value is positive, G is strictly interior to [a,b], and the two child product blocks both exclude the current point. If products are exact, the best minimum is zero and this criterion gives no gain. The statement is about summed raw product-row residuals in the specified coordinates, not arbitrarily scaled solver rows, LP-objective improvement, or MIP progress.

Proof of maximality: for p<=G, Phi_left>=Phi_right, so the minimum is the nondecreasing Phi_right; for p>=G the minimum is the nonincreasing Phi_left. At p=G the sums are equal. This accounts for selector masses rather than amplifying a nearly zero mass through a ratio. It still requires reliable numerical evaluation and cannot exclude alternative LP minimizers. In particular, it does not restore geometric finite-depth control: p=G may be arbitrarily close to an endpoint. A production LP-G split would require a separate termination argument or a retained, justified finite-tree safeguard. It is not combined with the depth-removal proposal by this note.
