# GI-TBC: a Gini-interval tailored branch-and-cut algorithm for equitable bicycle redistribution

## Abstract

Static bicycle redistribution couples inventory equity to routes with empty departures, prefix capacity and paid handling, including loaded returns. GI-TBC connects shared inventory states, movement and nonzero visits to objective products, then combines own feasible startup with complete true-Gini interval coverage. The breadth panel gives 9/12 certificates versus 7/12 for each compact control; a positive-resource panel gives 4/8 versus 0/8. Seed checks retain open and adverse endpoints. Compact and conditional state representations distinguish preserved information from complete computational efficiency. Verified fleet archives and global lower bounds yield continuous-weight guarantees: one fixed fleet stays within an absolute objective tolerance of 1.00002e-7 over its covered range. Two-sided route-time bounds establish strict optimal-objective improvement even where optimal routes remain unproved, while large-instance improvement magnitudes remain uncertain. These finite results support the integrated exact method and bounded transportation decisions; the controls leave the independent speed benefit of external interval scheduling unresolved.

## 1. Introduction and related work

Redistribution vehicles can improve station availability only when the chosen inventory vector can be realized by feasible routes and loading operations. Supply must be collected before it is delivered, capacity applies at every route prefix, and handling consumes the same time budget as travel. When equity is measured by inventory-to-target ratios, the final inventory vector also determines both the numerator and denominator of the Gini coefficient. These dependencies make routing and inventory allocation inseparable.

We study static bicycle redistribution with empty vehicle departure, loaded return, and at most one nonzero one-way service at each station. The objective combines inventory-to-target ratio-Gini dispersion and weighted relative target deviation. The operational model and HGA-TGBC heuristic framework originate in the available same-problem author manuscript [@hgaTgbcManuscript]. Our exact method reuses its decoder within a finite startup procedure and supplies the bounds and complete coverage needed for certification.

The research question is how a common inventory representation can connect allocation and routing, support a complete exact method, and yield decisions whose quality can be bounded. Three connected contributions address it. First, a shared stock state represents the objective product, absolute movement and nonzero visits. Under the inherited unique one-way service rules, integer stock implies integer service quantities. We characterize the joint local graph: at most five legal stock supports preserve its continuous convex hull, while a separate absolute-stock binary-product layer preserves integer exactness. The resulting common LP projection survives embedding only when all other state uses pass through the declared interface. This identifies both a compact representation and its precise boundary.

Second, GI-TBC combines inventory/service connections and physical valid inequalities with an own feasible startup and complete true-Gini interval control. Objective-preserving physical extensions, cutoff complements and complete region coverage establish correctness. The implementation supplies the full method, including exact continuation at depth/width guards. Custom valid rows are static; Gurobi performs branch-and-cut inside each canonical model. P, own-start PS, strengthened root-only control, complete B and the separate proof extension answer different formulation, startup and architecture questions. The compact representation is evaluated as the separately named C166 candidate; the conditional network discussed below remains an offline representation prototype.

Third, computational evidence and certified decision analysis use both feasible fleets and qualified problem bounds. The complete package improves finite certificate counts over the specified compact controls, with adverse endpoints and open cases retained. An offline archive of fully reconstructed physical fleets yields feasible upper envelopes and concavity-based lower bands over continuous objective-weight intervals. Controlled route-horizon pairs yield two-sided bounds on the improvement in the optimal objective, including pairs where neither optimum is certified. These decisions concern inventory-to-target ratio dispersion and target deviation. They do not imply demographic fairness, monetary benefit, a complete Pareto frontier or an independent speed gain from the outer controller.

### 1.1 Relation to previous work

Static bike redistribution has been studied under several target, service and vehicle conventions. Raviv et al. develop static repositioning models; Chemla et al. study static rebalancing; Erdogan et al. address demand intervals and an exact rebalancing algorithm [@raviv2013; @chemla2013; @erdogan2014; @erdogan2015]. Schuijbroek et al. connect inventory requirements to routing [@schuijbroek2017]. Forbidden temporary operations, repeated visits, robust inventory requirements and demand-interval disjunctions give related but different feasible sets [@bruck2019; @bulhoes2018; @bruck2025; @ikonen2025]. The HGA-TGBC manuscript is the direct same-problem antecedent; the other studies supply routing and formulation context rather than matched performance baselines.

Station-ratio dispersion measures a different object from vehicle-workload equity [@matl2018]. Qiao et al. balance task durations in a coordinated two-echelon rebalancing framework [@qiao2026]. Caggiani et al. consider free-floating electric micromobility, battery swapping and a modified Gini measure involving availability and state of charge, with zonal fair targets [@caggiani2026]. These equity measures concern different service objects and operational decisions from the station inventory ratios studied here. Here zero Gini means equal proportional station inventory, which can still represent inadequate stock. The deviation term separately rewards approaching targets.

Exact fixed-route loading has established precedents. Erdogan et al. formulate a minimum-cost network for their single-vehicle demand-interval model, including handling costs [@erdogan2014, section 2]. Szeto and Shui derive loading strategies under demand-dissatisfaction and service-time priorities, with empty depot returns [@szetoShui2018, sections 2–3]. Those objectives and depot rules differ from the present globally coupled Gini and target-deviation objective with paid loaded returns; their results do not imply vehicle-wise separability or greedy optimality here.

McCormick envelopes and convex epigraphs are standard tools [@mccormick1976; @boydVandenberghe2004]. Gupte et al. study unary/binary reformulations and relaxations of integer-continuous single-product sets [@gupte2013]. Köppe et al. develop finite block values, linking polyhedra and an aggregate representation [@koppe2008]. Our connection is the use of one final-stock state across the objective, absolute movement and nonzero-service indicator, within this physical routing problem. Embedding and piecewise-linear formulations provide established endpoint, encoding and convexification tools [@vielma2018embedding; @huchetteVielma2023]. Our compact result applies these tools to the jointly visible movement, visit and product functions, including their discrete service jump, and establishes the interface needed to embed the replacement. Neither binary expansion, finite disjunction, endpoint convexification nor spatial partitioning is claimed as new. The state-penalty comparison in Supplement S6 applies Jensen's inequality and a direct projection construction; the complete route model is not the hull of an isolated product block.

The distinction matters to an operator choosing a fleet plan and to a researcher choosing an exact representation. A stock mixture that supplies a strong root bound may cease to explain the service mixture after some encoding decisions have been fixed. Conversely, a representation that preserves more such information can require more continuous variables and conservation rows on the capacities encountered in practice. We therefore state exactly which information each formulation preserves, then assess its observable computational consequences. The decision analysis uses those fleets and bounds to assess extra route time or changed objective weights even while optimal routes remain unknown.

## 2. Problem and shared-state formulation

### 2.1 Physical semantics and objective

Let \(N\) contain \(n\) stations and let \(0\) be the depot. Station \(i\) has integer initial inventory \(b_i\), capacity \(C_i\), positive target \(D_i>0\), and weight \(\omega_i\ge0\). Vehicle \(k\) has capacity \(Q_k\) and route-duration limit \(T\). Routes depart empty. A station can be served by at most one vehicle, in one direction, with a nonzero operation. Loaded return is allowed and its unloading time is counted. The depot enters neither target deviation nor dispersion.

The computational text format stores integer targets. All present test targets also satisfy \(D_i\le C_i\), a data convention rather than an additional physical constraint; the inventory capacity bounds apply to \(b_i,Y_i\).

With pickup \(p_{ki}\) and delivery \(d_{ki}\),

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\qquad
R_k=\sum_i(p_{ki}-d_{ki})\in[0,Q_k],\qquad
\sum_iY_i=\sum_i b_i-\sum_kR_k.
\]

Thus total final station inventory is bounded above by \(B=\sum_i b_i\), rather than fixed at \(B\). Vehicle capacity limits the instantaneous prefix load, rather than cumulative pickup. If pickup and unloading/delivery take \(t_p,t_d\) per unit, complete handling time is

\[
t_p\sum_i p_{ki}+t_d\left(\sum_i d_{ki}+R_k\right)
=(t_p+t_d)\sum_i p_{ki}.
\]

Travel plus this quantity cannot exceed \(T\). The tested distance convention is Euclidean travel time from serialized metre coordinates at 1.5 m/s. Inventory, route, assignment, direction and prefix-load logic retain their original integer domains. Continuous pickup/delivery variables preserve the integer physical operations because unique one-way service and integer \(Y_i\) fix the sole inventory difference. Appendix A gives the complete formulation and embedding proof.

Define

\[
r_i=Y_i/D_i,\quad S=\sum_i r_i,\quad
A=\sum_{i<j}|r_i-r_j|,\quad
P=\sum_i\omega_i|r_i-1|,
\]
\[
G=\begin{cases}A/(nS),&S>0,\\0,&S=0,\end{cases}
\qquad F=G+\lambda P,\quad\lambda\ge0.
\]

This is ratio dispersion and two-sided relative target deviation. It is not a direct measure of population equity, rental failure or travel burden. Put \(\Omega=\sum_i\omega_i>0\), \(P_{\rm avg}=P/\Omega\) and \(\rho=\lambda\Omega\). Then \(F=G+\rho P_{\rm avg}\). The generator normalizes weights by their maximum, so equal \(\lambda\) across inputs does not hold \(\rho\) fixed. The breadth panel retains this convention; the resource panel fixes \(\rho=1\), and the weight study varies \(\rho\) within fixed physical configurations.

For positive total shortage \(s=\sum_iD_i-\sum_ib_i>0\), positive weights and \(\lambda>0\) (equivalently \(\rho>0\)), let \(a=\min_i\omega_i/D_i>0\). Nonnegative loaded return yields

\[
P\ge a\sum_i|D_i-Y_i|\ge a\left|\sum_iD_i-\sum_iY_i\right|\ge as,
\qquad F\ge\lambda as=\rho as/\Omega>0.
\]

We use this established stock-shortage construction to guarantee positive objectives in the resource study, without filtering on observed difficulty. It does not guarantee a binding route horizon. With all other physical and objective data fixed, \(T_1\le T_2\) gives \(X(T_1)\subseteq X(T_2)\) and \(F^*(T_2)\le F^*(T_1)\). Finite-budget primal/dual endpoints and runtimes need not be monotone.

### 2.2 A shared inventory, service and product state

For the legal finite inventory domain \(\mathcal Y_i\), binary selectors \(s_{iy}\) and continuous \(q_{iy}\) represent stock and products on a Gini interval \([\alpha,\beta]\):

\[
\sum_y s_{iy}=1,\quad Y_i=\sum_y ys_{iy},\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
\sum_yq_{iy}=g,\quad Z_i=\sum_y yq_{iy}.
\]

At an integer state, \(Z_i=gY_i\). The objective epigraph uses

\[
H_{ij}\ge r_i-r_j,\quad H_{ij}\ge r_j-r_i,\qquad
e_i\ge r_i-1,\quad e_i\ge1-r_i,
\]
\[
\sum_{i<j}H_{ij}\le n\sum_i Z_i/D_i,\qquad
\min f=g+\lambda\sum_i\omega_i e_i.
\]

For \(S>0\), integer state selection makes the numerator inequality imply \(g\ge G_{\rm true}\), so every integer completion satisfies \(f\ge F_{\rm true}\). Conversely a physical fleet assigned to its true-G interval has an objective-preserving extension: select its final inventories, set \(g=G_{\rm true}\), set each selected \(q_{iy}=g\), and use the true absolute differences and deviations. At \(S=0\), all ratios are zero and \(g=0\) supplies the physical extension. Valid domain and strengthening rows retain that extension, as established in Appendix A.

Let \(z_{ki}\) be the binary service assignment. The same state supports the service equations

\[
\sum_kp_{ki}=\sum_y(b_i-y)^+s_{iy},\quad
\sum_kd_{ki}=\sum_y(y-b_i)^+s_{iy},\quad
\sum_kz_{ki}=\sum_{y\ne b_i}s_{iy}.
\]

These links connect objective mixtures to movement and service. They are not the convex hull of all vehicle routes. In isolation, a finite-state product block with the same extreme stock bounds projects to the McCormick rectangle: its four corner graph points give one inclusion, and every state line lies in the rectangle hull, giving the other. An advantage must therefore come from the links, domain information or complete search, rather than the VD-P label alone.


**Lemma 1 (implicit service integrality).** Suppose initial and final inventories are integer, a station is assigned to at most one vehicle, and a binary direction permits either pickup or delivery at its unique service. Continuous pickup and delivery variables then take integer values at every integer solution of the remaining model.

**Proof.** An unassigned vehicle has zero quantities. At the unique assigned vehicle, pickup direction fixes delivery to zero, so inventory balance gives \(p_{ki}=b_i-Y_i\). Delivery direction fixes pickup to zero and gives \(d_{ki}=Y_i-b_i\). Each is integer. Integer load variables are unnecessary for this implication. The claim concerns integer feasible solutions; it does not equate the continuous relaxations of alternative formulations. \(\square\)

For an integer service, total movement is \(|b_i-Y_i|\), and nonzero one-way service occurs exactly when \(Y_i\ne b_i\). Hence the shared equations above reproduce the original operations without changing the physical problem. They also couple fractional inventory mixtures to the movement and visits that must support them.

### 2.3 What compact supports preserve

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

Continuous breakpoint weights and integer \(Y_i\) alone do not enforce the product, and binary breakpoint weights would delete legal interior stocks. B keeps its original \(e_i\) epigraph, so target deviation is not an additional shared-state function here. Exact state penalties, threshold counts and vehicle-state assignments need their own common pieces; holed integer membership must be retained by an explicit code or legal paths. The candidate C166 applies only this representation change, with the full B lifecycle and own startup. Equal raw LP projections do not imply identical presolve cuts, branch decisions or complete costs.

### 2.4 Preserving conditional code information

Preserving the physical hull does not preserve its relation to a separately chosen inventory code. Let \(c(y)\) be the absolute base-2 code with \(d=\max\{1,\operatorname{bit\_width}(C)\}\), and augment the joint graph by \(\delta=c(y)\) and \(w=gc(y)\). Denote its convex hull by \(E(D)\), where \(D=[l,u]\cap\mathbb Z\). For fixed digits \(a_h\), put \(D(F)=\{y\in D:c_h(y)=a_h,\ h\in F\}\). For \(D=\{0,\ldots,4\}\), \(b=2\), \(g\in[0,1/2]\), fixing \(\delta_0=1\) leaves stocks \(\{1,3\}\), hence movement and visits both equal one. C166 instead permits \(Y=2,M=V=0,g=1/4,Z=1/2\), with \(\delta=(1,1/2,0)\), \(w=(1/4,1/8,0)\). Its stock support chooses only the initial state while its independent code layer uses a different mixture.

**Proposition 1 (conditional joint representation).** A fixed MSB-first interval DAG, separated into donor, initial and receiver pieces, represents \(E(D)\) with \(O(1+\log(C+1))\) columns, rows and nonzeros. On the same edges let

\[
Af=e,\qquad Aq=ge,\qquad f\ge0,\qquad \alpha f\le q\le\beta f.
\]

Here \(e\) is unit source-sink balance. Path costs reconstruct \(Y,M,V\) from \(f\), \(Z\) from the same \(q\), and every code/product digit from the corresponding bit-one edges. Fixing any subset of absolute digits gives exactly \(E(D(F))\), with physical projection \(H(D(F))\).

**Proof sketch.** Tightness to interval bounds uses at most four states per bit layer; each legal stock has a unique complete path. For \(\alpha<\beta\), the nonnegative conserved flows \((\beta f-q)/(\beta-\alpha)\) and \((q-\alpha f)/(\beta-\alpha)\) decompose into legal paths at the two Gini endpoints. At \(\alpha=\beta\), use \(q=\alpha f\) directly. A fixed digit removes inconsistent paths by nonnegativity. Appendix A.11 gives both directions, integer exactness and the embedding condition. \(\square\)

The enumerated same-code reference R_abs retains every continuous stock/product weight and explicitly links its absolute digits; historical LOG uses the offset \(y-l\). D167 matches R_abs's enhanced projection and can strictly strengthen conditioned C166. The unconditioned physical projections coincide. Network-flow and disjunctive convexification are established tools [@behle2007; @balas2005; @muldoon2013]; the contribution here is their joint stock/service/product application and conditional boundary. The guarantee concerns these digit fixes, not arbitrary Native branches, a full routing hull or the historical cause of C166's search cost.

## 3. The complete GI-TBC method

### 3.1 Physical strengthening

Let \(\tau\) be metric travel time and \(h=t_p+t_d\). For each receiving station \(j\), define

\[
\mathcal C_{kj}=\{i\ne j:\tau_{0i}+\tau_{ij}+\tau_{j0}+h\le T\}.
\]

**Proposition 2 (ordered supply compatibility).** Every physical fleet with empty departure satisfies

\[
d_{kj}\le\sum_{i\in\mathcal C_{kj}}p_{ki}.
\]

**Proof.** Label the units collected by a vehicle. In route order, match each delivered unit to an earlier collected unit that has not yet been delivered. Nonnegative prefix loads guarantee such a match. A unit delivered at \(j\) from source \(i\) entails the ordered subsequence \((0,i,j, 0)\), whose travel lower bound follows by metric shortcutting. Collecting at least that unit incurs handling of at least \(h\), including delivery or final unloading. Thus its source lies in \(\mathcal C_{kj}\). Counting distinct matched units proves the inequality. Unmatched collected units can return to the depot. \(\square\)

For a set \(W\) of served stations, let \(\tau(W)\) be the shortest depot tour through \(W\), computed by explicit orders for pairs or triples. Write \(P_k^{\rm pick}=\sum_i p_{ki}\). Nonzero integer service and empty departure give

\[
|W|\le\sum_{i\in W}(p_{ki}+d_{ki})\le2P_k^{\rm pick},\qquad
P_k^{\rm pick}\ge\lceil |W|/2\rceil.
\]

Consequently \(\tau(W)+h\lceil|W|/2\rceil>T\) rules out serving all of \(W\) with that vehicle. Otherwise a conditional duration inequality combines the tour lower bound and pickup handling. Supply for \(W\) may come from outside \(W\); cumulative pickup is not bounded by \(Q_k\). Appendix A gives the exact conditional coefficients, deactivation proof and finite selection rule. GI-TBC keeps pair support uniformly and omits triple support. These rows strengthen necessary physical conditions without replacing route-prefix capacity.

### 3.2 Own startup and complete interval coverage

The startup \(H\) is a finite construction and descent procedure. It completes a joint insertion and 24 shuffled station/separator orders plus a constructive order, fully decodes them, applies guided first-improvement descent, and closes physical quantity/insertion and neutral balanced/exchange moves. The active path has no genetic generations. It provides a verified feasible upper bound and a possible MIP Start; it is never credited with a positive lower bound. Each GI-TBC and paid-start compact run pays for its own complete \(H\).

The controller starts from the complete potentially improving domain \([0,\min\{U,(n-1)/n\}]\). It maintains incumbent epoch, valid cutoff complements and complete interval coverage. A local bound is used only for its model, interval, cutoff and qualified source. Split children replace a parent atomically only after complete coverage and both results are checked. NEXT and child-target values are requests, rather than proof that a milestone was reached.

For finite valid child bounds \(\ell_0,\ell_1\), parent floor \(b\) and own incumbent \(U\), AM uses

\[
\Delta=\max\{U-b,\max(\epsilon,10^{-12})\},\quad
v_j=\operatorname{clip}_{[0,1]}((\ell_j-b)/\Delta),\quad
S_{\rm AM}=\min(v_0,v_1)(v_0+v_1)/2.
\]

The fixed threshold is .08. Infeasible children invoke logical coverage independently; invalid evidence cannot justify a split. The score estimates normalized two-sided bound progress, not remaining proof cost. Appendix B gives eligibility, tolerances and continuation semantics.

~~~text
Algorithm 1  GI-TBC (B)
Input: physical instance, lambda/weights, common deadline; fixed .08 AM rule,
       depth 8, minimum width 1e-4, numerical policy epsilon=1e-7.
Output: verified own fleet, physical U, qualified L, CERT or OPEN and cover.
1 Complete own H and verify the fleet; initialize U and incumbent epoch e=0.
2 Cover [0,min(U,(n-1)/n)] (also [0,0]); retain independent global floor 0.
3 While a relevant open region exists and the common deadline permits:
    select on the minimum-bound plateau, cycling widest-first (B.2);
    rebuild its canonical model at current epoch/cutoff c=U when necessary;
    qualify its complete LP and merge its applicable same-region floor.
    If proved infeasible or fathomable: retain the scoped closure; else:
      apply NEXT: requeue if noncontrolling, or request a parent-MIP target
      equal to the next strictly larger open-region bound (B.3);
      if NEXT permits lookahead and depth/width permit, solve both child LPs;
      split atomically if either is infeasible or the finite AM rule passes;
      otherwise request parent MIP to the valid child minimum when strict;
      if guarded or without strict child improvement, run full parent MIP.
    After each Native return, finalize/qualify its actual bound and source;
    verify fleet improvements, update U/epoch and invalidate stale artifacts;
    install both covering children, retain a scoped closure, or requeue the
    parent according to the returned evidence (ProcessLeaf, Appendix B.0).
    Recompute the full-cover minimum including cutoff-complement floors.
    On TimeLimit retain unresolved coverage; on failed qualification stop.
4 FinalizeAndUpdateCover retains every unresolved obligation (Appendix B.0).
  If native proof is rejected, final qualification restores the unresolved
  physical domain and independent floor 0; no dependent proof is credited.
5 Release Native resources; finalize the selected fleet's physical check.
  Apply the independent exact-zero rule or qualified full-cover gap rule;
  complete required output and return CERT, otherwise OPEN with its bounds.
~~~

**Proposition 3 (coverage).** In ideal arithmetic, a controller that preserves complete improving-domain coverage, retains valid bound/cutoff complements and closes a region only by an applicable proof provides a valid global lower bound. If it closes all relevant regions against a verified \(U\), it proves optimality to its declared certificate margin.

**Proof.** Every improving physical solution belongs to the root domain because \(F\ge G\) and \(G\le(n-1)/n\). A valid interval restriction and cutoff cover its regional solutions; the cutoff complement has floor equal to that cutoff. A complete split preserves the union. Taking the minimum over the valid regional floors and complements therefore bounds every physical solution from below. Closure against \(U\) eliminates every possible improvement to the margin. Revoking a source requires removing every conclusion that depends on it; an independent full-domain bound remains valid. \(\square\)

The scheduler accumulates same-unit bounds monotonically. Its final qualification rejects affected Native proof dependencies and restores the unresolved physical domain; Appendix B.4 distinguishes that conservative fallback from ideal source-revocation accounting. Numerical qualification and lifecycle evidence are required in addition to the ideal coverage proof.

The depth and width guards limit extra partitioning, then retain a full parent MIP continuation. In ideal arithmetic, complete terminal solutions on the bounded integer domains and valid coverage yield the corresponding finite proof. Under the actual common deadline an unresolved terminal obligation returns OPEN; the guards themselves establish no certificate.

### 3.3 A separately paid proof enhancement

The frozen enhancement E+ augments GI-TBC/B with an independently computed,
qualified inventory lower bound. It uses the run's own first canonical root,
actual supported inventories and valid final-stock total bounds. On an
epigraph interval \([\gamma_L,\gamma_U]\), its objective and domain are

\[
 \min_Y\;\max\{\gamma_L,G_{\rm true}(Y)\}
       +\lambda\sum_i\omega_i|Y_i/D_i-1|,
 \qquad G_{\rm true}(Y)\le\gamma_U.
\]

The lower interval endpoint constrains the epigraph; it does not impose
\(G_{\rm true}\ge\gamma_L\). At \(S=0\), \(G_{\rm true}=0\).
The inherited exact hard-total dynamic program and one uniform RN16384
producer retain their original absolute price gap, zero/fallback handling,
scope qualification and global deadline. This is an application of established
integer-inventory, normalization and proof-ledger techniques, not a new general
fractional-programming or convex-hull theorem.

Only an applicable proof ledger consumes the returned floor. Formal Native
rows, raw AM bounds, hints, Starts and branching inputs keep their intended B
design. On a common domain, independent bounds combine by maximum; complete
covering regions combine by minimum, including each source's cutoff
complement. Helper rejection supplies no new floor and retains the independent
B information. Every E+ run pays its own H, root, DP/RN work and qualification.
That cost changes remaining search time, and legitimate early certification
can change the finite trajectory. Preserving the formal expression therefore
does not guarantee identical B/E+ physical incumbents or solve times.

The supplement identifies the C++ complete method and historical Python helper separately. E+ is uniform, independently paid and evaluated only in its registered runs; B/P Seed repetitions do not retest it.

The validity of an inventory lower source and its net complete-method value are separate questions.

### 3.4 Numerical qualification, costs and termination

The complete clock starts before own startup and includes import, construction, all Native calls, online physical/numerical qualification, cleanup and required output. Required later verification is recorded separately; nested writer, helper, Runtime, Work and node counters explain this work and are not added again. Physical route horizon \(T\) and computational cap are distinct. The registered caps are 600/1200/2400 s by size. An OPEN observation has no certificate time, and its budget never substitutes for convergence. On the intersection where both methods qualify certificates, a paid-time difference is substantive when at least \(\max\{10\text{ s},.1\times\text{faster time}\}\).

All main runs use Gurobi 13.0.2, one thread and fixed processor affinity on an Intel i7-12700KF Windows host. Requested relative and absolute MIP gaps are zero; NodeLimit is unlimited and Native strategies retain their defaults. Solver tolerances are \(10^{-6}\) feasibility/optimality and \(10^{-5}\) integrality, with the separate \(10^{-7}\) project certificate/equivalence policy. A numerical proof source must match the actual input, objective, domain, interval, cutoff and model identity and pass the applicable primal/bound/physical-consistency gates. Raw LP values mean all integer types were relaxed before optimization; MIP-root values after cuts are a different observation. The implementation's qualification and conservative source-rejection fallback are specified in Appendices A.7 and B.4.

Feasible endpoints always come from a complete independently checked fleet evaluated with the original objective, including true Gini, all inventory balances, empty departure, every load prefix, nonzero one-way service, loaded return and unloading. A returned native objective with inflated epigraph auxiliaries cannot replace that evaluation. A bound restricted to one interval or cutoff does not certify the full physical problem until combined with all coverage and complement obligations. Source rejection removes the dependent certificate, while a sufficient independent zero proof remains available. Rounded display values are never reimported as physical witnesses or exact bounds.

**Independent zero termination.** Under the stated nonnegative objective premises, a complete physically verified fleet with exact objective zero is globally optimal, independently of the native search source.

**Proof.** For every original physical solution, \(F\ge0\). The verified fleet gives \(F^*\le0\), so \(0\le F^*\le0\). With positive \(\lambda\) and positive weights, integer equality \(Y_i=D_i\) for every station is a sufficient exact-zero condition. More generally equal exact ratios give zero Gini, and every positive-weight penalized station must meet its target. The implementation checks these conditions using integer stock arithmetic, then repeats the complete physical-fleet verification. A merely small positive floating objective does not establish exact zero. \(\square\)

The numerical \(\varepsilon\)-certificate policy is separate. A source-rejected positive solution without a sufficient independent bound remains open. Certification cost includes the verification needed to establish the proof, normal native cleanup and required output. A later offline audit cannot backdate a production proof.

## 4. Computational evidence

### 4.1 Comparators and registered evidence

The comparators isolate different questions. P is the independent cold compact model. PS recomputes and pays complete own H, then supplies only its own fleet to that model. The strengthened root-only control keeps shared states, physical rows and own startup, and solves the unsplit root using Native branch-and-cut; B adds the complete external control package. B/P and B/PS therefore compare integrated methods, whereas full/root tests the additional controller package. E+/B tests a separate paid proof source. C166/B changes the representation within the same complete B lifecycle. R_abs/C166/D167 below compare offline conditional LP expressions and do not supply new complete-method observations. No solution, bound, tree, Start or free helper crosses methods, Seeds, weights or physical configurations. Same solver Seed is a shared setting, not an identical random trajectory.

Each panel retains its own denominator. Matching AM/mechanism/resource/weight baselines refer to one historical record, counted once. Additional Seeds and representation tests on the later six configurations are exposed-input repetitions. Resource pairs change only T; each weight family retains one physical feasible set.

The fixed-source protocol was committed before once-only generation. Six known roles and six new draws form a twelve-input breadth panel (four each at \(n\in\{15,20,35\}\)); CITI, CABI and Divvy supply archived station geometry/capacity. Ten new draws in total include four additional shortage bases at \(n\in\{20,35\}\), each paired at two transparently designed route horizons. Targets, initial stock, weights and depot are synthetic or transformed; this is not observed demand, a new source, or independent population sampling. Every selected source row and serialized input is disclosed.

Breadth retains \(\lambda=.15\). Resource pairs fix \(\rho=1\) and alter only T; the two extra weight levels \(\rho\in\{.5,2\}\) reuse the matching \(\rho=1\) baseline at two preselected physical configurations. AM and mechanism defaults share only exactly matching input/T/weight/Seed/cap/configuration runs. The earlier main panels use Seed 0; four preselected full-method triplets and small overlapping AM/mechanism blocks use Seed 1. They are finite repeated observations, not independent new inputs or an estimated runtime distribution. The later six-input archived-source cohort uses Seed0 for its B/E+/P comparison and Seeds1/2 for the complete B/P confirmation in §4.3. The 24 additional Seed commands use the exposed six-input cohort.

For each new resource base, let \(d_{\max}\) be its maximum serialized station-to-depot distance and \(M\) its vehicle count. Before optimization, the route horizons were fixed by

\[
\begin{aligned}
T_{\rm base}&=2d_{\max}/1.5+120\sum_{i\in N}\max(b_i-D_i, 0)/M,\\
T_1&=300\left\lceil\frac{\max(1800,.75T_{\rm base})}{300}\right\rceil,\\
T_2&=300\left\lceil\frac{1.5T_1}{300}\right\rceil.
\end{aligned}
\]

This input-based rule uses geometry, initial stock, targets and fleet size; it supplies neither a binding-horizon guarantee nor an outcome-dependent difficulty filter. The weight study preselects R-B20-S-T1 and R-X35-S-T2. Within each T pair, every datum except T is identical.

**Table 1. Registered studies, observations and shared defaults.**

| Study | Configurations / observations | Purpose |
|---|---|---|
| Breadth | 12 physical inputs / 36 method runs | Sources, stock regimes and scales |
| Positive-resource pairs | 4 bases, 8 physical configurations / 24 method runs | \(\rho=1\), guaranteed positive objective |
| Weights | 2 physical configurations, 2 extra rho levels / 12 method runs | Relative method dependence on objective weight |
| AM | 4 roles, 2 extra thresholds / 8 method runs | Observed gates/actions and complete cost |
| Mechanisms | 4 roles, 4 contrasts / 16 method runs | Conditional formulation/control effects |
| Earlier second Seed | 12 main+4 AM+8 mechanism runs | Preselected limited repeat check |
| Archived-source Seed 0 cohort | 6 inputs / 18 B, E+, P method observations | Complete main method and separate proof extension |
| Exposed-cohort Seeds1/2 | 24 new B/P arms, plus 12 historical Seed0 B/P arms | Six inputs; three within-input paired observations |
| Compact shared-state comparison | 6 exposed inputs / 12 fresh same-build B/C166 Seed0 arms | Equivalent common LP information and complete-method costs |

### 4.2 Complete main-method panels

**Table 2. Qualified certificates in the main Seed 0 panels.**

| Panel | GI-TBC | P | PS |
|---|---|---|---|
| Breadth | 9/12 | 7/12 | 7/12 |
| Resource pairs | 4/8 | 0/8 | 0/8 |

Certificates in this table require formal performance eligibility. Earlier evidence retains its own source and policy: the two-Seed breadth study obtains 17/24 versus P 9/24 and PS 4/12; the earlier final confirmation obtains 12/14 versus P 9/14 and PS 2/4. These are separate panels and repeated observations, and are not pooled with the current denominators. The earlier breadth study also retains its disclosed source-reduced own-zero observation outside formal timing counts.

**Table 3. Certificate-time comparisons conditioned on both methods certifying.**

| Panel | Other | Both certified | GI-TBC W / L | Geo Other / GI-TBC |
|---|---|---|---|---|
| Breadth | P | 7 | 6 / 0 | 11.3534 |
| Breadth | PS | 7 | 4 / 1 | 4.22522 |
| Resource pairs | P | 0 | 0 / 0 | n/a |
| Resource pairs | PS | 0 | 0 / 0 | n/a |

Table 3 conditions on the stated joint-CERT intersections under §3.4. OPEN endpoints and certificate-only differences remain in the complete panels.

The new positive-objective certificate cases include N-B15-B, N-X15-S and N-C20-U. On N-B15-B, GI-TBC takes 24.0684 s versus P 279.663 s and PS 306.307 s. On N-X15-S the corresponding times are 10.2683/538.867/401.931 s. GI-TBC certifies N-C20-U in 265.529s while P and PS remain open. These observations retain the independent cost of each complete method.

PS substantively reverses B on X-35-B: 7.45014 versus 17.9046 s. On N-X20-B, 6.08515/7.45537 s is nonmaterial. All breadth PS/B runs independently pay matching semantic/fleet H; later search costs still differ.

GI-TBC remains open on K-20-S, K-35-U and N-B35-S. K-35-U exposes an opposed-endpoint result: P has the lower U, 0.664747 versus GI-TBC 0.692854, while GI-TBC has the higher L, 0.565766 versus P 0.335556. No single endpoint-dominance or certificate-time claim follows. On N-B35-S, GI-TBC improves both endpoints over P and PS but still leaves a positive proof gap. These qualified limits accompany the certification gains.

N-X20-B cold P has a rejected native bound source and an own zero feasible objective. Its 24.0892 s qualified certificate uses the separately finalized nonnegative full-domain floor, not the rejected native proof. The complete cost and rejection records remain. This current-policy independent-zero certificate does not retroactively change the separately preserved historical exclusion above.

### 4.3 Archived-source and within-input Seed evidence

The later cohort contains six archived-source configurations, selected once from a frozen recipe across three sources and two sizes before all 18 B/E+/P runs. Synthetic stock, targets and weights supply finite configuration coverage. Table 4 retains the complete Seed0 endpoints. The same inputs then receive two additional predeclared solver Seeds for B/P, paying fresh lifecycles and own H with fixed H seed 20260626; the 24 additional runs create twelve paired repetitions, not twelve new physical inputs.

**Table 4. Historical Seed0 configuration confirmation, separate from the earlier panels.** Each entry is state, physical U / qualified proof L, then paid T_cert for CERT (seconds). Full binary64 values, verification costs, Work/nodes and source identities are in the supplement.

| Configuration | B | E+ | P |
|---|---|---|---|
| C20-S | CERT; 0.1912805923 / 0.1912805923; T_cert=199.7793504 | CERT; 0.1912805923 / 0.1912805923; T_cert=225.8837082 | OPEN; 0.1912805923 / 0.1602342164 |
| B20-B | CERT; 0.4232321817 / 0.4232321817; T_cert=5.058292441 | CERT; 0.4232321817 / 0.4232321817; T_cert=6.756586993 | CERT; 0.4232321817 / 0.4232321815; T_cert=235.8555019 |
| X20-S | CERT; 0.4477476266 / 0.4477476266; T_cert=119.7493879 | CERT; 0.4477476266 / 0.4477476266; T_cert=125.9267332 | OPEN; 0.4609477662 / 0.2616496512 |
| C35-U | OPEN; 0.1295663897 / 0.01983750282 | OPEN; 0.1295663897 / 0.01983750282 | OPEN; 0.09331934375 / 0.008286772138 |
| B35-S | OPEN; 0.1942903111 / 0.1202340026 | OPEN; 0.1942903111 / 0.1202340026 | OPEN; 0.2492530135 / 0.1139794085 |
| X35-S | OPEN; 0.457475317 / 0.3949882559 | OPEN; 0.457475317 / 0.4231995496 | OPEN; 0.5415306805 / 0.362971432 |

B and E+ certify 3/6, versus P 1/6. Their physical U coincide on all six inputs; E+ raises X35's qualified L from .3949882559151472 to .42319954961578576 at U=.45747531701601785. The relative gap falls from 13.6591% to 7.49238%, without a new certificate. E+'s lower raw search L=.39492875817006656 identifies the independent proof contribution. Its three joint-CERT B comparisons add 26.10, 1.70 and 6.18 s on C20/B20/X20; only C20 is substantive under §3.4. The helper's paid cost and its remaining inventory-price widths, .0143871/.0229556 on B35/X35, accompany the proof gain. Earlier near-tight inventory prices cannot be assigned to these later domains.

The B/P joint-CERT denominator is only B20 (1/6). B has lower U than P on three inputs, worse U on C35 and equivalent U on two; its L is stronger on five and equivalent on B20. C35 retains P's historical U=.09331934374779818 against B's .12956638965196035. Thus even this favorable certificate panel includes a saved primal reversal and all large inputs OPEN. No best-of-B/E+ method is constructed.

**Table 5. Within-input paired differences in Seed order 0/1/2.** Seed 0 is historical; Seeds 1/2 are the subsequent confirmation observations. ΔU=B−P is favorable to B when negative; ΔL=B−P
is favorable when positive. Values within 1e-7 are displayed as 0; individual endpoints and costs remain in the supplement.

| Configuration | B CERT /3 | P CERT /3 | ΔU: S0 / S1 / S2 | ΔL: S0 / S1 / S2 |
| --- | --- | --- | --- | --- |
| C20-S | 3 | 0 | 0 / 0 / -0.0592739276 | 0.0310463758 / 0.0336984584 / 0.0394115797 |
| B20-B | 3 | 3 | 0 / 0 / 0 | 0 / 0 / 0 |
| X20-S | 3 | 0 | -0.0132001396 / -0.0172134837 / -0.0132001396 | 0.186097975 / 0.194824544 / 0.197495547 |
| C35-U | 0 | 0 | 0.0362470459 / -0.0501944461 / -0.0386805194 | 0.0115507307 / 0.0134743346 / 0.00933437769 |
| B35-S | 0 | 0 | -0.0549627024 / -0.101715977 / -0.132960007 | 0.00625459405 / 0.00466145812 / 0.00475241402 |
| X35-S | 0 | 0 | -0.0840553635 / -0.060652829 / -0.0617878527 | 0.0320168239 / 0.0466015852 / 0.0444201335 |

At every Seed, B certifies 3/6 and P 1/6. B35 and X35 retain better B U and L in all three observations, while every n35 B/P run remains OPEN. C35's within-Seed primal ordering reverses: P is better at Seed0 and B at Seeds1/2, while B's L remains higher. Nevertheless the historical P fleet improves all three saved B incumbents: their U are .129566390/.107429866/.108083936, versus P's .093319344/.157624313/.146764456. This is an incumbent deficit, not evidence for a persistent within-Seed ranking or an isolated causal route operator.

Paid B certificate times at Seeds0/1/2 are 199.779/354.388/341.810 s on C20, 5.05829/4.96364/5.27705 s on B20 and 119.749/136.999/131.829 s on X20. P certifies only B20, in 235.856/303.033/266.801 s. Those three within-Seed B20 comparisons are substantive; they do not yield a full-panel speedup. The independently pre-frozen feasible-target diagnostic also shows B missing C35's known target in all three runs and X35's target in both new Seeds, even when B beats the corresponding P run. The supplement retains availability intervals, censoring, all individual U/L and costs, together with the limited earlier four-role second-Seed check (B 3/4, P and PS 1/4 at each Seed).

![Three-Seed original-objective endpoints on the six archived-source inputs. Colours identify B and cold P; circles are physical U and triangles qualified L. Filled U circles denote CERT and open circles OPEN. Dotted lines mark the pre-frozen offline feasible target. Seed 0 is historical; Seeds 1/2 were added on these same exposed inputs. Lines connect repeated observations and imply neither independent inputs nor a performance distribution.](figures/three_seed_endpoints.png)

To localize the saved primal deficits, we examine complete nested route families rather than a finite exchange neighborhood. Each parent permits every legal integer inventory on its originally served stations, pickup/drop reversal and deletion of zero service, with true compressed travel, empty departure, prefix capacities and loaded-return unloading. The order family retains owner and relative order; the owner family releases order; the eligible family additionally releases ownership. All quantities share the original whole-system Gini-plus-penalty objective. A closed pool of six archived B/P final fleets defines one attainable target per physical input, with a frozen comparison allowance of 1e-7. Across three inputs and nine saved B parents, the two already attaining parents are direct HITs. Qualified lower bounds exclude all seven initially nonattaining order families. This does not rule out smaller quantity improvements: two X35 witnesses improve without reaching the target. On C35 Seed0, the order and owner lower bounds are respectively above 0.097021 and 0.093398, against a target threshold about 0.09331944. Thus any target-reaching fleet must change an old served owner or serve an old ineligible station; arbitrary reordering at original ownership is insufficient. The eligible query remains UNKNOWN after its 300-second cap, so ownership release is not shown sufficient and station 18 is not proved necessary. The raw eligible lower fails the stricter frozen residual gate; only objective nonnegativity is retained as its safe lower, while the owner witness supplies a feasible upper of about 0.115129. These numerical restricted-domain conclusions neither certify the full problem nor establish online benefit. Supplement S168 records every interval, witness and cost; no complete-method performance observation is added.

### 4.4 What the mechanism controls identify

The four selected Seed0 roles compare full B, strengthened root-only, and single deletion of movement/visit links A/B, resource group \(C_R\), or geometry/objective group \(C_G\). Core products, original integer physics, own startup and the configured controller policy remain. Row deletion can change reached states and realized actions, so these are conditional contrasts rather than additive shares of a speedup. Initial matched-scope LPs expose A/B increments on two roles; the other groups show no detected initial-root increments in this panel. Removing a valid group cannot improve the ideal minimization bound, but can improve complete Native search.

On K-15-S, full B certifies in 112.769 s. Deleting \(C_R\) reduces it to 75.2546 s, while deleting A/B or \(C_G\) increases it to 128.246/143.383 s. The \(C_R\) reversal occurs mainly inside MIP: Runtime falls 110.549 to 73.048 s, Work 160.926 to 109.31 and nodes 48701 to 29036; generation differs by .0231363 s. Seed1 reverses all three deletion-time directions: full 115.444 s versus 93.6997/132.475/99.6006 s after A/B, \(C_R\), \(C_G\) removal. Root-only times, 112.649/113.580 s at the two Seeds, differ nonmaterially from full. The complete tables and cost accounting are in Supplement S167.2.

Hard roles retain opposed endpoints. On K-20-S, full and root-only share U=.716807 and finish with L=.705356/.706405. Deleting \(C_R\) weakens full L to .703444. On K-35-U, full U/L=.692854/.565766; A/B deletion improves U to .654639 and weakens L to .564355, while \(C_G\) deletion gives .666262/.550980. Root-only shares full U and has L=.566106. All these runs remain OPEN. Across the four Seed0 roles, full has no substantive certificate-cost advantage over root-only: the two easier roles have nonmaterial differences, and root-only retains slightly better L on both harder roles. The integrated B/P gains therefore do not establish an independent net benefit of external scheduling.

AM thresholds .04/.08/.16 are tested on the same four roles and two preselected Seed1 repeats. Finite observed child scores stay below .04; logical-infeasibility splits are separate. The AM/mechanism ledgers retain every tested role, finite gate, terminal and logical split, plus guards and incomplete eligibility exposure. Unchanged observed actions at these thresholds are not general robustness or proof of low outer cost. They describe the states actually reached under the fixed policy.

Other structural results delimit the interpretation. The complete joint service hull still leaves the inherited four-station fixed-positive-stock original-objective gap of exactly 1/4; the corresponding loaded-return proof checks all legal totals. Local product ideality is therefore weaker than the integer objective or full routing hull. Full-physical shared-G completion excludes saved points, yet free reoptimization gives the same LP value on one domain and only about .00018725 gain on another. A projected row retains about 87% of that gain. Six complete primary-role arms then have worse U than both fresh controls, equal proof L and no certificate; four conditional positions remain unstarted. Those negative outcomes remain alongside the positive scoped LP result.

For a common inventory necessary problem, \(L_I\le f_I^*\le U_I\) and \(f_I^*\le f_P^*\le U_P\). Thus

\[
U_P-L_I=(U_P-f_P^*)+(f_P^*-f_I^*)+(f_I^*-L_I).
\]

Only the last term is controlled by the price width \(U_I-L_I\); precise inventory pricing does not settle physical realization or incumbent quality. The supplement retains each structural object's positive, mixed and adverse results.

### 4.5 Representation strength and complete cost

C166 changes only the representation in Section 2.3. Its six exposed-input Seed0 comparison uses fresh same-build B controls, with independently paid complete H and the original 1200/2400 s caps under §3.4. Offline fleets and bounds enter neither method.

Eight qualification LP pairs, six roots and two fixed children, differ by at most 3.33e-16. C166 reduces columns in every pair but can increase rows/nonzeros. These checks support the common physical LP projection; they give no root-bound gain or search-time guarantee.

**Table 6. Same-build complete B/C166 comparison on the six exposed inputs.**
Entries give qualified state and physical U / global L. The last column is paid production seconds; T_cert exists only for CERT. Full precision and separate verification costs are in the supplement.

| Input | B: state; U / L | C166: state; U / L | Paid production B / C166 (s) |
|---|---|---|---|
| C20-S | CERT; 0.191280592 / 0.191280592 | OPEN; 0.191280592 / 0.186598049 | 210.415 / 1171.44 |
| B20-B | CERT; 0.423232182 / 0.423232182 | CERT; 0.423232182 / 0.423232182 | 5.09644 / 5.66122 |
| X20-S | CERT; 0.447747627 / 0.447747627 | CERT; 0.447747627 / 0.447747627 | 125.3 / 544.902 |
| C35-U | OPEN; 0.12956639 / 0.0198375028 | OPEN; 0.12104327 / 0.0142065407 | 2371.28 / 2371.2 |
| B35-S | OPEN; 0.194290311 / 0.120234003 | OPEN; 0.179289627 / 0.116053251 | 2371.1 / 2372.23 |
| X35-S | OPEN; 0.457475317 / 0.394988256 | OPEN; 0.475871153 / 0.386699749 | 2371.14 / 2371.1 |

B certifies 3/6 and C166 2/6. Their joint-CERT denominator is 2/6. C166/B certificate-time ratios are 1.1108 on B20 (nonmaterial) and 4.3488 on X20 (substantive), under §3.4. The comparison adds no B/P pair or independent Seed evidence.

The three n20 pairs have matching recorded AM action sequences and equal initial raw LP values. On X20, Native Runtime is 122.891/542.289 s, Work 220.964/992.214 and nodes 8842/66425 for B/C166; writer time is .721/.724 s. Extra cost lies mainly inside Native optimization. Presolve, cuts and branching may all differ; no particular cause is established.

Retain B uniformly. C166 loses C20's certificate; its C35/B35 U improve by .00852312/.01500068 while L weakens, and X35 worsens on both endpoints. These mixed results remain part of the evidence, without a per-input portfolio or single-Seed generalization.

Separately, 72 fixed canonical raw LPs, twelve local LPs and four tiny physical MIPs qualify. In 24 frame/scope triples D167 matches R_abs within \(2.22\times10^{-16}\); F0 also matches C166. Among sixteen bit-conditioned triples, D167 raises C166's bound by .000358489 on X20 root F2 and .00000692904/.0000208111 on B35 root F1/F2. Thirteen show no increment. D167 has more rows/columns than R_abs in every frame. Recorded C++ subprocess wall time is 126.262s; management-inclusive and independent-check costs are reported separately. The modest gains and larger matrices support retaining this offline prototype, with no complete-integration or speed claim.

## 5. Certified transportation decisions

### 5.1 What more route time certifiably buys

The four input-designed resource pairs fix the physical data, normalized weights and \(\rho=1\), and change only route horizon T. Each base has positive shortage, positive weights and a pre-solve positive objective floor; the design uses no observed difficulty filter. Increasing T enlarges the physical feasible set, but finite-budget bounds and computational time can move in either direction.

**Table 7. Input-based positive-objective resource design.**

| Base / source | \(n\) | T1 / T2 (s) | Shortage s | \(\Omega\) | Floor lambda a s |
|---|---|---|---|---|---|
| R-B20-S /CABI | 20 | 3300 /5100 | 20 | 13.47 | 0.103935 |
| R-X20-S /DIVVY | 20 | 4800 /7200 | 20 | 7.88889 | 0.126761 |
| R-B35-S /CABI | 35 | 4800 /7200 | 35 | 18.1405 | 0.0797268 |
| R-X35-S /DIVVY | 35 | 4200 /6300 | 35 | 13.2617 | 0.0977471 |

GI-TBC certifies the two B20 objectives .480735/.198473 at 3300/5100 s, with certificate costs 784.143/538.603 s. It certifies X20's .645325/.434796 at 4800/7200 s, with costs 20.5065/337.305 s. Thus both pairs have the same resource-value direction and opposite proof-cost directions. On X20's smaller horizon every method attains the same feasible objective, but P/PS remain open at L=.589197/.590359. The distinction is proof-gap closure, not a transferred incumbent or certificate.

All three methods remain OPEN on all four n35 resource configurations. B has lower U and higher L than the compact controls at the registered caps. For X35's larger horizon B gives .403272/.210887, PS .404567/.203817 and P .490517/.201288. These are endpoint improvements with no certificate-time ranking. On B35 the smaller-horizon interval [.455904,.591518] lies above the larger-horizon upper .344643, even though both B runs are open. The same separation can be bounded in both directions on every pair.

If \([L_j,U_j]\) contains the optimum at \(T_j\), feasible-set nesting gives

\[
\max\{0,L_1-U_2\}\le F^*(T_1)-F^*(T_2)\le U_1-L_2.
\]

The computation uses the complete full-precision fleets and qualified global lower sources. Each original lower is reduced by \(10^{-7}\), and recomputed feasible objectives receive \(10^{-12}\) upward protection. These guards and outward display rounding are retained in Table 8; all arithmetic and source ownership are preserved in the decision data.

**Table 8. Two-sided resource-value improvement intervals.** The bounds use complete physical fleets and qualified global lower sources. Displayed interval endpoints are rounded outward after reducing each original lower by \(10^{-7}\) and adding \(10^{-12}\) to exactly recomputed feasible objectives; full original endpoints and arithmetic are retained in the decision data.

| Base | T1 / T2 (s) | Improvement interval | Interval width | B state T1 / T2 |
|---|---|---|---|---|
| R-B20-S | 3300 / 5100 | [0.2822618761, 0.2822620892] | 0.0000002131 | C / C |
| R-X20-S | 4800 / 7200 | [0.2105292995, 0.2105295021] | 0.0000002026 | C / C |
| R-B35-S | 4800 / 7200 | [0.1112611656, 0.3725317852] | 0.2612706196 | open / open |
| R-X35-S | 4200 / 6300 | [0.0600858983, 0.3813035291] | 0.3212176308 | open / open |

The n35 intervals prove strict optimal-objective improvement, but leave widths .261271 and .321218; positivity of the lower endpoints does not determine the magnitude precisely. The smaller pairs localize the change to about two parts in ten million in objective units. These are differences in the specified dispersion/deviation objective, not monetary savings or general marginal prices of vehicle time.

All four larger-horizon saved B fleets reduce both Gini and average target deviation and collect more units: pickups change 30 to 43, 16 to 22, 41 to 60 and 29 to 42 on B20/X20/B35/X35. Return loads change 0 to 0, 1 to 0, 2 to 3 and 1 to 0. B35 improves while returning more inventory and reducing total station stock by one; X35 returns less and increases that total by one. X35's normalized stock sum S nevertheless falls from 28.7591 to 28.2238, because target denominators weight allocation differently from mass. The saved route durations are near their limits, but near-full utilization does not prove that an unknown optimum has a binding horizon. The supplement retains every route's travel, handling, unloading, prefix peak and station inventory distribution.

![Original-objective endpoints at the two physical horizons. Solid lines join feasible U circles; dashed lines join qualified L triangles. Filled U circles denote qualified certificates, and grey dotted lines show the pre-solve positive floor. Connecting lines describe finite-budget observations, not an exact optimal-value curve.](figures/resource_endpoints.png)


### 5.2 Quality between sampled objective weights

**Table 9. Objective-weight evidence. (a) Sampled complete-method outcomes; C denotes an own qualified certificate.**

| Physical configuration | \(\rho\) | P: U / L | PS: U / L | GI-TBC: U / L |
|---|---|---|---|---|
| R-B20-S-T1 | 0.5 | 0.380389 /0.229542 (open) | 0.347458 /0.240479 (open) | 0.347458 /0.331864 (open) |
| R-B20-S-T1 | 1 | 0.540085 /0.358158 (open) | 0.486639 /0.365324 (open) | 0.480735 /0.480735 (C) |
| R-B20-S-T1 | 2 | 0.756988 /0.610312 (open) | 0.744646 /0.616106 (open) | 0.744646 /0.744646 (C) |
| R-X35-S-T2 | 0.5 | 0.260978 /0.108223 (open) | 0.257631 /0.108019 (open) | 0.255825 /0.122332 (open) |
| R-X35-S-T2 | 1 | 0.490517 /0.201288 (open) | 0.404567 /0.203817 (open) | 0.403272 /0.210887 (open) |
| R-X35-S-T2 | 2 | 0.620443 /0.36178 (open) | 0.611892 /0.363572 (open) | 0.524553 /0.388438 (open) |

The sampled comparisons retain different search outcomes: B certifies R-B20-S-T1 at \(\rho=1,2\), while all methods remain open at \(\rho=.5\); all three methods remain open at every tested R-X35-S-T2 weight. The table reports each original run's own U/L. Cross-weight information is used only for the following offline analysis.

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
We calculate the worst bound over the entire covered interval from all true affine-line intersections, active-chord intersections and domain endpoints using rational arithmetic. No dense grid or new solver is used. Actual binary64 lambda/weight coordinates are retained, including small differences from displayed .5/1/2. The numerical guards are those stated with Table 8.

**Table 10. Continuous-weight quality guarantees from the complete fleet archive.** Ranges below are display coordinates; the machine-readable data preserve exact loaded coordinates. Regret bounds are rounded upward.

| Fixed physical family | Covered rho range | Runs / distinct G,p lines | Supported archive lines | Worst absolute regret bound |
|---|---|---|---|---|
| K-15-S | [0.710502825, 2.8420113] | 8 / 3 | 3 | 0.002356282 |
| UC-B20-B | [0.88725, 3.549] | 6 / 1 | 1 | 0.000000100002 |
| R-B20-S-T1 | [0.5, 2] | 9 / 7 | 3 | 0.015594269 |
| R-X35-S-T2 | [0.5, 2] | 9 / 9 | 1 | 0.136115162 |

UC-B20-B has the same component line across the full historical range, with an essentially numerical-width bound for one fixed fleet. K-15-S exhibits three supported component choices; the largest archive regret bound occurs at \(\rho\approx1.217804157\), between sampled weights. R-B20-S-T1 has component tradeoffs but a wider low-weight search gap. R-X35-S-T2 has one archive line supported throughout, while its proof band remains wide. Dominated fleets and their owners remain in the archive. Stability among known fleets does not prove a complete optimal frontier.

The R-X35-S-T2 fleet found at the higher sampled weight improves both components of the original unit-weight B incumbent. Re-evaluated at its actual original rho coordinate, its feasible objective is 0.3365058165 instead of 0.4032719989, a known improvement of 0.06676618239. The old U, discovery time and certificate status are unchanged. This offline deficit diagnosis is not injected into the C166/B comparison's startup or treated as production acceleration.

![Certified continuous-weight bands for four fixed physical families. Blue is the best verified archive objective; black dashed chords are applicable qualified lower bounds; shading is the remaining quality band. Pale lines retain other feasible component choices, circles mark original run incumbents, and triangles mark qualified lower anchors. These are upper/lower bounds, not a known exact optimum curve.](figures/parameter_quality_bands.png)


## 6. Conclusions

GI-TBC connects shared inventory states, objective products, movement and nonzero visits within the inherited bicycle redistribution problem. Objective-preserving physical extensions and complete improving-interval coverage supply the exact-method argument; own startup, qualification, continuation and termination make it a complete implementable method. The HGA-TGBC problem and decoder lineage remain explicit. Standard convexification, network and binary-product tools retain their established attribution.

The finite complete comparisons support B as the uniform main method. The breadth panel gives 9/12 certificates versus 7/12 for each compact control, and the positive-resource panel gives 4/8 versus 0/8. In the later six-input cohort B's 3/6 versus P's 1/6 repeats at three solver Seeds. All large cases in that cohort remain open, C35 reverses its within-Seed primal ordering, and its historical P fleet exposes all three B incumbent deficits. E+ supplies a genuine stronger X35 proof endpoint at a separately paid cost, including a substantive C20 increase. The selected full/root controls leave the outer controller's independent net computational benefit unresolved.

Representation strength and complete value also remain distinct. Five legal stock supports preserve the joint physical LP interface, but C166 certifies 2/6 versus B's 3/6 and substantially increases X20 proof cost. Its C35/B35 primal improvements coexist with weaker lowers, and X35 worsens on both sides. The conditional network establishes precisely what its disjoint code layer can lose: one common stock/service/product/code hull survives every partial absolute-bit fix. D167 matches that enumerated hull, with three strict conditioned LP increments in the fixed frames, but costs more rows and columns at these capacities. It remains an offline research prototype; no full-method acceleration or causal Native-branch explanation follows.

The same verified fleets and qualified global bounds support decisions beyond certificate counts. Four continuous-weight archive envelopes give whole-range regret bounds .002356282, .000000100002, .015594269 and .136115162. They distinguish a stable known fleet, supported plan switches and unresolved quality without claiming the complete Pareto frontier. All four route-time pairs have strictly positive optimal-objective improvement bounds; the n35 magnitude intervals remain broad. Better displayed objectives can accompany more loaded return, as on B35, or less, as on X35. These are bounded conclusions about inventory-to-target ratio dispersion and target deviation, not demographic fairness or monetary returns.

Further algorithm comparisons require a representation whose conditional information survives the declared physical interface at an acceptable complete cost, followed by independently paid own-H full-method evidence with qualified endpoints and all adverse cases retained. Better local hulls, fewer binaries and small LP times are insufficient substitutes. The unresolved incumbent deficits, physical realization gaps and separate value of interval scheduling are specific scientific questions; the present study closes neither them nor the general scalability of equitable redistribution.
