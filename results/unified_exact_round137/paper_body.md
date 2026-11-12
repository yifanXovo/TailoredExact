# GI-TBC: a Gini-interval tailored branch-and-cut algorithm for equitable bicycle redistribution

## Abstract

Static bicycle redistribution must realize an equitable final inventory by routes that respect empty departure, intermediate vehicle capacity and paid handling, including loaded returns. We develop GI-TBC, an exact method that links finite inventory states to objective products, movement and visits, and controls complete regions of the true Gini coefficient. Under unique nonzero one-way service, integer final inventories imply integer service quantities; objective-preserving embeddings and cutoff-complement accounting establish the method's coverage conditions. Against independent cold and fully paid-start compact controls, the integrated method obtains 9/12 qualified certificates versus 7/12 and 7/12 in a registered breadth panel, and 4/8 versus 0/8 and 0/8 in a separately designed positive-objective resource panel. A later six-input archived-source cohort gives 3/6 GI-TBC certificates versus 1/6 cold compact at each of three solver Seeds; all 35-station observations remain open, and one input reverses its primal ranking. Conditional controls show small shared-state root gains and mixed complete costs, with no substantive certificate-time advantage over the strengthened root-only control in the tested roles. A separately paid inventory-proof extension raises one final lower bound without changing six physical upper endpoints or adding a certificate. The results establish finite competitiveness of the complete package and distinguish stronger inventory information from physical realization and net computational benefit; they do not isolate an independent speed gain from outer interval scheduling.

## 1. Introduction

Redistribution vehicles can improve station availability only when the chosen inventory vector can be realized by feasible routes and loading operations. Supply must be collected before it is delivered, capacity applies at every route prefix, and handling consumes the same time budget as travel. When equity is measured by inventory-to-target ratios, the final inventory vector also determines both the numerator and denominator of the Gini coefficient. These dependencies make routing and inventory allocation inseparable.

We study static bicycle redistribution with empty vehicle departure, loaded return, and at most one nonzero one-way service at each station. The objective combines inventory-to-target ratio-Gini dispersion and weighted relative target deviation. The operational model and HGA-TGBC heuristic framework originate in the available same-problem author manuscript [@hgaTgbcManuscript]. Our exact method reuses its decoder within a finite startup procedure and supplies the bounds and complete coverage needed for certification.

The research question is how finite inventory information can support a complete exact routing method, and how much of its observed competitiveness can be assigned to individual mechanisms. Three connected contributions answer it. First, the same stock state links the Gini product to movement and visits. We establish the conditional integer-service implication and physical embeddings, and derive ordered-supply and support/handling inequalities from the original operations. This identifies where the representation uses problem structure: an isolated product disjunction alone has the McCormick rectangle projection.

Second, GI-TBC combines that formulation, a fully paid feasible startup and complete true-Gini interval control. An explicit main algorithm connects region selection, lower-bound targets, midpoint probes, exact continuation and termination; the appendices specify every rule. These coverage arguments establish correctness conditions. They do not identify which controller decisions save computational time. Custom valid rows are inserted statically when a canonical interval model is built; Gurobi performs native branch-and-cut inside it, while our controller manages Gini intervals outside the solver.

Third, complete-method comparisons separate physical upper bounds, qualified lower bounds and paid certificate cost. Breadth, positive-resource pairs, within-input weights and a later three-Seed cohort retain their own designs. Root-only and row-deletion controls, AM exposure and independent inventory-proof extensions distinguish representation strength from complete performance. The integrated package has finite certificate and endpoint advantages over the specified compact controls. Its full-over-root incremental speed benefit is unestablished in the tested roles, and stronger stock information need not yield better feasible routes or lower total cost. These distinctions are part of the contribution's scope, rather than separate claims of general-purpose reformulation or scheduling breakthroughs.

### 1.1 Relation to previous work

Static bike redistribution has been studied under several target, service and vehicle conventions. Raviv et al. develop static repositioning models; Chemla et al. study static rebalancing; Erdogan et al. address demand intervals and an exact rebalancing algorithm [@raviv2013; @chemla2013; @erdogan2014; @erdogan2015]. Schuijbroek et al. connect inventory requirements to routing [@schuijbroek2017]. Forbidden temporary operations, repeated visits, robust inventory requirements and demand-interval disjunctions give related but different feasible sets [@bruck2019; @bulhoes2018; @bruck2025; @ikonen2025]. The HGA-TGBC manuscript is the direct same-problem antecedent; the other studies supply routing and formulation context rather than matched performance baselines.

Station-ratio dispersion measures a different object from vehicle-workload equity [@matl2018]. Qiao et al. balance task durations in a coordinated two-echelon rebalancing framework [@qiao2026]. Caggiani et al. consider free-floating electric micromobility, battery swapping and a modified Gini measure involving availability and state of charge, with zonal fair targets [@caggiani2026]. Their accessible abstracts identify these equity objects and operation settings; the unread complete formulations do not support equivalence or dominance claims. Here zero Gini means equal proportional station inventory, which can still represent inadequate stock. The deviation term separately rewards approaching targets.

McCormick envelopes and convex epigraphs are standard tools [@mccormick1976; @boydVandenberghe2004]. Gupte et al. study unary/binary reformulations and relaxations of integer-continuous single-product sets [@gupte2013]. Köppe et al. develop finite block values, linking polyhedra and an aggregate representation [@koppe2008]. Our connection is the use of one final-stock state across the objective, absolute movement and nonzero-service indicator, within this physical routing problem. Neither binary expansion, value disjunction nor spatial partitioning is claimed as new. The state-penalty comparison in Supplement S6 applies Jensen's inequality and a direct projection construction; the complete route model is not the hull of an isolated product block.

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

**Proof.** Label the units collected by a vehicle. In route order, match each delivered unit to an earlier collected unit that has not yet been delivered. Nonnegative prefix loads guarantee such a match. A unit delivered at \(j\) from source \(i\) entails the ordered subsequence \((0,i,j, 0)\), whose travel lower bound follows by metric shortcutting. Collecting at least that unit incurs handling of at least \(h\), including delivery or final unloading. Thus its source lies in \(\mathcal C_{kj}\). Counting distinct matched units proves the inequality. Unmatched collected units can return to the depot. \(\square\)

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

**Proposition 2 (coverage).** In ideal arithmetic, a controller that preserves complete improving-domain coverage, retains valid bound/cutoff complements and closes a region only by an applicable proof provides a valid global lower bound. If it closes all relevant regions against a verified \(U\), it proves optimality to its declared certificate margin.

**Proof.** Every improving physical solution belongs to the root domain because \(F\ge G\) and \(G\le(n-1)/n\). A valid interval restriction and cutoff cover its regional solutions; the cutoff complement has floor equal to that cutoff. A complete split preserves the union. Taking the minimum over the valid regional floors and complements therefore bounds every physical solution from below. Closure against \(U\) eliminates every possible improvement to the margin. Revoking a source requires removing every conclusion that depends on it; an independent full-domain bound remains valid. \(\square\)

The proof's source-dependency requirement is not a claim of a general online revocation engine. The frozen scheduler accumulates same-unit bounds monotonically. Its actual final qualification rejects affected native proof dependencies and conservatively restores the unresolved physical domain; Appendix B.4 distinguishes that fallback from ideal proof accounting. This proposition does not turn floating-point native calculations into exact rational proofs. Numerical qualification, physical objective agreement and lifecycle evidence are additional implementation conditions. The final implementation separates ordinary positive-objective native/outer certificates from the independent zero rule. Supporting material records numerical anomalies and version corrections without making them algorithmic contributions.

The depth and width guards limit extra partitioning, then retain a full parent MIP continuation. In ideal arithmetic, complete terminal solutions on the bounded integer domains and valid coverage yield the corresponding finite proof. Under the actual common deadline an unresolved terminal obligation returns OPEN; the guards themselves establish no certificate.

### 3.4 Numerical qualification and termination

**Independent zero termination.** Under the stated nonnegative objective premises, a complete physically verified fleet with exact objective zero is globally optimal, independently of the native search source.

**Proof.** For every original physical solution, \(F\ge0\). The verified fleet gives \(F^*\le0\), so \(0\le F^*\le0\). With positive \(\lambda\) and positive weights, integer equality \(Y_i=D_i\) for every station is a sufficient exact-zero condition. More generally equal exact ratios give zero Gini, and every positive-weight penalized station must meet its target. The implementation checks these conditions using integer stock arithmetic, then repeats the complete physical-fleet verification. A merely small positive floating objective does not establish exact zero. \(\square\)

The numerical \(\varepsilon\)-certificate policy is separate. A source-rejected positive solution without a sufficient independent bound remains open. Certification cost includes the verification needed to establish the proof, normal native cleanup and required output. A later offline audit cannot backdate a production proof.

### 3.5 A separately paid proof-only inventory source

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

The C++ complete-method implementation and the historical Python inventory
helper are separately identified in the supplement. No per-instance, source,
scale, machine-speed or elapsed-time enhancement switch is used. Stable B and
the paper recommendation remain separate from released defaults.

E+ evidence is confined to its separately registered runs. B/P solver-Seed
repeats do not retest the helper or establish its robustness. The inventory
source's mathematical validity, numerical qualification and net value for the
complete paid method remain separate questions.

## 4. Computational design

The main comparisons use the same physical problem and original objective. P is the independent cold compact model; PS pays its complete own H and maps only its own fleet into the original compact model; GI-TBC pays its complete own H, model construction, verification, interval search and proof/output. No solution, bound, tree or Start crosses methods, Seeds, objective weights or physical configurations. Gurobi 13.0.2 uses one thread and fixed processor affinity on an Intel i7-12700KF Windows host. H seed 20260626 is held fixed; each study registers its Gurobi Seeds separately. Same Seed does not mean different models follow the same random trajectory.

The fixed-source protocol was committed before once-only generation. Six known roles and six new draws form a twelve-input breadth panel (four each at \(n\in\{15,20,35\}\)); CITI, CABI and Divvy supply archived station geometry/capacity. Ten new draws in total include four additional shortage bases at \(n\in\{20,35\}\), each paired at two transparently designed route horizons. Targets, initial stock, weights and depot are synthetic or transformed; this is not observed demand, a new source, or independent population sampling. Every selected source row and serialized input is disclosed.

Breadth retains \(\lambda=.15\). Resource pairs fix \(\rho=1\) and alter only T; the two extra weight levels \(\rho\in\{.5,2\}\) reuse the matching \(\rho=1\) baseline at two preselected physical configurations. AM and mechanism defaults share only exactly matching input/T/weight/Seed/cap/configuration runs. The earlier main panels use Seed 0; four preselected full-method triplets and small overlapping AM/mechanism blocks use Seed 1. They are finite repeated observations, not independent new inputs or an estimated runtime distribution. The later six-input archived-source cohort uses Seed0 for its B/E+/P comparison and Seeds1/2 for the complete B/P confirmation in §5.5. The additional 24 commands and offline feasible targets are frozen together; this extends existing Seed research on exposed inputs rather than supplying new unseen inputs.

For each new resource base, let \(d_{\max}\) be its maximum serialized station-to-depot distance and \(M\) its vehicle count. Before optimization, the route horizons were fixed by

\[
\begin{aligned}
T_{\rm base}&=2d_{\max}/1.5+120\sum_{i\in N}\max(b_i-D_i, 0)/M,\\
T_1&=300\left\lceil\frac{\max(1800,.75T_{\rm base})}{300}\right\rceil,\\
T_2&=300\left\lceil\frac{1.5T_1}{300}\right\rceil.
\end{aligned}
\]

This input-based rule uses geometry, initial stock, targets and fleet size; it supplies neither a binding-horizon guarantee nor an outcome-dependent difficulty filter. The weight study preselects R-B20-S-T1 and R-X35-S-T2. Within each T pair, every datum except T is identical.

Caps are 600/1200/2400 s by size; every open certificate time remains null. Actual production, postverification and total clocks are retained separately. Native proof qualification and physical original-objective endpoints follow the registered numerical policy in §3.4 and Appendix A.7. Rejected native sources cannot support a bound. A current run can still qualify its own independently finalized exact-zero certificate under that policy; this basis and any rejected source are reported separately. Both-certified time differences are substantive when at least max(10s, 10% of the faster time); numerical values and the conditioned intersection denominator accompany the classification.

**Table 1. Registered studies, observations and shared defaults.**

| Study | Configurations / observations | Purpose |
|---|---|---|
| Breadth | 12 physical inputs / 36 methods | Sources, stock regimes and scales |
| Positive-resource pairs | 4 bases, 8 physical configurations / 24 methods | \(\rho=1\), guaranteed positive objective |
| Weights | 2 physical configurations, 2 extra rho levels / 12 methods | Relative method dependence on objective weight |
| AM | 4 roles, 2 extra thresholds / 8 methods | Observed gates/actions and complete cost |
| Mechanisms | 4 roles, 4 contrasts / 16 methods | Conditional formulation/control effects |
| Earlier second Seed | 12 main+4 AM+8 mechanism methods | Preselected limited repeat check |
| Archived-source Seed 0 cohort | 6 inputs / 18 B, E+, P method observations | Complete main method and separate proof extension |
| Exposed-cohort Seeds1/2 | 24 new B/P arms, plus 12 historical Seed0 B/P arms | Six inputs; three within-input paired observations |

## 5. Complete-method, resource and weight results

### 5.1 Current main panel and historical context

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

Time ratios and substantive time wins/losses in this table condition on both methods qualifying a certificate; their intersection sizes are shown explicitly. A ratio above 1 means a lower GI-TBC certificate time on this conditioned subset. An open cap supplies no certificate time and enters neither the ratio nor these time-win counts. Certificate-only differences and open endpoints remain in the complete panel.

The new positive-objective certificate cases include N-B15-B, N-X15-S and N-C20-U. On N-B15-B, GI-TBC takes 24.0684 s versus P 279.663 s and PS 306.307 s. On N-X15-S the corresponding times are 10.2683/538.867/401.931 s. GI-TBC certifies N-C20-U in 265.529s while P and PS remain open. These observations retain the independent cost of each complete method.

Paid startup and the subsequent method have distinct effects. On X-35-B, PS certifies in 7.45014 s versus GI-TBC 17.9046 s, a substantive PS reversal under the declared rule. On N-X20-B, PS 6.08515 s and GI-TBC 7.45537s differ by less than 10 s, so the nominal ordering is not substantive. All twelve breadth PS/GI-TBC pairs independently complete H with matching semantic and fleet hashes; the complete post-startup packages can still behave differently.

GI-TBC remains open on K-20-S, K-35-U and N-B35-S. K-35-U exposes an opposed-endpoint result: P has the lower U, 0.664747 versus GI-TBC 0.692854, while GI-TBC has the higher L, 0.565766 versus P 0.335556. No single endpoint-dominance or certificate-time claim follows. On N-B35-S, GI-TBC improves both endpoints over P and PS but still leaves a positive proof gap. These qualified limits accompany the certification gains.

N-X20-B cold P has a rejected native bound source and an own zero feasible objective. Its 24.0892 s qualified certificate uses the separately finalized nonnegative full-domain floor, not the rejected native proof. The complete cost and rejection records remain. This current-policy independent-zero certificate does not retroactively change the separately preserved historical exclusion above.

The complete paired interpretation, including substantive reversals and conditioned runtime statistics, is given in the stage decision and the full supplement. Smaller signed gap alone does not establish endpoint dominance: U and L are compared separately. No cap is substituted for a certificate time.

### 5.2 Positive objectives and physical resource pairs

All four serialized shortage bases have positive weights, a strictly positive analytic floor, and both local donor and receiver stations before movement. Relaxing T enlarges the feasible set; the observed feasible plans, qualified bounds and proof progress test how the methods use that resource, not a causal effect of n alone. The physical operation records distinguish travel, handling, returned stock, prefix peaks and route-duration utilization.

**Table 4. Input-based positive-objective resource design.**

| Base / source | \(n\) | T1 / T2 (s) | Shortage s | \(\Omega\) | Floor lambda a s |
|---|---|---|---|---|---|
| R-B20-S /CABI | 20 | 3300 /5100 | 20 | 13.47 | 0.103935 |
| R-X20-S /DIVVY | 20 | 4800 /7200 | 20 | 7.88889 | 0.126761 |
| R-B35-S /CABI | 35 | 4800 /7200 | 35 | 18.1405 | 0.0797268 |
| R-X35-S /DIVVY | 35 | 4200 /6300 | 35 | 13.2617 | 0.0977471 |

The floor is a pre-solve guarantee at \(\rho=1\), shared by the two physical horizons. It is not the reported solver L, and a larger T need not improve a finite-budget U or L monotonically.

On R-B20-S, GI-TBC qualifies certificates at F=0.480735 with T=3300 s and F=0.198473 with T=5100 s. The two qualified intervals establish a strict value improvement under the controlled resource change. Certificate times are 784.143/538.603 s respectively. The lower proof cost on this pair is an observed result; feasible-set inclusion supplies no runtime ordering for other inputs.

R-X20-S-T1 isolates a proof-gap difference. All three verified feasible objectives coincide at 0.645325, while GI-TBC forms its own qualified certificate in 20.5065 s. P and PS retain L=0.589197/0.590359, respectively, and remain open under their own evidence. The complete-method comparison concerns closure of the dual gap on this witness; the conditional controls delimit attribution to individual mechanisms. No other method inherits the GI-TBC proof or certificate time.

On R-X20-S, the larger horizon reduces the certified objective from 0.645325 to 0.434796, while the GI-TBC certificate cost increases from 20.5065 to 337.305 s. Together with R-B20-S, these two \(n=20\) pairs show the same resource-value direction and opposite observed proof-cost directions. They remain finite Seed 0 observations; the input differences across bases prevent a pure source or scale attribution.

Value improvement can also be demonstrated while both GI-TBC runs remain open. On R-B35-S, the qualified T1 lower endpoint 0.455904 exceeds the verified T2 feasible upper endpoint 0.344643. The separated intervals [0.455904,0.591518] and [0.218986,0.344643] support a strict resource-value improvement under the stated numerical policy. Each optimum remains inside its own interval, and no certificate-time comparison is reported.

All four resource bases admit this type of strict endpoint separation: an eligible T2 feasible upper endpoint lies below the qualified GI-TBC T1 lower endpoint. This offline value comparison preserves every method's own certificate/open status and clocks; no bound or feasible plan is transferred into another production run. It establishes strict improvement for these four designed pairs without claiming that every increase in T must improve the optimum strictly.

**Table 5. Strict resource-value improvements from separated qualified endpoints.**

| Base | GI-TBC L(T1) | Feasible U(T2) / owner | L(T1) - U(T2) | Source status T1 / T2 |
|---|---|---|---|---|
| R-B20-S | 0.480735 | 0.198473 /GI-TBC | 0.282262 | C /C |
| R-X20-S | 0.645325 | 0.434796 /GI-TBC | 0.210529 | C /C |
| R-B35-S | 0.455904 | 0.344643 /GI-TBC | 0.111261 | open /open |
| R-X35-S | 0.463358 | 0.403272 /GI-TBC | 0.060086 | open /open |

The T2 column identifies the owner of the lowest verified feasible upper endpoint among the three completed methods. A cross-method separation concerns the common problem value and does not certify either open source run.

The supplement reports operations of each verified own incumbent, including open configurations. The components and S distinguish changes in dispersion, target deviation and the inventory denominator. Duration utilization describes the displayed routes; a near-unit ratio alone does not establish a binding optimum. Full per-vehicle travel/handling, pickups/drops/returns and prefix peaks are retained in the [operations data supplement](reports/operations.json).

Both G and \(P_{\mathrm{avg}}\) decrease between the saved GI-TBC plans in every resource pair. The longest route uses at least 99.4109% of its horizon in each displayed plan. The separate strict endpoint separations establish resource-value relevance; near-full route use alone does not establish exact binding. R-X35-S also illustrates why S must be distinguished from inventory mass: loaded returns fall from 1 to 0, so total station inventory increases by one, while S falls from 28.7591 to 28.2238. The different target denominators make S depend on the allocation of units, not only their total. These are verified feasible-plan comparisons; the \(n=35\) optima remain unresolved.

All three methods remain open on all four \(n=35\) resource configurations. GI-TBC has lower U and higher L than both controls at the registered complete caps, but none of these endpoint improvements is a certificate-time gain. On R-X35-S-T2, GI-TBC reports U/L=0.403272/0.210887, versus PS 0.404567/0.203817 and P 0.490517/0.201288. The feasible-objective advantage over PS is only 0.00129523; primal and dual differences remain visible separately. These persistent open outcomes delimit the positive-objective scale reached by this finite panel.

Paid-start effects are conditional on the resource configuration. On R-B35-S-T1, cold P has lower U and higher L than PS; this two-endpoint direction reverses at T2. P also has both better endpoints on R-X20-S-T2. All of these compact runs remain open. These fixed-budget comparisons retain the complete cost of startup and do not establish an eventual proof-time ordering or a universal startup benefit.

![Original-objective endpoints at the two physical horizons. Solid lines join feasible U circles; dashed lines join qualified L triangles. Filled U circles denote qualified certificates, and grey dotted lines show the pre-solve positive floor. Connecting lines describe finite-budget observations, not an exact optimal-value curve.](figures/resource_endpoints.png)

\clearpage

### 5.3 Objective weights

**Table 6. Within-configuration weights; C denotes an own qualified certificate.**

| Physical configuration | \(\rho\) | P: U / L | PS: U / L | GI-TBC: U / L |
|---|---|---|---|---|
| R-B20-S-T1 | 0.5 | 0.380389 /0.229542 (open) | 0.347458 /0.240479 (open) | 0.347458 /0.331864 (open) |
| R-B20-S-T1 | 1 | 0.540085 /0.358158 (open) | 0.486639 /0.365324 (open) | 0.480735 /0.480735 (C) |
| R-B20-S-T1 | 2 | 0.756988 /0.610312 (open) | 0.744646 /0.616106 (open) | 0.744646 /0.744646 (C) |
| R-X35-S-T2 | 0.5 | 0.260978 /0.108223 (open) | 0.257631 /0.108019 (open) | 0.255825 /0.122332 (open) |
| R-X35-S-T2 | 1 | 0.490517 /0.201288 (open) | 0.404567 /0.203817 (open) | 0.403272 /0.210887 (open) |
| R-X35-S-T2 | 2 | 0.620443 /0.36178 (open) | 0.611892 /0.363572 (open) | 0.524553 /0.388438 (open) |

Certification depends on the weight even within the preselected \(n=20\) physical configuration. GI-TBC certifies R-B20-S-T1 at \(\rho=1\), whereas all three methods remain open at \(\rho=.5\). At \(\rho=.5\), GI-TBC and PS have the same verified U=0.347458, but their qualified L values are 0.331864/0.240479. This retains a finite-budget dual-progress advantage without a certificate-time claim at that weight.

At \(\rho=2\), GI-TBC certifies F=0.744646 in 309.113 s, while P and PS remain open. PS attains the same verified feasible objective but has L=0.616106 instead of the GI-TBC lower endpoint 0.744646. Thus the \(n=20\) complete-proof advantage is observed at two tested weights, and the third retains a dual-endpoint advantage without closure. Each method retains its own proof status.

At the fixed \(n=35\) horizon T=6300 s, all three methods remain open at \(\rho=.5\). GI-TBC reports U/L=0.255825/0.122332, with lower U and higher L than both controls. PS has the better feasible objective than cold P, while P has the higher qualified lower endpoint. This preserves an opposed-endpoint startup result alongside the finite GI-TBC endpoint advantages; no certificate-time ordering is assigned.

The \(n=35\) configuration remains open for every method at all three tested weights. GI-TBC has lower U and higher L than both controls within each weight. At \(\rho=2\), its U/L=0.524553/0.388438 compares with PS 0.611892/0.363572 and P 0.620443/0.36178. The feasible-objective advantage over PS is 0.0873392 at \(\rho=2\), compared with 0.00129523 at \(\rho=1\). Thus the magnitude of the finite primal advantage varies with the weight, while the unresolved proof gap persists. These observations do not imply a monotone weight effect or complete-proof-time robustness.

The saved \(n=20\) GI-TBC operating points show G increasing and \(P_{\mathrm{avg}}\) decreasing across \(\rho\in\{.5,1,2\}\); the low-weight run remains open. The \(n=35\) points expose a stronger finite-search limitation: at the same physical input and T, the \(\rho=2\) saved plan has \(G/P_{\mathrm{avg}}\)=0.148459/0.188047, both below the \(\rho=1\) saved plan values 0.18255/0.220722. Thus the \(\rho=1\) saved incumbent is dominated in the two objective components by another saved feasible plan. This is an offline comparison of completed observations that exposes a primal deficit in the retained \(\rho=1\) incumbent. Each run keeps its own U/L and proof status; no plan, Start or bound was transferred during production. It provides no exact optimal weight frontier and does not establish monotonic search behavior.

Cross-weight values refer to different objectives, while method comparisons are made within each weight. Uncertified weights report feasible operating points and qualified bounds; they do not define an exact optimal trade-off curve.

\clearpage

### 5.4 Limited preselected second Seed

**Table 7. Certificates in the four preselected second-Seed configurations.**

| Method | Selected Seed 0 certificates /4 | Seed 1 certificates /4 |
|---|---|---|
| P | 1 | 1 |
| PS | 1 | 1 |
| GI-TBC | 3 | 3 |

These four configurations were selected before the current results. Their Seed 1 observations remain distinct from the full main Seed 0 panel and do not replace an unfavorable first observation. Same Seed is a common setting for different models, not a shared random trajectory, and two Seeds do not estimate a runtime distribution. Complete H remains part of the defined algorithm configuration with its own fixed seed; the AM/mechanism repeat blocks use the corresponding actual Seed 1 baselines.

K-15-S retains the same certificate pattern in the limited repeat: only GI-TBC certifies, in 112.769 / 115.444 s at Seed 0 / Seed 1, a nonmaterial complete-cost difference under the declared rule. All six runs attain the same verified feasible objective, but each compact run retains its own open proof status. Finite dual progress is less stable in direction: Seed 0 cold P / paid-start PS end at L=0.527663/0.520583, whereas Seed 1 ends at 0.529115/0.53228. Thus the compact dual ordering reverses even while feasible objectives and this role-specific certificate pattern agree. This finite observation does not establish a distribution or an eventual proof-time ranking.

UC-B20-B also retains its certificate pattern, with all three methods certifying at both Seeds. GI-TBC takes 4.14897/4.0999 s and cold P 315.403/314.513 s, respectively; their cross-Seed differences are below the substantive rule. Paid-start PS changes from 236.091 to 125.391 s. This descriptive change exceeds that rule while the GI-TBC advantage over both compact controls persists in this role. Complete own H and matched within-Seed trace/fleet identities are retained; unchanged certification status does not make every complete runtime stable. Two Seeds still supply finite checks rather than a distribution or a best-Seed selection.

R-B20-S-T1 preserves own certification only for GI-TBC, whose certificate cost changes from 784.143 to 656.734 s, a substantive descriptive shift under the stated rule. At Seed 1, paid-start PS reaches the same feasible U=0.480735, but retains its own lower endpoint 0.367482 and remains open. Cold P improves its feasible objective from 0.540085 to 0.493224 while its lower bound falls from 0.358158 to 0.354626. The complete-method certificate pattern therefore coexists with material time variation and opposed cross-Seed endpoint changes. These are finite matched observations; the Seed 0 panel remains the primary evidence, and no certificate is transferred to a compact run.

K-35-U remains open for every method at both Seeds. At Seed 1, GI-TBC has U/L=0.668358/0.55478, compared with P 0.758852/0.330574 and PS 0.712648/0.335095. GI-TBC improves both endpoints over both controls within Seed 1, whereas Seed 0 retains the better P feasible objective and stronger GI-TBC lower bound. GI-TBC also improves its own U from 0.692854 to 0.668358 across Seeds while L falls from 0.565766 to 0.55478. A smaller signed gap therefore does not make both of its own endpoints better. The compact comparison reverses in both endpoints: P is better than PS at Seed 0, while PS is better than P at Seed 1. No open certificate time is supplied, and the adverse Seed 0 observations are retained.

### 5.5 Archived-source cohort and within-input Seed confirmation

The six-configuration cohort was generated once from a prospectively frozen recipe using three archived sources, two sizes and three compact/three regional selections. All configurations and all 18 Seed0 B/E+/P commands were sealed before the formal comparison; balanced/surplus and shortage selections were retained regardless of difficulty or inventory-floor value. Synthetic inventories, targets and weights are not observed demand. This supplies finite configuration coverage rather than new-city or IID validation. These same six configurations are now exposed when used for additional solver-Seed confirmation.

Each configuration has independently paid B, E+ and cold P runs under one common PE/DLL, original physical T, actual lambda and cap. The n20 cap is 1200 s and n35 cap 2400 s, including startup and helper. P has NumStart=0; B/E+ each execute their own H. Original complete fleets are independently recomputed. Qualified proof endpoints and the inherited signed/near-zero certificate policy determine state. OPEN cap values are not certificate times.

**Table 8. Historical Seed0 configuration confirmation, separate from the earlier panels.** Each entry is state, physical U / qualified proof L, then paid T_cert for CERT (seconds). Full binary64 values, verification costs, Work/nodes and source identities are in the supplement.

| Configuration | B | E+ | P |
|---|---|---|---|
| C20-S | CERT; 0.1912805923 / 0.1912805923; T_cert=199.7793504 | CERT; 0.1912805923 / 0.1912805923; T_cert=225.8837082 | OPEN; 0.1912805923 / 0.1602342164 |
| B20-B | CERT; 0.4232321817 / 0.4232321817; T_cert=5.058292441 | CERT; 0.4232321817 / 0.4232321817; T_cert=6.756586993 | CERT; 0.4232321817 / 0.4232321815; T_cert=235.8555019 |
| X20-S | CERT; 0.4477476266 / 0.4477476266; T_cert=119.7493879 | CERT; 0.4477476266 / 0.4477476266; T_cert=125.9267332 | OPEN; 0.4609477662 / 0.2616496512 |
| C35-U | OPEN; 0.1295663897 / 0.01983750282 | OPEN; 0.1295663897 / 0.01983750282 | OPEN; 0.09331934375 / 0.008286772138 |
| B35-S | OPEN; 0.1942903111 / 0.1202340026 | OPEN; 0.1942903111 / 0.1202340026 | OPEN; 0.2492530135 / 0.1139794085 |
| X35-S | OPEN; 0.457475317 / 0.3949882559 | OPEN; 0.457475317 / 0.4231995496 | OPEN; 0.5415306805 / 0.362971432 |

Both B and E+ certify 3/6 configurations, versus cold P 1/6. Their physical U agree on all six; E+ raises only X35's final qualified L, from .3949882559151472 to .42319954961578576 at U=.45747531701601785. The original relative gap falls from 13.659110945800548% to 7.492375244155952%, without a new certificate or primal improvement. Its slightly lower raw search L=.39492875817006656 distinguishes the independent proof contribution from AM/Native search progress. B/P tests the integrated main method, while E+/B isolates the complete enhancement comparison; no per-configuration best-of-B/E+ result is formed.

For the three joint-CERT E+/B pairs, E+ adds about 26.10 s on C20, 1.70 s on B20 and 6.18 s on X20; the ratios are 1.13067, 1.33574 and 1.05159. Only C20 meets the declared substantive scale \(\max\{10\text{ s},.1\times\text{faster time}\}\). The other two numerical increases remain nonmaterial. The helper and verification ledgers in the supplement retain their full costs without adding nested helper time twice. Uniform E+ is a reasonable alternative when its stronger X35 proof endpoint is prioritized. Choosing B as the main paper method balances certificate count, paid time and both endpoints; it is not a dominance theorem.

B and E+ each have lower U than P on three configurations, higher U on C35-U, and equivalent U on two. Their proof L are higher on five configurations and equivalent at the frozen numerical scale on B20. In particular, C35-U retains P's better U=.09331934374779818 against B/E+'s .12956638965196035, together with the opposite proof direction. The B/P and E+/P joint-CERT intersections each contain only B20 (1/6); their conditional time ratios supply no full-panel speedup. Every OPEN endpoint and paid cost remains included, and a single Seed does not estimate a runtime distribution.

C20, B20 and X20 finish with search L above their qualified inventory value uppers. C35's numerically near-zero inventory result is not an exact-zero physical proof. The capacity-limited B35/X35 inventory widths remain .014387103336740467/.02295563610060769. B35's floor is below final search L while its inventory upper is above it; X35's floor improves the final proof but its price remains unresolved. Earlier near-tight same-domain inventory results therefore do not bound these two remainders.

The proof-only helper adds no floor to Native rows or raw AM. Its separate return-time/floor/search-L ledger distinguishes dominated inventory values, zero optima, rejected sources and unresolved prices. A tighter inventory proof source supplies neither a physical incumbent nor an automatic complete-method benefit. These E+ observations retain their one-Seed scope.

#### Finite solver-Seed confirmation on the exposed cohort

The same six inputs were subsequently registered together for Gurobi Seeds1/2,
giving 24 additional B/P runs and twelve new paired comparisons. Historical
Seed0 qualifies under the same input, physical, method, executable, numerical
and paid-clock contracts, with matching documented runtime observations.
Each new run starts a fresh lifecycle; B recomputes and pays its own H with
seed20260626. These are six mathematical inputs with three within-input
observations each, rather than eighteen independent new inputs. No best Seed,
cross-Seed certificate, additional method or outcome-dependent stop is used.

**Table 9. Within-input paired differences in Seed order 0/1/2.** Seed 0 is historical; Seeds 1/2 are the subsequent confirmation observations. ΔU=B−P is favorable to B when negative; ΔL=B−P
is favorable when positive. Values within the frozen 1e-7 equivalence scale
are displayed as 0. Full individual U/L, raw search bounds, paid costs,
medians/ranges and binary64 values remain in the supplement.

| Configuration | B CERT /3 | P CERT /3 | ΔU: S0 / S1 / S2 | ΔL: S0 / S1 / S2 |
| --- | --- | --- | --- | --- |
| C20-S | 3 | 0 | 0 / 0 / -0.0592739276 | 0.0310463758 / 0.0336984584 / 0.0394115797 |
| B20-B | 3 | 3 | 0 / 0 / 0 | 0 / 0 / 0 |
| X20-S | 3 | 0 | -0.0132001396 / -0.0172134837 / -0.0132001396 | 0.186097975 / 0.194824544 / 0.197495547 |
| C35-U | 0 | 0 | 0.0362470459 / -0.0501944461 / -0.0386805194 | 0.0115507307 / 0.0134743346 / 0.00933437769 |
| B35-S | 0 | 0 | -0.0549627024 / -0.101715977 / -0.132960007 | 0.00625459405 / 0.00466145812 / 0.00475241402 |
| X35-S | 0 | 0 | -0.0840553635 / -0.060652829 / -0.0617878527 | 0.0320168239 / 0.0466015852 / 0.0444201335 |

At each Seed, B certifies 3/6 inputs and P 1/6. The three n20 B certificate
patterns persist, while cold P certifies only B20. B35 and X35 retain lower
B U and higher B L at every Seed, but all eighteen n35 method observations
remain OPEN. C35's primal ordering reverses: P is better at Seed0, whereas
B is better at Seeds1/2. B's C35 L remains higher at all three Seeds.
These input-specific consistencies do not establish a general success
probability or a structural cause of the observed differences.

**Table 10. Paid n20 certificate times, seconds.** A dash means OPEN, without
an imputed convergence time.

| Configuration | B T_cert: S0 / S1 / S2 | P T_cert: S0 / S1 / S2 |
| --- | --- | --- |
| C20-S | 199.7793504 / 354.3877476 / 341.81022 | — / — / — |
| B20-B | 5.058292441 / 4.963643252 / 5.277052939 | 235.8555019 / 303.0333761 / 266.8005886 |
| X20-S | 119.7493879 / 136.9986099 / 131.8292042 | — / — / — |

![Three-Seed original-objective endpoints on the six archived-source inputs. Colours identify B and cold P; circles are physical U and triangles qualified L. Filled U circles denote CERT and open circles OPEN. Dotted lines mark the pre-frozen offline feasible target. Seed 0 is historical; Seeds 1/2 were added on these same exposed inputs. Lines connect repeated observations and imply neither independent inputs nor a performance distribution.](figures/three_seed_endpoints.png)

Certificate-status consistency does not imply constant complete cost. B's
C20 and X20 times vary substantively across these observations under the
declared scale; its B20 spread is below 10 s, whereas P's B20 range is
235.8555019–303.0333761 s. Within each Seed, the joint-CERT B/P intersection
contains only B20 (1/6). Its B/P time ratios at Seeds0/1/2 are
.02144657385/.01637985662/.01977901536 and its signed paid differences are
−230.7972095/−298.0697328/−261.5235357 s. Each exceeds the 10 s substantive
scale in B's favor. These conditional comparisons supply no full-panel
speedup, and an OPEN budget is never treated as a certificate time.

The uniform offline target is the better qualified Seed0 U, frozen before
any new Optimize and absent from production. B reaches the saved target on
all three observations of each n20 input and B35; on C35 it reaches none,
and on X35 only the historical Seed0 observation reaches it. P reaches it
on all three B20 observations, two C20 observations and historical C35
Seed0, with none observed on X20/B35/X35. In particular, B's new X35 U are
both worse than its own Seed0 U while its L are stronger, despite favorable
within-Seed B/P directions. Recorded availability intervals and censoring,
not exact first-discovery times or impossible-target claims, support these
statements.

The C35 H value is .17449020363402973 at all three fixed-H-seed lifecycles.
Native improves B's U to .12956638965196035/.10742986645444105/
.10808393649972804; P's U are .09331934374779818/.15762431259566606/
.14676445594619023. The historical P fleet therefore still supplies a known
better feasible point for every B run. Its advantage is not a persistent
within-Seed P-over-B ranking. Seed0's fleets differ in ownership, service
amounts and co-served relative order simultaneously; no single operator or
route-feedback benefit is isolated. The fixed unserved-station penalty
.011402553447730399 cannot exclude attaining P's target. Setting the other
visited inventories to target gives .03359254619609878, but exceeds the
saved routes' time limits and one prefix capacity. It is neither a physical
solution nor a certificate about every legal service choice on that skeleton.

\clearpage

## 6. Mechanisms, AM and stage interpretation

### 6.1 AM rule and experimental interpretation

For finite valid child LP evidence, the actual controller uses

\[
\begin{aligned}
\Delta&=\max\{U-b,\max(\epsilon, 10^{-12})\},\\
v_j&=\operatorname{clip}_{[0,1]}((\ell_j-b)/\Delta),\qquad j=0,1,\\
\eta&=\min(v_0,v_1),\qquad
\mu=(v_0+v_1)/2,\qquad S_{\mathrm{AM}}=\eta\mu.
\end{aligned}
\]

The actual eligibility conditions, score tolerance, terminal decisions and
target continuation remain unchanged. An infeasible child invokes logical
coverage handling independently of this finite-score threshold. Missing or
invalid evidence cannot justify a split. A run without a finite gate exposure
does not test threshold sensitivity. Depth 8 and minimum width 1e-4 are fixed.
The preserved AM construction and threshold-validation evidence in the supplement supports the default .08; the bounded current study
compares .04/.08/.16 without per-instance selection.

The research control sets the actual first-class split threshold after presets; the implementation mapping and readback checks are specified in Appendix B.1.
Offline replay can describe different actions at observed states, but cannot
reuse the original post-divergence trajectory as a runtime counterfactual.
The score estimates gap-normalized two-sided bound improvement, not remaining
complete proof cost.

The Seed 0 AM comparison contains eight additional positions and twelve views after sharing the four matching default runs. The Seed 1 AM block contains four additional positions and six views, using its two independently measured Seed 1 defaults.

**Table 11. Observed Seed 0 AM score gates, actions and complete production cost.**

**Seed 0 main AM comparison**

| Role | \(\tau_{\mathrm{AM}}\) | Max gate score | Actions | Production (s) |
|---|---|---|---|---|
| K-15-S | 0.04 | 0.000356687 | native-target:1, exact-close:1 | 113.062 |
| K-15-S | 0.08 | 0.000356687 | native-target:1, exact-close:1 | 112.769 |
| K-15-S | 0.16 | 0.000356687 | native-target:1, exact-close:1 | 113.315 |
| UC-B20-B | 0.04 | 0.00031863 | split:3, native-target:1, exact-close:1 | 4.21966 |
| UC-B20-B | 0.08 | 0.00031863 | split:3, native-target:1, exact-close:1 | 4.14897 |
| UC-B20-B | 0.16 | 0.00031863 | split:3, native-target:1, exact-close:1 | 4.08117 |
| K-20-S | 0.04 | 0.000478466 | native-target:1, exact-close:1 | 1172.26 |
| K-20-S | 0.08 | 0.000478466 | native-target:1, exact-close:1 | 1172.19 |
| K-20-S | 0.16 | 0.000478466 | native-target:1, exact-close:1 | 1172.26 |
| K-35-U | 0.04 | n/a | exact-close:1 | 2371.02 |
| K-35-U | 0.08 | n/a | exact-close:1 | 2371.15 |
| K-35-U | 0.16 | n/a | exact-close:1 | 2371.03 |

Scores in this table summarize finite score gates only; all-child and finite-score ledgers are joined by decision sequence. Separate classes retain no-strict-improvement terminal, logical one/both-child infeasibility and other actions, including runs without a child decision exposure. Logical infeasibility has no finite score/margin and is independent of tau. Different thresholds need not create different actions, and no split was forced for table coverage.

K-15-S illustrates finite threshold exposure with a wide negative margin. Each Seed 0 run has one finite gate with normalized score 0.000356687; tolerance-adjusted margins at tau=.04/.08/.16 are -0.0396431 / -0.0796431 / -0.159643. All select native-target, followed by a separately classified no-strict-improvement exact-close terminal. All three qualify certificates in 113.062 / 112.769 / 113.315 s, respectively; their 0.545396 s spread is below the declared substantive-difference rule. This finite comparison reports the three actual complete runs and their observed gates; it does not establish sensitivity on other configurations.

UC-B20-B separates logical splitting from the finite score test. Each threshold run records three one-child-infeasible splits with no finite score or margin; those actions are independent of tau. The subsequent finite gate has score 0.00031863 and selects native-target at all three thresholds. Qualified certificate times are 4.21966 / 4.14897 / 4.08117 s in the same threshold order, with no substantive time difference. The split counts therefore do not establish that a finite AM score crossed a threshold.

All three K-20-S runs remain open at U=0.716807, with qualified L in [0.705356,0.705386]. The observed finite gate score is 0.000478466, below the tested thresholds. The later exact-close label names a scheduled exact solve; it does not mean that a qualified certificate was completed. These capped endpoints and unchanged finite-gate choices do not establish a general threshold ranking.

K-35-U reaches a finite no-strict-child-improvement terminal before a threshold comparison in each run. The paired child observations are present, but no finite score gate is exposed; the near-zero terminal score is not counted as a threshold test. All three remain open at U=0.692854, with L in [0.565766,0.566106]. This is distinct from both a logical-infeasibility split and a run with no recorded child decision.

Each tested threshold therefore yields two qualified certificates among the same four Seed 0 roles. The observed finite gates of K-15-S, K-20-S and UC-B20-B remain well below the smallest tested threshold; K-35-U stops at the separate no-strict-improvement test. These finite observations provide no basis for replacing the accepted \(\tau_{\mathrm{AM}}=.08\), while leaving sensitivity at unvisited states outside the claim. The limited Seed 1 checks remain separately identified.

The limited Seed 1 AM repeat preserves these reached action classes on both selected roles: one finite native-target gate and one no-strict terminal, plus three logical splits on UC-B20-B. All six observations certify, with no substantive within-role time difference across the three thresholds. Their finite scores remain below .04 with negative margins; the repeat does not test unvisited near-threshold states.

Across the eighteen AM views, all 51 recorded eligibility evaluations are reconstructible and none rejects depth 8 or width 1e-4. Across all 58 current outer-controller runs, the 125 recorded evaluations likewise contain no such rejection. These are checks of recorded guards, not proof that no unrecorded attempt occurred or that the limits are irrelevant elsewhere.

### 6.2 Conditional mechanism results

The Seed 0 mechanism comparison adds sixteen positions to four shared defaults, giving twenty views. The separately reported Seed 1 block adds eight positions to its two actual Seed 1 defaults, giving ten views. Root values below are observed complete LP optima, while the final search bounds discussed in the text are different quantities.

**Table 12. Observed Seed 0 initial LP optima for the conditional mechanism controls.**

| Role | Full | Root only | Minus A/B | Minus \(C_R\) | Minus \(C_G\) |
|---|---|---|---|---|---|
| K-15-S | 0.167137 | 0.167137 | 0.167016 | 0.167137 | 0.167137 |
| UC-B20-B | 0.479076 | 0.479076 | 0.479076 | 0.479076 | 0.479076 |
| K-20-S | 0.195149 | 0.195149 | 0.193825 | 0.195149 | 0.195149 |
| K-35-U | 0.200178 | 0.200178 | 0.200178 | 0.200178 | 0.200178 |

The entries are observed initial LP optima, with n/a for an unexposed complete point. Numerical deletion attribution also requires the paired domain, objective, cutoff and own-H checks in the supplement. Full per-variant complete clocks, returned effort counters and limited Seed 1 observations are retained there.

All 24 paired root comparisons meet the saved common-domain/objective/cutoff and complete-own-H conditions. A/B deletion lowers the initial optimum by 0.000121173 on K-15-S and 0.00132415 on K-20-S. No initial objective increment above tolerance 1e-7 is observed for either resource-group or geometry/objective-group retention on the four Seed 0 roles; the selected Seed 1 roots reproduce these patterns. Equal initial optimal objective values do not establish that retained rows are slack, inactive or redundant; the optimal face and later search can change. Final lower-bound changes cannot be relabelled as initial-root increments.

K-15-S exposes mixed conditional complete-method effects. All five methods qualify their own certificates at the same objective. The full method takes 112.769 s; deleting A/B or \(C_G\) takes 128.325 / 143.15 s, respectively, while deleting \(C_R\) takes 75.1064 s. Those three differences are substantive under the declared rule, including the deletion advantage for \(C_R\). GI-TBC-R takes 112.649 s, a nonmaterial difference from the full method. These contrasts retain the rest of the representation and complete own H, so their directions are conditional rather than additive component shares.

**Table 13. Conditional Seed 0 construction cost and returned solver effort on K-15-S.**

| K-15-S variant | Canonical generation (s) | Explicit LP Runtime (s) | MIP Runtime sum (s) | Work sum | Native B&B nodes sum |
|---|---|---|---|---|---|
| GI-TBC | 0.414438 | 0.196 | 110.549 | 160.926 | 48701 |
| GI-TBC-R | 0.14161 | 0.0600002 | 110.807 | 160.157 | 48700 |
| minus A/B | 0.413122 | 0.16 | 126.181 | 186.183 | 55424 |
| minus \(C_R\) | 0.391302 | 0.178 | 73.048 | 109.31 | 29036 |
| minus \(C_G\) | 0.271173 | 0.169 | 141.108 | 204.7 | 68560 |

The K-15-S \(C_R\) deletion reversal is accompanied by a change mainly inside native MIP search: summed returned MIP Runtime falls from 110.549 to 73.048 s, Work from 160.926 to 109.31, and summed native B&B nodes from 48701 to 29036. The cumulative canonical-generation timer differs by only 0.0231363 s. Conversely, \(C_G\) deletion reduces timed canonical generation to 0.271173 s but increases returned MIP Runtime to 141.108 s and the complete certificate cost. These matched conditional observations separate artifact-generation cost from the native search that follows. They do not identify an additive causal share or a net controller overhead. The diagnostics are nested inside production; explicit LP counts omit internal MIP relaxations, target-MIP families are included in the MIP sum, Work is not seconds, and node sums are per-call native counters rather than unique nodes of the outer interval tree. The full cost tables and actual phase statuses are retained in the supplement.

The preselected Seed 1 mechanism repeat reverses all three K-15-S row-deletion time directions. Full GI-TBC certifies in 115.444 s, versus 93.6997/132.475/99.6006 s after A/B, resource-group and geometry/objective-group deletion. Each difference is substantive: A/B and geometry/objective deletion are now faster, while resource-group deletion is slower. The corresponding returned MIP Runtime sums are 113.257 s for full and 91.513/130.239/97.652 s after deletion. The same initial-root pattern, independently paid H and recorded action classes coexist with these reversed native search costs. Root-only takes 113.58 s, a nonmaterial difference. The two Seeds therefore support conditional mixed effects, not a stable runtime ranking or an additive component share.

All five UC-B20-B methods qualify certificates between 1.87206 and 4.91775 s. Every pairwise difference is below the ten-second absolute floor, so this tiny case supplies no substantive complete-cost ranking. The logical split activity reported above and the net benefit of the whole outer package are assessed separately; visible outer actions alone do not determine a full-method speed advantage.

The \(C_R\) result differs on K-20-S. Both runs remain open at the same verified U=0.716807, while the full method has qualified L=0.705356 versus 0.703444 after deletion. Thus the deletion advantage in K-15-S certificate cost coexists with better finite-budget dual progress for the full method on K-20-S. These are final-endpoint observations at matched complete caps; root-LP attribution additionally requires its own matched-scope evidence.

The whole K-20-S contrast also retains an adverse endpoint for the full controller: GI-TBC-R has the same U and final qualified L=0.706405, above the full method's 0.705356. A/B and \(C_G\) deletion end at L=0.704128/0.705296. All five runs remain open. These are final qualified bounds from search under the registered budget; numerical root-LP optima require their separate matched-scope evidence. No certificate-time ranking follows. Row strengthening and outer scheduling therefore have distinct conditional interpretations.

**Table 14. Opposed Seed 0 open endpoints in the K-35-U mechanism panel.**

| K-35-U variant | Own feasible U | Qualified final L | Status |
|---|---|---|---|
| GI-TBC | 0.692854 | 0.565766 | open |
| GI-TBC-R | 0.692854 | 0.566106 | open |
| minus A/B | 0.654639 | 0.564355 | open |
| minus \(C_R\) | 0.689763 | 0.536996 | open |
| minus \(C_G\) | 0.666262 | 0.55098 | open |

K-35-U exposes an opposed-endpoint result for \(C_G\) deletion. The full method reports U/L=0.692854/0.565766, versus 0.666262/0.55098 after deletion. The deleted model finds a better feasible objective, while the full method retains the stronger qualified final lower bound. A smaller signed gap after deletion therefore does not establish endpoint dominance. Both ledgers record one no-strict-improvement exact-close action under the same outer policy; the native searches remain separate and both runs remain open. No certificate-time comparison is assigned.

A/B deletion also has opposed endpoints on K-35-U: its verified own U/L=0.654639/0.564355 improves the feasible objective by 0.0382155, while the full method retains L higher by 0.00141073. Both runs remain open. Thus the full-method certificate advantage of A/B on K-15-S and its higher final bound on K-20-S coexist with a better K-35-U feasible objective after deletion. A smaller deletion gap does not combine these distinct endpoint directions into dominance, and no instance-specific setting is selected.

\(C_R\) deletion has U/L=0.689763/0.536996 on this larger role. All three row-group deletions therefore improve the saved feasible objective while weakening the qualified final lower endpoint relative to the full formulation. This repeated within-role primal/dual opposition is retained alongside the easier certificate-cost advantages and the K-15-S \(C_R\) reversal. It does not justify an instance-specific setting or a complete-proof-time ordering.

The legal root-only comparison also retains a higher final lower endpoint on K-35-U: GI-TBC-R reports U/L=0.692854/0.566106, at the same U as the full method and a final L higher by 0.000340054. Both runs remain open under the matched complete cap. Together with K-20-S, these selected hard-role observations show no full-controller endpoint advantage over root-only at the saved Seed 0 endpoints. They do not compare initial root-LP optima or establish an eventual proof-time ordering; the remaining mechanism and limited Seed 1 findings retain their separate scopes.

Across these four preselected Seed 0 roles, no substantive full-over-root certificate-cost advantage is observed: the two easier roles certify with nonmaterial differences, while both harder roles remain open and root-only has the same U with slightly higher final L. The strengthened root already suffices for the two easier certificates in this panel. Thus visible outer activity and the strong integrated GI-TBC results relative to compact controls do not assign a separate incremental speed advantage to the outer package here. The accepted post-R130 attribution history remains relevant with its own version and cases; the current limited Seed 1 repeats are reported separately.

The row-deletion controls keep the configured outer policy fixed, but can change its reached states and realized actions. On K-15-S and K-20-S, A/B deletion records only a no-strict-improvement terminal, while full, \(C_R\)-deleted and \(C_G\)-deleted runs each also record one finite native-target gate. On UC-B20-B, each of the four outer variants records three logical-infeasibility splits, one finite gate and one terminal. On K-35-U, each records only the no-strict terminal; root-only has no child-AM record on any role. The complete Seed 0 mechanism observations therefore contain ten finite gates, sixteen terminals and twelve logical splits. These counts describe reached decisions, not independent instances. Conditional formulation effects include any induced control-path change; identical configured policy is not identical realized scheduling or native search.

The saved initial domain/objective/cutoff and independently paid H determine which numerical roots may be compared; the full paired report flags their actual matches. Root values require an observed OPTIMAL LP; n/a means no complete applicable point was exposed. The ideal deletion relation is not a runtime theorem. Work/nodes, LP/MIP time, model-construction cost, complete own H and outer actions accompany these conditional contrasts; no additive allocation of total speed-up is made. Depth 8 / minimum width 1e-4 remain fixed. Recorded eligibility rows are joined to retained scheduler-epoch geometry; a source-rejection reset or missing leaf makes the reconstruction unknown. Eligible child work may stop before its ledger row, so missing records do not prove no attempted test. The depth guard short-circuits the width check; a width that would also reject after depth failure is not counted as another causal trigger. Zero-width proofs without recorded guard evaluations are not counted as width-limit triggers. Final materialized-leaf and decision-parent/probed-child depths are distinct observations. The full-versus-variant results and exposure limits are interpreted in the stage decision and supplement.

\clearpage

### 6.3 Mechanism synthesis and boundaries

**Table 15. Mechanisms, mathematical roles, supporting evidence and boundaries.**

| Mechanism | Mathematical role | Corresponding experiment | Supported conclusion | Boundary |
|---|---|---|---|---|
| Complete own H | Constructs and checks its own feasible Start; supplies no lower-bound proof | P/PS across main panels and four Seed 1 triplets | PS materially wins X-35-B; P improves both endpoints on K-20-S and R-X20-S-T2 | Startup package only; no operator or H-seed attribution |
| Outer interval controller | Preserves improving-interval coverage through probing, targeting and exact continuation | Full/GI-TBC-R: four Seed 0 roles, two Seed 1 repeats | No substantive certificate-cost gain here; both hard Seed 0 roles have higher root-only final L | Reached actions do not establish net benefit; prior versioned evidence remains separate |
| Shared-state A/B links | Valid movement/visit equalities connect service to inventory mixtures | A/B deletion: four Seed 0 roles, two Seed 1 repeats | Two initial LP increments; K-15-S time direction reverses across Seeds; full K-20-S has higher final L | Core products retained; unique one-way service preserves implicit quantity integrality |
| Resource group \(C_R\) | Ordered-supply and pair-cover/handling inequalities strengthen necessary resource conditions | Single-group deletion: four Seed 0 roles, two Seed 1 repeats; pair-only unchanged | K-15-S deletion wins Seed 0 and loses Seed 1; full K-20-S has higher final L; initial increments undetected | Valid LP tightening need not accelerate search; no additive shares |
| Geometry/objective group \(C_G\) | Spread, centering and objective estimators use dedicated auxiliaries | Single-group deletion: four Seed 0 roles, two Seed 1 repeats; original domains/products retained | K-15-S time direction reverses; K-35-U deletion improves U and weakens L; initial increments undetected | This group does not contain all fairness structure; endpoint opposition persists |
| AM score and logic | Normalized child-bound score applies after eligibility, validity and terminal tests | Three thresholds: four Seed 0 roles, two Seed 1 repeats | Finite scores stay below .04; logical splits hold separately; K-35-U stops before its threshold test | Observed unchanged actions do not prove global robustness or small proof cost |

These rows summarize the observed conditional findings. The full Seed 0 and separately identified Seed 1 tables retain every selected role, and the accompanying paired/root and cost reports determine where numerical root attribution is actually exposed. Shared inventory-state/core products are retained throughout the current mechanism study, so they have no isolated runtime effect assigned here.

### 6.4 Structural information and complete algorithm value

The structural experiments distinguish exclusion of a saved point,
improvement of a freely reoptimized same-scope LP, improvement of a paid
Native call, improvement of the complete own-H method, and confirmation
outside candidate development. These are different evidence levels.
Inventory-budget certificate gains, selected reciprocal-normalization and
Gini-deviation gains, and inventory-objective proof-floor increments remain
positive results. Their adverse and mixed complete outcomes limit uniform
adoption.

The physical projection, an integer resource necessary domain and an inventory
necessary domain can be ordered only with a proved common objective/scope
embedding. A continuous expression replacement does not acquire an ordering
from integer equivalence alone. The retained four-station example has an exact
\(1/4\) original-objective gap on its fixed-positive-total slice even with the
complete joint service hull. At the loaded coefficient the inherited proof
also minimizes over all legal loaded-return totals; the physical problem is
not newly restricted to that slice. It distinguishes service compatibility from the integer
objective epigraph without needing a changing Gini denominator. The [fixed four-station derivation](https://github.com/yifanXovo/TailoredExact/blob/de01e8fb27a954d031abac5fe99442d6c8d29d44/results/unified_exact_round133/joint_objective_gap_note.md) gives the instance, feasible mixtures and full loaded-return lower proof. Shared-state
movement/visit links strengthen the fractional representation; they remain
unnecessary as premises of the implicit-integrality lemma.

The full-physical shared-G completion experiment illustrates this distinction.
Both saved points fail their fixed completion tests, but free reoptimization
on one domain returns the same qualified LP value; the other gains about
\(.00018725\). A projected row retains about 87% of that scoped increment.
Removing the complete duration rows removes the increment conditional on
the remaining constraints; it does not prove time alone sufficient or
separate travel from handling. In six complete primary-role arms the tested
completion has worse U than both fresh controls, equal proof L and no
certificate. Four conditional positions remain unstarted. The supplement
retains the source identities, row size, positive increment and adverse
complete outcomes.

For one common global inventory relaxation and original physical problem,
\(L_I\le f_I^*\le U_I\) and \(f_I^*\le f_P^*\le U_P\) give

\[
 U_P-L_I=(U_P-f_P^*)+(f_P^*-f_I^*)+(f_I^*-L_I).
\]

Only the last term is controlled by \(U_I-L_I\). A tightly priced inventory
value therefore limits the remaining numerical precision of that same
scalar floor, while incumbent suboptimality can still contribute to the
complete gap. This conclusion is scope-specific: the later B35/X35 inventory
prices retain widths about .0143871/.0229556, so the earlier near-tight
remainder cannot be assigned to them. Local interval/cutoff bounds need the
coverage contract before a global interpretation. A small continuous-Q
increment is not an upper bound on the integer physical gap. The supplement
preserves the exact domains, qualifications and both positive and negative
complete results; none of these observations excludes all future structural
progress.

## 7. Conclusions and implications

Physical equivalence, the shared inventory-state formulation and complete
interval coverage provide the algorithmic foundation. The historical breadth
panel certifies 9/12 inputs versus cold P 7/12 and paid-start PS 7/12; the
separate positive-resource panel certifies 4/8 versus 0/8 and 0/8. Their
versions and denominators remain distinct from the exposed-cohort repeats.
Conditional mechanism effects, time reversals and adverse endpoints remain
part of the evidence, rather than additive component shares or new theorems.

The completed three-Seed cohort supports a precise finite claim for uniform
GI-TBC/B: the n20 certificate patterns repeat, B35/X35 retain favorable
primal and proof directions, and B's C35 proof advantage persists. It does
not support a universal primal ordering, constant certificate time or
certification of the n35 inputs. C35 reverses the feasible-solution ranking,
and the known-feasible-target diagnostic exposes unreproduced absolute
primal values even where within-Seed B/P signs agree. These observations
support B as the paper's main method within the tested scope, without a
dominance theorem or population-level robustness claim.

E+ remains a separately named limited proof enhancement. Its historical
X35 lower-bound gain and earlier qualified inventory-proof gains are real;
the six Seed0 physical upper endpoints equal B's. Only C20's paired
certificate-time increase meets the substantive scale. The new B/P Seeds
do not establish E+ robustness. The unresolved B35/X35 inventory widths
also prevent transferring an earlier near-tight inventory remainder to this
cohort. A valid relaxation, stronger local information and improved complete
paid performance remain different conclusions.

The studied main algorithm is uniform GI-TBC/B. Its mathematical definition, measured implementation and study-specific configurations are identified separately in the reproducibility material. The shared-state representation and complete coverage make an exact method for the stated operations; the current controls leave the outer controller's independent computational value unresolved.

### 7.1 Remaining scientific limits

A suboptimal feasible incumbent and an unresolved proof lower are different
shortcomings. C35's historical P fleet witnesses suboptimality of all three
B incumbents, while the within-Seed P/B ordering changes. Joint ownership,
relative order and integer service differences do not identify a causal
operator. A weak necessary penalty or an infeasible target-inventory vector
also cannot settle the whole fixed-skeleton value question.

Finite repeated endpoints cannot identify structural causality or an
eventual proof-time ranking. Any future claim of improved joint service
information requires its own physical-domain contract and complete paid
evidence. Existing fixed-route quantity and route-feedback objects already
address parts of that question; their positive, mixed and adverse evidence
remains relevant. The archived diagnostic prerequisites are in the research
navigation, rather than a new mechanism or an executed query in this study.
