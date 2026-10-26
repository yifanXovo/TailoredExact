# An inventory-state exact algorithm for bicycle redistribution with ratio-Gini and target-deviation costs

## Abstract

Static bicycle redistribution couples station inventory decisions with vehicle routes, intermediate loads and handling time. We study the minimization of the Gini dispersion of inventory-to-target ratios plus weighted relative target deviation, with empty departure, loaded return and unique nonzero one-way service. The proposed GI-TBC algorithm, implemented as S2, shares finite inventory states between service and objective representations and controls a complete collection of Gini intervals around native LP and MIP solves. We distinguish the problem-specific links and coverage arguments from standard value disjunction and product linearization. Historical validation on twelve fixed inputs at two solver Seeds produced 17/24 qualified S2 certificates and 9/24 cold-compact certificates under its original version and policy. {{FINAL_ABSTRACT}} A separate threshold-count inequality connects the global inventory budget to the Gini numerator without new variables. On two complete tiny joint-service references it raises the exact original-objective relaxation by 3/16, closing 75% of a known integer-objective gap; {{ROOT_ABSTRACT}} The evidence supports the complete algorithm within the stated test scope, with adverse and unresolved observations retained.

## 1. Introduction

A redistribution fleet changes the quality of service that station inventories can provide, but a desired inventory vector is useful only when vehicles can realize it. Pickups precede the deliveries they supply, vehicle capacities apply at every route prefix, and handling time competes with travel. The inventory vector also determines both the numerator and denominator of a ratio-Gini objective. This creates an interaction between physical routing, discrete inventory and nonlinear dispersion that a target-allocation model alone cannot capture.

We study a specified static redistribution model with integer inventory, empty vehicle departure, loaded return and at most one nonzero service at a station. Its objective combines dispersion in inventory-to-target ratios with weighted relative target deviation. Equal but inadequate ratios have zero dispersion, so the target-deviation term is essential to interpreting a plan. We use the physical model and its supplied heuristic implementation as the starting problem, and claim an exact-method contribution rather than invention of the redistribution problem, the Gini index or the startup heuristic. The implementation lineage is identified in the supporting reproducibility material [@frozenImplementation].

The contribution has three parts. First, the inventory state that represents a station's final stock also represents its pickup or delivery and unique visit. This connects discrete objective information to the resources that make it attainable. Second, GI-TBC combines these links, valid physical and objective rows, a fully paid feasible startup and complete interval coverage into one specified algorithm. Physical feasibility, native-source qualification and independent optimality arguments are separate: a rejected native bound cannot close a region, while an independently verified zero objective can meet the global nonnegative floor. Third, the computational study assesses complete certification cost and retained open endpoints, and uses controlled references to explain both benefits and limits. A new research inequality is evaluated separately from the production method.

The method uses the same representation, pair-support policy and controller for all evaluated inputs. It has no instance-identity or size-based dispatch and no elapsed-time switch between algorithms. A finite run limit is an experimental resource constraint. We do not require every observation to favor S2: paid-start compact reversals, positive-objective size limits and unresolved native numerical mechanisms are part of the assessment.

### 1.1 Relation to previous work

Static bike redistribution has been studied with alternative target, visit and vehicle conventions. Raviv et al. model static repositioning; Chemla et al. address static rebalancing; Erdoğan et al. treat demand intervals and an exact rebalancing algorithm [@raviv2013; @chemla2013; @erdogan2014; @erdogan2015]. Schuijbroek et al. connect inventory requirements to vehicle routing [@schuijbroek2017]. Forbidden temporary operations, multiple visits and robust inventories yield different physical feasible sets [@bruck2019; @bulhoes2018; @bruck2025]. A disjunctive formulation with demand intervals supplies another relevant representation perspective [@ikonen2025]. The literature-access table in the supplement identifies the source version and level actually inspected; no unmatched speed comparison follows from similar station counts.

Equity objectives require similar care. Vehicle-workload equity differs from station-ratio dispersion [@matl2018]. Recent fairness-aware and equity-based micromobility models motivate attention to distributional effects, but their accessible abstracts do not establish equivalence to the present inventory, visit or objective definitions [@qiao2026; @caggiani2026]. We make no claim to the first fairness or Gini objective in rebalancing.

The representation uses established McCormick and value-disjunction tools [@mccormick1976; @gupte2013; @koppe2008]. Their presence alone is not a scientific contribution or a proof of strict relaxation improvement. The relevant question is what the common state links to service and resources on the same feasible set. Likewise, threshold representations of Gini dispersion and budget-derived cardinality restrictions have established antecedents [@yitzhakiSchechtman2013; @yuAhmed2017]. Section 6 derives the particular aggregate inventory inequality, proves its finite-reference increment and states the limited novelty conclusion.

## 2. Physical model and objective

Let \(N\) contain \(n\) stations and let \(0\) be the depot. Station \(i\) has integer initial inventory \(b_i\), capacity \(C_i\), integer target \(D_i>0\), and weight \(\omega_i\ge0\). Vehicle \(k\) has capacity \(Q_k\) and route-duration limit \(T\). Routes depart empty. A station can be served by at most one vehicle, in one direction, with a nonzero operation. Loaded return is allowed and its unloading time is counted. The depot enters neither target deviation nor dispersion.

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

This is ratio dispersion and two-sided relative target deviation. It is not a direct measure of population equity, rental failure or travel burden. Put \(\Omega=\sum_i\omega_i>0\), \(P_{\rm avg}=P/\Omega\) and \(\rho=\lambda\Omega\). Then \(F=G+\rho P_{\rm avg}\). The generator normalizes weights by their maximum, so equal \(\lambda\) across inputs does not hold \(\rho\) fixed. Sensitivity in Section 5.4 changes \(\lambda\) within a fixed physical instance.

**Proposition 1 (an independent zero certificate).** Under the stated nonnegative objective premises, a complete physically verified fleet with exact objective zero is globally optimal, independently of the native search source.

**Proof.** For every original physical solution, \(F\ge0\). The verified fleet gives \(F^*\le0\), so \(0\le F^*\le0\). With positive \(\lambda\) and positive weights, integer equality \(Y_i=D_i\) for every station is a sufficient exact-zero condition. More generally equal exact ratios give zero Gini, and every positive-weight penalized station must meet its target. The implementation checks these conditions using integer stock arithmetic, then repeats the complete physical-fleet verification. A merely small positive floating objective does not establish exact zero. \(\square\)

The numerical \(\varepsilon\)-certificate policy is separate. A source-rejected positive solution without a sufficient independent bound remains open. Certification cost includes the verification needed to establish the proof, normal native cleanup and required output. A later offline audit cannot backdate a production proof.

## 3. Shared inventory states and the S2 algorithm

For the legal finite inventory domain \(\mathcal Y_i\), binary selectors \(s_{iy}\) and continuous \(q_{iy}\) represent stock and products on a Gini interval \([\alpha,\beta]\):

\[
\sum_y s_{iy}=1,\quad Y_i=\sum_y ys_{iy},\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
\sum_yq_{iy}=g,\quad Z_i=\sum_y yq_{iy}.
\]

At an integer state, \(Z_i=gY_i\). The same state supports the service equations

\[
\sum_kp_{ki}=\sum_y(b_i-y)^+s_{iy},\quad
\sum_kd_{ki}=\sum_y(y-b_i)^+s_{iy},\quad
\sum_kz_{ki}=\sum_{y\ne b_i}s_{iy}.
\]

These links connect objective mixtures to movement and service. They are not the convex hull of all vehicle routes. In isolation, a finite-state product block with the same extreme stock bounds projects to the McCormick rectangle: its four corner graph points give one inclusion, and every state line lies in the rectangle hull, giving the other. An advantage must therefore come from the links, domain information or complete search, rather than the VD-P label alone.

S2 retains the A/B links, original integer route/inventory/assignment/direction logic, continuous quantities, ordered supply, valid objective rows and two-station support. It omits three-station support uniformly. Appendix A derives each strengthening family and its physical embedding. The repository's historical ENS-C default remains a distinct algorithm identity.

The startup \(H\) is a finite construction and descent procedure. It completes a joint insertion and 24 shuffled station/separator orders plus a constructive order, fully decodes them, applies guided first-improvement descent, and closes physical quantity/insertion and neutral balanced/exchange moves. The active path has no genetic generations. It provides a verified feasible upper bound and a possible MIP Start; it is never credited with a positive lower bound. Each S2 and paid-start compact run pays for its own complete \(H\).

The controller starts from the complete potentially improving domain \([0,\min\{U,(n-1)/n\}]\). It maintains incumbent epoch, valid cutoff complements and complete interval coverage. A local bound is used only for its model, interval, cutoff and qualified source. Split children replace a parent atomically only after complete coverage and both results are checked. NEXT and child-target values are requests, rather than proof that a milestone was reached.

~~~text
Algorithm 1  S2 / GI-TBC
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

This proposition does not turn floating-point native calculations into exact rational proofs. Numerical qualification, physical objective agreement and lifecycle evidence are additional implementation conditions. The final implementation separates ordinary positive-objective native/outer certificates from Proposition 1. Supporting material records numerical anomalies and version corrections without making them algorithmic contributions.

## 4. Computational design

P is an independently started cold original compact model, with no \(H\) or Start. PS pays its own complete \(H\) and then solves that original compact model. S2 pays its own \(H\) and complete interval method. All native solves are single-threaded and run serially with the same fixed parameter policy. No fleet, bound, tree or Start passes across methods, Seeds or objective weights. A common complete-production cap includes startup, modeling, online checks, solving, proof formation, cleanup and normal required output. Postproduction verification and delivery are reported separately.

We distinguish three evidence layers. R130-R132 provide the historical breadth and mechanism controls under their own executable, certificate policy and timing environment. R133 supplies finite source/correctness repair checks and a four-pair version bridge. The present final-version panel supplies targeted confirmation on six already known roles; it is not a holdout or a substitute for a broad benchmark. Solver Seeds are repeated runs on fixed inputs, not independent problem samples. Geographic station coordinates and synthetic inventories, targets and weights are distinguished in the input manifests.

The final panel was fixed before new results: SM-B10-B uses two opposite method-order repetitions at each Seed 0/1, with P/S2 and a 90-second cap; K-15-S uses P/PS/S2 at 600 seconds; UC-B20-B uses P/S2 at 1,200 seconds; K-35-U and X-35-U use P/S2 at 2,400 seconds; X-35-B uses P/PS/S2 at 2,400 seconds. There are 32 method positions. Four additional S2 runs at \(\lambda=.075,.30\) supplement the \(.15\) Seed0 observations for K-15-S and UC-B20-B. The finite research LPs in Section 6 use a separate model copy, with no production TC row.

Certification is assessed before time. An open run has no certification time; neither a time cap nor a feasible incumbent time is substituted for one. We report signed \(U-L\), retaining tiny tolerated negative values. For two certified final-panel methods, a difference is labelled substantive when

\[
t_{\rm slow}-t_{\rm fast}\ge\max\{10\text{ s},0.10t_{\rm fast}\}.
\]

The micro panel instead shows every absolute repeated time directly. A direction and its size are distinct. Historical labels retain their original definitions. Timing changes across historical environments are descriptive, while matched methods within a final-panel comparison share its cap and environment.

## 5. Complete-method and operational results

### 5.1 Historical breadth and attribution

The R132 twelve-input/two-Seed validation has 24 S2 and 24 P observations and 12 PS observations. Its original qualified certificate counts are 17/24, 9/24 and 4/12. S2/P has 16 favorable time/certificate directions, one adverse direction, six both-open comparisons and one comparison ineligible under its source policy. The excluded S2 observation has its own legal zero fleet but no production certificate qualified by that historical policy. These counts remain historical; the new independent-proof rule does not rewrite them.

Earlier six-role final-version evidence and the support-policy study show useful complete-method performance, but PS reversals matter. PS and inclusive-root controls establish that an initial feasible solution does not explain every S2 gain. They do not isolate a statistically or practically strong independent speed benefit from the outer controller. Equivalent-expression controls have mixed cost effects. S2 is supported as an integrated method; component-level causality requires its corresponding matched controls.

R133 completed 14 exposed implementation/failure-handling positions: eight certificates, five qualified-open outcomes and one source-rejected safe-open outcome. Its four complete old/new S2 pairs had two time directions each way, all close under that protocol, with maximum slowdown about 1.264 seconds or 0.128%. Those healthy checks were reused rather than repeated. The present change adds independent proof finalization and leaves the production matrices, \(H\), representation, support, search and numerical tolerances fixed.

### 5.2 Final-version confirmation

{{C_RESULTS}}

{{C_MAIN_TABLE}}

The full per-arm table in the supplement includes every micro repetition, certificate class, endpoint and complete production/verification cost. Source-rejected native conclusions remain rejected even where an independent exact-zero certificate exists. Actual split, child-target and cache observations describe exposed controller behavior rather than proving an independent controller speed effect. No natural NEXT observation is required to complete this finite confirmation.

### 5.3 Size and physical interpretation

{{OPERATIONAL_RESULTS}}

The positive-objective 35-station boundary differs from a 35-station exact-zero solution. A positive qualified lower bound in K-35-U has its actual native/cover source in the per-arm evidence. K-35-B's optimum class remains unconfirmed; a surplus inventory label or an unsuccessful search does not prove a positive optimum. Loaded-return feasibility and cumulative pickup must also be interpreted physically: an existing legal fleet picks up 58 units with vehicle capacity 20 by unloading at intermediate stations, and returns stock to the depot. This illustrates capacity reuse rather than a capacity violation.

### 5.4 Within-instance objective weights

For a fixed physical feasible set and \(0<\rho_a<\rho_b\), let \(x_a,x_b\) be globally optimal. Write \(\Delta P=P_{\rm avg}(x_a)-P_{\rm avg}(x_b)\) and \(\Delta G=G(x_b)-G(x_a)\). The two optimality inequalities give

\[
\Delta P\ge0,\qquad \rho_a\Delta P\le\Delta G\le\rho_b\Delta P.
\]

Indeed, optimality at \(\rho_a\) gives the lower inequality, optimality at \(\rho_b\) gives the upper one, and their compatibility yields \((\rho_b-\rho_a)\Delta P\ge0\). Increasing the penalty weight therefore weakly reduces average relative deviation and weakly increases Gini among global optima; a platform and multiple optima are allowed.

If only feasible solutions with qualified objective errors \(\varepsilon_a,\varepsilon_b\ge0\) are known, the justified statements are

\[
\rho_a\Delta P-\varepsilon_a\le\Delta G\le\rho_b\Delta P+\varepsilon_b,
\qquad
\Delta P\ge-\frac{\varepsilon_a+\varepsilon_b}{\rho_b-\rho_a}.
\]

Here errors must be supported by valid original-objective upper/lower bounds and their numerical policy. A primal feasibility tolerance is not an objective-error bound.

{{D_RESULTS}}

Figure 1 locates all six measured points. Connecting segments guide the eye and do not estimate an unobserved optimal frontier.

{{D_TABLE}}

![Within-instance changes in ratio-Gini and average target deviation. Labels identify lambda; filled symbols are certified observations and open symbols are feasible uncertified observations.](figures/weight_tradeoff.png)

## 6. Inventory-threshold counting: an independent research result

### 6.1 Construction and validity

Let the legal finite supports \(\mathcal Y_i\) contain every physical stock in the applicable domain, including all donors and receivers. Put \(m_i=\min\mathcal Y_i\) and \(R=B-\sum_i m_i\). If \(R<0\), this inventory domain is empty. Otherwise sort the distinct allowed positive ratios as \(0=t_0<t_1<\cdots<t_L\), let \(\Delta_\ell=t_\ell-t_{\ell-1}\), and define \(K_\ell=\#\{i:Y_i/D_i\ge t_\ell\}\).

**Proposition 3 (threshold identities and TC).** At integer inventory points,

\[
S=\sum_\ell\Delta_\ell K_\ell,\qquad
A=\sum_\ell\Delta_\ell K_\ell(n-K_\ell).
\]

For each threshold, count stations already above it at \(m_i\). For every other station that can reach it, find the smallest actual allowed state \(a_{i\ell}\) above it, with incremental inventory cost \(a_{i\ell}-m_i>0\). Let \(u_\ell\) be the forced count plus the largest number of the cheapest increments that fit \(R\). Then the following single aggregate row is valid:

\[
\sum_{i<j}H_{ij}\ge
\sum_\ell\Delta_\ell(n-u_\ell)
\sum_i\sum_{y\in\mathcal Y_i:\,y/D_i\ge t_\ell}s_{iy}.
\tag{TC}
\]

**Proof.** A station contributes its ratio's height to the first sum. For a pair, the threshold levels between its two ratios contribute exactly their absolute difference; at a level there are \(K_\ell(n-K_\ell)\) high/low pairs. Any active set pays at least its forced baseline plus the specified minimum increments, hence \(K_\ell\le u_\ell\). Therefore \(K_\ell(n-K_\ell)\ge(n-u_\ell)K_\ell\). Sum over thresholds, use \(\sum H\ge A\), and linearly extend the integer inequality through the state selectors. \(\square\)

Here \(H_{ij}\) is a ratio-difference epigraph variable, not the startup \(H\). The right side can be preaggregated to \(\sum_{i,y}c_{iy}s_{iy}\), without new variables or a new combinatorial DP. Construction uses \(O(Ln\log n)\) threshold-count work plus state lookup/coefficient accumulation on explicit supports. This is not an input-bit-complexity claim for binary-encoded capacities. A leaf-specific support gives a leaf-specific row and cannot be moved outside its valid domain. At \(S=0\) its right side is zero.

The integer identity does not identify fractional threshold counts computed from LP state marginals with the threshold counts of the mean inventory ratios. Heterogeneous targets are allowed. For a strict comparison on a loaded matrix, the construction uses the exact rational interpretation of its ratio coefficient \(r_i=\widehat c_iY_i\) and state ratio \(\widehat c_i y\), rather than mixing independently rounded ideal ratios. Nonnegative state variables permit downward rounding of the aggregate TC and old state-penalty coefficients. Exact threshold decisions, loaded coefficients and actual written values are retained.

The threshold/CDF representation is an established way to express Gini dispersion [@yitzhakiSchechtman2013]. The sorted-increment count is a knapsack cardinality bound; Yu and Ahmed use such budget-derived cardinality information in concave epigraph formulations [@yuAhmed2017]. The chord bound is elementary. Our claim concerns their specified inventory-state combination and the comparisons below, rather than first discovery of these tools or a completed literature priority claim.

### 6.2 Strict increment on two complete tiny references

J2 and J3 have four stations, unit targets and weights, stock states \(0,1,2\), budget \(B=3\), and actual \(g\)-interval \([0,3/4]\). Their full common reference includes current S2 rows, complete per-vehicle service hulls, theta consistency, all tiny station-event ranks, cutset rows and complete fleet-pair service marginals. We additionally retain the old state-penalty lower bound and complete R88 pairwise CDF/product controls. This explicitly named reference is not the closure of every historical oracle.

The two threshold counts are bounded by 3 and 1, so TC is

\[
\sum_{i<j}H_{ij}\ge\sum_i(s_{i1}+4s_{i2}).
\]

Mix the four real fleets with inventories \((0,1,1,1),(1,0,1,1),(1,1,0,1),(1,1,1,0)\) equally. Their route, load, owner, theta and state extensions give \(s_{i0}=1/4,s_{i1}=3/4,s_{i2}=0\), \(Y_i=r_i=3/4\), \(e_i=1/4\). With \(g=q=Z=H=W=0\), this is a complete old-reference feasible point with objective \(\widehat\lambda\), the exact loaded binary64 value of .15. The old state penalty and complete CDF controls still hold. Sparse CDF and q-CDF prefix variables take their actual cumulative values; only their pairwise absolute-difference auxiliaries are zero.

More explicitly, define the state and product prefixes at stock threshold \(h\) as \(\sum_{y\le h}s_{iy}\) and \(\sum_{y\le h}q_{iy}\). At \(h=0,1\), their two-value vectors are \((1/4,1)\) and \((0,g)\) at every station, both for the old point and the attaining new point below. Every between-station difference of either prefix is therefore zero. The retained pairwise CDF/product controls admit zero absolute-difference auxiliaries; their cumulative prefix variables themselves keep these stated values. The explicit extension and actual old formulas are checked in the supporting mathematical record.

Put \(a=\sum_i s_{i1}\), \(b=\sum_i s_{i2}\). The stock budget gives \(a+2b\le3\), and the old penalty gives \(P\ge4-a\). From VD-P,
\(\sum_iZ_i\le4g+\beta b\), with \(\beta=3/4\le1\). TC and the numerator row imply \(a+4b\le4\sum_i Z_i\), hence \(g\ge a/16\). Since \(\widehat\lambda>1/16\) and \(a\le3\),

\[
F_{LP}\ge a/16+\widehat\lambda(4-a)\ge\widehat\lambda+3/16.
\]

Keep the balanced mixture and set \(g=q_{i1}=Z_i=3/16\), \(q_{i0}=q_{i2}=0\) and \(H_{ij}=1/2\). This attains the bound: both TC sides are 3. Complete exact rational checks pass all 583 actual rows and 284 variable bounds for J2, and all 583 rows and 298 bounds for J3; the old state-penalty and R88 CDF extensions also pass. These are actual-matrix checks plus explicit algebraic extensions, rather than a claim to have reexported every old control into one new native matrix.

The complete integer universe has optimum \(1/4+\widehat\lambda\). Thus the new exact LP value is \(\widehat\lambda+3/16\approx.3375\), its increment is \(3/16\), and the remaining gap is \(1/16\). It closes 75% of the old 1/4 gap. The conclusion uses these actual intervals and supports; it is not a full-size performance guarantee.

The retained pairwise CDF controls see identical station marginals and give no positive numerator floor at the old point. TC uses the all-station stock budget to exclude that zero numerator. Its gain supplies missing objective information even though the service mixture already has a complete joint physical extension. This explains the strict tiny result without implying that the same row must bind a real-root LP optimum.

### 6.3 Historical mechanisms and real-root value

State-weighted penalty was already present in R55's VD-J proposal. Its strict-improver penalty-budget covers and DP have a different premise; failure of a prerequisite gate did not prove them ineffective. R88 couples pairwise CDF/product marginals, R98 theta links vehicle and stock marginals, and R101/R103 use ranks/Hall and independent single-vehicle support. Those tiny common-reference structures are retained where specified. The older inventory DP, R118 stock-deficit/greedy penalty floor and R120 scalar \(g\)-envelope also remain separate references. R114 supplies the nonnegative/source rule, not the positive stock-deficit theorem. The supplement maps the exact read sources and the limited comparisons; no claim of dominance over all historical DP or joint closures is made.

The real-root comparison uses K-20-S/Seed0 and K-35-U/Seed0, with identical input, inventory support, interval and cutoff at all three layers: current S2 continuous LP, that LP plus the old state-penalty lower bound, and the latter plus TC. Non-comparison auxiliaries reoptimize freely. It uses no new integer solve or favorable-cutoff search, and does not rebuild every old oracle.

{{ROOT_RESULTS}}

{{ROOT_TABLE}}

![Exact tiny-reference improvement and the separate numerical real-root comparison. Old state penalty is retained before TC is assessed on the real roots.](figures/count_bound_scope.png)

## 7. Conclusions and implications

The strongest established result is the complete S2 method on its stated model and evidence layers. Shared inventory/service states organize physically relevant information, while valid coverage and independent physical verification determine what native progress can prove. Existing controls show that a good initial solution is useful but insufficient to explain all observed gains. They do not establish a separate large speed contribution from every component.

{{FINAL_CONCLUSION}}

The operational weight experiments address a fixed feasible set and effective weight \(\rho\), rather than comparing equal \(\lambda\) across unrelated instances. The threshold-count result adds an exact tiny original-objective increment beyond the named retained controls, while its real-root and production implications remain distinct. Native hidden-tree numerical causes remain unresolved and are not reopened as a prerequisite for the manuscript. Generalization beyond these inputs, native backend and synthetic inventory construction requires further evidence. A formal submission should also complete the specific bibliographic/provenance checks listed in the supplement before making stronger model-priority or literature-dominance claims.

