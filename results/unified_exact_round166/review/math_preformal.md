# Independent mathematical/model review: preformal stage

Reviewer: `/root/math_review`, an actual independent child agent. Date: 2026-11-14 (Asia/Shanghai). This is a read-only mathematical/source review; no Optimize, executable, native state, or performance sample was produced. Implementation admission remains conditional on the final code and finite qualification readback.

## Finding and scope

The proposed local compression is correct for the stated joint object and the current contiguous integer domains. The five-point claim is a direct finite-disjunction/piecewise-affine consequence, not a new general formulation theorem. The separate absolute-inventory binary-product block is needed for integer exactness. Its LP relaxation does not strengthen the common local projection, because it is a convex extension containing every true graph point.

I found no unmentioned state-dependent function in the frozen B writer. In particular, `penalty_reconstruction` is computed inside the VD loop but is emitted only for `station_state_vdj`; frozen VD-P/B retains the original e epigraph. The target value is therefore not a missing breakpoint for B. This conclusion does not extend to AP, VD-J, threshold counts, reciprocal-normalization or vehicle-state modes.

## Independent constructive proof

Put f(y)=(y,|b-y|,1[y!=b]). Partition the legal integer interval into the nonempty portions of [l,b-1], {b}, [b+1,u]. On each portion f is affine. For an interior legal integer y of a portion with legal endpoints a<c, set theta=(c-y)/(c-a). Then f(y)=theta f(a)+(1-theta)f(c), and, at the same g, gy=theta ga+(1-theta)gc. The singleton case uses its point with weight one. Every graph segment over every legal y is consequently in the convex hull of the endpoint graph segments, and the reverse inclusion holds because the chosen endpoints are themselves legal. Those endpoints are contained in K={l,u} union ({b-1,b,b+1} intersect [l,u]), proving equality.

For any perspective solution, if t_a>0 set g_a=q_a/t_a in [alpha,beta]. Zero t forces q=0. The reconstructions produce a convex combination of (a,f_M(a),f_V(a),g_a,a g_a). Conversely any convex combination defines t and q by aggregation. This proves the perspective representation without adjacency or SOS2 constraints. The interpolation proof uses a common g for each original y, while an arbitrary hull point can mix distinct g_a.

For integer exactness, assign binary digits of the legal integer Y and w_h=g b_h. The standard four product inequalities over [alpha,beta] enforce that equality at binary b_h, so Z=sum 2^h w_h=gY. A physical one-way nonzero service with unique assignment already gives M=|b-Y| and V=1[Y!=b] from the original inventory balance, binary z/m and quantity bounds. Thus its unchanged physical columns extend by the interpolation above. Conversely, any C166 integer solution has the original route/service/inventory constraints and exact gY. The old VD-P extension is obtained by s_Y=1,q_Y=g. This proves the common integer physical projection and original-objective correspondence, including epigraph g values; no assumption that arbitrary model g is the true Gini is needed.

Let Pbit be the relaxed bit extension. It is convex and has an extension for every legal true (Y,g,gY) point. Hence its projection contains the convex hull of all these points. The breakpoint extension projects to H. With disjoint auxiliaries and only (Y,g,Z) shared, every point of H has a Pbit extension; intersecting the blocks therefore still projects to H. This is a projection statement, not ideality of the combined extended formulation, equality of branching relaxations after a bit/state branch, or a native-cut/search-path statement.

## Five points and boundaries

If l<=b-2 and u>=b+2, the V=1 slice in (Y,M,V) is the quadrilateral with coordinates (l,b-l), (b-1,1), (b+1,1), (u,u-b). Each is a vertex: two lie on each side of the absolute-value graph and the distinct slopes force all four endpoints. The b point is the only V=0 point. Every representation selecting only legal graph points therefore needs those five points. This is not an extension-complexity lower bound for arbitrary lifted formulations.

Singleton domains, b absent, one-sided domains, b=0/C, alpha=beta (including zero) work without division by a zero piece width. For alpha=beta, q=alpha t gives Z=alpha Y directly, but a uniform bit layer remains valid. An empty mathematical domain is infeasible; source storage resetting its bounds to [0,C] does not change that semantics.

The general statement extends to any finite family psi of functions affine on each common legal integer piece, provided every outside use of the deleted columns is through the declared reconstructed interface. The number of continuous support states depends on the number of common pieces. This does not bound the total exact encoding independently of capacity.

Two sharp failure cases are useful:

* Add an exact state penalty |Y-2| with b=5 and domain [0,10]. Old K={0,4,5,6,10} cannot represent the true graph point Y=2, M=3, V=1, penalty=0. A target breakpoint is needed if that function is actually reconstructed from shared state mass. Keeping B's separate e epigraph does not add this function to the state interface.
* For a holed inventory set {1,3} with b=0, the continuous endpoint hull and an exact binary product permit Y=2, M=2,V=1. The local continuous hull is still correct, but the integer domain is enlarged unless its holes are enforced elsewhere. The current proof explicitly requires the original contiguous integer interval.

## Counterexamples checked algebraically

The prescribed b=0, y in {1,2,3}, g in [0,1/2] witness t_1=t_3=1/2,q_1=0,q_3=1/4 has Y=2,g=1/4,Z=3/4 rather than gY=1/2. Integer Y, direction and visits cannot repair that product. Binary t instead deletes the legal internal y=2 inventory.

For the independent-block issue, use b=1, domain {0,1,2}, g in [0,1/2], Y=1,M=V=0,g=1/4,Z=0. The service hull admits its initial-inventory point. The separate product hull admits this point by mixing (y=0,g=1/2) and (y=2,g=0) with equal weights. A common mixture with M=0 must put all state mass at y=1, forcing Z=g=1/4. Thus independently correct product and service hulls can give a strictly larger common-coordinate set. This restates the inherited R98 linkage, not a new Round166 discovery.

## Actual source/interface readback

Source positions below refer to inherited R165 HEAD 239db6a80c944f1e7b5a55504ce5202ea35c2586; later edits must update or recheck locations.

| Source location | Independently read fact | Required C166 action |
|---|---|---|
| CplexBaseline.cpp:813-840 | mode predicates, VD-P-only state-service check, static segmented incompatibility | Admit one explicit new mode; do not pretend C166 is VD-P |
| CplexBaseline.cpp:953-981 | full state columns versus absolute bit/prod declarations | continuous breakpoint mass/product plus separate old absolute bit/prod |
| CplexBaseline.cpp:1145 | VD modes skip factory bit-McCormick rows | C166 must retain bit rows |
| CplexBaseline.cpp:1189 | domain_infeasible emits explicit contradiction | Keep it even if storage domain was reset |
| CplexBaseline.cpp:2981-3094 | state joint reconstruction and optional theta/code/direction/VD-J | Only mass/Y/G/Z/movement/visit in current B; reject other states |
| CplexBaseline.cpp:3104-3134 and IntervalRowFactory.cpp:579-608 | old P has three global product rows plus four interval-tight rows | Reuse exact layer without accidental bit filtering |
| CplexBaseline.cpp:3154-3181 | AP explicitly uses per-state penalty coefficients | Off, incompatible until separately proved |
| CplexBaseline.cpp:3183-3246 | STOCK RLT uses only Y/G/Z but its current gate is VD-P-specific | Main B has it off; do not silently broaden this round |
| CplexBaseline.cpp:3247-3289 | R140 counts use per-state coefficient maps | Off and reject |
| CplexBaseline.cpp:3513 and GurobiBaseline.cpp:3981 | RN builds state products; R141 reads root selectors | Off and reject |
| IntervalRowFactory.cpp:519-521 | empty propagated domain resets storage bounds, flag remains true | Flag is mathematical authority, not reset bounds |
| MipStartMapping.cpp:286-346 | one-hot mapping, then old bit/product mapping | New t/q interpolation and full actual-column/row checks; keep bit mapper |
| PaperExternalGiniTree.cpp:1225,1515,4104 | canonical specs inherit representation policy | Include identity on root/child/target/terminal paths |
| CplexBaseline.cpp:4831-4841 | actual LP SHA and row signature bind complete matrix | No opaque native state transferred across representations |

The remaining frozen rows and objective use common Y/r/e/H/S/G/Z and route/vehicle columns, not individual s/q. Pairwise absolute H, service/resource rows, SCF/MTZ, cutoff and epigraph constraints therefore remain literally outside the replaced block. A common interface hull with every such outside row unchanged gives equal complete raw LP projection. This assertion precedes presolve and generated native cuts, and requires actual mode guards and row-readback qualification.

## Size accounting

Let N=u-l+1, k=|K|<=5, d=max(1,ceil(log2(C+1))) as in the inherited absolute-bit implementation. Excluding unchanged original columns and all outside rows, B uses 2N columns, N binary declarations and 2N+6 rows (two perspective rows per state plus mass/Y/G/Z/M/V). C166 with the inherited three global plus four interval-tight product inequalities uses 2k+2d columns, d binary declarations and 2k+8+7d rows. If one specifies the mathematical minimal four-row product hull instead, the last term is 4d; that is not the inherited P writer's redundant-row convention.

For exact nonzero accounting of the joint block, let n_y count nonzero support values, n_m count values unequal to b, delta_b=1[b in support], A=1[alpha!=0], B=1[beta!=0], and Mveh denote vehicle count. With the short visit row V+t_b=1, and zero coefficients omitted, the joint rows have 3+3 Mveh+(4+A+B)n+2 n_y+n_m+delta_b nonzeros for n support values. The old/new comparison substitutes N versus k. If the new writer instead uses V-sum_{a!=b}t_a=0, replace its last delta_b by n-delta_b; the two visit rows are equivalent under the mass equation but have different nonzero counts. The separate inherited bit block adds 2+(15+2A+2B)d nonzeros when all seven inequalities are emitted. Actual serialized/read native counts supersede these expressions if generic coefficient omission applies. Bounds are excluded from row counts.

## Historical and primary-source distinction

Actual historical text read: R55 station_state_projection_mapping.md and aggregate_mccormick_implication.md; R67 mathematics.md and lp_projection_attribution.md; R98 mathematical_algorithm.md; R100 mathematical_algorithm.md; R104 mathematical_algorithm.md and final_report.md; targeted R132 mathematical_analysis.md and R133 objective-gap/final-report passages. LOG retains all continuous s/q, merely replacing their binary declarations with code bits. R104 preserves one selected objective value by a dual aggregate and explicitly need not preserve the feasible set or descendant bounds. Neither is the present joint-support compression. R98 already establishes the same joint movement/visit linkage and implicit service integrality. R132/R133 retain positive fixed-total-stock original-objective gaps; the present local hull does not invalidate them or give a route/integer-objective hull.

Primary author PDFs actually opened on 2026-11-14: Vielma, *Embedding Formulations and Complexity for Unions of Polyhedra*, 25-page author PDF, Definition 1 on PDF p2, Proposition 1 on pp6-7 and Corollary 1 on p7; Huchette-Vielma, *Nonconvex piecewise linear functions: Advanced formulations and simple modeling tools*, 45-page author PDF, graph/disjunctive definitions in section 2 (PDF pp4-6), Definition 1 and Proposition 1 on PDF p8. The latter explicitly assumes continuous piecewise-linear functions in its initial setup; the present visit indicator is a discrete-integer piece system, so its treatment must be derived as above, not passed off as the same continuous graph theorem. Both papers already provide systematic embedding/strong formulation constructions and warn by their framework that formulation size/strength and branching behavior are separate. No claim of inventing disjunctive hulls, sparse breakpoints, or binary-product linearization is warranted.

Sources: https://juan-pablo-vielma.github.io/publications/Embedding-Formulations-and-Complexity.pdf ; https://optimization-online.org/wp-content/uploads/2017/07/6148.pdf . These are the versions actually read, not an assertion that all final journal theorem numbering is identical.

## Parameter and resource direction checks

For a fixed physical feasible set and fixed normalized weights, v(rho)=inf_x(G(x)+rho p(x)) is concave. A convex combination of endpoint lower values is therefore a lower bound only between those endpoint coordinates. Taking the maximum of applicable chords preserves lower validity; distinct same-coordinate lower values may be maximized but do not define a chord. A finite recovered physical archive gives an upper envelope by minimizing its affine lines. No rounded G/P or unqualified local/cutoff bound can substitute for their actual sources.

Every finite affine-line/chord endpoint and valid pairwise intersection partitions the covered parameter range into intervals with fixed active affine branches. The gap is affine on each cell, so its maximum occurs at cell endpoints. This gives a continuum guarantee without a grid. Any negative upper-minus-lower value must trigger source/numerical investigation, not clipping. Physical equality across weights requires matching normalized omega, not merely its sum. If relative weights change, separate the family.

For nested physical-time domains T1<T2, Delta=F*(T1)-F*(T2)>=0, Delta>=L1-U2 and Delta<=U1-L2. Thus [max(0,L1-U2), U1-L2] is valid with qualified global L and physical U. Neither an almost-saturated observed route nor changes in return stock prove which constraints are active at an optimum or a causal optimal mechanism. These are objective units, not monetary prices.

## Preformal disposition

Mathematical proposal: PASS within the declared scope. Historical distinctness: PASS for compressing continuous support of the inherited joint object, with standard-tool attribution. Current-mode full LP embedding: mathematically PASS conditional on the explicit mode/guard/Start/type/factory implementation and actual qualification. No formal batch admission is issued by this preliminary source-only report; inspect final implementation and qualification before starting the fixed matrix.
