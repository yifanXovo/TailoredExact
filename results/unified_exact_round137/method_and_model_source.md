# GI-TBC: a Gini-interval tailored branch-and-cut algorithm for equitable bicycle redistribution

## Abstract

Static bicycle redistribution couples final station inventories with vehicle routes, prefix loads and handling time. We minimize ratio-Gini dispersion plus weighted relative target deviation under empty departure, loaded return and unique nonzero one-way service. Our exact method shares finite inventory states between service and objective representations, uses problem-specific supply and support inequalities, and maintains complete Gini-interval coverage around native LP and MIP solves. We prove implicit service integrality and establish the physical embeddings and coverage conditions needed for certification. In historical twelve-input/two-Seed validation, the method obtains 17/24 qualified certificates versus 9/24 for a cold compact control. Final implementation confirmation on six known roles obtains 12/14 versus 9/14, while retaining two substantive paid-start compact reversals and unresolved positive-objective 35-station endpoints. Six certified within-instance weight points show an equity-target trade-off on one input and a stable operating platform on another. The results support the integrated exact method within the specified model and test scope, and a bounded state-penalty study distinguishes relaxation improvement from complete-search performance.

## 1. Introduction

Redistribution vehicles can improve station availability only when the chosen inventory vector can be realized by feasible routes and loading operations. Supply must be collected before it is delivered, capacity applies at every route prefix, and handling consumes the same time budget as travel. When equity is measured by inventory-to-target ratios, the final inventory vector also determines both the numerator and denominator of the Gini coefficient. These dependencies make routing and inventory allocation inseparable.

We study static bicycle redistribution with empty vehicle departure, loaded return, and at most one nonzero one-way service at each station. The objective combines ratio-Gini dispersion and weighted relative target deviation. The model and HGA-TGBC framework originate in the direct same-problem project manuscript [@hgaTgbcManuscript]. The supplement records author/publication and source-metadata questions for confirmation. The present contribution is an exact solution method for that operational setting. The supplied decoder remains a feasible-solution component; the exact method supplies the bounds, coverage and termination arguments needed to distinguish a good plan from a certified optimum.

Our first contribution is a shared finite-state representation of final inventory, service and objective information. Unique service and binary direction imply integer pickup and delivery even when these quantities are declared continuous. Linking the same states to movement and visits prevents the relaxation from treating service decisions independently of the inventory mixtures used in the objective. We develop this representation with ordered supply compatibility and support/handling inequalities, and state their assumptions and physical embeddings.

Second, the Gini-interval tailored branch-and-cut method (GI-TBC, historically called S2, configuration ms2) combines a fully paid feasible startup, the shared representation, valid inequalities and complete interval coverage. The controller preserves the physical problem while refining objective intervals. Its correctness depends on applicable bounds and complete coverage; numerical source qualification and physical solution verification are stated separately.

Third, we evaluate complete-method cost against independent cold compact and fully paid-start compact controls. A predeclared multi-source breadth panel, shortage-guaranteed positive-objective resource pairs, and within-configuration effective-weight contrasts separate the scientific questions. AM thresholds and four conditional mechanism controls are accompanied by a limited preselected second Gurobi Seed. We report certificates and two-sided endpoints, including paid-start reversals, opposed endpoint trade-offs and unresolved cases; historical evidence retains its own versions and denominators. These comparisons distinguish mathematical strengthening, root behavior and complete-algorithm cost.

### 1.1 Relation to previous work

Static bike redistribution has been studied under several target, service and vehicle conventions. Raviv et al. develop static repositioning models; Chemla et al. study static rebalancing; Erdogan et al. address demand intervals and an exact rebalancing algorithm [@raviv2013; @chemla2013; @erdogan2014; @erdogan2015]. Schuijbroek et al. connect inventory requirements to routing [@schuijbroek2017]. Forbidden temporary operations, repeated visits, robust inventory requirements and demand-interval disjunctions give related but different feasible sets [@bruck2019; @bulhoes2018; @bruck2025; @ikonen2025]. The HGA-TGBC manuscript is the direct same-problem antecedent; the other studies supply routing and formulation context rather than matched performance baselines.

Station-ratio dispersion measures a different object from vehicle-workload equity [@matl2018]. Recent fairness-aware rebalancing and equity-based micromobility models motivate distributional objectives, while their distinct inventory, vehicle and operational definitions preclude a claim of model equivalence based on their abstracts alone [@qiao2026; @caggiani2026]. Here zero Gini means equal proportional inventory, which can still represent inadequate stock. The deviation term gives a separate incentive to approach station targets.

McCormick envelopes, value disjunctions and convex state epigraphs are established formulation tools [@mccormick1976; @gupte2013; @koppe2008; @boydVandenberghe2004]. Our claim concerns their connection to this problem's service structure and the resulting complete method. The preserved historical state-penalty comparison in Supplement S6 applies Jensen's inequality and an elementary projection construction; it is not a new general theory of aggregation. Source access and the remaining narrowly defined bibliographic questions are documented in the supplement.

## 2. Physical model and objective

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

## 3. Shared inventory states and GI-TBC

### 3.1 Discrete states and implicit service integrality

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

### 3.2 Ordered supply and support/handling information

Let \(\tau\) be metric travel time and \(h=t_p+t_d\). For each receiving station \(j\), define

\[
\mathcal C_{kj}=\{i\ne j:\tau_{0i}+\tau_{ij}+\tau_{j0}+h\le T\}.
\]

**Proposition 1 (ordered supply compatibility).** Every physical fleet with empty departure satisfies

\[
d_{kj}\le\sum_{i\in\mathcal C_{kj}}p_{ki}.
\]

**Proof.** Label the units collected by a vehicle. In route order, match each delivered unit to an earlier collected unit that has not yet been delivered. Nonnegative prefix loads guarantee such a match. A unit delivered at \(j\) from source \(i\) entails the ordered subsequence \((0,i,j,0)\), whose travel lower bound follows by metric shortcutting. Collecting at least that unit incurs handling of at least \(h\), including delivery or final unloading. Thus its source lies in \(\mathcal C_{kj}\). Counting distinct matched units proves the inequality. Unmatched collected units can return to the depot. \(\square\)

For a set \(W\) of served stations, let \(\tau(W)\) be the shortest depot tour through \(W\), computed by explicit orders for pairs or triples. Write \(P_k^{\rm pick}=\sum_i p_{ki}\). Nonzero integer service and empty departure give

\[
|W|\le\sum_{i\in W}(p_{ki}+d_{ki})\le2P_k^{\rm pick},\qquad
P_k^{\rm pick}\ge\lceil |W|/2\rceil.
\]

Consequently \(\tau(W)+h\lceil|W|/2\rceil>T\) rules out serving all of \(W\) with that vehicle. Otherwise a conditional duration inequality combines the tour lower bound and pickup handling. Supply for \(W\) may come from outside \(W\); cumulative pickup is not bounded by \(Q_k\). Appendix A gives the exact conditional coefficients, deactivation proof and finite selection rule. GI-TBC keeps pair support uniformly and omits triple support. These rows strengthen necessary physical conditions without replacing route-prefix capacity.

### 3.3 Complete startup and interval search

The startup \(H\) is a finite construction and descent procedure. It completes a joint insertion and 24 shuffled station/separator orders plus a constructive order, fully decodes them, applies guided first-improvement descent, and closes physical quantity/insertion and neutral balanced/exchange moves. The active path has no genetic generations. It provides a verified feasible upper bound and a possible MIP Start; it is never credited with a positive lower bound. Each GI-TBC and paid-start compact run pays for its own complete \(H\).

The controller starts from the complete potentially improving domain \([0,\min\{U,(n-1)/n\}]\). It maintains incumbent epoch, valid cutoff complements and complete interval coverage. A local bound is used only for its model, interval, cutoff and qualified source. Split children replace a parent atomically only after complete coverage and both results are checked. NEXT and child-target values are requests, rather than proof that a milestone was reached.

~~~text
Algorithm 1  GI-TBC
1 Complete the run's own H; physically verify its fleet and upper bound U.
2 Initialize the complete potentially improving Gini interval, allowing
  the degenerate interval [0,0] when the own upper bound is zero.
3 While unresolved coverage and the common deadline permit:
    select the controlling leaf by the fixed bound/plateau rule;
    run its prescribed LP, lookahead/target or terminal MIP;
    verify any own fleet improvement and qualify the returned source;
    install valid scoped bounds or complete covering children;
    stop under the declared complete-proof or finite termination rules.
4 On source rejection, discard dependent closures and restore the unresolved
  full physical domain with its independent nonnegative floor and own U.
  A separately established zero proof can still finalize the original problem.
5 Release native resources and finalize the selected own fleet's physical check;
  apply the independent exact-zero rule, complete required output, and return
  certificate type, U/L and unresolved coverage.
~~~

**Proposition 2 (coverage).** In ideal arithmetic, a controller that preserves complete improving-domain coverage, retains valid bound/cutoff complements and closes a region only by an applicable proof provides a valid global lower bound. If it closes all relevant regions against a verified \(U\), it proves optimality to its declared certificate margin.

**Proof.** Every improving physical solution belongs to the root domain because \(F\ge G\) and \(G\le(n-1)/n\). A valid interval restriction and cutoff cover its regional solutions; the cutoff complement has floor equal to that cutoff. A complete split preserves the union. Taking the minimum over the valid regional floors and complements therefore bounds every physical solution from below. Closure against \(U\) eliminates every possible improvement to the margin. Revoking a source requires removing every conclusion that depends on it; an independent full-domain bound remains valid. \(\square\)

This proposition does not turn floating-point native calculations into exact rational proofs. Numerical qualification, physical objective agreement and lifecycle evidence are additional implementation conditions. The final implementation separates ordinary positive-objective native/outer certificates from the independent zero rule. Supporting material records numerical anomalies and version corrections without making them algorithmic contributions.

### 3.4 Numerical qualification and termination

**Independent zero termination.** Under the stated nonnegative objective premises, a complete physically verified fleet with exact objective zero is globally optimal, independently of the native search source.

**Proof.** For every original physical solution, \(F\ge0\). The verified fleet gives \(F^*\le0\), so \(0\le F^*\le0\). With positive \(\lambda\) and positive weights, integer equality \(Y_i=D_i\) for every station is a sufficient exact-zero condition. More generally equal exact ratios give zero Gini, and every positive-weight penalized station must meet its target. The implementation checks these conditions using integer stock arithmetic, then repeats the complete physical-fleet verification. A merely small positive floating objective does not establish exact zero. \(\square\)

The numerical \(\varepsilon\)-certificate policy is separate. A source-rejected positive solution without a sufficient independent bound remains open. Certification cost includes the verification needed to establish the proof, normal native cleanup and required output. A later offline audit cannot backdate a production proof.

