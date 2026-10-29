# Inventory budgets strengthen discrete Gini threshold counts

Round140 research increment, 29-30 October 2026 (Asia/Shanghai). This standalone section extends the maintained Round137 complete manuscript and the Round138/Round139 increments. The selected panel is known research data. The study separates a valid structural strengthening, an optimized continuous bound gain, and complete-method performance.

## 1. Mathematical structure and exact scope


This is a problem-specific resource/count strengthening and a finite algorithm
study. The concave chord inequality and McCormick/RLT envelopes are standard
tools; neither is claimed as a new general theorem. The inherited R137 stable
method, R138 shared-stock result and R139 placement result retain their scopes.

### Inventory budget and exact finite supports

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

### Necessary lower and upper counts

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

### Aggregate TC2 and its precise relation to old TC

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

### Rational strict separation and its boundary

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

### Writer and proof interface

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

McCormick/RLT product envelopes are inherited standard tools [@AdamsSherali1990R138; @SheraliAdams1999R138]. The project-specific contribution is the inventory-driven two-sided count information, its qualified implementation, and its finite complete-method evaluation. No general chord inequality, cardinality bound, or product envelope is claimed as a new theorem.

## 2. Saved points and same-domain reoptimization

The fixed R138 diagnostics archive and saved solution SHA values were checked before new Optimize. All four saved old TC+stock optima are separated. This does not imply a bound gain until reoptimization. RB35-T2 was absent from the old four-root TC panel; its old-TC control is newly optimized here. Nine new explicit continuous LPs use exactly matched objective, support, cutoff and g endpoints, explicit Seed0, one thread and serial execution.

| Role | STK L | STK+TC L | STK+TC+TC2 L | Increment |
|---|---|---|---|---|
| K-20-S | 0.2045904392 | 0.2245420209 | 0.2348218779 | 0.01027985698 |
| R-B35-S-T2 | 0.1291512915 | 0.1342432954 | 0.1354492348 | 0.001205939385 |
| R-X35-S-T2 | 0.1931361142 | 0.1945218656 | 0.1947597626 | 0.0002378970184 |
| K-35-U | 0.218088779 | 0.218088779 | 0.2260440515 | 0.007955272454 |
| R-X20-S-T1 | 0.3775575303 | 0.3775575303 | 0.377563941 | 6.410663424e-06 |

| Role | Thresholds | Budget adds q>0 | Forced-only ell>0 |
|---|---|---|---|
| K-20-S | 137 | 30 | 27 |
| R-B35-S-T2 | 96 | 30 | 0 |
| R-X35-S-T2 | 66 | 15 | 0 |
| K-35-U | 130 | 56 | 64 |
| R-X20-S-T1 | 44 | 0 | 17 |

RB35-T2 and RX35-T2 have no forced-high stations at any threshold. Their positive lower counts and bound increments require the inventory lower budget. RX20 has q=0 at every threshold: its small gain instead uses forced-high support information. K20 and K35 combine these sources without an additive allocation of objective gains. Detailed G, H_sum, J, tau, legal U, coefficient distributions, construction costs, row counts, residuals and identity hashes remain in reports/LP.json and sealed position records. These are numerical continuous optima, not Native MIP root bounds or complete performance samples.

Two additional finite RX20 LP confirmations use FeasibilityTol and OptimalityTol 1e-9, explicit Seed0 and one thread. The increment remains 6.41066342449e-06; both objectives match the primary observations. This is numerical confirmation of a small effect, with unchanged complete-algorithm parameters and original result identities.

The K20 no-stock BASE/TC/TC+TC2 control confirms complementarity with the shared-stock product rows on the same domain. The additional RB35-T2 no-stock TC+TC2 position remains a labelled auxiliary, not a complete no-stock ablation panel. The return-product alternative is screened offline only: all four old stock points admit W extensions within the recorded numerical residual tolerance. K35 old TC+stock first violates a linear vehicle-return upper bound, so it cannot establish a product benefit.

The five newly optimized TC2+stock vectors receive a separate zero-Optimize projection check with an explicit 1e-7 numerical residual tolerance. Return bounds are checked before the W interval-sum condition; passing this numerical screen does not assert exact rational feasibility of the saved binary64 vector. A saved-point obstruction is distinct from an optimized objective gain; absence of an obstruction does not prove global redundancy.

| Role | First obstruction | Bg-J |
|---|---|---|
| K-20-S | none at this point | 1.110223025e-16 |
| R-B35-S-T2 | none at this point | 5.068861997e-15 |
| R-X35-S-T2 | none at this point | -1.734723476e-17 |
| K-35-U | none at this point | -4.440892099e-16 |
| R-X20-S-T1 | none at this point | 7.112366252e-17 |

## 3. Complete uniform algorithms

The initial five-role candidate uses STK+TC+TC2 uniformly in outer LP and native target/terminal. Independent old STK+TC controls start with K20 and RB35-T2; result-selected additional comparisons and the final uniform candidate choice are stated below. BASE and STK reuse the accepted matched R137/R138 evidence, retaining primary V1 and accepted V2 bridge identities. Every new method starts independently and pays complete own H, construction, validation, search and online proof; no cross-method or cross-Seed solution, bound, Start or tree is injected.

All primary solves use explicit Gurobi Seed0, one thread, affinity mask 4, the same verified 13.0.2 DLL, and separately fixed H seed 20260626. Resource roles retain rho=1 and original binary64 lambda=1/Omega. Physical T and experiment cap retain their frozen meanings; they are not elapsed-time algorithm switches. The two cap90 qualifications are excluded from performance counts.

| Role | Method | Verified U | Supported L | T_cert (s) |
|---|---|---|---|---|
| K-15-S | base | 0.5922648823 | 0.5922648792 | 112.7693031 |
| K-15-S | both | 0.5922648823 | 0.5922648823 | 33.81822655 |
| K-15-S | TC_STOCK | 0.5922648823 | 0.5922648799 | 45.24253812 |
| K-15-S | TC2_STOCK | 0.5922648823 | 0.5922648823 | 36.1332107 |
| K-20-S | base | 0.7168065463 | 0.7053557935 | open |
| K-20-S | both | 0.7168065463 | 0.7168065463 | 101.6353849 |
| K-20-S | TC_STOCK | 0.7168065463 | 0.716806546 | 135.6968128 |
| K-20-S | TC2_STOCK | 0.7168065463 | 0.7168065463 | 115.0196233 |
| K-35-U | base | 0.6928543586 | 0.5657656815 | open |
| K-35-U | both | 0.6695955692 | 0.556776898 | open |
| K-35-U | TC_STOCK | 0.650438712 | 0.5682885263 | open |
| K-35-U | TC2_STOCK | 0.7021486134 | 0.5419703766 | open |
| R-B35-S-T2 | base | 0.3446426256 | 0.2189859496 | open |
| R-B35-S-T2 | both | 0.4012002178 | 0.2291815997 | open |
| R-B35-S-T2 | TC_STOCK | 0.3190804927 | 0.2339272621 | open |
| R-B35-S-T2 | TC2_STOCK | 0.3242757178 | 0.2299042085 | open |
| R-X35-S-T2 | base | 0.4032719989 | 0.2108870199 | open |
| R-X35-S-T2 | both | 0.4098554822 | 0.2149801627 | open |
| R-X35-S-T2 | TC_STOCK | 0.3702071037 | 0.2050709555 | open |
| R-X35-S-T2 | TC2_STOCK | 0.3666359874 | 0.2116991961 | open |
| R-X20-S-T1 | base | 0.6453250304 | 0.6453250304 | 20.5064616 |
| R-X20-S-T1 | both | 0.6453250304 | 0.6453250304 | 15.34047923 |
| R-X20-S-T1 | TC_STOCK | 0.6453250304 | 0.6453250304 | 7.512173176 |
| R-B35-S-T1 | base | 0.5915176348 | 0.4559038913 | open |
| R-B35-S-T1 | both | 0.569975107 | 0.5008429884 | open |
| R-B35-S-T1 | TC_STOCK | 0.5776346624 | 0.4989321494 | open |
| R-X35-S-T1 | base | 0.5921904489 | 0.4633579972 | open |
| R-X35-S-T1 | both | 0.5920260899 | 0.4910233047 | open |
| R-X35-S-T1 | TC_STOCK | 0.5841151465 | 0.492793738 | open |

Open T_cert is null and displayed as open. No cap is imputed as convergence time or exact speedup. Signed/relative gap and T_produce/T_cert/T_verify/T_total, Work, nodes and all actual call controls remain in reports/. Native returned ObjBoundC and externally merged final L are separate columns. The table contains only actual entered complete comparisons and matching references; missing old-TC positions are not inferred.

TC2+stock certifies K15 and K20 in 36.133 and 115.020 seconds. Stock certifies them in 33.818 and 101.635 seconds; old TC+stock takes 45.243 and 135.697 seconds. TC2 preserves the established proof benefit but adds no new certificate in its five-role panel. K35 is a material adverse result: TC2 U/L .7021486134/.5419703766 is worse than BASE, stock and old TC+stock. RB35-T2 improves over BASE/stock under TC2, but old TC+stock is better at both endpoints, so this repair is not a TC2-exclusive benefit. RX35-T2 under TC2 improves U relative to both references and L relative to BASE, while remaining below the stock L.

The selected uniform old TC+stock method completes all eight configurations on six base inputs. It certifies three, matching stock's three versus BASE's two. K35 and RB35-T2 improve both U and L over both references in Seed0; RX35-T1 also improves both over stock by smaller amounts. RB35-T1 is slightly worse than stock at both endpoints. RX35-T2 improves U but weakens L against both references, and TC2 is better than old TC at both endpoints there. K15/K20 retain proof but are substantively slower than stock under the inherited max(10 seconds,10 percent) comparison rule. RX20 takes 7.512 versus stock 15.340 seconds; the difference is below the inherited absolute 10-second threshold and does not alone drive selection.

The one decision-selected RB35-T2 Seed1 changes the priority assessment. Old TC+stock returns U/L .3730513800/.2308383524 versus the accepted stock Seed1 .3222448417/.2311394491: U worsens by .0508065383 and L by .0003010967. Relative to BASE Seed1 .3595536804/.2181462246 it has worse U and stronger L. The large Seed0 repair of stock is not robust in this confirmation. The reference retains its original V2 source/PE and clocks; this is not a same-PE causal intervention. No average or favorable role erases these adverse observations.

| Role | Method | Seed | Signed U-L | Relative gap |
|---|---|---|---|---|
| K-15-S | TC2_STOCK | 0 | 7.105427358e-15 | 1.199704317e-14 |
| K-15-S | TC_STOCK | 0 | 2.393768073e-09 | 4.041718738e-09 |
| K-20-S | TC2_STOCK | 0 | 2.775557562e-15 | 3.872115253e-15 |
| K-20-S | TC_STOCK | 0 | 2.366037366e-10 | 3.300803234e-10 |
| K-35-U | TC2_STOCK | 0 | 0.1601782368 | 0.2281258323 |
| K-35-U | TC_STOCK | 0 | 0.08215018563 | 0.1262996561 |
| R-B35-S-T2 | TC2_STOCK | 0 | 0.09437150925 | 0.2910224358 |
| R-B35-S-T2 | TC_STOCK | 0 | 0.08515323055 | 0.2668706878 |
| R-B35-S-T2 | TC_STOCK | 1 | 0.1422130276 | 0.3812156588 |
| R-X35-S-T2 | TC2_STOCK | 0 | 0.1549367913 | 0.4225902437 |
| R-X35-S-T2 | TC_STOCK | 0 | 0.1651361482 | 0.4460642341 |
| R-X20-S-T1 | TC_STOCK | 0 | 4.440892099e-16 | 6.881636213e-16 |
| R-B35-S-T1 | TC_STOCK | 0 | 0.07870251302 | 0.1362496369 |
| R-X35-S-T1 | TC_STOCK | 0 | 0.0913214085 | 0.1563414492 |

| Role | Method | Seed | T_produce | T_verify | T_total |
|---|---|---|---|---|---|
| K-15-S | TC2_STOCK | 0 | 36.1332107 | 2.7067648 | 38.8399755 |
| K-15-S | TC_STOCK | 0 | 45.24253812 | 3.1091034 | 48.35164152 |
| K-20-S | TC2_STOCK | 0 | 115.0196233 | 5.3283726 | 120.3479959 |
| K-20-S | TC_STOCK | 0 | 135.6968128 | 6.7370574 | 142.4338702 |
| K-35-U | TC2_STOCK | 0 | 2371.170893 | 8.7755562 | 2379.946449 |
| K-35-U | TC_STOCK | 0 | 2371.118721 | 7.465527 | 2378.584248 |
| R-B35-S-T2 | TC2_STOCK | 0 | 2371.221794 | 8.2985554 | 2379.520349 |
| R-B35-S-T2 | TC_STOCK | 0 | 2371.078087 | 7.7585257 | 2378.836612 |
| R-B35-S-T2 | TC_STOCK | 1 | 2371.19577 | 10.2230051 | 2381.418775 |
| R-X35-S-T2 | TC2_STOCK | 0 | 2371.093551 | 6.8236145 | 2377.917166 |
| R-X35-S-T2 | TC_STOCK | 0 | 2371.085589 | 8.6783004 | 2379.763889 |
| R-X20-S-T1 | TC_STOCK | 0 | 7.512173176 | 1.8722417 | 9.384414876 |
| R-B35-S-T1 | TC_STOCK | 0 | 2371.150148 | 8.3265926 | 2379.476741 |
| R-X35-S-T1 | TC_STOCK | 0 | 2371.171639 | 6.776441 | 2377.94808 |

These two compact tables cover every new formal complete position. Qualifications are separate. Matched old references retain their full costs and gaps in reports/reused_arms.csv. Physical T, actual binary64 objective weight and experiment cap are independent fields in reports/new_arms.csv.

### 3.1 Observable mechanism

The actual canonical writer puts stock and the declared counts uniformly in outer LP, native target and terminal. TC2 improves all five matched continuous LP objectives over old TC+stock, including K35 and the precision-confirmed small RX20 increment. This does not predict capped complete outcomes. At K20 both old TC and TC2 take native-target then exact-close, unlike inherited stock's immediate exact-close; that action change is not unique to TC2. The target lifts the qualified parent above the cached left-child bound before exact-close.

K35 makes the distinction particularly clear. Old TC has parent and left-child LP bounds both .2180887790 and selects exact-close, despite no root objective increment over stock. TC2 raises the parent to .2260440515 and left child to .2276013978, triggers native-target, then raises the parent to .2660215686 and selects exact-close. Its stronger early bounds coexist with worse capped U/L. These are observable whole-method control/search changes with identical initial H; they do not isolate additive causal runtime per row or imply a general rule that stronger rows hurt search. Native returned ObjBoundC and externally merged final L stay separate. All 137 saved witness records in five explicitly selected new trajectories, including 132 MIPSOL records, are physically replayed; these are not independent experiments or unique discovery clocks. The old accepted 184 records are not newly replayed.

| Role | Method | First AM action | LP / target / terminal |
|---|---|---|---|
| K-15-S | TC2_STOCK | native-target | 3 / 1 / 1 |
| K-15-S | TC_STOCK | native-target | 3 / 1 / 1 |
| K-20-S | TC2_STOCK | native-target | 3 / 1 / 1 |
| K-20-S | TC_STOCK | native-target | 3 / 1 / 1 |
| K-35-U | TC2_STOCK | native-target | 3 / 1 / 1 |
| K-35-U | TC_STOCK | exact-close | 3 / 0 / 1 |
| R-B35-S-T2 | TC2_STOCK | native-target | 3 / 1 / 1 |
| R-B35-S-T2 | TC_STOCK | native-target | 3 / 1 / 1 |
| R-X35-S-T2 | TC2_STOCK | native-target | 3 / 1 / 1 |
| R-X35-S-T2 | TC_STOCK | native-target | 3 / 1 / 1 |
| R-X20-S-T1 | TC_STOCK | native-target | 3 / 1 / 1 |
| R-B35-S-T1 | TC_STOCK | native-target | 3 / 1 / 1 |
| R-X35-S-T1 | TC_STOCK | native-target | 3 / 1 / 1 |

AM decisions use parent-relative child gains. A stronger parent bound need not increase this gain. Actual calls, parent bounds and action sequences support mechanism interpretation; they do not allocate additive causal runtime to the two new rows. Saved native witness vectors are physically replayed. Rounded native-log timestamps and controller publication after return do not establish exact discovery clocks.

### 3.2 Conditional extensions and limited Seed1

After the initial five TC2 roles, the required K20/RB35-T2 old-TC controls and the critical K35 attribution showed that old TC had stronger complete value on two hard roles. The last K15/RX35-T2 old-TC controls completed the same five-role comparison; their nominal comparison caps total 9000 seconds. Independent review then allocated the planned 6000-second remaining-three-role allowance only to uniform TC+stock. TC2 stops at five complete roles; only old TC reaches eight. No instance-specific algorithm rule or asymmetric placement is introduced.

One RB35-T2 Seed1 is justified by a real decision uncertainty: stock Seed1 was already near old-TC Seed0. It reuses matched accepted BASE1/STOCK1, retaining their input, physical T, cap, exact lambda, Seed, threads, affinity, H, different measured source/PE and original costs. No new stock solve, second Seed1 role, or TC2 repeat is run. The unfavorable confirmation supports retaining research tools and stopping full promotion. Return-product exploration closes after the old eight-point and new five-point offline screens; all five new TC2 optima pass the return-bound and W-projection screen within the recorded 1e-7 numerical residual tolerance. No product LP or third complete-method line is opened.

| Role | Method | Seed | Verified U | Supported L | T_cert (s) |
|---|---|---|---|---|---|
| R-B35-S-T2 | BASE | 1 | 0.3595536804 | 0.2181462246 | open |
| R-B35-S-T2 | STOCK | 1 | 0.3222448417 | 0.2311394491 | open |
| R-B35-S-T2 | TC_STOCK | 1 | 0.37305138 | 0.2308383524 | open |

The two Seed1 references retain their accepted original BASE/V2 STOCK source, PE and complete clocks; the fresh TC_STOCK method uses the current PE. This is a matched complete-method comparison, not a same-PE intervention. Original reference and new production/verification/total clocks remain in reports/seed1_arms.csv. No favorable confirmation replaces an adverse Seed0 observation.

## 4. Research decision and remaining question

RESEARCH ONLY; STOP FULL-ALGORITHM PROMOTION. TC2 is a qualified inventory-driven discrete strengthening with strict block separation even under exact common/return products and real optimized LP gains beyond old TC+stock. It is retained as a default-off research component, with no claim of a full BRP cutoff strictness theorem or new integer gap closure. Its important K35 regression rejects promotion as a uniform complete candidate. The selected old TC+stock combination is also retained research-only: its useful Seed0 hard-role outcomes are qualified by slower proofs, horizon tradeoffs and the adverse critical Seed1. Neither configuration is recommended for stable-default replacement or further full benchmarking without new structural evidence. The R137 GI-TBC stable entry and earlier R138/R139 entries stay unchanged. The independent Round140 research entry defaults to the selected tested old-TC mode and explicitly exposes TC2 for reproduction; this does not promote the stable default.

The most useful next question is whether explicitly enforcing each vehicle's return upper bound can yield a genuine optimized increment beyond TC+stock at the K35 domain whose retained old-TC optimum violates that bound. Begin with a bounded same-domain reoptimization separating linear return bounds from product rows, and proceed to complete comparison only after an actual objective gain. Positive return load or saved-point separation alone does not establish that gain.

## 5. Cost and reproducibility

New charged experiment computation is 21831.718967 seconds (6.064366 hours), within 43200 seconds. All qualification and failed native attempts are included. Complete outer methods are charged once; nested H/LP/MIP/Work are not added twice. Old references retain their original clocks without fictitious new charges. Builds, pure offline checks, postverification, documents and public I/O are separately measured where explicit, without invented precision for interactive reading or editing.

The pre-Optimize Path-type LP failure and narrow retry are retained. The singleton empty-row defect was fixed before qualification; the earlier build supplies no performance sample. An early pure postreader ordering failure had zero Optimize/Native loads and was corrected by explicit sealed scope. Final all-group checks pass; no native observation was rerun or replaced. Actual Native coefficient/RHS/type reads cover root, child, cutoff refresh and every used LP/target/terminal artifact. Independent preflight, admission, selection and integration records remain distinct.

The actual source/PE/DLL, input, configuration, controls and helper identities are bound by candidate_manifest.json and frozen batches. Local physical/scientific/semantic checks and once-only public archive/member readability are different claims. No public check runs Optimize, compilation or a commercial Native load. Stable GI-TBC remains independently usable. The final continuation record gives actual Draft PR, base/head, fixed science, public read and bounded cleanup status; it does not infer completed delivery from a scientific decision.
