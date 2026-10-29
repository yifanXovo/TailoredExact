# Round140: inventory budgets and two-sided threshold counts

This is a problem-specific resource/count strengthening and a finite algorithm
study. The concave chord inequality and McCormick/RLT envelopes are standard
tools; neither is claimed as a new general theorem. The inherited R137 stable
method, R138 shared-stock result and R139 placement result retain their scopes.

## Inventory budget and exact finite supports

Only stations, excluding the depot, contribute to stock. With empty departures
and possibly loaded returns, let

\[
B=\sum_i b_i,\qquad R_k=\sum_i(p_{ki}-d_{ki}),\qquad
\tau=\sum_iY_i=B-\sum_kR_k.
\]

An integer physical route has $0\le R_k\le Q_k$. Thus
$B^-:=\max(0,B-\sum_kQ_k)\le\tau\le B^+:=B$.
The old writer explicitly enforces $R_k\ge0$; this derivation does not assert
that its LP explicitly contains the same expression's upper bound. Intersect
the budget with the sum of supported minima/maxima. An observed LP stock total
never replaces a global inventory bound. In particular K35 has $B=326$ and
saved $\tau=295$, with 31 units returned.
In that saved K35 root domain the sums of supported minima/maxima are 37 and
541, so intersecting the supports leaves the physical budget $[251,326]$
unchanged; 295 is solely the observed point's inventory total.

For each actual nonempty support $\mathcal Y_i$, selectors sum to one and
$Y_i=\sum_yys_{iy}$. The loaded binary64 coefficient $c_i>0$ in
$r_i-c_iY_i=0$ is interpreted as its exact dyadic rational. Thresholds are all
distinct positive supported $c_iy$, with $t_0=0$ and
$\Delta_j=t_j-t_{j-1}$. No decimal rounding or tolerance merges thresholds.
Define $K_j=\sum_i\sum_{y:c_iy\ge t_j}s_{iy}$ and
$A=\sum_{i<l}|r_i-r_l|$. At integer selectors,

\[
A=\sum_j\Delta_j K_j(n-K_j).
\]

For each pair, a threshold separates its two ratios exactly on the intervals
between them. Summing interval lengths gives its absolute difference, then
summing pairs gives the identity. No division by $\sum r_i$ is needed; the
existing zero-denominator convention remains unchanged.

## Necessary lower and upper counts

At threshold $t_j$, a station is forced high if every support reaches it,
forced low if none reaches it, and optional otherwise. Write these sets as
$H_j,L_j,O_j$. The old R134 upper count starts at supported minima $m_i$,
sorts optional minimum crossing increments in ascending order, and buys as
many as possible within $B^+-\sum m_i$. Add $|H_j|$ to obtain $u_j$.
The old aggregate TC uses $(n-u_j)K_j$, even when forced high is nonempty.

For a lower count let $M_i=\max\mathcal Y_i$ and, for optional stations,

\[
b_{ij}^{<}=\max\{y\in\mathcal Y_i:c_iy<t_j\},\quad
d_{ij}=M_i-b_{ij}^{<}>0,
\]
\[
C_{0j}=\sum_{i\in H_j\cup L_j}M_i+
         \sum_{i\in O_j}b_{ij}^{<}.
\]

Sort $d_{ij}$ descending. The smallest $q_j\ge0$ with
$C_{0j}+\sum_{r\le q_j}d_{(r)j}\ge B^-$ gives
$\ell_j=|H_j|+q_j$. If $C_{0j}\ge B^-$ then $q_j=0$.
Indeed, with at most $q$ optional stations high, even the maximum possible
inventory is at most this expression. Every smaller $q$ is impossible when
it stays below $B^-$. This proves $\ell_j\le K_j\le u_j$ on the original
integer feasible domain. It does not assert that all counts in the interval
are physically achievable. Failure of the total supported maximum to reach
$B^-$, or $\ell_j>u_j$, is a real support/budget incompatibility and is encoded
as an impossible row. Counts are never clamped into a fabricated interval.

## Aggregate TC2 and its precise relation to old TC

For $\ell\le K\le u$,

\[
K(n-K)-\{(n-\ell-u)K+\ell u\}=(K-\ell)(u-K)\ge0.
\]

With $H_\Sigma=\sum_{i<l}h_{il}$, the new integer-valid row is

\[
H_\Sigma\ge\sum_j\Delta_j\{(n-\ell_j-u_j)K_j+\ell_ju_j\}.
\]

It uses existing selector columns only. Its coefficients can be negative and
its constant is usually positive. The row complements the product side
$H_\Sigma\le n\sum_i c_iZ_i$: TC2 captures joint discrete station counts,
whereas stock couples the common Gini factor to total inventory.

The new and old threshold chords differ by $\ell_j(u_j-K_j)$. The sign is
guaranteed only if $K_j\le u_j$. Fractional points of the old LP need not
respect explicit integer count bounds. Consequently **the old TC aggregate
row is retained**, and TC2 is an additional row. Adding both proves inclusion
of the old relaxation; a TC2-only replacement is not claimed to dominate it
on the full fractional domain. No per-threshold count rows are added by default.

For an exact counterpoint, take four supports $\{0,2\}$ with budget $[3,5]$.
At threshold 2, $\ell=u=2$. Each selector $(3/8,5/8)$ gives $K=5/2$ and
$\tau=5$. With $g=2/5$, exact common products give $J=2$; choose
$H_\Sigma=8$. TC2 requires only 8, while old TC requires 10. The four stock
envelopes on $g\in[0,1/2]$ and $H_\Sigma\le4J$ hold. This fractional block
point concretely demonstrates the need to retain old TC; it is not a full
BRP feasibility witness.

## Rational strict separation and its boundary

Take four stations, support $\{0,1,2\}$, $c_i=1$, and inventory budget $[3,5]$.
At thresholds 1 and 2, count intervals are $[2,4]$ and $[0,2]$.
At every station take $s=(1/2,1/4,1/4)$. Then $\tau=3$,
$K_1=2,K_2=1$, old TC is 2, and TC2 is 6.

Let $g=1/6$, $q_{iy}=gs_{iy}$, $Z_i=1/8$, $J=\sum_i Z_i=1/2$, and set
each of the six $h_{il}=1/3$, so $H_\Sigma=2$. All individual common-factor
products are exact. The four stock envelopes for $g\in[0,1/2]$ and
$\tau\in[3,5]$ hold; $H_\Sigma\le4J$ and old TC hold at equality.
TC2 is violated by 4. Thus count information remains genuinely incremental
even when this product block is completely consistent.

This same block also admits the proposed single-vehicle return-product
extension: take $Q=2$, $R=B-\tau=2$, and $W=gR=1/3$.
The effective lower and upper McCormick bounds both equal $1/3$, and
$J+W=5g=5/6$.
Thus adding these exact return products does not remove this strict block
point. This statement retains the same relaxation-block scope below.

This is a **strict point separation of the declared relaxation block**, not
a full BRP cutoff-domain strictness theorem, optimal LP gain, integer gap
closure or claim of new convexification theory. The suggested starting stock
$(2,2,1,0)$ admits routes for all 12 permutations of $(2,1,0,0)$ with one
capacity-2 vehicle. Mixing those routes supplies the selector marginals, but
does not by itself verify the actual complete exported matrix, cutoff and
all retained controls. The all-ones integer inventory is also feasible, so
an own-H cutoff may invalidate this proposed full-model witness. This study
uses the exact block witness plus actual complete-model continuous LP
reoptimization as its strictness and practical-strength evidence.

## Writer and proof interface

The production implementation is in `include/Round140Research.hpp` and the
canonical writer in `src/CplexBaseline.cpp`. `--round140-counts tc2` adds both
aggregates; `tc` adds only the retained old aggregate; default `off` preserves
old behavior. Stock remains the existing V2 BOTH formulation for the main
candidate. All methods keep own H, M-B/VD-P, pair-only support, AM .08,
maximum depth 8, minimum width $10^{-4}$, and AP off.

Exact checked 128-bit dyadic arithmetic represents the loaded coefficients,
threshold ordering/equality and accumulation on the measured GCC runtime.
The current instance/parser uses positive 32-bit integer targets: their
reciprocals exceed $10^{-12}$, and only target 1 gives coefficient exactly 1.
Thus the old generic writer's tiny-term filter and near-unit abbreviation do
not change these ratio coefficients; all six frozen inputs were also checked.
Any future floating-target extension would require a new coefficient audit.
Unsupported ranges fail closed instead of approximating counts. Python's
independent unbounded Fraction implementation is the qualification oracle.
Each right-side selector coefficient and the constant are rounded downward;
selectors are nonnegative, so this underestimates the exact right side even
for negative coefficients. Moving those coefficients to the left reverses
their signs correctly. An exact positive power-of-two row scale preserves
very small nonzero terms through Native import. Max-digits10 output bypasses
the legacy tiny-coefficient filtering/near-unit abbreviation. Empty rows use
the established `0 G` syntax.

Counts depend on the actual support of that canonical model. Root, child and
cutoff refresh construction each bind their own artifact SHA and domain.
Controls stay fixed throughout a process; no row is transferred from a
smaller domain to a larger one. The same writer serves outer LP, native
target and native terminal; no extra columns or Start mapping are introduced.
Existing epoch invalidation, full-frontier coverage, physical witness and
strict numerical/proof policies remain in force. An LP bound $\ell$ on an
improvement domain $f\le c$ transfers as $\min\{\ell,c\}$ to the full domain.
Native returned bounds and the controller's merged bound remain separate.

Actual saved-point separation, same-domain optimized gains, and complete
algorithm outcomes are distinct evidence levels. Their numerical results,
adverse outcomes, identity bindings and costs are given in the companion
scientific report and compact tables.
