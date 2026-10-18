# A tailored exact method for static bicycle redistribution with inventory-ratio dispersion

Round125 self-contained methods revision, 18 October 2026. The maintained mathematical appendix is [Appendix A](model_appendix.md); full published-result tables and three clocks are in [Supplement S](tables/complete_results.md). The complete algorithm supplement is [Appendix B](algorithm_appendix.md). Citation keys resolve in [references.bib](references.bib).

## Abstract

Static bicycle redistribution must allocate limited routing resources while choosing how far each station can be brought toward its target inventory. We study a multi-vehicle problem that minimizes the Gini dispersion of station inventory-to-target ratios plus a weighted two-sided relative target deviation. Vehicles leave empty, may return loaded, and perform at most one nonzero, unidirectional service at each visited station. Travel and loading resources constrain the attainable inventory vector. We present the frozen M-B method: a finite constructive and neighborhood startup, an inventory-state product representation with implicitly integer service quantities, valid physical and interval strengthening, and a controller that maintains a complete cover of improving Gini values around scoped native LP/MIP solves. We state the embedding, cutoff-complement and coverage arguments and distinguish ideal mathematical validity from floating-point numerical certification. A prospectively fixed two-source panel comprises six new problems with 20, 35 or 50 stations, two fixed solver-Seed repeats, 32 complete-method arms and 48 directed comparisons. M-B and the ENS-C reference each win all six new-problem comparisons against the cold original compact Gurobi baseline under the declared materiality rule. Their mutual outcomes include losses, and nonzero certificates on this panel occur only at 20 stations. A separate 18000-second study on one known positive-objective 50-station problem leaves all three methods open; M-B attains \(U=0.3723417754990474\), \(L=0.3580114855518426\). The evidence supports useful finite-window improvements for this model, while exposing unresolved proof obligations and limited certification reach. No same-model comparison against all published algorithms, universal speed advantage or firstness claim is established.

**Keywords:** bicycle redistribution; inventory-to-target ratio; Gini dispersion; mixed-integer programming; valid inequalities; numerical optimality certificate.

## 1. Introduction

An overnight redistribution plan has two coupled tasks: choose final station inventories and realize them by feasible vehicle routes. A desired inventory vector may look balanced yet require more travel, capacity or handling time than the fleet can provide. Conversely, optimizing routes toward fixed targets can obscure the allocation decision when those targets cannot all be attained. We consider this interaction directly. A final inventory is assessed by its ratio to a station-specific target, and routes determine which combinations of ratio changes are physically attainable.

Two objective components are useful for different reasons. Dispersion of inventory-to-target ratios measures how unevenly proportional attainment is distributed across stations. Weighted relative target deviation measures the magnitude of departure from the individual targets. Dispersion alone cannot express target attainment: a uniform 50% shortage has zero dispersion. Target deviation alone permits concentrating the remaining discrepancy where its weights are small. Their weighted sum defines a precise optimization preference without claiming that it identifies customer service, revenue or socioeconomic equity. Those broader meanings require additional demand data and a justified mapping from station targets to user outcomes.

The objective also changes the computational structure. Its Gini denominator is the endogenous sum of ratios, rather than a constant conserved stock total. Station stock need not be conserved because vehicles can return loaded. The numerator couples every station pair, and the denominator couples all stations, while feasible inventory changes are supported by an ordered load-feasible fleet. This is a different interaction from minimizing travel subject to exact target restoration or demand-interval satisfaction. An inventory relaxation can explain an objective floor, but an inventory solution does not establish route feasibility.

We evaluate a complete tailored exact method, denoted M-B, for this stated problem. “Exact” identifies the formulation and complete proof obligations of the method; reported certificates remain numerical certificates under a declared floating-point policy. The method combines an independently paid feasible-solution startup with exact inventory-state products, a service representation retaining binary direction, valid strengthening and a Gini-interval controller. Gurobi provides native optimization. The controller decides which complete domains to solve or subdivide and how their returned bounds cover the original problem. A good incumbent from the startup is valuable, but is not an optimality proof.

The computational question is deliberately narrower than a claim of general superiority. Does this integrated method improve the cold original compact formulation under a complete common production budget, and where does its certificate capability stop in the available evidence? A prospective panel from two station sources provides the primary evaluation. A separate longer window on one known positive-objective instance tests a proof boundary, rather than enlarging the independent sample. Both successes and losses are retained, so a useful overall method need not dominate every representation variant on every role.

The paper has three contributions.

1. It gives a complete, source-faithful formulation and a problem-specific derivation of the inventory-state/service representation. The service quantities can be continuous without changing integer solutions under explicit uniqueness and direction premises; state/service equalities are proved valid. The physical and auxiliary Gini values are kept distinct.
2. It organizes the complete integrated algorithm and its proof contract. Objective-preserving embeddings, cutoff complementation and a maintained cover explain when local native information can support an original-problem bound. Numerical closure, finite termination and optimality certification have separate meanings.
3. It reports a finite, fully denominated comparison with the cold original model and competing frozen implementations, followed by a single known-instance long-window study. This identifies common gains, representation tradeoffs, solver-Seed sensitivity and outstanding regional proof obligations without turning open caps into times to optimality.

The constituent tools include standard product linearization, McCormick envelopes, multistart construction, local exchange, MIP Starts and bound pruning. We do not claim new general branch-and-cut theory for these tools. The scientific object is their particular integration for a nonseparable inventory objective and its measured behavior under one budget. Literature positioning in Section 2 limits the contribution relative to neighboring models; Appendix A makes the formulation and mathematical premises explicit. Sections 3–5 describe the problem, representations and algorithm; Section 6 presents the evidence, and Section 7 discusses what can and cannot be inferred.

## 2. Related work and contribution position

Static bicycle rebalancing covers several materially different problems. [Raviv, Tzur and Forma](https://doi.org/10.1007/s13676-012-0017-6) [@raviv2013] use station dissatisfaction and routing considerations with time resources. Their arc and sequence formulations have different service restrictions; the early full preprint inspected here must not be collapsed into one blanket single-visit model. Our objective is the specified ratio dispersion and relative target deviation, without a travel-cost objective term. Final-article metadata and the early preprint are distinguished in the literature ledger.

The publisher abstract of [Chemla, Meunier and Wolfler Calvo](https://doi.org/10.1016/j.disopt.2012.11.005) [@chemla2013] describes a single capacitated vehicle restoring a target distribution with revisits and temporary storage. It distinguishes branch-and-cut lower bounding of a relaxation from tabu-search feasible upper bounds. We use only these abstract-supported features; its detailed initial-load and handling constraints were not obtained. Our unique one-way station service excludes both revisits and buffering, while permitting target deviations.

[Erdoğan, Laporte and Wolfler Calvo](https://doi.org/10.1016/j.ejor.2014.04.013) [@erdogan2014] study interval inventory requirements with one vehicle, route/handling cost and exact branch-and-cut formulations, including Benders decomposition. Their fixed-route network explicitly accounts for depot supply and handling. [Erdoğan, Battarra and Wolfler Calvo](https://doi.org/10.1016/j.ejor.2015.03.043) [@erdogan2015] instead address target restoration with revisits and temporary storage using an exact routing/feasibility framework. Its depot imbalance and target-equality semantics differ from empty departure and optional target attainment here. Neither problem can be adopted unchanged as a matched benchmark.

[Schuijbroek, Hampshire and van Hoeve](https://doi.org/10.1016/j.ejor.2016.08.029) [@schuijbroek2017] connect service-level inventory intervals with multi-vehicle routing. Their routing objective is makespan, with given initial vehicle inventories and an artificial ending node; their formulation permits more service flexibility than unique one-way visits, subject to its transshipment limits. The cluster-first framework is an approximate multi-vehicle approach, alongside MIP and CP models. This provides a close allocation/routing comparison, but not the same physical model, objective or certificate scope.

The openly available [Ikonen, Heljanko and Harjunkoski](https://doi.org/10.1007/s11081-024-09942-z) article [@ikonen2025] reformulates routing/load disjunctions into a MILP for demand intervals. Duplicated stations permit split visits without temporary storage; prescribed initial load and open/loop options are explicit. Its single-vehicle exact model can be combined with approximate multi-vehicle clustering. Its disjunctions and our Gini proof cover address different structures, despite shared terminology. Reported larger station counts cannot establish relative speed across the different objectives, instances, hardware and thread limits.

Its certificates concern its finite duplication model; solutions requiring additional visits or temporary operations can lie outside that generated model.

Equity requires specifying the resource being balanced. [Matl, Hartl and Vidal](https://doi.org/10.1287/trsc.2017.0744) [@matl2018] analyze workload-equity functions and consequences in vehicle routing. We use their distinction as modeling context; driver-workload conclusions are not transferred as theorems about station inventory-to-target ratios. The bibliography consistently uses the 2018 volume year and records first online publication in 2017.

The search was updated through 18 October 2026. [Qiao et al.](https://doi.org/10.1016/j.tre.2026.104984) [@qiao2026] describe two-echelon coordination with task-duration fairness, an exact first-echelon subproblem and a hybrid second-echelon method. [Caggiani et al.](https://doi.org/10.1016/j.trc.2026.105691) [@caggiani2026] combine free-floating electric relocation, battery swapping and equity evaluation. These are abstract/excerpt-level checks; their complete constraints remain unverified here. They establish that fairness-aware rebalancing is an active prior topic, and preclude any broad claim that introducing fairness or Gini into rebalancing is itself our novelty.

**Table 1. Closest model distinctions.** “Unknown” means not established by the accessed source. The three middle detailed comparisons were checked against their full model sections. Table entries do not assert interchangeable feasible sets.

| Work | Objective / target requirement | Fleet and visits | Temporary or split service | Initial/return and time semantics | Exact scope |
|---|---|---|---|---|---|
| Chemla 2013 | Target distribution | Single; revisits | Buffering allowed | Detailed constraints unknown from abstract | Relaxation bound plus feasible search |
| Erdoğan 2014 | Travel/handling; hard inventory intervals | Single; at most once | No split visit | Depot stock bounds departure; depot handling charged | Full and Benders branch-and-cut |
| Erdoğan 2015 | Travel; exact targets | Single; revisits | Temporary storage allowed | Depot imbalance participates; not our empty-departure model | Routing plus time-extended feasibility |
| Schuijbroek 2017 | Makespan; service-level intervals | Multiple; sequence indexed | Limited transshipments; service not uniquely assigned as here | Given initial load; artificial open end; handling cost | Joint MIP/CP; clustering heuristic |
| Ikonen 2025 | Time/distance/handling; intervals | Single model; duplicated visits | Split permitted; temporary storage forbidden | Given initial load; open or loop option | MILP per vehicle; clustered fleet approximate |
| Present model | Ratio Gini plus weighted relative target deviation | Multiple; one nonzero service per station | Neither split nor temporary service | Empty departure; loaded closed return with unloading; hard route horizon | Complete joint original-model numerical cover |

The relevant standard mathematics is also explicit. Bilinear envelopes are attributed to the established global-relaxation literature [@mccormick1976]; their four inequalities are derived in Appendix A. An exact product with a selected discrete inventory is an application of known disaggregation, not a generic new linearization theorem. Likewise, continuous declaration of a variable already determined integrally by the remaining integer decisions is a formulation choice whose premises must be proved. The empirical question is whether the resulting method helps this problem.

The project lineage is narrower than a literature genealogy. The current cold P is the repository's canonical compact writer and original objective evaluator [@frozenImplementation]. Inspection of the relevant writer, evaluator, startup bridge and representation headers found no verified mapping that identifies one of the public BRP formulations above as its exact original model. Shared routing ideas are insufficient evidence for that identification. H retains the project's inherited decoder and later constructive/exchange components; the paper does not claim to have invented a full genetic algorithm or to have proved H optimal. The code and evidence maps in the appendix and reproducibility notes separate these inherited components from M-B's representation and complete-method comparison.

## 3. Problem definition and objective interpretation

Let \(N=\{1,\ldots,n\}\) contain service stations and 0 be the depot. Each station has capacity \(C_i\), initial inventory \(b_i\), target inventory \(D_i>0\), and weight \(\omega_i\). Each vehicle k has capacity \(Q_k\), begins empty and follows at most one depot-closed route. A station may be left unserved or visited once by one vehicle, with an integer nonzero pickup or drop. Simultaneous pickup and drop at the same station, split service and temporary storage operations are excluded. These are physical restrictions of the problem being evaluated, not conclusions about all rebalancing applications.

Write \(p_{ki}\) and \(d_{ki}\) for pickup and drop quantities. Final station inventory obeys

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\qquad 0\le Y_i\le C_i.
\tag{1}
\]

Every route prefix and its return load must lie in \([0,Q_k]\). A vehicle can collect, deliver and collect again; cumulative pickup is therefore not bounded by \(Q_k\). Loaded return is allowed. If \(R_k=\sum_i(p_{ki}-d_{ki})\), empty departure and nonnegative return imply

\[
\sum_iY_i+\sum_kR_k=\sum_i b_i.
\tag{2}
\]

Station inventory can decrease through depot returns. The capacity/initial values serialized for the depot are excluded from the objective and do not supply a preloaded fleet. In particular, a large depot stock entry cannot repair a station shortage in this model.

Travel time is the Euclidean distance between the serialized coordinates divided by 1.5. With unit handling times \(t_p,t_d\), total duration of route k is

\[
\operatorname{travel}_k+t_p\sum_i p_{ki}
+t_d\left(\sum_i d_{ki}+R_k\right)
=\operatorname{travel}_k+(t_p+t_d)\sum_i p_{ki}\le T.
\tag{3}
\]

The equality follows from load conservation and includes depot unloading. Thus the form used in the writer is not an approximation that ignores return handling. All reported fleets are replayed with their assigned capacities, ordered operations and complete durations. The parameter \(T\) is physical route time; the computational cap is a separate resource.

Set \(r_i=Y_i/D_i\), \(S=\sum_i r_i\), and \(A=\sum_{i<j}|r_i-r_j|\). The objective is

\[
G_{\rm true}(Y)=
\begin{cases}A/(nS),&S>0,\\0,&S=0,\end{cases}
\qquad
F(Y)=G_{\rm true}(Y)+\lambda\sum_i\omega_i|r_i-1|.
\tag{4}
\]

The denominator depends on the final inventory vector. The convention at \(S=0\) sets dispersion to zero but retains all relative target penalties. For nonnegative ratios, \(0\le G_{\rm true}\le(n-1)/n\). The target penalty is two-sided: inventories above as well as below target are penalized. We consistently call it relative target deviation, rather than observed unmet demand.

A zero Gini indicates identical ratios, including the stipulated all-zero case. It does not indicate that stations meet their targets. For example, a common ratio .5 has zero dispersion but positive target deviation when weights and lambda are positive. Conversely, under strictly positive lambda and weights, \(F=0\) requires every ratio to equal one. The study's positive-objective instances cannot be interpreted through a zero-dispersion shortcut.

The weights are max-normalized within the constructed inputs rather than normalized to sum one. Therefore \(\lambda\sum_i\omega_i\) varies across the panel. A fixed lambda does not imply a fixed aggregate tradeoff between target deviation and Gini as station count or the weight distribution changes. This matters both for interpreting objective magnitudes and for the difficulty of proving optimality. Cross-instance values of F are not a common operational service score.

The static assumption freezes inventories during redistribution; customer rentals and returns do not alter them while trucks operate. Coordinates have a real station-source basis, but stock levels, targets, weights and the centroid depot follow a synthetic, declared construction. We therefore evaluate a physical optimization model on traceable constructed instances, not an end-to-end deployment validated against realized rental outcomes.

## 4. Formulations and problem-specific strengthening

### 4.1 Why the inventory representation matters

The cold baseline P-GRB is the canonical compact MILP for the physical problem in Section 3. Binary arcs and assignments, unique station service, direction indicators, MTZ ranks, prefix loads and the complete duration constraint couple routing to final inventory. Appendix A.1–A.3 gives the full numbered formulation in one place. It retains apparently redundant rows actually written by the implementation; it does not substitute a more familiar routing model. The difficulty is not just route selection: integer station stocks enter both the numerator and the variable denominator of ratio Gini.

Write \(H_{ij}\ge\pm(r_i-r_j)\), \(e_i\ge\pm(r_i-1)\), \(P=\sum_i\omega_i e_i\), and introduce a Gini epigraph g. Exact products \(Z_i=gY_i\) give

\[
n\sum_i Z_i/D_i\ge\sum_{i<j}H_{ij},\qquad \min f=g+\lambda P.
\tag{5}
\]

Cold P uses binary inventory bits and binary-continuous products. M-B selects one integer inventory from the necessary domain \(\mathcal Y_i\) in each interval \([\alpha,\beta]\):

\[
\sum_{y\in\mathcal Y_i}s_{iy}=1,\quad Y_i=\sum_y y s_{iy},\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
\sum_yq_{iy}=g,\quad Z_i=\sum_y yq_{iy}.
\tag{6}
\]

At integer selectors one state y=Y_i is active; all other q are zero and the active q equals g, proving \(Z_i=gY_i\). This is an application of discrete product disaggregation, not a new general product theorem. Its LP relaxation differs from the bit model. The actual mode retains the original ratio and deviation constraints rather than replacing them with state-based deviation equalities.

M-B declares pickup/drop continuous while retaining integer Y, unique service, binary assignment and binary direction. At an unserved station both quantities are zero. At the sole serving vehicle either d=0 and p=b−Y, or p=0 and d=Y−b. The nonzero quantity is therefore integer. Integer load declarations are retained but are unnecessary for this inference. Multiple serving vehicles, simultaneous pickup/drop or fractional inventory would invalidate it. Independently, one-way nonzero service proves the state/service equalities

\[
\sum_k(p_{ki}+d_{ki})=\sum_y|b_i-y|s_{iy},\qquad
\sum_kz_{ki}+s_{i,b_i}=1.
\tag{7}
\]

A missing initial-inventory state means \(s_{i,b_i}=0\). These equalities link movement and visit to the selected state; they are not extra premises of the integrality argument. ENS-C keeps integer p/d and omits these two equalities, while sharing H, the static package and the controller. Neither a representation comparison nor an ideal implication between rows identifies the independent computational contribution of a constituent without its ablation.

### 4.2 Physical strengthening and the role of integer service

Conservation gives \(\sum_i b_i-\sum_kQ_k\le\sum_iY_i\le\sum_i b_i\), because the fleet's return stock lies between zero and total vehicle capacity. Visit/inventory links fix Y=b when unserved. Summing route durations gives global handling \(h\sum_{ki}p_{ki}\le mT\). Single-station reachability intersects the inventory domain with the largest operation any one vehicle can support after paying its necessary depot round trip. These physical bounds hold before any Gini interval or incumbent is chosen.

Two less immediate families encode route support and supply compatibility. For a two- or three-station support W, the smallest explicit depot-cycle travel \(\tau(W)\) is the minimum of two or six orders. Metric shortcutting makes it a lower bound on any full tour containing W. If all W are served, their integer nonzero operations and empty departure yield

\[
|W|\le\sum_{i\in W}(p_{ki}+d_{ki})\le P_k+D_k^{\rm drop}\le2P_k,
\quad P_k\ge\lceil|W|/2\rceil.
\tag{M1}
\]

Thus \(\tau(W)+h\lceil|W|/2\rceil>T\) excludes their simultaneous service. Here P_k is **all** pickup on the route; the supplies may be outside W. The alternative conditional row is

\[
h\sum_{i\in W}p_{ki}+M_{kW}\sum_{i\in W}z_{ki}
\le T-\tau(W)+M_{kW}|W|,
\quad M_{kW}=T+\tau(W)+h\max(1,\sum_{i\in W}\min(b_i,Q_k)).
\tag{M2}
\]

All served cancels the M terms and leaves a necessary travel/handling inequality. With one missing service, its available right side is at least \(2T+h\max(1,\sum_W\min(b_i,Q_k))\), enough for every bounded pickup on W. Appendix A.5.4 proves both branches and gives the exact shared 50000-support enumeration. Capacity limits prefixes, never cumulative pickup.

For transfer, label collected units and match every delivered unit to an earlier pickup on its vehicle; nonnegative prefix load makes such matching possible. A source i for delivery j implies the ordered subsequence 0,i,j,0, whose metric travel plus at least one unit of handling is necessary. Therefore

\[
d_{kj}\le\sum_{i\ne j:\ \tau_{0i}+\tau_{ij}+\tau_{j0}+h\le T}p_{ki}.
\tag{M3}
\]

An empty compatible source set forbids delivery; an unvisited source contributes zero; extra stations cannot manufacture stock. Loaded return consists of unmatched pickups and does not break the argument. This row supplies a relaxation-level connection between stock decisions and route time, while the original ordered loads remain indispensable. Appendix A states the emitted numerical guards, indices and all remaining physical rows.

### 4.3 Gini and cutoff strengthening through a physical embedding

For nonnegative ratios let \(A=\sum_{u<v}|r_u-r_v|\). Fix i<j. For every other u, triangle inequality gives \(|r_i-r_u|+|r_j-r_u|\ge|r_i-r_j|\). These n−2 contributions, the pair itself and nonnegative omitted pairs prove

\[
A\ge(n-1)|r_i-r_j|,\qquad
(n-1)|r_i-r_j|\le n\beta S\quad\text{when }G_{true}\le\beta.
\tag{M4}
\]

The static H-spread row uses \((n-1)H_{ij}\le n\beta S\). Combining it with the original H lower rows implies both signed variable-S centering rows; \(S\le\bar S\) then implies fixed centering. The ideal containment is useful for understanding, not a reason to remove current rows or claim measured redundancy. The direct interval cap/floor \(n\alpha S\le H_\Sigma\le n\beta S\) and these spread rows admit the **tight physical completion** H=absolute differences.

That qualification is essential. Every physical fleet in the stated true-G interval and cutoff has a completion with g=true G, exact e,H, Z=gY and W_SP=SP, preserving F. An arbitrary native completion may inflate g,e,H or W, and need not survive the added rows. Conversely native integer objective is at least decoded physical F. The proof contract is objective-preserving physical projection, not preservation of every original auxiliary assignment as required by an unrestricted user-cut claim. At S=0 all ratios/differences are zero; g=0 realizes the original convention and the penalty remains payable.

From true \(F\le c\) and \(G\ge\alpha\), nonnegative penalties give \(\omega_i|Y_i/D_i-1|\le(c-\alpha)/\lambda\). Outward-rounded integer intersections and reachability give the domain rectangle, its penalty floor \(\underline P\) and S bounds. The active writer performs the finite sequence in Appendix A.5.1; a preset field requesting two propagation rounds does not implement an infinite fixed point or even two feedback rounds. Required movement follows immediately from inventory balance on this tightened rectangle.

For positive S, multiplying F≤c yields \(A+n\lambda SP\le ncS\). Replacing S in the denominator by its upper bound gives \(A+n\bar S\lambda P\le n\bar Sc\). Four standard McCormick inequalities [@mccormick1976], obtained by expanding the four nonnegative rectangle products, relax W_SP=SP and support the lifted row \(H_\Sigma+n\lambda W_{SP}\le ncS\). Appendix A.5.7 gives every coefficient, bound and derivation. The original objective cutoff is retained: at S=0 cross multiplication becomes tautological and would otherwise forget the positive penalty. These are cutoff-scoped rows, regardless of a “Global” implementation metadata label.

### 4.4 Native and project responsibilities

The project supplies the original model, inventory representation, static physical/interval rows, H, complete verified Starts and domain controller. Gurobi supplies native LP/MIP optimization, presolve, cuts and branching. Native monitoring callbacks can terminate on a mathematical bound target; M-B does not implement dynamic separation of these static families or custom native branching. Benders, pricing, dynamic resource cuts, D1, AMF/RC, single-child contraction and timed-quanta research branches are off. Standard triangle, cover, product and McCormick reasoning is not claimed as new general theory. The [method specification matrix](method_spec_matrix.csv) maps the finite active list to numbered proofs and actual generation points.

## 5. Complete M-B algorithm and certificate logic

### 5.1 Startup and maintained information

H is a finite constructive and neighborhood procedure. It constructs a verified fleet by joint insertion; generates 24 shuffled station/separator orders under seed 20260626 and one completed constructive order; fully decodes each; performs first-improvement guided order descent; then alternates strict physical insertion/quantity closure with neutral balanced relocation/equal-net exchange. Appendix B.6–B.11 supplies the encoding, legal amounts, compensation, full compaction, candidate generation, cache policy and actual ties. This active path does not execute genetic generations. H supplies an own upper bound, never a lower certificate. Every compared integrated arm pays for its own H; saved or cross-arm routes are not free incumbents.

The controller stores own verified fleet, U, its true G, incumbent epoch and a coverage registry. Each unit carries interval, qualified bound and source scope, cutoff, parent/children, depth and status. Runtime caches separately bind canonical matrix identity and complete LP evidence to their generation/epoch. Maintaining this distinction prevents a good LP point from becoming a physical incumbent or a child-domain bound from being promoted to its parent.

### 5.2 Two bound targets and complete decision procedure

After the selected parent's LP return, let its updated bound be b and the other relevant unit bounds be b_j. Requeue first if any \(b_j+\epsilon<b\). Otherwise, until the unit's NEXT milestone has been reached, request

\[
t_{next}=\min\{b_j:b_j>b+\epsilon\},\qquad \epsilon=10^{-7},
\tag{M5}
\]

if this set is nonempty. Once the milestone is reached, or no strict higher competitor exists, allow child lookahead. NEXT therefore raises a controlling unit toward the next frontier level before paying for subdivisions. It is not the child target and not a time slice.

For two qualified finite raw child LP bounds ℓ_j, put

\[
\Delta=\max(U-b,\max(\epsilon,10^{-12})),\quad
v_j=\operatorname{clip}((\ell_j-b)/\Delta,0,1),\quad
\eta=\min(v_0,v_1),\quad\mu=(v_0+v_1)/2.
\tag{8}
\]

If \(b_+=\min(\ell_0,\ell_1)\le b+\epsilon\), run terminal MIP. If it strictly improves b and ημ plus the explicitly defined floating score tolerance (B2) reaches .08, split. If the gain is positive but score insufficient, retain the parent and run its MIP with target b+. Recompute decisions from the actual return. With an infeasible child, the frozen policy installs both children atomically and marks the proved empty ones; it does not invoke the dormant contraction variant.

The following algorithms specify the complete active flow. `Native` means the request contract in B.4 (actual model identity, type restoration, remaining global deadline, optional validated complete Start, native return and request cleanup). `Qualify` tests its stated identity/finalization/settings/consistency gates; it is not a new oracle. Geometry, tie order, cache tests and all return cases are fully defined in B.1–B.4.

~~~text
Algorithm 1  FrozenMB
Input: instance and physical parameters; frozen method settings; one process deadline
Output: own fleet/U, qualified complete-cover L, unresolved units and evidence status
1  Run H (B.6), admitting only complete physically verified fleets.
   If own verified zero and the inherited zero-evidence policy passes,
       finalize its independent F>=0 certificate and return.
   If no admissible fleet exists, retain U=+infinity and report startup failure;
       RETURN failure without initializing a finite-cutoff proof.
2  Create root L0=[0,min(U,(n-1)/n)], bound 0, Open, epoch 0;
   retain outside-range analytic floor U. For n=1 use root [0,0].
3  While time remains and unresolved relevant coverage remains:
       select a controlling unit with B.2's epsilon-plateau cyclic tie rule;
       if no unit selectable, stop and retain all remaining obligations;
       outcome := ProcessLeaf(unit);
       FinalizeAndUpdateCover(outcome);
       if deadline, engineering failure or terminal interruption: stop.
4  Finish native cleanup and lifecycle outputs; qualify sources and own witness.
   Return the raw complete-cover minimum L without clipping to U;
       distinguish its numerical policy from exact complement accounting (B.4).
   Return own U/L and all unresolved coverage; certify only if the inherited
       numerical gap, source, physical and lifecycle gates all pass.
~~~

~~~text
Algorithm 2  ProcessLeaf / ChooseAction
Precondition: selected unit is still represented; no pending native call.
1  Validate/rebuild artifact for current epoch; reuse a qualified same-epoch
   parent LP or request its complete LP relaxation.
   On deadline/invalid LP return OPEN_STOP/ERROR, with parent unchanged.
   On qualified infeasible LP return CLOSE(parent,cutoff evidence).
   Merge a finite optimal parent-LP bound on this same domain.
   If b >= current U-epsilon return FATHOM with its bound source.
2  Apply NEXT rule (M5) in its stated priority order:
       noncontrolling -> REQUEUE;
       strict target -> Native(parent MIP,target NEXT), then RETURN_NATIVE;
       otherwise proceed to 3.
3  If depth>=8 or width<=1e-4+1e-12:
       Native(complete parent MIP,no target), then RETURN_NATIVE.
4  Form midpoint children [alpha,mid],[mid,beta], ids parent.0,parent.1.
   Obtain both complete current LP results or reuse B.2's valid cached pair.
   A child starts with max(parent bound,its qualified finite LP bound),
       but retain raw child LP fields for AM. Children are not active leaves.
   On either incomplete/invalid result return OPEN_STOP/ERROR; keep parent.
5  If either child is qualified infeasible: return SPLIT(children,empty flags).
   Otherwise compute (8), (B2), b+=min(raw child bounds):
       b+<=b+epsilon -> Native(complete parent MIP,no target);
       score+score_tolerance>=.08 -> return SPLIT(both children);
       otherwise -> Native(parent MIP,target b+,kind CHILD).
   For a native action return its actually finalized outcome and source identity.
Postcondition: no unresolved domain removed; no target value admitted as proof
   merely because it was requested; no speculative child counted as active.
~~~

~~~text
Algorithm 3  FinalizeAndUpdateCover
Input: ProcessLeaf outcome, current cover, own witness/epoch/runtime caches
1  For native outcomes require actual return and request cleanup first.
   On failed engineering qualification: stop ERROR; leave unresolved region.
   Admit any finite qualified native bound only on its recorded domain/cutoff.
   Retain the source cutoff for proof accounting in A.6; do not clip the
       raw stored numerical bound (B.4).
2  Replay a candidate fleet and original objective. If own U improves by >1e-9,
       replace own witness, increment epoch and tighten current cutoffs.
       Keep qualified old scoped floors; invalidate retained models/LP/children
       on next access using B.2; never transfer a child-only floor upward.
3  SPLIT: validate parent identity, both child ids/lineage/endpoints, shared
       midpoint, inherited bounds and full union. Install both in one transaction,
       mark parent Replaced, then mark proved infeasible children Empty.
       Discard replaced/empty backend models; failed transaction retains parent.
4  CLOSE/FATHOM or qualified native OPTIMAL/INFEASIBLE: close only this
       cutoff obligation and keep its complement floor and evidence.
   Target reached + termination requested + bound>=target-epsilon:
       set NEXT milestone only for NEXT, then requeue parent (no forced split).
   REQUEUE: retain all state/coverage, return to selection.
   TimeLimit/interrupted before proof/target: retain eligible partial bound,
       keep unit Open, stop common lifecycle. Unknown/error is never Empty.
5  Recompute full-cover minimum; output unresolved units if any remain.
Postcondition: every potential physical improver is still covered by an open
   obligation or a qualified closed/complement floor.
~~~

Own-U updates and native-bound admission share a source ledger but not a meaning: a feasible fleet can remain valid even if a dependent proof source is later rejected. Start ineligibility is neither infeasibility nor evidence that a low-G region lacks feasible fleets. The next strict target has priority before geometry eligibility; a narrow/deep leaf can still do a NEXT phase, but eventually uses complete MIP rather than deleting its region.

### 5.3 Why the returned bounds cover the original problem

For a source bound ℓ on an interval model with objective-preserving embeddings of all physical points in \(F\le c\), points inside that cutoff have \(F\ge\ell\), while points outside have \(F>c\). Its unconditional regional floor is therefore min(ℓ,c). Infeasible cutoff models yield floor c, not an infinite original-region bound. This is why old cutoffs remain in the evidence scope after U improves.

For a complete covering family ᶜ with such floors β_I, plus the analytic outside-range floor U,

\[
L=\min\{U,\min_{I\in\mathcal C}\beta_I\}
\tag{9}
\]

is a lower bound. Every physical point belongs to at least one covering region or the complement. Both closed midpoint children preserve the parent's union, including their shared endpoint. Max may combine independent valid floors on the same domain; min combines siblings. An unsplit parent or incomplete lookahead remains an obligation. These observations prove coverage inductively, without treating depth limits, milestones, target termination or repeated U as certificates. Appendix B.5 gives both synthetic teaching states and one labelled R123 atomic-cover event.

### 5.4 Exact mathematics and numerical evidence

The embedding, triangle, support and cover arguments above concern real/exact arithmetic under their explicit physical premises. Actual matrices use binary64 coefficients and Gurobi tolerances; the retained evidence policy is (10^{-7}). The implemented penalty closure test \(\alpha+\lambda\underline P\ge c-10^{-9}\) can close a non-strict cutoff containing a mathematical point at or just below c. It is a **numerical closure**, not proof of strict rational infeasibility. A local (10^{-9}<10^{-7}) comparison does not bound global accumulated error. H's internal floating descent likewise does not prove exact rational monotonicity, although its admitted physical neutral moves preserve the exact recomputed objective and improve the entire duration tuple.

Reported original-problem certificates additionally need own verified U, qualified complete coverage, source/return identities and normal lifecycle completion. The sealed nonzero policy requires −1e−7≤U−L≤1e−7 without clipping; this is stronger than the native certificate function’s one-sided test. B.4.1 states every admission gate, the no-native clean own-zero branch \(U≤1e−12\), and the exact-zero source-reduced fallback. Invalid proof dependencies cannot be repaired by a good incumbent or independent zero floor; source-reduced outcomes remain separate. The single deadline guarantees an operational end, not certification within every window. No solver tolerance or historical certificate field is changed in this revision. The finite sample and nonfactorial design in Section 6 limit empirical attribution; these mathematical details add no new performance evidence.

## 6. Computational study

### 6.1 Primary prospective panel and measurement

The primary panel [@benchmark122] was fixed before its six new inputs were generated once. It uses two frozen station sources: CITI with 442 eligible physical stations from 443 original rows, and CABI with 865 stations. Source identities, station selections and overlap records remain in the input manifest. The sources provide geographic station information; inventory landscapes and targets are constructed by the declared recipe.

The recipe retains four-anchor/hash selection and tie rules, target fractions .44–.56, coordinates serialized to three decimal places, weights to six decimals with maximum normalization, a centroid depot, stock-total correction and the declared heterogeneous or homogeneous capacity vectors. No H, LP or MIP screening selected problems by difficulty. There was no outcome-driven redraw, salt change or best-of-replicate selection.

**Table 2. Six new Seed0 problems.** Stock labels describe the construction. Lambda is .15 and pickup/drop are 60/60 throughout.

<!-- DESIGN_START -->

| Role | Source | n/m | Geometry / inventory | Q | Physical T \(s\) | Cap \(s\) | sum weights | lambda sum weights |
|---|---|---|---|---|---|---|---|---|
| PB-C20-B | CITI | 20/2 | compact / balanced | [30, 30] | 3600 | 900 | 7.288265 | 1.09323975 |
| PB-B20-S | CABI | 20/2 | regional / shortage | [20, 40] | 7200 | 900 | 7.2840239999999996 | 1.0926035999999999 |
| PB-C35-U | CITI | 35/3 | regional / surplus | [20, 25, 30] | 10800 | 2400 | 11.590113000000001 | 1.7385169499999999 |
| PB-B35-B | CABI | 35/3 | compact / balanced | [25, 25, 25] | 7200 | 2400 | 14.720000000000001 | 2.2080000000000002 |
| PB-C50-S | CITI | 50/4 | compact / shortage | [30, 30, 30, 30] | 10800 | 3600 | 20.216045000000001 | 3.0324067500000003 |
| PB-B50-U | CABI | 50/4 | regional / surplus | [20, 25, 35, 40] | 18000 | 3600 | 22.597221000000001 | 3.38958315 |

<!-- DESIGN_END -->

Each new problem has four complete arms: cold P-GRB, ENS-C, M-B and MB-D1. Two additional fixed blocks repeat PB-B35-B and PB-C50-S with solver Seed1. Thus there are six new problems, eight method/Seed blocks, 32 arms and 48 directed pairs. The repeats are sensitivity observations on known inputs, not two new problems. Within a block all methods share the same physical input and production cap. Serial method order rotates across the planned blocks; the complete schedule is retained with the published design.

All methods use the same frozen executable and Gurobi 13.0.2 DLL, one native thread, one MIP thread, PresolveAuto, the stated Seed, FeasibilityTol/OptimalityTol \(10^{-6}\), IntFeasTol \(10^{-5}\), and requested MIPGap/MIPGapAbs zero. The evidence policy remains \(10^{-7}\). The common 30-second native reserve is part of the one process deadline. Larger caps can change a method's search path, so a prefix of a longer run is not assumed to reproduce a shorter run.

Production time \(T_{\rm produce}\) includes all own online startup, models, LP/MIP work, Starts, callbacks, cleanup and sealing. Post-seal verification is \(T_{\rm verify}\); \(T_{\rm total}\) is their sum. Cross-arm reconciliation is group cost, and nested native timers are not added again. A verification tail beyond the native reserve is not a producer timeout. We preserve original final output fleets as the primary U endpoints, even where a separately legal historical witness is slightly better.

The machine/software identity and full clocks are documented in Supplement S and the reproducibility notes. The comparison is within matched complete-method windows, rather than a mixture of historical executables, hardware states and caps. The finite nonfactorial design varies source, scale, geometry, stock, Q, T and aggregate weight together. It does not isolate their individual causal effects or estimate a population win probability.

### 6.2 Comparison and evidence tiers

The fixed rule is certificate first. A candidate-only qualified certificate wins; a control-only certificate is a severe loss. When both certify, the time-materiality threshold is \(\max(30\text{ s},.10T_{\rm control})\). Severe certified regression additionally requires twice the control time and at least 120 seconds excess. Actual time ratios are meaningful only for two certified results.

For two open results let \(\mathrm{gap}=U-L\), \(a_U=\max(.001,.01|U_{\rm control}|)\), and \(a_{\rm gap}=\max(.001,.10|\mathrm{gap}_{\rm control}|)\). Material improvement in U or gap without opposing material deterioration is WIN; the reverse is LOSS; opposing changes are MIXED; otherwise TIE. Severe open regression requires both specified U and gap deteriorations, with thresholds \(\max(.001,.05|U_{\rm control}|)\) and \(\max(.005,.25|\mathrm{gap}_{\rm control}|)\). Missing necessary evidence remains UNEVALUABLE. These are experiment-selection/materiality labels, not statistical significance tests.

We distinguish nonzero numerical certification, an independent own-zero certificate, reliable open bounds, source-reduced evidence and missing evidence. The primary panel has seven nonzero certified arms and 25 open arms; it has no zero certificate, source-reduced arm or missing arm. All seven certificates are at 20 stations. The Seed0 layer contains 24 arms; the Seed1 layer contains eight open arms. PB-B35-B Seed0 cold P uses the explicitly independent lower floor zero, rather than a positive native proof. The tiny positive Seed1 bound is retained.

### 6.3 All primary outcomes and adverse cases

**Table 3. All 32 published primary-panel arms.** N denotes a nonzero numerical certificate and O a reliable open result, including the stated independent floor. U/L and signed gap are role-specific; caps are production windows. Supplement S1 retains full precision and \(T_{\rm verify},T_{\rm total}\) for every row. The displayed tiny signed gaps are not clipped.

<!-- R122_START -->

| Role | Seed | Method | Cap \(s\) | U | L | Signed gap | Tier | T_produce \(s\) |
|---|---|---|---|---|---|---|---|---|
| PB-C20-B | 0 | P-GRB | 900 | 0.2246803118 | 0.1765783752 | 0.04810193667 | O | 872.58902 |
| PB-C20-B | 0 | ENS-C | 900 | 0.2246803118 | 0.2246803118 | -1.110223025e-16 | N | 430.55759 |
| PB-C20-B | 0 | M-B | 900 | 0.2246803118 | 0.2246803118 | 1.054711873e-15 | N | 395.85954 |
| PB-C20-B | 0 | MB-D1 | 900 | 0.2246803118 | 0.2246803118 | 2.498001805e-16 | N | 665.06878 |
| PB-B20-S | 0 | ENS-C | 900 | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 4.6224331 |
| PB-B20-S | 0 | M-B | 900 | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 2.6319677 |
| PB-B20-S | 0 | MB-D1 | 900 | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 2.6983887 |
| PB-B20-S | 0 | P-GRB | 900 | 0.8631523206 | 0.8631523206 | 1.110223025e-16 | N | 116.03278 |
| PB-C35-U | 0 | M-B | 2400 | 0.1696364022 | 0.08395185429 | 0.0856845479 | O | 2372.5264 |
| PB-C35-U | 0 | MB-D1 | 2400 | 0.1793004366 | 0.08353399353 | 0.09576644305 | O | 2370.6204 |
| PB-C35-U | 0 | P-GRB | 2400 | 0.1747718876 | 0.05970290317 | 0.1150689844 | O | 2370.6162 |
| PB-C35-U | 0 | ENS-C | 2400 | 0.1642374878 | 0.08157539377 | 0.08266209402 | O | 2370.5989 |
| PB-B35-B | 0 | MB-D1 | 2400 | 0.2345814099 | 0.09200798362 | 0.1425734262 | O | 2372.4404 |
| PB-B35-B | 0 | P-GRB | 2400 | 0.3055557782 | 0 | 0.3055557782 | O | 2370.5561 |
| PB-B35-B | 0 | ENS-C | 2400 | 0.2465044704 | 0.132287968 | 0.1142165024 | O | 2370.5527 |
| PB-B35-B | 0 | M-B | 2400 | 0.2465044704 | 0.1276343018 | 0.1188701686 | O | 2371.7862 |
| PB-C50-S | 0 | MB-D1 | 3600 | 0.3723417755 | 0.3568747399 | 0.01546703556 | O | 3572.8812 |
| PB-C50-S | 0 | M-B | 3600 | 0.3723417755 | 0.3568747399 | 0.01546703556 | O | 3570.5953 |
| PB-C50-S | 0 | ENS-C | 3600 | 0.3723417755 | 0.3579807999 | 0.01436097562 | O | 3571.8954 |
| PB-C50-S | 0 | P-GRB | 3600 | 0.4259500753 | 0.3492206958 | 0.07672937949 | O | 3583.0202 |
| PB-B50-U | 0 | P-GRB | 3600 | 1.176955759 | 0.06837938241 | 1.108576376 | O | 3572.991 |
| PB-B50-U | 0 | MB-D1 | 3600 | 0.677298419 | 0.4712348696 | 0.2060635494 | O | 3570.563 |
| PB-B50-U | 0 | M-B | 3600 | 0.6974735096 | 0.4553454 | 0.2421281096 | O | 3571.8624 |
| PB-B50-U | 0 | ENS-C | 3600 | 0.8325480152 | 0.4523603674 | 0.3801876478 | O | 3570.5731 |
| PB-B35-B | 1 | ENS-C | 2400 | 0.2345814099 | 0.1146410114 | 0.1199403984 | O | 2372.9734 |
| PB-B35-B | 1 | P-GRB | 2400 | 0.2797984344 | 2.027189664e-18 | 0.2797984344 | O | 2370.5117 |
| PB-B35-B | 1 | MB-D1 | 2400 | 0.2345814099 | 0.138322042 | 0.09625936783 | O | 2370.6168 |
| PB-B35-B | 1 | M-B | 2400 | 0.2465044704 | 0.0982245518 | 0.1482799186 | O | 2370.4896 |
| PB-C50-S | 1 | M-B | 3600 | 0.3723417755 | 0.357008334 | 0.01533344153 | O | 3572.6028 |
| PB-C50-S | 1 | ENS-C | 3600 | 0.3723417755 | 0.358161762 | 0.01418001348 | O | 3570.6597 |
| PB-C50-S | 1 | P-GRB | 3600 | 0.3917805586 | 0.3494508596 | 0.04232969893 | O | 3570.6723 |
| PB-C50-S | 1 | MB-D1 | 3600 | 0.3723417755 | 0.357008334 | 0.01533344153 | O | 3572.5642 |

<!-- R122_END -->

**Table 4. Directed-pair classifications by denominator.** All 48 individual records, including the nine LOSS/MIXED observations, are in Supplement S2.

<!-- PAIRS_START -->

| Seed | Denominator | Pair | WIN | LOSS | MIXED | TIE | UNEVALUABLE |
|---|---|---|---|---|---|---|---|
| 0 | 6 new problems | MB-D1/P-GRB | 5 | 0 | 1 | 0 | 0 |
| 0 | 6 new problems | M-B/P-GRB | 6 | 0 | 0 | 0 | 0 |
| 0 | 6 new problems | ENS-C/P-GRB | 6 | 0 | 0 | 0 | 0 |
| 0 | 6 new problems | MB-D1/M-B | 1 | 2 | 1 | 2 | 0 |
| 0 | 6 new problems | MB-D1/ENS-C | 1 | 2 | 1 | 2 | 0 |
| 0 | 6 new problems | M-B/ENS-C | 1 | 1 | 0 | 4 | 0 |
| 1 | 2 fixed repeats | MB-D1/P-GRB | 2 | 0 | 0 | 0 | 0 |
| 1 | 2 fixed repeats | M-B/P-GRB | 2 | 0 | 0 | 0 | 0 |
| 1 | 2 fixed repeats | ENS-C/P-GRB | 2 | 0 | 0 | 0 | 0 |
| 1 | 2 fixed repeats | MB-D1/M-B | 1 | 0 | 0 | 1 | 0 |
| 1 | 2 fixed repeats | MB-D1/ENS-C | 1 | 0 | 0 | 1 | 0 |
| 1 | 2 fixed repeats | M-B/ENS-C | 0 | 1 | 0 | 1 | 0 |

<!-- PAIRS_END -->

M-B/P and ENS-C/P each produce six WIN on the six new roles. This common complete-method advantage is the main positive empirical result. It includes both certificate gains and better finite-window open endpoints. The two fixed Seed1 repeats retain WIN against cold P for each integrated method, but add no independent problems. M-B versus ENS-C has one WIN, one LOSS and four TIE on new roles; over all eight blocks it has one WIN, two LOSS and five TIE. Thus the chosen paper reference does not dominate the unchanged default instance by instance.

On PB-C20-B, all methods have the same final physical value, approximately .2246803118. M-B, ENS-C and D1 certify, while cold P remains open. M-B takes 395.8595 production seconds and ENS-C 430.5576; their difference is below the declared materiality threshold. D1 takes 665.0688 seconds and loses both incremental certified-time comparisons. Cold P's open run supplies no ratio of times to optimality.

PB-B20-S gives the other certification case. All four methods certify approximately .8631523206. Cold P takes 116.0328 production seconds, compared with 2.6320 for M-B, 4.6224 for ENS-C and 2.6984 for D1. This case permits actual certified-time comparisons. The small integrated-method differences fall below the 30-second minimum materiality floor; the panel's TIE labels should not be mistaken for identical measured times.

The V35 cases expose tradeoffs. PB-C35-U is open for every method. M-B has better U and gap than cold P, yet loses to ENS-C because its final U and gap are worse at the material scale. D1/P is MIXED: its weaker physical endpoint accompanies a stronger lower endpoint and smaller gap. D1 loses to both M-B and ENS-C. These outcomes remain even though the complete integrated family improves over cold P.

On PB-B35-B Seed0, D1 has a better U than M-B and ENS-C but a sufficiently weaker lower bound and larger gap that both incremental pairs are MIXED. With Seed1, those two D1 comparisons become WIN, and M-B/ENS-C changes from TIE to LOSS. All remain open. These fixed repeats show meaningful sensitivity without authorizing selection of the better Seed.

PB-B50-U supplies the sole new-role material D1/M-B WIN: D1 improves both physical U and the lower endpoint relative to M-B, and also improves on ENS-C. It nevertheless remains open. PB-C50-S supplies common integrated gains without natural D1 installation at either Seed. Such an unexposed candidate result is still a valid complete-method observation; no extra probe is forced to manufacture mechanism exposure.

D1's five new-role exposures and its two V20 certificates do not satisfy the declared promotion requirement of at least two exposed new roles with an incremental M-B win or added certificate. Only PB-B50-U qualifies. The completed panel therefore retains the MIXED selection conclusion, with M-B as the existing paper reference and ENS-C as project default. D1 keeps research/ablation value. D0 is not a reserve selection, and the discontinued MB-PC development is not revived.

Historical evidence is used only to constrain attribution. Earlier paid-start/backend comparisons distinguish the value of an own feasible startup from backend representation changes; they do not justify assigning an integrated win to an unexposed row. Earlier D1 C2 Seed0 severe loss and later Seed1 gain, and the F2 D0 Seed reversal, remain separately scoped adverse observations. We do not combine their executables or windows with this panel to construct a formal acceleration factor.

The completed five-role historical paid-start layer is MIXED for both integrated methods against P-S, which pays the same complete H before the original compact backend. Some tailored results improve proof completion after matched startup, while other roles favor P-S. Rejected native positive bounds and surviving independent own-zero witnesses keep their separate evidence grades. That layer also spans different measurement policies and cannot yield a pooled exact speedup. The [finite attribution note](historical_attribution.md) identifies the concrete source reports and their limitations.

### 6.4 One known positive-objective long-window problem

The separate long-window study [@proof123] concerns PB-C50-S only, with 50 stations, four capacity-30 vehicles, physical \(T=10800\), solver Seed0, and three freshly paid 18000-second caps in the fixed order P-GRB, M-B, ENS-C. No previous route, bound, tree, basis or cutoff is loaded. The study adds zero independent problem samples and does not include D1.

Its station totals are \(\sum b_i=495\) and \(\sum D_i=562\). Empty departure and nonnegative return imply \(\sum Y_i\le495\); therefore \(\sum_i|Y_i-D_i|\ge67\). Positive lambda and weights give

\[
F\ge67\min_i(\lambda\omega_i/D_i)>0.
\tag{10}
\]

The prior exact-decimal explanation gives .24814831875, with a tighter inventory-only penalty floor .26064825 already documented. These are weaker than the published production bounds and are not injected into this method. Their purpose is to rule out an independent zero certificate for this role. No new inventory relaxation or route optimization is performed in preparing the paper.

**Table 5. One known-problem long-window study.** All three endpoints are reliable and open. No row is a time to optimality.

<!-- R123_START -->

| Method | Cap \(s\) | U | L | Signed gap | Certified | T_produce | T_verify | T_total |
|---|---|---|---|---|---|---|---|---|
| P-GRB | 18000 | 0.37764170855020796 | 0.35037793304081627 | 0.027263775509391686 | False | 17971.7112989 | 1.96611939999 | 17973.6774183 |
| M-B | 18000 | 0.3723417754990474 | 0.35801148555184259 | 0.014330289947204811 | False | 17970.5725766 | 40.964555 | 18011.5371316 |
| ENS-C | 18000 | 0.3723417754990474 | 0.35894366616771595 | 0.013398109331331454 | False | 17970.8751446 | 58.2420274 | 18029.117172 |

<!-- R123_END -->

Under the same fixed rule, M-B/P and ENS-C/P are WIN, and M-B/ENS-C is TIE. M-B improves U over cold P by .005299933051160555 and raises L by .00763355251102632; the signed gap decreases by .012933485562186875. ENS-C has the same final U as M-B and a .000932180615873357 higher L. The latter difference is below the pair's gap-materiality threshold. Arithmetic endpoint gains are not ratios of solver speed, and F* remains unknown.

M-B's final-quality fleet appears in the raw process record at 34.328 seconds; its qualified arm-availability upper time is 35.7173270817 seconds. No better own U is observed afterward. This does not establish that U is optimal, nor that all remaining work is pure proof. ENS-C has an early raw startup record at 34.312 seconds, but its clock-origin spread of 1.5845544376 seconds fails the predeclared one-second conversion check. Its four pre-end arm-clock checkpoints remain unknown. The sealed endpoint and separately measured QPC production/verification clocks remain qualified. We neither widen the guard nor compare those raw times as precise cross-method arm times.

The final coverage explains the outstanding proof rather than extrapolating from a plateau.

**Table 6. Actual final integrated-method covers.** “Empty” excludes improvement under the applicable cutoff; it does not assert unrestricted physical infeasibility.

<!-- COVER_START -->

| Method | Unit | True-G lower | True-G upper | Regional floor | State |
|---|---|---|---|---|---|
| M-B | L0.1 | 0.1861708877495237 | 0.3723417754990474 | 0.3723417754990474 | empty |
| M-B | L0.0.1 | 0.09308544387476185 | 0.1861708877495237 | 0.3723417754990474 | empty |
| M-B | L0.0.0.0 | 0 | 0.046542721937380925 | 0.35801148555184259 | open |
| M-B | L0.0.0.1 | 0.046542721937380925 | 0.09308544387476185 | 0.35882784229299913 | open |
| ENS-C | L0.1 | 0.1861708877495237 | 0.3723417754990474 | 0.3723417754990474 | empty |
| ENS-C | L0.0.1 | 0.09308544387476185 | 0.1861708877495237 | 0.3723417754990474 | empty |
| ENS-C | L0.0.0.0 | 0 | 0.046542721937380925 | 0.35894366616771595 | open |
| ENS-C | L0.0.0.1 | 0.046542721937380925 | 0.09308544387476185 | 0.36638496476834997 | open |

<!-- COVER_END -->

The low interval \(I_0=[0,.046542721937380925]\) and adjacent \(I_1=[.046542721937380925,.09308544387476185]\) remain unresolved. The final own \(G_{\rm true}=.050119584194518604\) lies in \(I_1\), so that fleet cannot provide an exact-g Start for \(I_0\). M-B makes seven LP and one MIP request; its \(I_0\) NEXT request uses about 17808.127 seconds. ENS-C makes nine LP and three MIP requests, including both interval targets and a subsequent low-interval terminal request. Child LP count and committed split count are different; counts do not establish retained native search trees or an internal cause of difficulty.

A fixed-endpoint counterfactual ledger illustrates why more than one obligation matters. Hold U and all other regional floors fixed. Raising only M-B's \(I_0\) floor to U leaves \(U-L_1=.013513933206048268\); closing only \(I_1\) leaves the global minimum at the old \(I_0\) floor. This follows from the union minimum in (9). It is not a prediction that a different leaf schedule would perform better, and does not justify launching another experiment.

All three normal long-window observations are complete, qualified open results. The finite study records a proof limit, not an execution failure. The longer cap ends here. There is no final certification-time ratio, linear remaining-time prediction or automatic extension until a certificate appears.

## 7. Discussion, limitations and reproducibility

The strongest supported empirical statement is complete-method advantage over cold P-GRB for the particular original model and matched finite budgets in the prospective panel. That comparison is meaningful because the physical problem, input and full production costs are common. It does not establish state-of-the-art superiority against all algorithms solving this same physical model. Neighboring published methods differ in target feasibility, visits, depot supply, time treatment or objective. A matched adaptation would require its own justified design and validation.

The method's exact representation also has a precise scope. Implicit quantity integrality follows from the remaining integer decisions and unique one-way service. Its proof would fail under split service even if the same variable names were retained. Inventory-product exactness is an integer embedding property, while the SP estimator is a continuous relaxation. Local native success is usable globally only through cutoff complementation and full coverage. These distinctions identify what must be rederived before extending the model.

Certification is more limited than feasible-solution improvement. On the primary panel, all nonzero certificates occur at V20 and every V35/V50 outcome is open. The known V50 long study keeps two integrated-method improvement obligations. This does not prove that V50 is intrinsically intractable or that no larger instance can certify; other historical cases remain valid in their own scope. It does rule out describing the present evidence as stable certification of all instances up to 50 stations.

H and the exact backend have complementary roles. H rapidly finds an effective physical fleet on the long role; its unchanged U leaves uncertainty about both primal suboptimality and lower-bound shortfall. Native MIP work dominates the recorded large-instance cost, but its internal search/proof allocation is not fully observable. The incompatible low-interval Start is a geometric fact about true Gini, not proof that all difficulty is primal. Inventory/ratio attainability and full fleet-route attainability must be distinguished before proposing an additional mechanism.

The numerical guarantee should be read literally. Qualified bounds and certificates use the frozen floating-point evidence policy, including the explicitly numerical closure guard. Exact coefficient arithmetic and physical replay support specific algebraic and witness checks; they are not an a posteriori rational certificate for every native optimization operation. The available evidence reveals no new same-domain counterexample, but the policy supplies no global accumulation theorem merely from the relative sizes of two tolerances.

Generalization is constrained by the experimental design. Six non-IID problems from two station tables are not six independent cities. Station overlaps are recorded, and source, size, inventory regime, geometry, fleet and time vary together. The two fixed Seeds expose sensitivity but cannot estimate a population probability. There is no best-of-Seed endpoint or instance-wise winner dispatcher. The tested lambda value and varying total weights do not establish robustness across tradeoff preferences. Objectives and time scales should therefore be reported per role.

Real station coordinates do not make the constructed inventories operational observations. Targets are not inferred service-level guarantees, the depot is synthetic, and Euclidean travel ignores the road network and traffic. The static model excludes concurrent customer demand and permits only the stated service semantics. Demographic fairness, station access, realized availability, staff workload and revenue would each need their own data and objective interpretation. The title's ratio dispersion should not be read as an empirical equity outcome.

The manuscript preserves unfavorable scientific evidence while moving engineering detail to its supporting files. Supplement S retains all 32 arms and 48 pairs, all three clocks, the three long endpoints and checkpoint unknowns. The original final-fleet endpoint is retained in the Seed1 cold-P case where an earlier legal witness was slightly better; its verification recovery and waiting costs remain in \(T_{\rm verify}\). This distinction prevents changing an endpoint after observing its trajectory.

Reproduction has two levels. The frozen published campaigns retain detailed native source/call/model/return and fleet evidence [@benchmark122; @proof123]. R124’s separate small dependency set supported three complete long-study endpoint replays and all 51 directed-pair classifications. This revision preserves its published tables byte for byte and adds a compact method-check package: rational inequalities, sampled saved matrix rows, finite decision states and declared H-move replay. It does not repeat the full historical reconstruction. It does not claim a fresh native replication or revalidation of every historical matrix row. Exact input/software identities and the separate review scope are supplied in the reproducibility notes and review record.

The appropriate next action is substantive academic assessment of this bounded contribution. The paper is organized so a reader can judge whether the physical modeling choice, specific integration and finite evidence are scientifically useful, and whether one additional matched comparison or sensitivity question is essential. The present open proof alone supplies no mandate to resume solver time or invent another numbered component.

## 8. Conclusion

We have described a complete tailored method for static multi-vehicle redistribution with inventory-to-target ratio dispersion and relative target deviation. The formulation preserves the original routing, service, load and time semantics. Integer inventory states support exact products, and unique one-way service explains why M-B can relax quantity declarations. A complete scoped proof cover explains how returned native information can support an original-problem numerical bound.

The prospective two-source evidence shows six new-role wins against the cold original model for both M-B and ENS-C, alongside material tradeoffs between them. Nonzero certification remains confined to the panel's 20-station problems. A separate known 50-station long window improves endpoints relative to cold P but leaves every method open and exposes multiple remaining regional obligations. These results support finite-window usefulness and a concrete certificate boundary, without universal speed or operational equity claims.

The frozen M-B method is the paper reference; ENS-C remains the implementation default, and the completed D1 comparison is not reopened. The immediate research decision is to obtain academic feedback on the complete bounded account. Any subsequent experiment requires a specific falsifiable question and separate authorization.

## References and supporting material

The thirteen citation entries are in [references.bib](references.bib). Access level, DOI, source URL, checked sections and limits are recorded in [literature_evidence.csv](literature_evidence.csv) and [literature_scope.md](literature_scope.md). The complete mathematical specification is [Appendix A](model_appendix.md). [Supplement S](tables/complete_results.md) is inherited unchanged from R124’s published arithmetic derivation; the present finite check script validates the new method examples. [Reproducibility notes](reproducibility.md), [research decision](research_decision.md), and [review actions](review_actions.md) keep source identity, readiness and actual review scope separate from the scientific results.
