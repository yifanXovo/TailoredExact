"""Direct revision of the one maintained paper; no legacy prose generator."""
from round166_common import *
P=ROOT/'results/unified_exact_round137'
def replace(text,old,new):
    assert text.count(old)==1,(old[:80],text.count(old));return text.replace(old,new)
def edit():
    body=(P/'paper_body.md').read_text(encoding='utf-8-sig')
    start=body.index('The research question is how finite inventory information')
    end=body.index('### 1.1 Relation to previous work')
    body=body[:start]+r'''The research question is how a common inventory representation can connect allocation and routing, support a complete exact method, and yield decisions whose quality can be bounded. Three connected contributions address it. First, a shared stock state represents the objective product, absolute movement and nonzero visits. Under the inherited unique one-way service rules, integer stock implies integer service quantities. We further characterize the joint local graph: at most five legal stock supports preserve its continuous convex hull, while a separate absolute-stock binary-product layer preserves integer exactness. The resulting common LP projection survives embedding only when all other state uses pass through the declared interface. This identifies both a compact representation and its precise boundary.

Second, GI-TBC combines inventory/service connections and physical valid inequalities with an own feasible startup and complete true-Gini interval control. Objective-preserving physical extensions, cutoff complements and complete region coverage establish correctness. The implementation supplies the full method, including exact continuation at depth/width guards. Custom valid rows are static; Gurobi performs branch-and-cut inside each canonical model. P, own-start PS, strengthened root-only control, complete B and the separate proof extension answer different formulation, startup and architecture questions. The compact representation is evaluated as the separately named C166 candidate; it does not change B's definition.

Third, computational evidence and certified decision analysis use both feasible fleets and qualified problem bounds. The complete package improves finite certificate counts over the specified compact controls, with adverse endpoints and open cases retained. An offline archive of fully reconstructed physical fleets yields feasible upper envelopes and concavity-based lower bands over continuous objective-weight intervals. Controlled route-horizon pairs yield two-sided bounds on the improvement in the optimal objective, including pairs where neither optimum is certified. These decisions concern inventory-to-target ratio dispersion and target deviation. They do not imply demographic fairness, monetary benefit, a complete Pareto frontier or an independent speed gain from the outer controller.

'''+body[end:]
    anchor='Neither binary expansion, value disjunction nor spatial partitioning is claimed as new.'
    body=replace(body,anchor,'Embedding and piecewise-linear formulations provide established endpoint, encoding and convexification tools [@vielma2018embedding; @huchetteVielma2023]. Our compact result applies these tools to the jointly visible movement, visit and product functions, including their discrete service jump, and establishes the interface needed to embed the replacement. Neither binary expansion, finite disjunction, endpoint convexification nor spatial partitioning is claimed as new.')
    compact=r'''#### 3.1.1 A compact shared-state representation

On a legal contiguous stock domain \(\mathcal Y_i=\{l_i,\ldots,u_i\}\), define \(m_i(y)=|b_i-y|\), \(v_i(y)=\mathbf1\{y\ne b_i\}\), and the common local object

\[
\mathcal H_i=\operatorname{conv}\{(y,m_i(y),v_i(y),g,gy):y\in\mathcal Y_i,\ g\in[\alpha,\beta]\}.
\]

The relevant physical coordinates are inventory, aggregate movement, aggregate visits, \(g\) and \(Z_i\). Balance linearly recovers aggregate pickup and delivery from inventory and movement. The relaxed VD-P block and A/B links represent this joint object; independently convexifying service and the product can instead use inconsistent inventory mixtures.

**Compact joint-state proposition.** For \(0\le\alpha\le\beta\le1\), let

\[
\mathcal K_i=\{l_i,u_i\}\cup\bigl(\{b_i-1,b_i,b_i+1\}\cap\mathcal Y_i\bigr).
\]

Replacing \(\mathcal Y_i\) by these at most five legal supports preserves \(\mathcal H_i\). Continuous perspective weights on those supports, combined with an independent absolute-\(Y_i\) binary-product layer, preserve B's integer physical projection, original objective and common raw LP projection, provided every other deleted-state use passes through the common interface.

**Proof sketch.** On the legal donor, initial singleton and receiver pieces, all three functions \(y,m_i(y),v_i(y)\) are affine. An interior integer stock is interpolated between its piece's legal endpoints at the same \(g\), preserving \(gy\) as well. The converse uses the legality of every retained support. The bit layer makes \(Z_i=gY_i\) exact at integer stocks. Its relaxed projection contains every true stock/product graph point, hence their convex hull; its disjoint auxiliary variables therefore do not change the breakpoint block's common LP projection. Intersecting with unchanged outside constraints preserves this equality under the stated interface condition. Appendix A.9 supplies the construction, both directions, sizes and failure cases. \(\square\)

Continuous breakpoint weights and integer \(Y_i\) alone do not enforce the product, and binary breakpoint weights would delete legal interior stocks. B keeps its original \(e_i\) epigraph, so target deviation is not an additional shared-state function here. Exact state penalties, threshold counts, vehicle-state assignment or holed stock domains need additional supports or restrictions. The candidate C166 applies only this representation change, with the full B lifecycle and own startup. Equal raw LP projections do not imply identical presolve cuts, branch decisions or complete costs.

'''
    body=replace(body,'### 3.2 Ordered supply and support/handling information',compact+'### 3.2 Ordered supply and support/handling information')
    # Replace the old one-sided table by the new two-sided resource decision.
    start=body.index('**Table 5. Strict resource-value improvements')
    end=body.index('The supplement reports operations',start)
    body=body[:start]+r'''For fixed physical data and objective, let \([L_j,U_j]\) contain \(F^*(T_j)\), with \(T_2>T_1\). Feasible-set inclusion gives the complete improvement interval

\[
\max\{0,L_1-U_2\}\le F^*(T_1)-F^*(T_2)\le U_1-L_2.
\]

**Table 5. Two-sided resource-value improvement intervals.** The bounds use complete physical fleets and qualified global lower sources. Displayed interval endpoints are rounded outward after reducing each original lower by \(10^{-7}\) and adding \(10^{-12}\) to exactly recomputed feasible objectives; full original endpoints and arithmetic are retained in the decision data.

| Base | T1 / T2 (s) | Improvement interval | Interval width | B state T1 / T2 |
|---|---|---|---|---|
| R-B20-S | 3300 / 5100 | [0.2822618761, 0.2822620892] | 0.0000002130 | C / C |
| R-X20-S | 4800 / 7200 | [0.2105292995, 0.2105295021] | 0.0000002025 | C / C |
| R-B35-S | 4800 / 7200 | [0.1112611656, 0.3725317852] | 0.2612706196 | open / open |
| R-X35-S | 4200 / 6300 | [0.0600858983, 0.3813035291] | 0.3212176307 | open / open |

The two 35-station pairs prove a strictly positive optimal-objective improvement despite both runs remaining open, but leave substantial uncertainty about its magnitude. The two smaller pairs localize the improvement much more closely. These intervals measure the change in the specified objective, not monetary savings or a general marginal price of vehicle time. No source run acquires another run's certificate or clock.

'''+body[end:]
    # Preserve all sampled per-method results, then replace repeated weight prose.
    start=body.index('Certification depends on the weight even within')
    end=body.index('### 5.4 Limited preselected second Seed',start)
    weight=r'''The sampled comparisons retain different search outcomes: B certifies R-B20-S-T1 at \(\rho=1,2\), while all methods remain open at \(\rho=.5\); all three methods remain open at every tested R-X35-S-T2 weight. The table reports each original run's own U/L. Cross-weight information is used only for the following offline analysis.

We reconstruct every available complete fleet from the two configurations above and from the earlier K-15-S and UC-B20-B weight study: 32 run records, with all method/Seed owners retained. Routes, nonzero one-way operations, stock balance, empty departure, load prefixes, loaded returns and unloading time are independently checked. Each family has identical physical data and normalized station weights. True Gini and weighted penalty are recomputed from the full inventories and actual loaded weights; rounded table components are not used to manufacture fleets or certificates.

For a fixed family, put \(p(x)=P(x)/\Omega\) and

\[
v(\rho)=\min_{x\in\mathcal F}\{G(x)+\rho p(x)\},\qquad
U_{\mathcal A}(\rho)=\min_{x\in\mathcal A}\{G(x)+\rho p(x)\}.
\]

The archive \(\mathcal A\) contains only verified physical fleets. Thus \(U_{\mathcal A}\) is an upper bound, not the algorithm's result at unrun weights. The value \(v\) is concave as an infimum of affine functions. For qualified global \(L_a\le v(\rho_a)\), \(L_b\le v(\rho_b)\), \(\rho_a<\rho_b\), concavity gives the lower chord

\[
v(\rho)\ge\frac{\rho_b-\rho}{\rho_b-\rho_a}L_a+
\frac{\rho-\rho_a}{\rho_b-\rho_a}L_b,\qquad \rho\in[\rho_a,\rho_b].
\]

Let \(L_C\) be the maximum of applicable chords. A repeated actual coordinate uses the greatest qualified lower and contributes no zero-length chord. Chords are never extrapolated. These standard parametric-optimization facts yield
\(0\le U_{\mathcal A}(\rho)-v(\rho)\le U_{\mathcal A}(\rho)-L_C(\rho)\).
We calculate the worst bound over the entire covered interval from all true affine-line intersections, active-chord intersections and domain endpoints using rational arithmetic. No dense grid or new solver is used. Actual binary64 lambda/weight coordinates are retained, including small differences from displayed .5/1/2. The numerical guards are those stated with Table 5.

**Continuous-weight quality guarantees from the complete fleet archive.** Ranges below are display coordinates; the machine-readable data preserve exact loaded coordinates. Regret bounds are rounded upward.

| Fixed physical family | Covered rho range | Runs / distinct G,p lines | Supported archive lines | Worst absolute regret bound |
|---|---|---|---|---|
| K-15-S | [0.710502825, 2.8420113] | 8 / 3 | 3 | 0.002356282 |
| UC-B20-B | [0.88725, 3.549] | 6 / 1 | 1 | 0.000000100002 |
| R-B20-S-T1 | [0.5, 2] | 9 / 7 | 3 | 0.015594269 |
| R-X35-S-T2 | [0.5, 2] | 9 / 9 | 1 | 0.136115162 |

UC-B20-B has the same component line across the full historical range, with an essentially numerical-width bound for one fixed fleet. K-15-S exhibits three genuinely supported component choices; the largest archive regret bound occurs at \(\rho\approx1.217804157\), between sampled weights. R-B20-S-T1 has component tradeoffs but a wider low-weight search gap. R-X35-S-T2 has one archive line supported throughout, while its proof band remains wide. Dominated fleets and their owners remain in the archive. Stability among known fleets does not prove a complete optimal frontier.

![Certified continuous-weight bands for four fixed physical families. Blue is the best verified archive objective; black dashed chords are applicable qualified lower bounds; shading is the remaining quality band. Pale lines retain other feasible component choices, circles mark original run incumbents, and triangles mark qualified lower anchors. These are upper/lower bounds, not a known exact optimum curve.](figures/parameter_quality_bands.png)

The R-X35-S-T2 fleet found at the higher sampled weight improves both components of the original unit-weight B incumbent. Re-evaluated at its actual original rho coordinate, its feasible objective is 0.3365058165 instead of 0.4032719989, a known improvement of 0.06676618239. The old U, discovery time and certificate status are unchanged. This offline deficit diagnosis is not injected into the C166/B comparison's startup or treated as production acceleration.

\clearpage

'''
    body=body[:start]+weight+body[end:]
    resource=read(OUT/'analysis/resource_intervals.json');facts=[]
    for r in resource:
        a,b=r['operations_T1'],r['operations_T2']
        facts.append(f"{r['base'].replace('R-','')} {a['pickups']} to {b['pickups']}")
    body=replace(body,'The supplement reports operations of each verified own incumbent, including open configurations.',
        'All four own-fleet comparisons show lower Gini and lower average target deviation at the larger horizon, accompanied by more cumulative pickup ('+'; '.join(facts)+'). Returns change from 0 to 0 on B20, 1 to 0 on X20, 2 to 3 on B35, and 1 to 0 on X35. B35 therefore improves its objective while returning more stock. Its final station total decreases by one; X35 recovers one additional station unit. Counts of under-target, at-target and over-target stations and every route\'s travel/handling utilization are retained together in the supplement. These are descriptions of displayed feasible plans, not causal explanations of the unknown optimal fleets. The supplement reports operations of each verified own incumbent, including open configurations.')
    (P/'paper_body.md').write_text(body,encoding='utf-8')
    bib=(P/'references.bib').read_text(encoding='utf-8-sig')
    assert 'vielma2018embedding' not in bib and 'huchetteVielma2023' not in bib
    bib+='''\n@article{vielma2018embedding,
 author={Vielma, Juan Pablo}, title={Embedding Formulations and Complexity for Unions of Polyhedra},
 journal={Management Science}, year={2018}, volume={64}, number={10}, pages={4721--4734},
 doi={10.1287/mnsc.2017.2856},
 url={https://juan-pablo-vielma.github.io/publications/Embedding-Formulations-and-Complexity.pdf},
 note={Author manuscript read: Definition 1, Proposition 1, Corollary 1 and Definition 2; published online 2017}
}
@article{huchetteVielma2023,
 author={Huchette, Joey and Vielma, Juan Pablo}, title={Nonconvex Piecewise Linear Functions: Advanced Formulations and Simple Modeling Tools},
 journal={Operations Research}, year={2023}, volume={71}, number={5}, pages={1835--1856},
 doi={10.1287/opre.2019.1973},
 url={https://optimization-online.org/wp-content/uploads/2017/07/6148.pdf},
 note={Author manuscript Section 2 and Proposition 1 read; published online 2022}
}
'''
    (P/'references.bib').write_text(bib,encoding='utf-8')
    print('Directly revised introduction, compact representation, all four continuous-weight families, two-sided resource values and attribution.')
if __name__=='__main__':edit()
