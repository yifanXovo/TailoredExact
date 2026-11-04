# Evidence-led refinement, before residual-potential results

The first three AP+GD+STOCK+TC/TC2+count-range LP points have explicit
hard-resource joint mixtures, and every inventory in those mixtures satisfies
the actual Gini upper interval. Thus these points are compatible with the
same necessary oracle domain (to the recorded floating residuals).

N-B35's zero-potential inventory price separates: LB .3929789535186394,
UB .39604654895666136, against strong reference .3866980286738351.
All six positive bins are covered; no unprocessed component was discarded.
This scalar result does not characterize the whole epigraph. K35 and N-C20
have feasible inventory UBs below their LPs and are nonseparating in this
direction only. Their full epigraphs remain untested.

Before attributing an increment beyond old count expressions, also append
the existing shared-Gini count-factor inequalities on every supported
threshold (R142's algebra in this root scope). This is a targeted stronger
reference, not a new family. Reconstruct its joint mixtures when used.

For nonzero directions use the exact decomposition Theta(s)=H(s)+Gamma(s).
Search residual potentials psi on the states with positive observed mass,
with the largest-mass state anchored to zero and |psi| <= .05. Set original
pi=h+psi, translated by one constant per station. The restricted dual master
only proposes directions and can never supply the installed intercept.

The 537-state full oracle is potentially wasteful at sparse marginal points.
The structural refinement partitions its full domain into (i) all stations
using active states and (ii) at least one inactive state. Bin-MILP pricing is
used on (i); an exact one-bit, hard-total unary DP supplies a conservative
bound for (ii), dropping G/bin restrictions only as relaxation. The global
intercept is the minimum of both bounds. Negative inactive potentials are
reduced by a deterministic 12-step scalar bisection while maintaining the
actual complement bound, to avoid unnecessarily weak transported rows.
The whole original parent domain is thereby covered explicitly. No child
pricing row is sent upward without this complement qualification.

Tiny or negative floating selector masses are discarded only in direction
discovery. Full-domain row validity is independent of this choice. Separation
uses the saved raw point with a reported potential-weighted dropped-mass
uncertainty, and the complete LP retains every original selector and auxiliary
free. Row coefficients omitted by Native-scale filtering receive exact
one-hot intercept correction. Independent static review admits this lifting
argument; a small exhaustive complement check precedes its real use.

These are offline diagnostics. Production is still unentered. No role-based
or wall-clock dispatch rule is being installed. The expense ceiling and full
evidence retention remain those of the original goal.

## Finite cut-loop question (recorded before its results)

The first N-B35 support row separates its old optimum by .0263928, but the
free complete LP retains exactly the same optimum .3866980 by moving its
marginals. The known CP rows have no distinguishable LP increment on any
of the three roles. One point separation is therefore insufficient evidence
of root-bound gain or online value.

Give the expression a deterministic eight-support-round diagnostic on each
preselected role. At each newly reoptimized point, reconstruct a joint
mixture and qualify a new full-domain support direction. Include the already
qualified zero-potential scalar floor where it separates (this criterion is
uniform; only N-B35 currently meets it). Each LP keeps all prior rows and
every original variable free. Stop if pricing or the joint-distribution
qualification is unresolved, or after eight support rounds; a first zero
root increment does not stop the loop. No complete method is admitted yet.
This answers whether the first zero increment is merely movement along a
large optimal face, and measures the cost/strength of a small row collection.

## Exact normalized pricing and the RN attribution contrast

All eight rounds completed. The N-B35 loop costs 444.08 outer seconds and
retains only its scalar-floor increment. K35 gains .00002045 and N-C20 gains
.00016133 over the CP reference. Thus sparse point separation is easy while
the small lifted row collection is weak after free marginal movement.
N-B35's later bin pricing also becomes materially slower than its first row.

Use the already known normalized-state formulation as an exact integer
pricing model: binary one-hot x and tL*x<=w<=tU*x, sum_y w=t force w_selected=t;
sum_i c_i sum_y y*w=1 gives tS=1. Pairwise absolute differences in normalized
ratios therefore give the exact Gini objective. Keep hard stock on x and the
old scaled-stock rows on w/t. Handle the zero inventory separately. This
eliminates bin approximation error, not Native MIP uncertainty. The independent
theoretical review and exhaustive three-domain qualification passed. It is
an integer use of R143's RN expression, not a new normalization theorem.

First append continuous RN+scaled-stock to each full CP reference. The actual
free values are N-B35 .38673718656544753, K35 .2788356429814587 and N-C20
.17446526778483834. K35's old RN gain exceeds the prior row-loop gain, so that
small earlier gain cannot establish new strength beyond RN. The first N-B35
inventory floor remains above this stronger reference and will be installed
before judging residual-support gains there.

For each of the three same domains, a full-state residual dual master uses
|psi|<=.05, largest-mass per-station gauge and at most six candidate/pricing
iterations. Pricing uses the normalized integer model, at most 120 seconds
per direction, Seed0/Threads1, with full-domain bounds and no inactive penalty.
Only a qualified separating bound admits a row to the same free model. A
pricing UB disproves only its own direction; an unresolved MIP remains
undecided. This contrast tests whether the inexpensive complement lift,
rather than the objective object itself, explains marginal migration.
