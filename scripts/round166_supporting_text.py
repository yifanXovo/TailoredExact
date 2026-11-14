"""Maintain model appendix, mathematical companion and offline decision account."""
from round166_common import *
P=ROOT/'results/unified_exact_round137'
APPENDIX=r'''## A.9 Compact joint-state alternative C166

This separately named candidate changes only the inventory representation of B. Let \(M_i=\sum_k(p_{ki}+d_{ki})\), \(V_i=\sum_kz_{ki}\), and fix the legal integer interval \(\mathcal Y_i=\{l_i,\ldots,u_i\}\) and \(0\le\alpha\le\beta\le1\). Put \(m_i(y)=|b_i-y|\), \(v_i(y)=\mathbf1\{y\ne b_i\}\). The shared object is

\[
\mathcal H_i=\operatorname{conv}\{(y,m_i(y),v_i(y),g,gy):y\in\mathcal Y_i,\ g\in[\alpha,\beta]\}.
\tag{AC1}
\]

The continuous relaxation of (A15)-(A16) projects to (AC1). Inventory balance recovers aggregate pickup/drop as \((M_i+b_i-Y_i)/2\) and \((M_i-b_i+Y_i)/2\). This assertion adds neither a linked-direction equation nor a vehicle-state product to B.

**Proposition A9 (legal-piece compression).** Define
\(\mathcal K_i=\{l_i,u_i\}\cup(\{b_i-1,b_i,b_i+1\}\cap\mathcal Y_i)\).
Then (AC1) is unchanged when its stock support is restricted to \(\mathcal K_i\), which contains at most five values.

*Proof.* Partition the legal integers into their nonempty donor piece below b, initial singleton and receiver piece above b. On each piece, \((y,m_i(y),v_i(y))\) is affine. If a legal interior integer y lies between the legal endpoints a<c of its piece, choose \(\theta=(c-y)/(c-a)\). At the same g,
\((y,m_i(y),v_i(y),g,gy)\) equals the \(\theta,1-\theta\) combination of the endpoint graph points. Singletons require no interpolation. All endpoints are in \(\mathcal K_i\), proving one inclusion for all convex mixtures. Every retained endpoint is legal, proving the reverse. ∎

Use continuous variables \(t_{ia},q_{ia}\) for a in \(\mathcal K_i\):

\[
\begin{aligned}
&\sum_a t_{ia}=1,\quad Y_i=\sum_a a t_{ia},\quad
M_i=\sum_a|b_i-a|t_{ia},\\
&V_i=\sum_a\mathbf1\{a\ne b_i\}t_{ia},\quad
\sum_a q_{ia}=g,\quad Z_i=\sum_a a q_{ia},\\
&t_{ia}\ge0,\qquad\alpha t_{ia}\le q_{ia}\le\beta t_{ia}.
\end{aligned}
\tag{AC2}
\]

If \(t_{ia}>0\), set \(g_a=q_{ia}/t_{ia}\in[\alpha,\beta]\); zero t forces zero q. Hence (AC2) is a convex combination of legal graph points. Conversely collect any such combination into t/q. This proves its exact continuous projection without imposing adjacency or SOS2 on hull mixtures.

Continuous (AC2) plus integer Y does not make the product exact. For b=0, domain \(\{1,2,3\}\), g=1/4, supports \(\{1,3\}\), weights 1/2 each and q=(0,1/4), it gives Y=2,Z=3/4 instead of gY=1/2. Making t binary excludes that legitimate interior stock. C166 therefore also keeps the independent absolute-Y binary layer (A14), with interval products

\[
\begin{aligned}
&Y_i=\sum_h2^h b_{ih}^{\rm bit},\quad Z_i=\sum_h2^h w_{ih},\\
&\alpha b_{ih}^{\rm bit}\le w_{ih}\le\beta b_{ih}^{\rm bit},\\
&g-\beta(1-b_{ih}^{\rm bit})\le w_{ih}\le
g-\alpha(1-b_{ih}^{\rm bit}),\quad b_{ih}^{\rm bit}\in\{0,1\}.
\end{aligned}
\tag{AC3}
\]

The implementation retains the three additional original [0,1] product rows in (A14) and all four factory interval rows in (AC3). It does not skip the bit family as VD-P does.

**Proposition A10 (integer correspondence and common LP projection).** Under B's original unique nonzero one-way service, balance and integer inventory constraints, replacing (A15)-(A16) by (AC2)-(AC3) preserves the integer physical projection and original objective. Their raw LP projections in \((Y_i,M_i,V_i,g,Z_i)\) are equal. Global equality holds when every remaining row and the objective uses deleted state variables only through that common interface.

*Proof.* Extend an old integer physical point by the absolute bits of its legal stock, exact w=g*bit, and the same-g legal-piece interpolation of Proposition A9. It keeps all physical columns and the original g/e objective. Conversely (AC3) gives exact Z=gY; retained physical constraints and Lemma A1 give the original integer service. The old extension s_Y=1,q_Y=g reproduces that point. For the LP claim, the relaxed bit block is convex and contains an extension of every true legal (Y,g,gY) graph point, so its projection contains the projection of (AC1). Its auxiliary columns and those of (AC2) are disjoint, sharing only (Y,g,Z). Every point of (AC1) therefore still extends to their intersection. Equal projected local sets, intersected with the same outside system through their shared coordinates, give equal global projection, station by station. ∎

For actual B, r=Y/D and e retain (A10), H/S/Gini and physical/resource rows use common or route columns, and the objective uses G and weighted e. The computed state-penalty/ratio reconstructions are emitted only by VD-J, which is not active. Thus no target kink is missing from (AC2). AP, exact state penalties, threshold counts/CDF, theta, linked direction, RN and historical state-dependent resource/decomposition combinations are not silently extended; the research entry rejects unsupported combinations. Original domain-infeasibility flags and explicit contradiction rows remain authoritative even if storage bounds reset.

Singleton and one-sided domains, b outside a tightened domain, b=0/C and fixed/zero g are covered by the same construction. Holes must remain separately enforced: on legal \(\{1,3\}\), integer Y=2 would otherwise be added by a breakpoint-plus-bit model. An additional exact state penalty \(|Y-2|\) with b=5 and domain [0,10] cannot use only \(\{0,4,5,6,10\}\), because its legitimate zero at Y=2 is absent. Additional state functions require their own common affine-piece endpoints.

More generally, if an integer state is externally visible only through y,gy and a finite collection of functions affine on common legal integer pieces, retaining all legal piece endpoints preserves that local continuous graph hull. This is a standard disjunctive consequence, specialized here to the joint service interface [@vielma2018embedding; @huchetteVielma2023]. When both sides of b have length at least two, the four V=1 endpoints are vertices of their quadrilateral and b is the unique V=0 graph point. Five supports are then necessary *within legal graph-point generator representations*, not among arbitrary extended formulations.

Let \(N_i=u_i-l_i+1\), \(k_i=|\mathcal K_i|\), \(d_i=\max\{1,\lceil\log_2(C_i+1)\rceil\}\). Excluding common physical columns/rows, B uses 2N columns, N binaries and 2N+6 rows. The implemented C166 uses 2k+2d columns, d binaries and 2k+8+7d rows. The continuous support is bounded by five; total exact encoding still depends logarithmically on capacity. Nonzero formulas and actual counts are retained with the implementation study. These are raw-model projection statements, not ideality of the combined extension, route/objective hull claims, or predictions of native cuts and branch trajectories. Fewer columns or binaries need not reduce complete cost.

## A.10 Continuous decision bounds from existing physical fleets

For a fixed physical domain and normalized weight vector, \(v(\rho)=\min_x\{G(x)+\rho P(x)/\Omega\}\) is concave: for \(0\le\theta\le1\), every feasible x has
\(G(x)+(\theta\rho_a+(1-\theta)\rho_b)p(x)=\theta F_{\rho_a}(x)+(1-\theta)F_{\rho_b}(x)\ge\theta v(\rho_a)+(1-\theta)v(\rho_b)\); minimize over x. Replacing endpoint values by qualified global lower bounds preserves the lower chord on its closed endpoint interval. Taking the maximum of applicable chords is safe. The minimum of the verified archive's objective lines is an upper bound. These facts require no assertion that the sampled incumbents are optimal or Pareto efficient.

All feasible-line intersections, overlapping lower-chord intersections and chord interval endpoints partition the covered parameter range into finitely many pieces on which both envelope expressions are affine. Their difference therefore attains a maximum at a partition endpoint (or everywhere on a constant piece). Checking all such points proves the stated continuous-interval regret bounds; a grid would not suffice. Same-coordinate lowers combine by maximum, never by a zero-length chord. Outside a chord's endpoint interval no extrapolation is granted.

The application reconstructs complete fleets, verifies fixed physical/normalized-weight identity and uses actual loaded lambda/omega values. Rational G/P/coordinate arithmetic supplements the inherited numerical lower qualifications; it does not turn native solves into rational proofs. Original lowers are conservatively reduced by 1e-7, and exact feasible objectives receive a 1e-12 upward guard. No source crossing is clipped. The original run objectives, statuses and clocks remain unchanged. Likewise, nested physical time domains give the two-sided difference interval in Table 5; this is an objective-value decision bound, not a monetary resource price.

\clearpage

'''
def write_texts():
    app=(P/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    assert '## A.9 Compact joint-state alternative C166' not in app
    app=app.replace('# Appendix B. Executable method specification',APPENDIX+'# Appendix B. Executable method specification',1)
    (P/'model_and_algorithm_appendices.md').write_text(app,encoding='utf-8')
    math=(P/'mathematical_analysis.md').read_text(encoding='utf-8-sig')
    math=math.replace('../unified_exact_round165/source_manifest.json','../unified_exact_round166/source_manifest.json',1)
    math+=r'''

## Compact shared-state graph and embedding

The current representation study characterizes the joint graph of integer inventory,
absolute movement, nonzero visits and a common Gini product. Legal donor/initial/
receiver pieces give at most five continuous perspective supports. A separate
absolute-Y binary product layer keeps integer Z=gY exact; integer Y plus continuous
supports alone fails, while binary supports remove legal internal stocks. Since
the relaxed bit block contains the true product graph hull and shares no auxiliaries
with the joint support block, the common raw LP projection is unchanged. Current
B's unchanged e epigraph and outside-row interface make the full embedding valid.
Appendix A.9 proves both directions, scope and scale. Holed domains and additional
exact state functions require additional restrictions/supports. This result applies
standard disjunction/product tools; it is not an ideality or route-hull claim.

The C++ implementation uses a distinct default-off mode and complete Start mapping.
Finite diagnostics compare all six fixed roots, two child scopes, 64 local LPs and
hand-enumerable native boundary examples. The local/full common LP result does not
predict native branch trajectories. Complete paired costs remain a separate test,
with B and C166 independently paying H and receiving no archive information.

## Certified parameter and physical-resource decisions

For a fixed physical domain and normalized omega vector, v(rho)=min_x(G+rho*p)
is concave. Every reconstructed physical fleet gives an affine upper line; chords
between qualified global lower anchors give lower bounds only inside their anchor
intervals. The maximum applicable chord and minimum archive line form a quality
band. Rational evaluation at every true line/chord intersection and endpoint yields
continuous interval guarantees, without new optimization or a grid. The source
coordinate is actual loaded lambda times the exact loaded weight sum, not its
rounded display. Appendix A.10 gives the argument and numerical safety policy.

The four whole-range archive regret upper bounds are .002356282, .000000100002,
.015594269 and .136115162 for K15, UC-B20, resource B20-T1 and X35-T2 respectively
(upward rounded). The first exhibits three supported component choices, the second
has one stable component line, and the last remains substantially unproved despite
one known fleet supporting its entire archive envelope. The higher-weight X35 fleet
is feasible at the original unit weight with objective .3365058165, improving the
old incumbent by .06676618239 offline; it does not backfill production U or timing.

All four T-pairs have strict optimal-objective improvement under the existing source
qualifications. The new two-sided intervals quantify remaining magnitude uncertainty:
the small pairs have widths about 2.13e-7/2.02e-7 after safety guards, while the open
B35/X35 widths remain .261270620/.321217631. All four displayed larger-horizon fleets
have better G/P and more pickup, but B35 returns more stock (2 to3) while X35 returns
less (1 to0). Route utilization describes these witnesses and does not prove which
time constraint binds an unknown optimum. Full fleets, every owner, exact intersections
and both original/safe resource endpoints are in the
[decision record](../unified_exact_round166/decision_analysis.md).
'''
    (P/'mathematical_analysis.md').write_text(math,encoding='utf-8')
    print('Maintained Appendix A.9/A.10 and mathematical companion.')
if __name__=='__main__':write_texts()
