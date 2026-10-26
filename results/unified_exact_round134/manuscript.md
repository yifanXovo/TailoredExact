# An inventory-state exact algorithm for bicycle redistribution with ratio-Gini and target-deviation costs

## Abstract

Static bicycle redistribution couples station inventory decisions with vehicle routes, intermediate loads and handling time. We study the minimization of the Gini dispersion of inventory-to-target ratios plus weighted relative target deviation, with empty departure, loaded return and unique nonzero one-way service. The proposed GI-TBC algorithm, implemented as S2, shares finite inventory states between service and objective representations and controls a complete collection of Gini intervals around native LP and MIP solves. We distinguish the problem-specific links and coverage arguments from standard value disjunction and product linearization. Historical validation on twelve fixed inputs at two solver Seeds produced 17/24 qualified S2 certificates and 9/24 cold-compact certificates under its original version and policy. The targeted final implementation certifies 12/14 S2, 9/14 cold-compact and 2/4 paid-start observations across 32 fixed positions; four additional within-instance weight runs examine Gini, deviation and vehicle work. A separate threshold-count inequality connects the global inventory budget to the Gini numerator without new variables. On two complete tiny joint-service references it raises the exact original-objective relaxation by 3/16, closing 75% of a known integer-objective gap; neither fixed real root shows an additional TC gain after retaining the old state-penalty control. The evidence supports the complete algorithm within the stated test scope, with adverse and unresolved observations retained.

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

All 32 fixed positions completed, with qualified certificates: S2 12/14, P 9/14, PS 2/4. The fourteen S2/P comparisons comprise 9 both certified, 3 S2 only certified, 2 both open; their directions are 12 favorable, 2 undetermined. The four S2/PS comparisons comprise 2 S2 only certified, 2 both certified, with 2 favorable, 2 adverse directions. There are 7 substantive both-certified differences outside the micro panel. There are 2 adverse directions across both controls; these are retained individually. 1 observations have a rejected native source and an independent exact-zero certificate. They are eligible under the new independent-proof policy, while their native-source flag remains false. The new panel is targeted final-version evidence; it does not retroactively change historical counts. Substantive certified differences are UC-B20-B Seed0 S2/P -315.094s, UC-B20-B Seed1 S2/P -314.557s, X-35-U Seed1 S2/P -1612.108s, X-35-B Seed0 S2/P -140.348s, X-35-B Seed0 S2/PS +10.355s, X-35-B Seed1 S2/P -31.873s, X-35-B Seed1 S2/PS +11.082s. Micro S2 complete times range from 0.773 to 0.857s; P ranges from 1.016 to 1.641s. Table 1 reports every repetition.

**Table 1. All final-panel matched groups. C is a certificate with complete production seconds; O reports feasible U / qualified L and has no certificate time. Seed and repeat follow the problem name.**

| Problem / Seed / repeat | P | PS | S2 | S2/P result |
|---|---|---|---|---|
| SM-B10-B / 0 / 1 | C 1.641s | - | C 0.857s | S2 faster (micro) |
| SM-B10-B / 0 / 2 | C 1.041s | - | C 0.774s | S2 faster (micro) |
| SM-B10-B / 1 / 1 | C 1.043s | - | C 0.805s | S2 faster (micro) |
| SM-B10-B / 1 / 2 | C 1.016s | - | C 0.773s | S2 faster (micro) |
| K-15-S / 0 / 1 | O 0.59226/0.52741 | O 0.59226/0.52022 | C 112.935s | S2 only certified |
| K-15-S / 1 / 1 | O 0.59226/0.5289 | O 0.59226/0.53187 | C 115.021s | S2 only certified |
| UC-B20-B / 0 / 1 | C 319.060s | - | C 3.966s | S2 faster; substantive |
| UC-B20-B / 1 / 1 | C 318.377s | - | C 3.821s | S2 faster; substantive |
| K-35-U / 0 / 1 | O 0.66475/0.3355 | - | O 0.69285/0.56494 | both open |
| K-35-U / 1 / 1 | O 0.75885/0.33055 | - | O 0.66836/0.55427 | both open |
| X-35-U / 0 / 1 | O 0.016265/6.9389e-18 | - | C 120.257s (ind.) | S2 only certified |
| X-35-U / 1 / 1 | C 2064.949s (ind.) | - | C 452.841s (ind.) | S2 faster; substantive |
| X-35-B / 0 / 1 | C 157.954s (ind.) | C 7.251s (ind.) | C 17.606s (ind.) | S2 faster; substantive |
| X-35-B / 1 / 1 | C 50.151s (ind.) | C 7.196s (ind.) | C 18.277s (ind.) | S2 faster; substantive |


The full per-arm table in the supplement includes every micro repetition, certificate class, endpoint and complete production/verification cost. Source-rejected native conclusions remain rejected even where an independent exact-zero certificate exists. Actual split, child-target and cache observations describe exposed controller behavior rather than proving an independent controller speed effect. No natural NEXT observation is required to complete this finite confirmation.

### 5.3 Size and physical interpretation

K-35-U Seed0 has U=0.692854, L=0.564942, an unresolved original-objective gap. K-35-U Seed1 has U=0.668358, L=0.554272, an unresolved original-objective gap. X-35-U Seed0 has U=0, L=0, a certificate. X-35-U Seed1 has U=0, L=0, a certificate. X-35-B Seed0 has U=0, L=0, a certificate. X-35-B Seed1 has U=0, L=0, a certificate. Complete vehicle quantities, target-under/equal/over counts, return loads and prefix peaks are retained for each method in the operations tables. They describe legal fleets even when optimality remains unresolved.

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

All six prescribed weight points are reported; 6/6 have a qualified certificate. For K-15-S, Omega=9.47337, so rho is 0.710503, 1.42101, 2.84201. The observed Gini/deviation points change with the penalty weight. In ascending weight order, pickups are 26, 28, 28, returns are 0, 0, 0, and maximum route-duration fractions are 0.9902, 0.9983, 0.9983. For UC-B20-B, Omega=11.83, so rho is 0.88725, 1.7745, 3.549. The three observed points lie on a platform. In ascending weight order, pickups are 14, 14, 14, returns are 6, 6, 6, and maximum route-duration fractions are 0.9891, 0.9891, 0.9891. The relation table evaluates the error-aware inequalities using only accepted original-objective U/L gaps, without treating feasibility tolerance as objective error. These remain conditional on the engineering bound policy rather than new rational optimality claims.

Figure 1 locates all six measured points. Connecting segments guide the eye and do not estimate an unobserved optimal frontier.

**Table 2. Fixed physical instances at all three weights. Gap is signed original-objective U-L.**

| Problem | lambda / rho | G | P average | F | certificate | gap |
|---|---|---|---|---|---|---|
| K-15-S | 0.075 / 0.710503 | 0.20237 | 0.276702 | 0.398967 | yes | 5.55112e-16 |
| K-15-S | 0.15 / 1.42101 | 0.222147 | 0.260462 | 0.592265 | yes | 3.01757e-09 |
| K-15-S | 0.3 / 2.84201 | 0.225433 | 0.258588 | 0.960344 | yes | 2.22045e-16 |
| UC-B20-B | 0.075 / 0.88725 | 0.170833 | 0.229079 | 0.374083 | yes | 1.11022e-16 |
| UC-B20-B | 0.15 / 1.7745 | 0.170833 | 0.229079 | 0.577333 | yes | 2.22045e-16 |
| UC-B20-B | 0.3 / 3.549 | 0.170833 | 0.229079 | 0.983833 | yes | 4.44089e-16 |


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

Both fixed root domains completed the three prescribed LP layers. K-20-S gives L0=0.1951491524, Lold=0.3187585426, Lold+TC=0.3187585426, with TC increment 0. K-35-U gives L0=0.2001776619, Lold=0.2738576813, Lold+TC=0.2738576813, with TC increment -1.665334537e-16. These are floating-point LP observations with recorded primal/dual quality and added-row residuals; the tiny result above is an exact rational theorem. No reliable positive TC increment is established on these real roots. The present exploration stops with the exact tiny result and this negative real-root evidence; it does not expand the root or Seed set.

**Table 3. Identical root domain at three relaxation layers. Times are native LP seconds; all non-comparison auxiliaries are free.**

| Problem | L0 | Lold | Lold+TC | TC increment | U / remaining gap | LP seconds 0 / old / TC |
|---|---|---|---|---|---|---|
| K-20-S | 0.195149152 | 0.318758543 | 0.318758543 | 0 | 0.716807 / 0.398048 | 0.131 / 0.165 / 0.175 |
| K-35-U | 0.200177662 | 0.273857681 | 0.273857681 | -1.665335e-16 | 0.692854 / 0.418997 | 0.322 / 1.122 / 0.876 |


![Exact tiny-reference improvement and the separate numerical real-root comparison. Old state penalty is retained before TC is assessed on the real roots.](figures/count_bound_scope.png)

## 7. Conclusions and implications

The strongest established result is the complete S2 method on its stated model and evidence layers. Shared inventory/service states organize physically relevant information, while valid coverage and independent physical verification determine what native progress can prove. Existing controls show that a good initial solution is useful but insufficient to explain all observed gains. They do not establish a separate large speed contribution from every component.

The final confirmation certifies 12/14 S2 observations, alongside 9/14 P and 2/4 PS observations. It retains 2 adverse directions and 2 open S2 positions. There are 2 substantive adverse both-certified comparisons under the prespecified final-panel rule. The role-by-role evidence, rather than a requirement to win every Seed, determines the implementation assessment. The independent zero rule resolves a proof-source distinction while preserving normal positive proofs and rejection of insufficient native evidence.

The operational weight experiments address a fixed feasible set and effective weight \(\rho\), rather than comparing equal \(\lambda\) across unrelated instances. The threshold-count result adds an exact tiny original-objective increment beyond the named retained controls, while its real-root and production implications remain distinct. Native hidden-tree numerical causes remain unresolved and are not reopened as a prerequisite for the manuscript. Generalization beyond these inputs, native backend and synthetic inventory construction requires further evidence. A formal submission should also complete the specific bibliographic/provenance checks listed in the supplement before making stronger model-priority or literature-dominance claims.


\clearpage

# Appendix A. Complete model, scoped strengthening and proof obligations

The complete physical formulation and strengthening proofs below are retained from the maintained manuscript. S2 uses uniform pair support and no triple support. The final production implementation adds the independent exact-zero proof in Proposition 1; native-source qualification and all normal positive-objective rules remain separate. Historical source pointers identify their own snapshots and are not claims that an old executable produced the final panel.

This appendix is the single maintained model specification for the manuscript. It transcribes the frozen writer, including constraints sometimes redundant for integer solutions. It does not replace the implemented model by a different vehicle-routing formulation. Equations are mathematical real-arithmetic expressions; A.7 states the separate numerical implementation boundary. Historical source-line pointers retained in this derivation refer to snapshot 355eefd2be3fe5651195681faf7b3a63ee4032f8. That historical E3 source base and its binding belong to the earlier attribution controls [@frozenImplementation]. The final production source and PE are fixed by candidate_manifest.json; source_publication.json provides the exact source-byte capsule. Current state/service, own-H, pair-only and inclusive-domain conditions are checked against these final identities, rather than inferred from historical line numbers.

## A.1 Sets, data and variables

Let \(N=\{1,\ldots,n\}\) be service stations, \(N_0=N\cup\{0\}\), \(K=\{1,\ldots,m\}\), and \(A=\{(i,j)\in N_0^2:i\ne j\}\). Depot 0 is absent from every inventory, ratio, weight and Gini sum. Vehicle indexing is shifted by one relative to source indices \(0,\ldots,M-1\). All vehicle-indexed formulas hold for each \(k\in K\); all station formulas hold for each \(i\in N\), unless otherwise stated.

Station capacity \(C_i\) and initial inventory \(b_i\) are integers with \(0\le b_i\le C_i\); target inventory \(D_i\) is a positive integer no larger than \(C_i\). The parser's depot capacity/stock fields do not provide departure supply. Vehicle capacity \(Q_k>0\) is integer. A vehicle starts empty and returns to the same depot, possibly loaded. Travel time \(\tau_{ij}=\|v_i-v_j\|_2/1.5\) uses the serialized planar coordinates. The route horizon is \(T\); unit pickup/drop times are \(t_p,t_d\), with \(h=t_p+t_d\). Penalty multiplier \(\lambda\ge0\) and station weights \(\omega_i\ge0\) are data; the baseline panel uses \(\lambda=.15\), with within-instance sensitivity at \(.075,.30\), positive weights and \(t_p=t_d=60\). No inventory floor is imposed by the compatibility field min_ratio.

The binary variables are arc decisions \(x_{kij}\), station service assignments \(z_{ki}\), and pickup-direction indicators \(a_{ki}\). Source calls the last variable mName(k,i); we rename it \(a\) to avoid confusing it with the fleet size. Pickup \(p_{ki}\), drop \(d_{ki}\), final inventory \(Y_i\), and post-service load \(\ell_{ki}\) are nonnegative. The rank \(u_{ki}\) is continuous. Define \(\bar p_{ki}=\min(b_i,Q_k)\) and \(\bar d_{ki}=\min(C_i-b_i,Q_k)\).

| Variable | Domain and bound in the active formulation |
|---|---|
| \(x_{kij},z_{ki},a_{ki}\) | Binary, for all stated indices; no self arcs |
| \(p_{ki},d_{ki}\) | Integer for cold P and ENS-C; continuous for M-B; upper bounds \(\bar p_{ki},\bar d_{ki}\) |
| \(\ell_{ki}\) | Integer in \([0,Q_k]\), retained by all three methods |
| \(u_{ki}\) | Continuous in \([0,n]\) |
| \(Y_i\) | Integer in \([\underline y_i,\bar y_i]\); plain model has \([0,C_i]\) |
| \(r_i\) | Continuous in \([0,C_i/D_i]\) |
| \(e_i\) | Continuous in \([0,\max(1,C_i/D_i-1)]\) |
| \(H_{ij}\), \(i<j\) | Continuous in \([0,C_i/D_i+C_j/D_j]\) |
| \(g,Z_i\) | Continuous; \(g\in[0,1]\) in the unsliced writer, \(g\in[\alpha,\beta]\subseteq[0,1]\) for an interval; \(Z_i\in[0,C_i]\) |
| \(f_{kij}\) | Continuous in \([0,n]\), F0 connectivity flow only |
| \(s_{iy},q_{iy}\) | Binary inventory selectors and continuous selected-G products, for \(y\in\mathcal Y_i=\{\underline y_i,\ldots,\bar y_i\}\), VD-P only |
| \(b_{it}^{\rm bit},w_{it}\) | Binary inventory bits and continuous products, plain P only |
| \(W_{SP}\) | Continuous in \([\max(0,\underline S\underline P),\max\{\max(0,\underline S\underline P),\bar S\bar P\}]\), when the aggregate SP estimator is active |

The model objective is \(f=g+\lambda P\), where \(P=\sum_i\omega_i e_i\); \(f,S=\sum_i r_i\), and \(H_\Sigma=\sum_{i<j}H_{ij}\) are expressions, not new columns. Constants \(\underline y,\bar y,\underline S,\bar S,\underline P,\bar P\) are defined in A.5. Bound-only extrema columns r_min,r_max may still be allocated by the writer; with the shared factory their centering inequalities use the projected pair form below and those columns have only their original bounds \([0,\max_i C_i/D_i]\). No additional vehicle-used binary exists: \(v_k=\sum_jx_{k0j}\) is an expression.

## A.2 Routing, service and physical resources

The complete routing core is

\[
\sum_{j\in N}x_{k0j}=\sum_{i\in N}x_{ki0},\qquad
\sum_{j\in N}x_{k0j}\le1,
\tag{A1}
\]
\[
\sum_{j\in N_0\setminus\{i\}}x_{kji}
=\sum_{j\in N_0\setminus\{i\}}x_{kij}=z_{ki},\qquad
\sum_kz_{ki}\le1,
\tag{A2}
\]
\[
z_{ki}\le u_{ki}\le nz_{ki},\qquad
u_{ki}-u_{kj}+nx_{kij}\le n-1
\quad(i,j\in N,\ i\ne j).
\tag{A3}
\]

These are the writer's original depot degree, station degree and MTZ rows. Any selected station cycle contradicts the sum of (A3) around the cycle. Thus an integer nonempty selection has one depot-connected elementary tour; an unused vehicle has all arcs and assignments zero. A depot-to-depot empty route is represented without a self arc. The MTZ rows remain when F0 also adds the following connectivity flow:

\[
0\le f_{kij}\le n x_{kij}\quad((i,j)\in A),\qquad
\sum_{j\ne i}f_{kji}-\sum_{j\ne i}f_{kij}=z_{ki},
\tag{A4}
\]
\[
\sum_{j\in N}(f_{k0j}-f_{kj0})=\sum_{i\in N}z_{ki}.
\]

F0 here means the round20-current flow variant, including return-arc columns, with no \(f\ge x\) normalization or start-coupling additions. A route visiting \(q\) stations admits downstream-count flows \(q,q-1,\ldots,1,0\). These flows establish validity for every original route, independently of MTZ. Cold plain P does not receive this strengthening. The row package also called F0 has additional families in A.5; these two uses of the historical label must not be confused.

All protected service rows are retained:

\[
p_{ki}\le\bar p_{ki}z_{ki},\quad d_{ki}\le\bar d_{ki}z_{ki},\quad
a_{ki}\le z_{ki},\quad p_{ki}\le\bar p_{ki}a_{ki},
\tag{A5}
\]
\[
d_{ki}\le\bar d_{ki}(z_{ki}-a_{ki}),\quad
p_{ki}+d_{ki}\ge z_{ki},\quad
0\le\ell_{ki}\le Q_kz_{ki}.
\]

The first pair is not silently dropped even where implied by direction rows. Zero directional bounds cause no division. Unique service, a binary direction and the last service inequality forbid split service, simultaneous pickup/drop and zero-operation visits.

Loads are the writer's original two-sided Big-M recurrences:

\[
-Q_k(1-x_{k0i})\le\ell_{ki}-p_{ki}+d_{ki}
\le Q_k(1-x_{k0i}),
\tag{A6}
\]
\[
-Q_k(1-x_{kij})\le\ell_{kj}-\ell_{ki}-p_{kj}+d_{kj}
\le Q_k(1-x_{kij})\quad(i,j\in N,\ i\ne j),
\tag{A7}
\]
\[
R_k:=\sum_i(p_{ki}-d_{ki})\ge0,\qquad
\sum_{(i,j)\in A}\tau_{ij}x_{kij}+h\sum_i p_{ki}\le T.
\tag{A8}
\]

The first selected arc fixes departure load to zero. Selected internal arcs propagate each post-service load. A return has no service operation: its load equals the last \(\ell\), hence is at most \(Q_k\). Summing the recurrence gives \(R_k\) as that load, so its upper bound follows without a separate \(R_k\) column or explicit upper row. Inactive recurrence rows are valid because their difference is between a feasible before-service load and another feasible post-service load, each in \([0,Q_k]\). Empty vehicles have \(p=d=\ell=R=0\).

In (A8), let \(P_k=\sum_i p_{ki}\) and \(D_k^{\rm drop}=\sum_i d_{ki}\). Since \(R_k=P_k-D_k^{\rm drop}\), original handling time is

\[
t_pP_k+t_d(D_k^{\rm drop}+R_k)=(t_p+t_d)P_k.
\tag{A9}
\]

Return unloading is paid. Capacity \(Q_k\) limits every load, not cumulative pickup \(P_k\), which may exceed \(Q_k\) after intermediate drops. There is one physical time limit per vehicle and a separate computational deadline.

Inventories and objective auxiliaries satisfy

\[
Y_i+\sum_k(p_{ki}-d_{ki})=b_i,\quad r_i=Y_i/D_i,\quad
e_i\ge r_i-1,\quad e_i\ge1-r_i,
\tag{A10}
\]
\[
H_{ij}\ge r_i-r_j,\quad H_{ij}\ge r_j-r_i\quad(i<j).
\tag{A11}
\]

Consequently \(\sum_iY_i+\sum_kR_k=\sum_i b_i\). Loaded returns permit a decrease of station inventory; no external depot inventory can increase it.

## A.3 Original and disaggregated Gini objective

The physical objective is

\[
F(Y)=G_{\rm true}(Y)+\lambda\sum_i\omega_i|Y_i/D_i-1|,\quad
G_{\rm true}=\begin{cases}
\dfrac{\sum_{i<j}|r_i-r_j|}{n\sum_i r_i},&S>0,\\
0,&S=0.
\end{cases}
\tag{A12}
\]

The native epigraph is

\[
n\sum_i Z_i/D_i\ge H_\Sigma,\qquad\min f=g+\lambda\sum_i\omega_i e_i.
\tag{A13}
\]

Cold P uses inventory bits. With \(B_i=\max(1,\lceil\log_2(C_i+1)\rceil)\), for \(t=0,\ldots,B_i-1\),

\[
Y_i=\sum_t2^t b_{it}^{\rm bit},\quad Z_i=\sum_t2^t w_{it},\quad
0\le w_{it},\quad w_{it}\le g,\quad w_{it}\le b_{it}^{\rm bit},
\quad w_{it}\ge g+b_{it}^{\rm bit}-1.
\tag{A14}
\]

The capacity bound removes unused bit encodings. These products are exact at binary bits. ENS-C and M-B instead use the finite value-disaggregated perspective block VD-P:

\[
\sum_{y\in\mathcal Y_i}s_{iy}=1,\quad
Y_i=\sum_y y s_{iy},\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
\sum_yq_{iy}=g,\quad Z_i=\sum_y yq_{iy}.
\tag{A15}
\]

The active mode is VD-P, not VD-J: equalities reconstructing \(r_i\) or \(e_i\) from selectors are not substituted for (A10). The shared factory's bit-product McCormick rows are skipped for this block because those bit columns are absent. Products (A15) already use interval bounds. M-B additionally writes the original A/B rows

\[
\sum_k(p_{ki}+d_{ki})=\sum_{y\in\mathcal Y_i}|b_i-y|s_{iy},
\qquad \sum_kz_{ki}+s_{i,b_i}=1.
\tag{A16}
\]

A missing initial state means \(s_{i,b_i}=0\), not a new selector. The independent ENS-Q option is false. The mode-linked direction equality of another variant is absent; M-B retains its original binary \(a_{ki}\). ENS-C uses integer \(p/d\) and omits (A16). These are the material representation differences; the complete H and controller are shared.

## A.4 Integrality, embedding and fairness propositions

**Lemma A1 (implicit service integrality).** With integer \(b_i,Y_i\), (A2), (A5), and binary assignments/directions, M-B's continuous quantities are integer.

*Proof.* If \(z=0\), its quantities and direction are zero. At the only assigned vehicle, direction 1 forces \(d=0\), so \(p=b_i-Y_i\) is integer. Direction 0 forces \(p=0\), so \(d=Y_i-b_i\) is integer. No other vehicle contributes. Retained integer loads are not needed for this argument. Removing unique service, one-way direction or integer inventory invalidates the inference. The statement concerns integer feasible solutions, not equality of LP convex hulls. ∎

**Validity of A/B.** For an integer original service, total movement at a station equals \(|b_i-Y_i|\), which its selected state reproduces. An assigned service is nonzero and one-way, so \(Y_i\ne b_i\) exactly when the station is served. This proves both (A16); neither is an extra premise of Lemma A1.

**Lemma A2 (physical objective embedding).** Assume inventory domains and rows preserve all physical points assigned to a true-G interval \([\alpha,\beta]\) and cutoff \(F\le c\). Every such fleet has an extension satisfying the applicable original or VD-P groups, with \(g=G_{\rm true}\) and \(f=F\), up to permutation of identical vehicle labels if symmetry rows are present.

*Proof.* Use the physical arcs, service, load prefixes, tour ranks and downstream flows. Select its integer inventory state, put \(q_{iy}=g\) at the selected state and zero at others; (A15) yields \(Z_i=gY_i\). Set \(e_i=|r_i-1|\) and \(H_{ij}=|r_i-r_j|\). Then (A13) holds, with equality for \(S>0\). At \(S=0\) all inventories, ratios and differences are zero and \(g=0\) realizes the stipulated convention. Bounds and valid strengthening are satisfied by assumption. Conversely an integer product completion has \(Z_i=gY_i\), hence \(g\ge G_{\rm true}\) for \(S>0\) and \(f\ge F\); at zero sum, \(g\ge0\) suffices. ∎

Arbitrary native \(g\) may exceed physical Gini. A fleet with \(G_{\rm true}<\alpha\) can have an inflated-g auxiliary completion. The proof assigns physical points by their true Gini and requires their objective-preserving extension; it does not classify every completion by its auxiliary g. An inventory vector without compatible routes is not an upper-bound witness.

For \(n>1\), triangle inequalities give \(A:=\sum_{i<j}|r_i-r_j|\le(n-1)S\), so \(G_{\rm true}\le(n-1)/n\). For \(S>0\), \(G_{\rm true}=0\) means every ratio is equal; at \(S=0\) all are zero by nonnegativity. A common ratio below one is a common proportional shortage, not target attainment. If \(\lambda>0\) and all \(\omega_i>0\), \(F=0\) if and only if every \(Y_i=D_i\). These are dispersion and target-deviation statements, with no implied demographic/service/revenue interpretation.

## A.5 Enabled strengthening: construction, proofs and scope

The finite list below describes the actual M-B path, not every option in the repository. All rows are assembled **statically when a canonical interval model is written**, before its LP or MIP request. A new cutoff epoch rewrites the relevant model; it does not separate these rows at fractional native nodes. The writer supplies physical rows, and the shared interval factory supplies the interval rows. Families registered by the factory are not all rows emitted by it. In particular, the factory's bit-product rows are filtered out for VD-P. The original objective and physical constraints remain present.

### A.5.1 Construction of the inventory rectangle (D1)

Let the current true-G interval be \(I=[\alpha,\beta]\), the independently verified own incumbent be \(U_e\), and the cutoff be \(c=U_e\). **The active controller sets incumbent_epsilon to zero**, so this is a non-strict objective cutoff; a generic writer can subtract an epsilon, but that is not this frozen request. Start with \(l_i=0,u_i=C_i\). With \(\lambda>10^{-12}\), finite positive \(U_e\), and \(B=(c-\alpha)/\lambda\ge-10^{-10}\), for each \(\omega_i>10^{-12}\) intersect with

\[
l_i\gets\max\{l_i,\lceil D_i(1-\max(0,B/\omega_i))-10^{-9}\rceil\},\quad
u_i\gets\min\{u_i,\lfloor D_i(1+\max(0,B/\omega_i))+10^{-9}\rfloor\}.
\tag{A19}
\]

This is followed by one intersection with physical movement reachability. Write \(t_i=\tau_{0i}+\tau_{i0}\) and

\[
\begin{aligned}
M_{ki}&=\begin{cases}
\min\{Q_k,\lfloor(T-t_i)/h+10^{-9}\rfloor\},&T+10^{-9}\ge t_i,\ h>10^{-12},\\
Q_k,&T+10^{-9}\ge t_i,\ h\le10^{-12},\\0,&\text{otherwise}.
\end{cases}\\
l_i&\gets\max\{l_i,b_i-\max(0,\max_k\min(b_i,Q_k,M_{ki}))\},\\
u_i&\gets\min\{u_i,b_i+\max(0,\max_k\min(C_i-b_i,Q_k,M_{ki}))\}.
\end{aligned}
\tag{A20}
\]

The outer max with zero transcribes the actual zero-initialized reachability accumulators, including a slightly negative quotient admitted by a floating travel guard. The mathematical version omits the floating guards, uses \(h=0\) for the second case, and clips movement below at zero. Positive published \(h=120\) avoids the small-positive-h threshold ambiguity. If an interval becomes empty, the code flags domain infeasibility, resets that station's storage bounds to \([0,C_i]\), and emits an impossible row. The reset prevents malformed column ranges; it does not reinstate the excluded domain as feasible.

**Proposition A5 (budget and reachability).** Every physical point in \(I,F\le c\) satisfies the ideal versions of (A19)–(A20). Indeed \(F=G+\lambda P\), \(G\ge\alpha\), and nonnegative weighted deviations imply \(\omega_i|Y_i/D_i-1|\le(c-\alpha)/\lambda\). Integer \(Y_i\) gives the rounded bounds. A visited station requires a depot tour with travel at least \(t_i\). Its pickup is at most \(Q_k,b_i\), and its drop is at most \(Q_k,C_i-b_i\); because \(D_k^{\rm drop}\le P_k\), either operation is at most cumulative pickup, which has handling cost \(hP_k\le T-t_i\). Maximize over its unique possible vehicle. These are necessary, not sufficient, attainability conditions: a delivery still needs a source. Zero weight or zero lambda supplies no individual penalty bound and is skipped. ∎

**Actual order and pass count.** The writer first computes budget bounds, intersects reachability, and derives interval extrema; the shared factory recomputes this same sequence from \([0,C_i]\) and replaces the local arrays. It does not feed the first result into a second tightening pass. There is no propagation loop in this enabled path and no iterative fixed point. The preset advertises `iterative` and requested rounds 2, but the legacy completion field is capped at 1. Thus the operative definition is one budget intersection plus one reachability intersection, independently recomputed by the factory. R124's “original two passes” description was incorrect; production is unchanged.

Set \(\underline y_i=l_i,\bar y_i=u_i,\mathcal Y_i=\{l_i,\ldots,u_i\}\), and

\[
\begin{aligned}
\underline r_i&=l_i/D_i,\quad\bar r_i=u_i/D_i,\\
\underline S&=\sum_i\underline r_i,\quad\bar S=\sum_i\bar r_i,\\
\underline e_i&=\operatorname{dist}(1,[\underline r_i,\bar r_i]),\quad
\bar e_i=\max\{|\underline r_i-1|,|\bar r_i-1|\},\\
\underline P&=\sum_i\omega_i\underline e_i,\quad\bar P=\sum_i\omega_i\bar e_i.
\end{aligned}
\tag{A21}
\]

The last extrema bound the **tight physical completion** of \(e\). They do not assert that every nonminimal native epigraph \(e_i\) is at most \(\bar e_i\). There is no stock-weighted knapsack or optimization in the denominator calculation: these are sums over the rectangle, with no extra conservation-driven tightening.

### A.5.2 Physical conservation and activation (P1–P4)

The following rows hold on the full physical domain, independently of (I,c):

\[
\sum_i b_i-\sum_kQ_k\le\sum_iY_i\le\sum_i b_i;
\quad -b_i\sum_kz_{ki}\le Y_i-b_i\le(C_i-b_i)\sum_kz_{ki}\quad(i\in N);
\tag{A22}
\]
\[
h\sum_{k,i}p_{ki}\le mT;
\qquad z_{ki}\le0\quad\text{if }t_i+h>T+10^{-9}.
\tag{A23}
\]

**Proof.** Each return load lies in \([0,Q_k]\); insert this into conservation (A10). If no vehicle serves \(i\), inventory balance fixes \(Y_i=b_i\); otherwise unique assignment makes the visit sum one and the two activation bounds reduce to \(0\le Y_i\le C_i\). Sum (A8) and drop nonnegative travel for global handling. Any nonzero integer service has at least one pickup somewhere on the vehicle: for a drop use empty departure and load nonnegativity. Consequently a tour through \(i\) takes at least \(t_i+h\). The physical meaning of the historical `transfer_subset_capacity` flag here is this singleton visit exclusion, not a separate general subset-flow formulation. All vehicles and stations are enumerated in increasing index order. These inequalities are implied for integer physical points, but can strengthen the relaxation. The global-handling impossible-row diagnostic based on accumulated required pickup is inactive in the shared-factory path because that legacy accumulator is not populated there. ∎

### A.5.3 Ordered supply compatibility (P5)

For every vehicle \(k\) and receiving station \(j\), define

\[
\mathcal C_{kj}=\{i\in N\setminus\{j\}:\tau_{0i}+\tau_{ij}+\tau_{j0}+h\le T+10^{-9}\}.
\qquad d_{kj}\le\sum_{i\in\mathcal C_{kj}}p_{ki}.
\tag{A24}
\]

All stations passing this test enter the set, even those with zero stock; their pickup column is then fixed at zero. Common \(T,h,\tau\) make the sets identical across vehicles, but their pickup bounds still use \(Q_k\). No demand assumption or target sign is used.

**Proposition A6.** (A24) is necessary for a physical fleet under metric travel and empty departure. Label the integer units collected by a vehicle. Scan its route in order, assigning each delivered unit to one previously collected, not yet delivered unit. Every prefix load is nonnegative, so this matching always exists. If a unit received at \(j\) came from \(i\), the route includes the ordered subsequence (0,i,j,0). Repeated triangle inequalities give travel at least \(\tau_{0i}+\tau_{ij}+\tau_{j0}\), and its at least one collected unit entails \(hP_k\ge h\). Hence \(i\in\mathcal C_{kj}\). Counting matched units at \(j\) proves the row; a pickup unit can be delivered only once. Intermediate stations can add travel or receive other units but cannot create supply. Unmatched collected units may return to depot. An unvisited source has \(p_{ki}=0\); an empty compatibility set forces \(d_{kj}=0\). Preloading, cross-vehicle handoffs, or nonmetric shortcut assumptions would break this proof and are excluded. ∎

The row is a coarse aggregate necessity, not a claim that all compatible pickups can simultaneously reach \(j\). It neither imposes \(P_k\le Q_k\) nor substitutes for prefix loads.

### A.5.4 Two- and three-station support (P6)

For \(W=\{a,b\}\),
\[
\tau(W)=\min\{\tau_{0a}+\tau_{ab}+\tau_{b0},\tau_{0b}+\tau_{ba}+\tau_{a0}\}.
\]
For \(W=\{a,b,c\}\), take the minimum of the six expressions

\[
\tau_{0\pi_1}+\tau_{\pi_1\pi_2}+\tau_{\pi_2\pi_3}+\tau_{\pi_30},\quad \pi\text{ a permutation of }(a,b,c).
\tag{A25}
\]

These are explicit finite formulas, not new shortest-route optimization calls. Metric shortcutting of a complete tour yields one such order, so its travel is at least \(\tau(W)\).

**Lemma A7 (integer handling).** If all stations in \(W\) are served by \(k\), their nonzero integer operations give

\[
|W|\le\sum_{i\in W}(p_{ki}+d_{ki})\le P_k+D_k^{\rm drop}\le2P_k,
\quad P_k\ge\lceil |W|/2\rceil.
\tag{A26}
\]

Here \(P_k=\sum_{i\in N}p_{ki}\), not \(\sum_{i\in W}p_{ki}\): supplies may lie outside \(W\). Integer \(P_k\) gives the ceiling; the LP relaxation alone cannot justify it. Capacity does not bound cumulative pickup. Therefore the writer emits exactly one of the following rows for each selected support:

\[
\begin{aligned}
&\begin{cases}
\sum_{i\in W}z_{ki}\le |W|-1,&\tau(W)+h\lceil|W|/2\rceil>T+10^{-9},\\
h\sum_{i\in W}p_{ki}+M_{kW}\sum_{i\in W}z_{ki}\le T-\tau(W)+M_{kW}|W|,&\text{otherwise},
\end{cases}\\
&M_{kW}=T+\tau(W)+h\max\{1,\sum_{i\in W}\min(b_i,Q_k)\}.
\end{aligned}
\tag{A27}
\]

**Proposition A8 (both branches).** The cover branch follows from (A8), (A25), (A26). In the conditional branch, if every station is served, cancel \(M_{kW}|W|\). Since full travel is at least \(\tau(W)\) and \(\sum_Wp\le P_k\), the remaining inequality is necessary. If at least one is unserved, put \(q=|W|-\sum_Wz\ge1\), \(B_W=\sum_W\min(b_i,Q_k)\). The right side after moving the visit terms is \(T-\tau(W)+qM_{kW}\ge2T+h\max(1,B_W)\ge hB_W\ge h\sum_Wp\). This proves deactivation for all nonnegative \(T,h\), including \(B_W=0\), empty vehicle and \(h=0\). It does not rely on an invalid cumulative-capacity bound. ∎

**Selection is finite and ordered.** For k increasing, enumerate every increasing pair \(a<b\), then every increasing triple \(a<b<c\). One shared counter starts at zero outside the vehicle loop. The helper returns without adding a row once the counter is 50000; it increments once before choosing cover versus conditional. Outer loops continue (and can still evaluate cycle formulas), but no more rows are added. This is not “stop after 50000 violated covers”, not 50000 per vehicle, and not pairs interleaved with triples. At n=50 each full vehicle contributes 1225+19600=20825 supports; the third vehicle receives only the prefix needed to reach the shared limit. Row validity is independent of this selection policy. The dormant exhaustive-subset and rank3 variants have different coefficients/order and are excluded.

### A.5.5 Dispersion, spread and centering (G1–G4)

For every pair \(i<j\), let \(d_{ij}=|r_i-r_j|\). For each \(u\notin\{i,j\}\), triangle inequality gives \(d_{iu}+d_{ju}\ge d_{ij}\). These pairs are distinct in the unordered numerator; the omitted pairs among the other stations are nonnegative. Hence

\[
A=d_{ij}+\sum_{u\ne i,j}(d_{iu}+d_{ju})+\sum_{u<v;\ u,v\ne i,j}d_{uv}
\ge[1+(n-2)]d_{ij}=(n-1)d_{ij}.
\tag{A28}
\]

For \(n=2\) the other sums are empty and equality holds. For \(n=1\), spread and centering are skipped. For true \(G\in[\alpha,\beta]\) and \(S>0\), \(n\alpha S\le A\le n\beta S\). At \(S=0\), all ratios and \(A\) are zero; only the interval containing true \(G=0\) needs that physical embedding. With **tight** \(H_{ij}=d_{ij}\), the emitted rows are

\[
n\alpha S\le H_\Sigma\le n\beta S;\qquad
(n-1)H_{ij}\le n\beta S\quad(i<j).
\tag{A29}
\]

This proves existence of an objective-preserving completion. It does **not** prove that an arbitrary inflated native \(H_{ij}\), even at integer physical variables, satisfies the new row. For example \(r=(1,1),g=.5,H_{12}=1\) satisfies the unsliced original epigraph \(2gS\ge H\); the true-G-zero cap excludes this completion while preserving \(H=0,g=0\). Accordingly these static rows are not advertised as callback user cuts preserving all original native integer completions.

Using the retained \(H_{ij}\ge\pm(r_i-r_j)\) in the pairwise row gives the two variable-S rows, and \(S\le\bar S\) then gives the fixed rows:

\[
(n-1)(r_i-r_j)\le n\beta S,\quad(n-1)(r_j-r_i)\le n\beta S;
\quad \pm(r_i-r_j)\le\frac{n\beta\bar S}{n-1}.
\tag{A30}
\]

The fixed form is the projection of a common min/max ratio band. The allocated extrema columns do not receive that extended formulation in the shared path. All increasing pairs, forward then reverse, are generated. The ideal implication chain is (A29)+absolute-value lower rows → variable-S → fixed-S. Redundancy in ideal arithmetic is not an ablation and authorizes neither row deletion nor an individual speedup claim. The cap/floor, H-spread and signed-difference rows constrain different auxiliary completions even though they preserve the same tight physical embedding.

### A.5.6 Required movement and penalty closure (C1–C3)

For each station, emit only the applicable bound consequence:

\[
\sum_k(d_{ki}-p_{ki})\ge l_i-b_i\quad(l_i>b_i),\qquad
\sum_k(p_{ki}-d_{ki})\ge b_i-u_i\quad(u_i<b_i).
\tag{A31}
\]

These follow by substituting inventory balance in \(Y_i\ge l_i\) or \(Y_i\le u_i\). Their scope inherits the domain: a cutoff-derived \(l_i\) is not an unrestricted physical bound. If \(b_i\notin\mathcal Y_i\), A/B forces service, consistently with required movement. If \(\mathcal Y_i=\{b_i\}\), A/B forces no service. A singleton zero domain and zero operation bounds require no divisions.

For all active finite positive-cutoff requests write

\[
g+\lambda P\le c,\qquad P\ge\underline P,\qquad
e_i\le\max(0,B/\omega_i)\ (\omega_i>10^{-12}).
\tag{A32}
\]

The last row uses the same budget activation tests as A19. The floor follows station by station from the distance to 1 in (A21); the original e upper bound is retained and the budget row intersects it. \(\alpha+\lambda\underline P>c\) proves ideal cutoff infeasibility. The frozen implementation instead tested \(\alpha+\lambda\underline P\ge c-10^{-9}\) and wrote an impossible row. Equality to c is not infeasibility of the non-strict cutoff set, so that row fails the inclusive embedding contract. The replacement deletes it in both emitters and keeps the legal floor; A.7 states the exact boundary check and the separate version qualification. The factory's “Global” metadata on the incumbent row means the entire current model, not all physical objectives at every cutoff.

Historical Round128 clarification (the ordinary rule was unchanged at that stage): if the actual cutoff-domain bound is \(L_a=\alpha+\lambda\underline P\), its unconditional regional bound is \(\min\{L_a,c\}\) by coverage with the cutoff complement. \(L_a>c\) excludes the inclusive cutoff domain; \(L_a=c\) permits equality and excludes only strict improvement. For \(c-10^{-9}\le L_a<c\), the raw supported bound remains \(L_a\) and does not rule out every arbitrarily small improvement. The impossible-row shortcut is not a physical embedding inequality for all \(F\le c\). A known witness contradicting its alleged own-domain bound takes priority for investigation. The separately defined MD-R omits only this named shortcut and checks its own Start against the inclusive root; no frozen production numerical policy is upgraded by that control.

### A.5.7 Scalar objective estimate and SP lifting (C4–C6)

For \(S>0\), multiplying the true cutoff inequality by \(nS\) gives

\[
A+n\lambda SP\le ncS.
\tag{A33}
\]

Since \(A\ge0\), \(\bar S\ge S\) gives \(A/(n\bar S)\le A/(nS)\), so \(A+n\bar S\lambda P\le n\bar Sc\) when \(\bar S>0\). Equivalently A33 implies \(A\le nS(c-\lambda P)\le n\bar S(c-\lambda P)\), because the original cutoff and nonnegative G imply \(c-\lambda P\ge0\). The emitted scalar row is

\[
H_\Sigma+n\bar S\lambda\sum_i\omega_i e_i\le n\bar S c\quad(\bar S>10^{-12}).
\tag{A34}
\]

The bound on S is the rectangular upper estimate (A21), not a new optimum of S. Tight H/e complete every physical point. If \(S=0\), then \(A=0\), \(P=\sum_i\omega_i\), and the original condition is \(\lambda P\le c\). Multiplication alone makes A33 tautological and cannot enforce that condition. Thus the original objective cutoff (A32) remains essential. A34 also holds directly at S=0 if that cutoff holds.

Introduce \(W=W_{SP}\) and take \(W=SP\) on physical completions. The four nonnegative products on the rectangle are \((S-\underline S)(P-\underline P)\), \((\bar S-S)(\bar P-P)\), \((\bar S-S)(P-\underline P)\), and \((S-\underline S)(\bar P-P)\). Expanding them proves respectively

\[
\begin{aligned}
W&\ge\underline S P+\underline P S-\underline S\underline P,\\
W&\ge\bar S P+\bar P S-\bar S\bar P,\\
W&\le\bar S P+\underline P S-\bar S\underline P,\\
W&\le\underline S P+\bar P S-\underline S\bar P.
\end{aligned}\tag{A17}
\]

These are the standard McCormick envelopes [@mccormick1976], derived here without attributing an unread theorem number. They are relaxations, not an exact continuous-product identity. The writer bounds \(W\) by \(w_l=\max(0,\underline S\underline P)\), \(w_u=\max(w_l,\bar S\bar P)\), and emits

\[
H_\Sigma+n\lambda W-nc\sum_i r_i\le0.
\tag{A35}
\]

Every coefficient is explicit: H coefficients 1; r coefficients \(-nc\); W coefficient \(n\lambda\); e coefficients in each McCormick row are the corresponding S coefficient times \(\omega_i\). The active objective remains \(g+\lambda\sum_i\omega_i e_i\) with **ObjCon=0**; W is absent from the objective. Equal S or P bounds cause valid degenerate envelopes. Zero S forces the physical W to zero but does not remove the original penalty. These rows preserve a joint tight completion of g,e,H,W and must not be claimed to preserve all loose auxiliary assignments. No GS or disaggregated-SP lift is enabled.

### A.5.8 Symmetry, skipped rows and dependency order

With the active symmetry option, if **all** capacities are equal and \(m>1\), the writer adds \(\sum_i z_{ki}\ge\sum_i z_{k+1,i}\) for adjacent vehicles. Common T, travel and handling make those vehicles interchangeable; relabel routes by nonincreasing visits to obtain an objective-preserving representative. Heterogeneous capacities skip the whole writer family. Start normalization may sort within equal-capacity classes, which is harmless relabelling but does not add mixed-fleet symmetry rows. A physically feasible labelled route need not itself satisfy the symmetry rows before relabelling.

Bit-only interval envelopes are \(\alpha b\le w\le\beta b\), \(g-\beta(1-b)\le w\le g-\alpha(1-b)\). They follow by the cases b=0,1; they are **not emitted in active VD-P**, whose q block already embeds its interval bounds. Dormant receiver-source covers, Benders, pricing, D1, exhaustive subset duration, dynamic resource cuts, custom branch priorities, S buckets, GS, AMF/RC, and old timed quanta are not part of this specification. Monitoring/target callbacks do not turn the static strengthening into dynamic separation.

The proof dependency is: physical core → implicit integer service and conservation → reachability/transfer/support; budget plus reachability → rectangle → movement/penalty/S bounds; triangle lemma plus true-G membership → Gini rows; rectangle plus original cutoff → SP/scalar rows. A/B use unique nonzero one-way service independently of the implicit-integer lemma. All can be satisfied by the same physical completion, which avoids circularly assuming the validity of a tightened domain to prove its own construction. Analytic validity and actual partial support selection are separate from computational contribution; no family-level performance attribution is made without an ablation.

## A.6 Cutoff and coverage proof

**Lemma A3 (cutoff complement).** Suppose a returned lower bound \(\ell\) is qualified for a model containing objective-preserving embeddings of every physical point with \(G_{\rm true}\in I\) and \(F\le c\). Then \(\min(\ell,c)\) is an unconditional regional lower bound.

*Proof.* A point in the cutoff set has \(F=f\ge\ell\). A point outside has \(F>c\). The minimum covers both. If the cutoff model is infeasible, only that cutoff set is empty, so c, rather than \(+\infty\), is the original-region floor. ∎

**Lemma A4 (complete cover).** Let every possible improving true-G value belong to at least one registered unit \(I\), with a qualified unconditional floor \(\beta_I\). Include the analytic complement, whose applicable floor is U. Then

\[
L=\min\{U,\min_{I\in\mathcal C}\beta_I\}
\tag{A18}
\]

is a lower bound on the original optimum.

*Proof.* Any feasible point is in the complement or at least one covering region. Its corresponding floor bounds its objective. Taking the minimum is safe for the union. Initially \(F\ge G_{\rm true}\) allows \([0,\min((n-1)/n,U)]\) as the improving Gini range. Replacing \([\alpha,\beta]\) by both closed children \([\alpha,\mu]\), \([\mu,\beta]\) preserves coverage, including the shared endpoint. Replacement commits both children atomically with their evidence. An unsplit parent, unresolved leaf, or qualified closed leaf remains represented. Induction over updates proves the invariant. ∎

Bounds on the same physical domain can be combined by maximum; the union of sibling domains requires minimum. Transfer to a narrower domain requires containing scope and a handled cutoff complement, and does not construct that domain's feasible Start. Proof identities include actual model SHA, input, call, epoch, domain, cutoff and return. A local terminal status cannot certify the whole original problem. Depth/width/scheduling limits can select a request or leave an obligation open; they cannot delete it.

For a compatible own fleet, the mapped complete Start includes unused vehicles and all auxiliaries. Setting \(g=G_{\rm true}\) outside a leaf is not a valid exact-g Start. Submission, API acceptance and an improved native incumbent are different observations. No optimality proof follows from H, repeated physical U or Start acceptance.

## A.7 Numerical implementation boundary

Lemmas A1-A4 concern ideal exact arithmetic and valid mathematical domains. Stored matrices use binary64 arithmetic and Gurobi 13.0.2. Native FeasibilityTol and OptimalityTol are \(10^{-6}\), IntFeasTol \(10^{-5}\), requested MIPGap/MIPGapAbs zero; retained evidence closure uses \(10^{-7}\). Ordinary native/outer certificates are numerical certificates under this policy. The stock-based independent zero theorem and the rational tiny-reference proof have their separately stated exact premises.

A historical inclusive-cutoff writer could serialize an artificial contradictory row at a legal cutoff boundary. R133 removed that row while retaining valid penalty and domain rows. Its exact boundary fixture and finite qualification remain in the supplement; historical raw and performance denominators are not rewritten. The final implementation retains the corrected writer. For a native-derived bound or closure, the complete physical embedding, applicable cutoff complement and qualified source are required even when an analytic floor independently exists.

Every final selected own fleet is physically verified. Ordinary positive numerical certification additionally requires qualified source/return chains and complete coverage, normal lifecycle completion and a signed gap in \([-10^{-7},10^{-7}]\). Rejected native proof dependencies cannot close a domain. A sufficient independent original-objective zero proof can instead establish optimality while the native-source flag stays rejected. A near-zero positive objective is not exact zero. The finalizer, normal process completion and required output belong to the production clock; later postproduction checks cannot backdate a certificate.

The source-rejected zero observations in R132/R133 keep their historical unqualified certificate/performance decisions. They are distinct from the newly executed final-panel observations under the independent-proof rule. Historical numerical anomalies and readout repairs are collected in the supporting material, with unavailable hidden-tree causes left unresolved.

The total process deadline makes a run finite, rather than guaranteeing certification in every finite window. Finite physical space and ideal complete search provide no linear forecast from a remaining objective gap.

## A.8 Writer and variable map

| Appendix group | Frozen source authority / mapping |
|---|---|
| Data, travel, physical objective | Parser.cpp; Evaluator.cpp; Result.cpp physical objective evaluator around line 109 |
| Variables and VTypes | CplexBaseline.cpp 890–1005; \(a\leftrightarrow mName\), \(Y\leftrightarrow yName\), \(\ell\leftrightarrow lName\), \(H\leftrightarrow hName\), \(Z\leftrightarrow zprodName\) |
| A1–A4 | Same writer 1600–1695 and 1807–1824; ConnectivityFlow.cpp downstream-count embedding and Round20Current bounds |
| A5–A9 | Same writer 1826–1932; no Round66 arc-load replacement or Round92 handling activation |
| A10–A11 | Same writer 2241–2274 and 2329–2335 |
| A13–A16 | Same writer 2975–3154; stateName and stateGName give \(s,q\); bitName and prodName give plain bits/products |
| F0 configuration and domains | PaperK1AmSf.cpp 38–114; IntervalRowFactory.cpp 391–807; writer 1697–1750, 2049–2108, 2203–2238, 2311–2327 |
| Factory global/local metadata | IntervalRowFactory.cpp 402–451; verified-incumbent “Global” remains cutoff-scoped |
| M-B mode isolation | include/Round98StateService.hpp; no projected direction, linked direction, ENS-Q or other opt-in mode |
| AM, targets, cover and lifecycle | PaperExternalGiniTree.cpp; GurobiBaseline.cpp; ProcessPhaseLedger.cpp; MipStartMapping.cpp |

The linked [implementation snapshot](https://github.com/yifanXovo/TailoredExact/tree/355eefd2be3fe5651195681faf7b3a63ee4032f8) is the historical source authority for this unchanged formulation map. The final implementation and its exact byte capsule are identified by candidate_manifest.json and source_publication.json in the current reproduction entry. Line locations aid review; they do not replace derivations. This appendix supplies constraint groups and validity premises without claiming every engineering identifier as a mathematical contribution.


\clearpage

# Appendix B. Executable method specification

**Current frozen method.** S2/MS2 uses the unchanged H and controller specified below with uniform pair-only support. Historical full-M-B traces and development variants retain their named identity. S2R is a diagnostic deletion control, not a second proposed method.


This supplement defines the controller and finite feasible startup H shared by the adopted S2/MS2 method and its full-M-B predecessor. The current S2 row policy is uniformly pair-only; the underlying H and controller definitions are unchanged. Algorithm 1 appears in Section 3; its two complete subprocedures are given below in B.0; this appendix supplies their data, numerical decisions, decoding and return semantics. Mathematical symbols refer to Appendix A. Historical names are source-map aliases, not additional algorithm variants. The definitions and proofs are retained from R125. The historical Round126 panel used the fixed full-M-B predecessor and cold P-GRB; it is retained under its own identity in [the R130 historical account](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/manuscript.md).



## B.0 Complete leaf and cover subprocedures

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
   Otherwise compute score (B2) in B.3, b+=min(raw child bounds):
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

## B.1 Active entry and parameters

The inherited settings below originate in the saved R123 full-M-B command. The current S2 command additionally selects `--round127-mode ms2`, so every three-station support predicate is false. Both versions select `gcap-frontier`, preset `research-round83-vds-equal-net-exchange`, `round98-state-service=m-binary`, `round90-lp-g-split=false`, candidate mode off, witness audit on and H verified-zero stop on. The preset recursively selects joint-seeded interroute decoded descent, VD-P and verified Start; the canonical paper configuration supplies the static row package and first-class interval controller. R122 uses this same M-B method with the panel's declared limits/Seeds. Input, lambda, capacities and physical times remain data, not tuned choices in this round.

| Item | Frozen active value / interpretation |
|---|---|
| Initial geometry | One true-G interval \([0,\min(U,(n-1)/n)]\), n>1; n=1 has G=0 |
| Split | Midpoint; two closed children; depth <8 and width >\(10^{-4}+10^{-12}\) |
| Score | Balanced normalized closure, threshold .08; exact formula B.3 |
| Infeasible child policy | Two-child split, then mark proved children empty; contraction_enabled=false |
| Native work | Gurobi 13.0.2; one thread; Seed from arm; PresolveAuto; requested MIP gaps 0 |
| Numerical policy | Scheduler epsilon \(10^{-7}\); FeasibilityTol/OptimalityTol \(10^{-6}\), IntFeasTol \(10^{-5}\) |
| Cutoff | Current own U; writer epsilon=0; ObjCon=0 |
| Resource | One process deadline; 30 s shutdown reserve in the saved runs; preparation and H are charged |
| Products | VD-P; continuous p/d; binary direction retained; A/B on; integer loads retained |
| Row generation | Uniform two-station support, no three-station support; static physical plus shared interval factory; no dynamic user/lazy cut separation; native Gurobi cuts remain available |
| Domain option vs execution | Requested iterative/2; operative one budget intersection plus reachability intersection, recomputed by shared factory; no feedback iteration |
| H orders | 24 shuffled chromosomes from mt19937 seed 20260626; appended constructive order; no genetic generations |
| H decoder | Full compaction mode 1; cache limit 200000 complete decoded orders; no generation/stagnation quota in this active branch |

The “interval-mip-core-no-exhaustive-subset-duration” policy is overridden by the VD-P preset to `round55-vd-p`, still excluding exhaustive subset duration. Compiler identity is the frozen MSYS2 UCRT64 g++ binary SHA256 `8cd0aa578687e4182532222c8734439b3f34ac78b6ce23cba1071c5838025fc1`. Library shuffle and equivalent-key sort order are implementation-version details; the paper does not invent a canonical cross-library tie rule absent in the source.

The final paper entry is fixed by [candidate_manifest.json](candidate_manifest.json), [C_matrix_frozen.json](C_matrix_frozen.json) and [D_matrix_frozen.json](D_matrix_frozen.json), together with the [inherited R130 configuration](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/paper_method_config.json). The original R132 launch freezes remain historical evidence, rather than relative links to current files. The template below is one S2 token vector; complete actual launches, including P and PS, are in the current matrices. INPUT, OUT, physical T, cap B, B_MINUS_6, LAMBDA and SEED take their registered values. LAMBDA is .15 in C and .075 or .30 in the added D positions. H seed20260626 and native settings remain explicit configuration choices. The retained zero-stop flag does not assert that MS2 returns before its native lifecycle: an own zero U can produce the degenerate [0,0] root, and the shared independent proof is finalized after resource release and complete physical verification. The supervisor starts the production clock before admission and seals normal required output; native Runtime alone is not T_cert.

~~~text
PE --input INPUT --lambda LAMBDA --T T
   --pickup-time 60 --drop-time 60 --time-limit B_MINUS_6
   --process-wall-time-limit B --process-shutdown-margin 30
   --threads 1 --mip-threads 1 --gurobi-seed SEED --gurobi-presolve -1
   --method gcap-frontier
   --algorithm-preset research-round83-vds-equal-net-exchange
   --round90-lp-g-split false --round61-candidate-mode off
   --round65-witness-audit true --round65-hga-zero-stop true
   --out OUT/result.json --log OUT/native.log
   --process-phase-ledger OUT/phases.csv
   --external-gini-artifact-dir OUT/external
   --primal-heuristic-generation-log OUT/hga.csv
   --progress-log OUT/progress.csv --native-evidence-dir OUT/journal
   --round98-state-service m-binary --round127-mode ms2
~~~

## B.2 State, identity and order

A coverage unit has id, interval endpoints, parent id, child index, depth, base/inherited bound, current bound and sources, cutoff, status, and replacement flag. Active statuses are Open (Invalid may remain selectable as an unresolved obligation); Closed, Empty and Fathomed retain their proof role. Replaced parents are represented by their committed children. TerminalReady/Coalesced are dormant sibling-coalescing states, not normal M-B actions. Native status is not interchangeable with coverage status.

Runtime state separately contains canonical artifact path/SHA/row signature, generation and incumbent epoch; LP result (terminal-valid, optimal/infeasible, bound available, raw bound), LP epoch/SHA/endpoints; cached speculative child objects; terminal-started state; native phase count; and the NEXT milestone bit. Own witness state contains complete routes, integer operations, inventory, recomputed U and true G. The model's epigraph G never replaces the latter. Epoch starts at zero and increments on an independently verified incumbent improvement exceeding \(10^{-9}\). Callback observations and physical witnesses retain separate identities.

Selection uses the **current own U** as cutoff, not an old source cutoff. It considers unreplaced Open/Invalid units with α<U−epsilon and b<U−epsilon. Find their minimum bound and form the epsilon plateau \(b_I\le b_{min}+\epsilon\). Sort the plateau by decreasing width, increasing lower endpoint, increasing upper endpoint, then lexicographic id (the first three comparisons use \(10^{-12}\)). Cycle through this order. Reset the cursor when the plateau membership/order changes or its minimum changes by more than epsilon; after a full cycle increment the tie round. Effort, elapsed time and requested_quantum fields do not affect this `selectNextByBoundOnly` call.

On a new epoch, before reusing a selected artifact verify its old saved bytes, discard its retained backend model, clear artifact/LP state, terminal flags and child cache, and build a new generation at the current cutoff. Qualified old-domain lower bounds remain on their covering units: a smaller cutoff does not invalidate a bound already completed by its old cutoff complement. The NEXT milestone bit is initialized false in each newly created runtime and set true only by a returned NEXT target. **It is not reset in the active epoch invalidation block.** Child-target returns do not set it. No stronger child bound is sent upward to the parent merely because the child has a higher value.

Parent LP reuse requires complete evidence and the same incumbent epoch. A retained artifact must exist and match its SHA. The ordinary cached-child reuse gate requires the parent's ready flag, exactly two cached children and complete child runtime LPs; epoch invalidation clears that flag before reuse. The more elaborate endpoint/path/SHA `validRound90LpGCachedChild` check is conditional on round90 and is off here; its existence is not claimed as an active gate. When reusing children, their stored bounds inherit max(old child bound,current parent bound) and their cutoff is refreshed. AM still reads the **raw LP bound fields**, not those inherited maxima. Missing/incomplete cache falls back to constructing and solving both children; it is never interpreted as infeasible.

## B.3 NEXT, child target and terminal decisions

Call NEXT after the selected parent has completed its LP and merged any qualified bound; re-read the current bound b. The function first rejects nonfinite bounds, and first requeues if any other relevant bound satisfies \(b_j+\epsilon<b\), even if the milestone was already reached. Otherwise, if the milestone is false and any \(b_j>b+\epsilon\), return NEXT with \(t=\min\{b_j:b_j>b+\epsilon\}\). If there is no such bound, or the milestone is true, allow lookahead. The caller supplies only other **Open/Invalid schedulable units** whose current bound is below current U−epsilon (and whose interval remains relevant). Closed, Empty, Fathomed and replaced units are excluded from NEXT competitors even though their floors remain in proof coverage. Thus a lone closed unit at .40 does not supply a NEXT target to an open unit at .20. Source-cutoff metadata governs bound scope, never this current scheduling filter. The function does not use a timed quantum.

If geometry is ineligible, proceed to terminal MIP after NEXT permits lookahead. If eligible, form closed midpoint children in index order 0,1. Each is speculative until the complete replacement transaction. Solve both complete LP relaxations, or use the current admissible cache. A terminal valid child means either proved infeasible, or optimal with an available finite bound; TimeLimit/UNKNOWN is not terminal valid. Deadline exits retain the parent; an unexpected nonterminal/invalid LP is an engineering failure with the parent retained, not permission to prune it. The optional UNKNOWN→core-due research branch is off.

If either qualified child LP is infeasible, AM immediately requests a two-child atomic split. With contraction=false this applies also when both are infeasible; only after installing both does the controller mark the infeasible child or children Empty and discard those backend models. The inactive one-child contraction/both-child parent-close code is not part of M-B.

For two finite optimal LPs with raw bounds ℓ0,ℓ1, use

\[
\Delta=\max(U-b,\max(\epsilon,10^{-12})),\quad
v_j=\min(1,\max(0,(\ell_j-b)/\Delta)),\quad
\eta=\min(v_0,v_1),\quad\mu=(v_0+v_1)/2.
\tag{B1}
\]
\[
\begin{aligned}
s&=\max(1,|b|,|\ell_0|,|\ell_1|,|U|),\\
\delta_b&=\max(\epsilon,32\epsilon_{mach}s),\\
\delta_{score}&=\min(1,\delta_b/\Delta+32\epsilon_{mach}),\quad \epsilon_{mach}=2^{-52}.
\end{aligned}
\tag{B2}
\]

Put \(b_+=\min(\ell_0,\ell_1)\). If \(b_+\le b+\epsilon\), return terminal; else if \(\eta\mu+\delta_{score}\ge.08\), split; else request a **parent-domain MIP** with bound target \(b_+\). A child target is an intended stopping threshold, not a bound to merge into the parent before native evidence returns. A returned target requeues the parent and re-evaluates the current rule; it does not force a delayed split. This distinguishes NEXT (competitors), child target (lookahead), and terminal (complete parent MIP without a bound-target stop). The recorded adaptive rho is \(\min(1,.08/\max(\mu,\max(\epsilon,10^{-12})))\); it is diagnostic, not another active score rule.

## B.4 Native requests, Starts and returned actions

An LP request relaxes the actual original VTypes, keeps the complete row set, and retains the model when permitted. A MIP request restores the exact saved VTypes before optimization. Targets and terminal requests receive the remaining common deadline after preparation, with native TimeLimit set/read back; no new per-leaf budget is created. Native bound callbacks can request termination when the qualified target is reached. Such a request is not the native return itself.

For enabled verified Start, normalize the current own fleet only among equal-capacity vehicle classes, stable sorting by decreasing number of operations and assigning smaller vehicle ids first. Clear explicit previous Starts even if the replacement is ineligible. Reverify routes, true G and F. Check interval membership with \(10^{-8}\) and non-strict cutoff with \(10^{-8}\max(1,|F|,|c|)\). An outside-interval/cutoff fleet is simply ineligible, and the MIP can run without it. Other mapping failures fail the request's engineering gate; they do not establish infeasibility.

For each used route set selected arcs to one, visit z=1, direction to pickup indicator, quantities to its integers, load to each prefix and rank to position. Flow along a q-station route is q,q−1,...,1,0. All absent route columns, including unused vehicles, are zero. Set (Y,r,e,H,G,Z) to physical values, state selector to one at Y, state_g to true G there and zero elsewhere, W_SP=SP, and the unused extrema to actual min/max ratios. Check every actual column bound/type, every actual linear row at \(10^{-7}\), and actual objective including ObjCon at \(10^{-7}\); require minimization and no unexpected nonlinear structure. Then submit a complete Start and read it back. Submission, native-log acceptance, integer-vector observation and a later improved incumbent are different observations.

The outcome object is consumed only after the optimize call returns and request finalization detaches callbacks/settles native data. Retaining the same in-memory model can preserve useful solver state, but this paper does not promise that the entire native branch-and-bound tree survives type changes or later calls. Once returned, merge finite qualified bounds only on the actual interval/cutoff; replay a proposed fleet before accepting an improved own U. This order precedes the next controller transaction.

| Returned condition after required identity, finalization, zero-gap-setting and consistency gates | Coverage action |
|---|---|
| LP optimal with finite qualified bound | Merge into that parent, or save on speculative child; child alone changes no active cover |
| LP infeasible | Parent Empty, or speculative infeasibility retained until atomic split |
| Target MIP OPTIMAL with bound / INFEASIBLE | Close selected cutoff obligation; retain cutoff-complement floor; discard its model and speculative child models |
| Target reached flag, termination-request flag, available bound ≥target−epsilon | Merge returned bound; set milestone only for NEXT; requeue; preserve parent and siblings |
| MIP interrupted/TimeLimit before target | Keep qualified partial bound if engineering gates passed; leave region open and end the common lifecycle |
| Terminal MIP OPTIMAL / INFEASIBLE | Close its own cutoff obligation; never certify siblings by this status |
| Terminal MIP interrupted | Leave region open and stop |
| Unsupported status, missing optimal bound, failed identity, incomplete LP or native error | Stop with explicit failure; preserve unresolved coverage; dependent unqualified evidence is not admitted |
| No launch because deadline expired | Leave region and previous evidence unchanged; finalize open result |

The frozen implementation merges same-unit bounds with max(old bound,new bound), without clipping to U. Such monotonic accumulation does not itself support revocation of a later-refuted source; replacement qualification must audit actual dependent state rather than simply rename the trace. Empty/Fathomed stores max(previous bound,cutoff); Closed keeps its qualified returned floor. The raw returned L is the scheduler's complete-cover minimum, also **without clipping to U**. Tiny negative signed gaps can therefore occur and remain recorded. On the empty relevant-set path the scheduler helper alone returns 0; the enclosing lifecycle/closure logic determines the outcome.

For the exact mathematical proof, each cutoff-bound source has unconditional regional floor min(bound,source cutoff), and the analytic complement contributes its cutoff floor (A.6). This describes proof accounting, rather than an extra min-assignment performed by the frozen scheduler. Raw numerical evidence and exact proof-accounting expressions must not be interchanged. The final implementation retains the R133 source qualification and corrected inclusive-domain writer, as explained in A.7 and B.4.1. Its independent zero proof is separate from native-dependent coverage; the supplement retains the historical correction evidence. Remaining numerical limitations still apply.

### B.4.1 Final independent and native proof rules

Every own final fleet is independently checked against the original physical problem. An exact stock proof of equal ratios and zero positive-weight target penalties establishes F=0; the shared production predicate additionally repeats complete per-vehicle physical verification. It does not accept a merely near-zero positive objective. P, PS and S2 use the same predicate. P obtains no H, while PS and S2 pay their complete own startup.

An independently valid full-domain nonnegative floor may prove a zero fleet even after native-source rejection. The rejected native journal and conservative restoration of the full unresolved domain remain unchanged; this is not a successful native proof or a repaired hidden search tree. Without sufficient independent proof, source-rejected positive outcomes retain the restored open domain. Ordinary qualified positive native and outer coverage certificates retain their original policy.

The proof is finalized after the final selected own fleet is known, necessary physical checks have finished and native resources are released. Required outputs and normal process completion are included in the complete production clock. Postproduction verification has its own elapsed time and cannot backfill a proof or an earlier production timestamp. Engineering source anomalies, the finite R133 checks and historical bridge tables are collected in the supplement.

## B.5 Teaching states and a separately sourced event

These first numbers are **synthetic teaching states**, not measurements. Take U=1, epsilon=\(10^{-7}\). With selected b=.20 and competitor bounds (.20,.35,.60), the plateau contains the tied .20 units and NEXT=.35. After a qualified NEXT return b=.35 the milestone is true; if all other relevant bounds are at least .35, lookahead is permitted. (If the tied .20 unit still exists, the requeue check wins first.)

For a fresh controlling parent b=.20 with no strict competitor, children (.21,.30) give Δ=.8, v=(.0125,.125), score=.000859375, b+=.21: run parent MIP to .21. Children (.20,.90) instead give b+=b: terminal, regardless of the strong sibling. Children (.50,.60) give v=(.375,.5), score=.1640625: split, install both children, with union floor .50. If the other covering unit has floor .25, global L remains .25. A target TimeLimit at .205 keeps the parent open at its qualified .205 bound; a missing Start changes none of these implications.

The following is an **actual R123 saved event** from M-B's `adaptive_mass_decision_ledger.csv` and `paper_tree_events.csv`, selected as a finite trace excerpt. On L0.0.0=[0,.09308544387476185], depth 2, b=.33371261877766062, raw child LPs (.34112380854511071,.35882784229299913), U=.3723417754990474 give eta=.19185481632186216, mu=.42100858578645295, score=.08077252489598688 and score tolerance=.0000025887181797865216. The decision is split; the event at telemetry 127.2749697 records atomic replacement and global floor .34112380854511071. Earlier recorded splits at 38.3552841 and 72.829994 used the infeasible-child two-child branch. These times are native-run telemetry, not newly measured clocks or a reconstructed unknown checkpoint. Compact source excerpts and hashes accompany the finite checks.

## B.6 H encoding and top-level procedure

Physical routes are labelled lists \(0,i_1,\ldots,i_q,0\) with one signed integer operation \(a_i=p_i-d_i\ne0\) per station; missing vehicle means empty route. H's **order encoding** is different: M ordered lists partition all n stations, including a tail that the decoder may not execute. A chromosome is a permutation of station ids 1..n and M−1 identical separator tokens; splitting at separators preserves empty vehicle lists. Reordering an encoded tail does not itself describe a feasible service plan. Decoding returns signed operations; materialization deletes zero-operation stations, closes used routes at depot and verifies the entire fleet.

~~~text
H(instance, common deadline):
    C := empty physical fleet, verify Y=b
    repeat choose and admit best joint insertion (B.7) until none/deadline
    keep verified C as an own candidate
    generate all 24 shuffled order chromosomes with mt19937(20260626)
    append C's order after deterministic tail completion (below)
    initialize a shared complete-decode cache, empty
    decode all 25 orders in order, publishing verified improvements
    for each seed in order:
        repeat generate guided candidates (B.10), order by proxy fitness
        fully decode candidates in that order
        accept first fitness improvement >1e-12; restart this seed's pass
        if every candidate checked without improvement: finish this seed
        honor verified-zero/deadline between calls and candidates
    take the best independently verified candidate, including C
    run strict insertion/quantity closure followed by best neutral block move;
        repeat these two phases (B.11) until zero/no neutral/deadline/failure
    return best admitted complete fleet and stop reason
~~~

Constructive tail completion starts with C's visited order and each vehicle's complete physical duration as a proxy. For each unvisited station i in increasing id, append it to the vehicle minimizing proxy[k]+tau(last,i)+tau(i,0)−tau(last,0), choosing the first vehicle on an exact tie; update that proxy. The remaining operations are decided by the same full decoder. Twenty-four shuffles are generated before appending this extra seed, preserving random draws. `constructive_mode=0` means there are no additional biased population members. The snapshot's C++ shuffle is authoritative for exact seed orders; the algorithm specifies the generator/seed/order and permits cross-library sequence differences. HGA crossover, mutation, education generations, 2000-generation stagnation and obsolete “10 iterations” fields do not run in this decoded-descent branch.

The outer physical candidate store keeps a candidate only after full verification and an improvement greater than \(10^{-10}\), unless no incumbent exists. Verified-zero can terminate startup early. This publication threshold differs from inner \(10^{-12}\) move thresholds; an internally accepted tiny improvement need not replace the outer witness.

## B.7 Joint insertion

At a verified fleet let \(L_k(a)\) be load on leg a, numbering the original legs from 0 through the number of visited stations. For each ordered (pickup station i or 0,drop station j or 0), excluding (0,0), i=j, and already visited nonzero stations, enumerate vehicles and positions. Zero denotes an absent side, not depot stock. Both sides use the same integer quantity q. For a pair choose original legs a≤b, inserting i then j; on one leg the sequence is predecessor,i,j,successor. Travel increment is the sum of replaced arc differences (one combined expression when a=b).

The load upper amount is \(Q_k-\max_{v=a..b}L_k(v)\) for a pair; \(Q_k-\max_{v=a..end}L_k(v)\) for pickup only; \(\min_{v=a..end}L_k(v)\) for drop only. Intersect with available inventory at i, room at j and max vehicle capacity. Complete duration increment is travel increment plus hq when a pickup is inserted, and just travel increment for drop only (that drop replaces return unloading). The time test uses T+\(10^{-7}\). For each amount, retain the cheapest feasible travel placement, ties (vehicle,a,b), by a suffix scan of placement amount limits. Evaluate all amounts 1..limit using F on the changed one/two inventories; accept only gain>\(10^{-12}\).

Choose globally: nonpositive added duration before positive; then greatest gain per added duration (compare cross products, or gain for both nonpositive), greater gain, smaller added duration, and lexicographically (i,j,q,k,a,b). Apply and fully replay; require objective agreement within \(10^{-10}\) and verified gain>\(10^{-12}\). Every insertion adds at least one previously unvisited station, so construction has at most n accepted insertions. This finite placement/amount scan is a heuristic neighborhood, not an optimization backend.

## B.8 Single and paired quantity modification

Only currently served stations participate. Enumerate a increasing, then b=0 (single) and each served b>a (pair). For every nonzero integer t set \(a'_a=a_a+t\), and \(a'_b=a_b-t\) if b exists. Station bounds give

\[
b_a-C_a-a_a\le t\le b_a-a_a;\qquad
a_b-b_b\le t\le a_b-b_b+C_b\quad(b\ne0).
\tag{B3}
\]

Intersect these with every affected prefix load \(0\le L+\chi t\le Q_k\), where chi is +1 after a, −1 after b, zero before/beyond the cancelling pair. This includes cross-vehicle modifications; each route has its own capacity. Enumerate all integers in the resulting interval increasing, skip zero. Convert signed operations to pickup=max(a',0), drop=max(−a',0), remove zero stops and shortcut travel. Sign reversal is allowed. Check complete duration, including depot unloading, at \(10^{-7}\); evaluate F; require gain>\(10^{-12}\). Choose lowest proposed objective, tie (a,b,t). Full replay and objective agreement within \(10^{-10}\) precede acceptance. Missing stations cannot be added by this operator; insertion handles them.

Strict closure computes both the best insertion and best quantity move on the same current fleet, chooses smaller proposed F, insertion on an exact tie, admits the verified strict improvement, and repeats. If neither exists, that union neighborhood is exhausted. Verification failure retains the previous fleet and records failure. This is exactly the Round76 subprocedure called by active exchange descent; the standalone Round75/76 preset entry branches are not separately run by main.

## B.9 Complete greedy decoder and its compensating moves

For each encoded route take its maximal prefix whose travel with direct return stays within T+\(10^{-12}\), stopping at the first exceeding station. Fix this travel during that decoder pass. Set the cumulative pickup budget \(B_k=\max(0,\lfloor(T-travel+10^{-12})/h\rfloor)\) (an integer sentinel max-int/4 if \(h\le10^{-12}\)); this is a handling budget, not Q. Initialize all operations zero and Y=b. The single-route proxy version instead keeps other-route operations fixed. The active mode is 1: visit vehicles and stations forward, greedily match each current surplus above clipped target to later deficits, as much as remaining supply, demand, station bounds, all intervening load bounds and pickup budget allow; leftover surplus may be collected for depot return. This constructive initialization does not require each step to decrease F.

Define an interval move by vehicle k, positions a<b, sign \(\sigma\in\{+1,-1\}\), amount \(q\ge1\). Increase a's signed operation by sigma q and decrease b's by sigma q. The sink may instead be the depot after the last position, in which case only a changes. Loads on [a,b) change by sigma q. Each final inventory must stay in [0,C], loads in [0,Q], and total positive operations in [0,B_k]. Thus an earlier delivery can be reduced/reversed and a pickup compensated elsewhere; there is still only one net one-way operation per physical station. Feasible amount bounds come from station room and the minimum/maximum load on the changed interval; the positive-part pickup change is piecewise linear with breakpoints at operation sign changes. The implementation finds the largest feasible q by these segments, then evaluates every positive integer up to it. The feasible amount sublevel contains q=0 and is an interval, so no integer hole is skipped. Objective arithmetic updates the changed ratios, pairwise absolute sum and penalties; it is not an LP/DP solve.

The active decoder loop is:

~~~text
repeat:
    repeatedly apply the best strict atomic interval move, until none
    if a strict same-route composite exists: apply best; restart
    if a strict two-route composite exists: apply best; restart
    if a strict unit interval polish exists: apply best; restart
    if a strict flow-pair redistribution exists: apply best; restart
    if no atomic move occurred in this pass: return current operations
~~~

Atomic enumeration is vehicle, source position, later sink positions then depot, sign + then −, amount increasing. Keep the best move and the eight best atoms per route. To update the best, initialize value F−EPS and replace only when candidate+EPS<best, EPS=\(10^{-12}\); this gives an effective initial gain test >2EPS. For each bounded list, append candidates until size K (\(K=8\) atoms or \(K=6\) local candidates), maintaining a max heap with comparator a.objective<b.objective. Once full, replace its front only if candidate.objective+EPS<front.objective, then restore the heap. Final sorting compares only ascending objective, with no secondary key. Equivalent-key heap positions consequently depend on the frozen standard library. Local candidates comprise each retained atom and each pair of distinct atoms on one route, adding their operation deltas simultaneously. Recheck all combined loads, positive-operation budget and station bounds, then retain at most six best candidates per route using the same bounded-heap objective logic. Candidates can individually worsen F: their combination may compensate that worsening. Same-route best selection uses F−EPS and candidate+EPS<best. Cross-route candidates combine one retained local candidate from each pair of vehicles, recompute the full common Gini/penalty objective for their jointly changed (up to eight) stations, and use the same strict test. Distinct routes have disjoint stations, so combined physical feasibility follows from their checked local feasibility; joint objective evaluation remains necessary.

Unit polish checks amount 1 for every legal atomic interval, with initial best F−\(10^{-14}\) and candidate+\(10^{-14}\)<best. Flow-pair polish ignores zero operations, partitions the route into consecutive same-sign runs, and pairs each pickup run with its immediately following drop run. For each ordered pair of distinct such run pairs, choose one pickup and drop position in each: subtract one unit from the first pickup/drop flow and add one to the second. Check both interval load changes together, station bounds and original signs; pickup total is unchanged. Its candidate helper still requires gain>\(10^{-12}\), followed by the \(10^{-14}\) best-comparison guard. Residual pair-unit, route-exact and pair-exact neighborhoods return false in this active implementation; they are not hidden optimization oracles.

After a first full decode, if its executed prefix contains zero-operation stations, delete them, keep only its nonzero active order, and run this same full decoder from zero operations **once more** on those compacted routes. Return whichever has smaller F, first decode on exact tie. This does not repeat compaction to a fixed point and does not restore the removed tail. The cached object contains complete signed operations and fitness=−F. Materializing that object removes remaining zero operations and independently checks the original physical route duration.

Decoder cache key is compaction mode plus the ordered lists with separators; it includes tail positions, even if they decode identically. On a hit return the entire stored decode. On a miss at size≥200000 clear the whole map before inserting; this is neither LRU nor a permanent visited-state ban. Internal atomic/local caches are tied to an incremented operation-state epoch and cleared after accepted updates. The static ratio/penalty preprocessing cache keys capacities, targets and weights (including source slice offsets); it affects arithmetic reuse, not candidate admission. No general accepted-state de-duplication is claimed.

## B.10 Guided order descent and ties

For each route compute the travel-only executable prefix as above. Within it record first negative-operation position and last positive-operation position. A station's role is pickup if its decoded operation>0, drop if <0; if zero, use surplus/shortage of decoded final inventory relative to target, otherwise neutral. Supply anchor is first drop, or position 0; demand anchor is immediately after last pickup, otherwise prefix end.

Generate, in vehicle order: move the last zero-operation prefix station to that route's end; collect every nonneutral prefix position plus the first supply and first demand in its tail. Move a supply lying after first drop, or in tail, to the supply anchor; move a demand before last pickup, or in tail with a last pickup present, to the demand anchor. Duplicate generated candidates are not globally removed. Same-route erase/insert decrements destination position if it originally lay after the erased position; skip unchanged order. For interroute proposals take only the first supply/demand in each source tail, each different destination in order: insert supply at destination's supply anchor if that route contains any demand-role station; insert demand at its demand anchor if it has an executed pickup.

The proxy fully runs the single-route incremental decoder with other-route operations fixed. For a two-route change try both route decoding orders and take the larger fitness (smaller F). Proxies only order proposals: sort decreasing proxy fitness, then fully decode in that order and accept the first fitness increase>\(10^{-12}\). An unsuccessful pass evaluates every generated proposal, including a poor proxy. There is no top-k rejection here.

The guided comparator has no secondary key: equal proxy values are equivalent to C++ `std::sort`, which is not stable. Likewise internal bounded-heap/objective-only sorts have implementation-dependent equivalent-key order. For the frozen compiler/library they supply the recorded run's repeatable behavior; a cross-language implementation may choose a different equivalent-key order and consequently a different heuristic path. Specifying lexicographic ties here would change the frozen algorithm. By contrast B.7/B.8 and the physical block operators do have explicit deterministic ties. This limitation affects path-level reproduction, not feasibility, exact model scope or native lower-bound validity.

## B.11 Neutral block moves and exit argument

Strict closure is followed by one best neutral move from the union below. The potential is the **complete** vector of all vehicle durations, sorted decreasingly, including zeros for unused vehicles; compare it with exact C++ lexicographic `<`, never by an aggregate sum or a tolerance that ignores an earlier increase.

Balanced relocation enumerates source vehicle, all nonempty contiguous half-open position blocks [a,b), other target vehicle and every insertion leg. Require net signed operation zero. If relative prefix load extrema inside the block are lo,hi, require target load+lo≥0 and target load+hi≤Q_target. Removing a net-zero block leaves source suffix loads unchanged; inserting it leaves target suffix loads unchanged. Keep operation quantities and order inside the block; recompute both full durations and accept only if each≤T+\(10^{-7}\) and the sorted vector strictly improves. Choose smallest potential, tie (source,a,b,target,leg).

Equal-net exchange enumerates every contiguous nonempty block per route, bucketed by integer net operation in increasing net order; pair vehicles s<t and blocks from equal-net buckets. At each insertion prefix require its old load plus the incoming block's relative extrema in that vehicle's [0,Q]. Equal net preserves all suffix loads, even when the common net is nonzero. Replace the two blocks in their original internal order, preserve all station operations, recompute complete durations and compare the same potential. Choose smallest potential, tie \(kind,source,a,b,target,target_a,target_b\), with kind 0 relocation before kind 1 exchange. `bestRound83Neutral` evaluates the whole relocation neighborhood first and then exchanges.

Before accepting a neutral candidate, independent replay requires identical final-inventory vector, **exactly equal recomputed objective**, and exact equality between recomputed duration potential and the proposed potential, which must strictly improve the prior one. Failed admission retains the prior fleet. After an accepted neutral move, run strict closure again. Stop on exact verified objective zero, common deadline, failed verification, or closure plus no improving neutral move. A selected no-move event is an exhaustion claim only for these enumerated neighborhoods.

In ideal arithmetic, after the finite construction the accepted physical phases strictly decrease (F,sorted durations) lexicographically, and the finite space of labelled routes/integer quantities excludes cycles. The order-descent phase strictly increases its deterministic decoded fitness on a finite set of orders. The implementation uses incremental floating arithmetic and tolerances in the decoder; these comparisons are not a proof of exact rational monotonicity or an accumulated error bound. The physical block phases have exact inventory/objective equality for neutral steps, unlike a merely tolerance-neutral rule. There is no fabricated de-duplication argument. The common deadline and external lifecycle cap are the operational stopping boundary; expensive decoder calls are finite routines and do not have a separate native optimization timeout. H neighborhood closure never certifies the original optimum.


## B.12 Separately identified inclusive-root research control (Round128)

MD-R version 1 is a research ablation, not another proposed algorithm. Historical supplement [the R130 historical account](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/manuscript.md) Section 6.8 and the root contract define its same-H inclusive domain, semantic shortcut omission, mandatory actual own-Start pre-LP check, one LP plus one integer MIP, fixed cutoff and complete native optimal-root return obligation. It retains the physical and signed numerical evidence policy. TIME_LIMIT/INTERRUPTED may yield a qualified open endpoint with null T_cert; a near-equal bound alone cannot satisfy its missing optimal-return obligation. Its extra checks and complete costs are paid. These control-specific guards leave the frozen ordinary procedure and the historical evidence in this appendix unchanged.


## B.13 Uniform support candidate confirmation (Round129)

Round129 changes no production source, H, model generator, numerical policy or controller. It reuses original E2 modes mb/ms2/p. The sole candidate MS2 suppresses triple support for every input while retaining pairs, ordered supply and the shared enumeration order/cap. The five fixed candidate rules and thirty complete paid observations are in [the R130 historical account](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/manuscript.md) Section 6.9. At the R129 selection stage, MS2 was the proposed candidate and full M-B was the then-current frozen method. That historical distinction and all tables remain; R130 adopted S2/MS2 as the sole paper method, unchanged through Round132. The independent finite review and public recovery are evidence checks, not new native solves or rational proofs of all matrices.

## B.14 Historical pair-support adoption and attribution controls

The sole paper method retains the historical E2 `ms2` identity, called S2. Historical E3 retains that version's source behavior and adds the off-by-default unique `s2-root` identity plus PS parameter evidence readback. E2 is retained unchanged. PS reuses the full original-compact mapper/validator; S2R reuses R128 inclusive-root semantics with triple emission disabled. Historical supplement [the R130 historical account](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/manuscript.md) Section 6.10 states the paid workflows, exact cutoff complement, nonzero LP/MIP obligations, source/return/coverage requirements, actual exposure and attribution limits. No individual cut, H, threshold or native parameter is optimized here. The passed R129 candidate selection is not rerun.


\clearpage

# Appendix C. Equivalent-expression proofs and actual-model conditions

## C.3. Projection of the three geometry row families

Delete only H-spread, variable-\(S\) centering and fixed-\(S\) centering. Keep all \(H\) absolute-value lower bounds, individual bounds, total cap/floor, original Gini epigraph, scalar/SP estimators, cutoff, real domains and domain-generation rules. For \(n\ge2\) the ideal three families are

\[
(n-1)H_{ij}\le n\beta S,\quad
\pm(n-1)(r_i-r_j)\le n\beta S,\quad
\pm(r_i-r_j)\le \frac{n\beta\bar S}{n-1}.
\]

Let \(H_\Sigma=\sum_{i<j}H_{ij}\). The retained original epigraph is \(H_\Sigma\le n\sum_i Z_i/D_i\). Nonnegative states and \(q_{iy}\le\beta s_{iy}\) give \(Z_i\le\beta Y_i\), hence \(H_\Sigma\le n\beta S\). Triangle inequalities give \(A\ge(n-1)|r_i-r_j|\): for each third station \(t\), \(|r_i-r_t|+|r_t-r_j|\ge|r_i-r_j|\), together with the pair itself; unused pair distances are nonnegative. Thus both centering families follow from the retained inequalities and \(S\le\bar S\).

### Root interval

When \(\alpha=0\), replace every \(H_{ij}\) by \(|r_i-r_j|\). This decreases the sum, respects its upper bounds and all individual upper bounds under the audited conditions, and the floor reduces to nonnegativity. The new \(H\) satisfies H-spread and leaves all non-\(H\) variables and the objective unchanged. Reverse inclusion follows by adding constraints. Thus projecting away all \(H\) gives equal LP sets and equal ideal LP objective values. Because \(H\) is continuous, the same extension preserves any remaining integer restrictions.

### Positive lower endpoint

Assume \(0\le\alpha\le\beta\), \(r_i\ge0\), \(S\le\bar S\); individual \(H\) upper bounds \(U_{ij}=c_i+c_j\) with \(c_i\ge0\) and \(r_i\le c_i\); and outside the deleted families \(H\) appears only in absolute lower bounds, individual bounds, a total floor/cap and other uniform total upper bounds. It has zero objective coefficient and no additional individual positive lower bounds or nonuniform linear uses.

Fix every non-\(H\) variable in a feasible point of the deletion model. Put \(d_{ij}=|r_i-r_j|\), \(A=\sum_{i<j}d_{ij}\), \(L=n\alpha S\) and \(t=n\beta S/(n-1)\). Let \(B\) be the smallest retained total upper bound, including the implied \(n\beta S\). Feasibility gives

\[
T^*=\max(A,L)\le\min\left(B,\sum_{i<j}U_{ij}\right).
\]

The triangle argument gives \(d_{ij}\le t\). Set \(U'_{ij}=\min(c_i+c_j,t)\). For \(C=\sum_i c_i>0\), the function \(f(\mathbf c)=\sum_{i<j}\min(c_i+c_j,t)\) is concave on the nonnegative simplex of sum \(C\). With \(e_i^{\rm unit}\) denoting the standard unit vector, write \(\mathbf c=\sum_i(c_i/C)C e_i^{\rm unit}\). Concavity gives

\[
\sum_{i<j}U'_{ij}=f(\mathbf c)\ge(n-1)\min(C,t)
=\min\left(\sum_{i<j}U_{ij},n\beta S\right)\ge T^*.
\]

If \(\sum_{i<j}U'_{ij}>A\), set

\[
\theta=\frac{T^*-A}{\sum_{i<j}U'_{ij}-A},\qquad
H'_{ij}=d_{ij}+\theta(U'_{ij}-d_{ij}).
\]

Then \(0\le\theta\le1\); every individual bound and spread bound holds, \(\sum_{i<j}H'_{ij}=T^*\le B\), and the floor holds. The centering rows already follow without \(H\). All non-\(H\) variables and their objective remain unchanged. If the denominator vanishes, \(T^*=A\) and \(H'=d\) suffices. If \(C=0\), all \(c,r,S,A,L\) vanish and \(H'=0\). If \(S=0\), nonnegative ratios vanish and \(H'=0\). For \(n=1\) none of these three families is generated. This proves both projected inclusions, including the nonzero-floor case in which setting \(H=d\) alone can fail.

### Actual-model application and numerical boundary

The current shared canonical factory generates the named three families, and the frozen paper profile disables local/subset nonuniform \(H\) uses. The Cplex writer sets \(H\) upper bounds to \(\operatorname{fl}(C_i/D_i+C_j/D_j)\), with zero objective coefficients. The independent reviewer inspected an actual saved S12 S2R matrix: 66 \(H\) bounds, five uniform full-\(H\) rows and 198 individual-\(H\) rows. \(W\) appears in five rows, as required below. This is a canonical-model result, not a theorem about arbitrary native node cuts.

The exact additive upper-bound hypothesis concerns real algebra. In the saved S12 matrix, 41 of 66 serialized \(H\) bounds differ from the exact rational sum of the two serialized \(r\) upper bounds at roughly \(10^{-16}\). Therefore the ideal theorem is not asserted as strict rational equality for every serialized floating matrix. Necessary actual coefficient/domain checks and extension residuals accompany the research comparisons. In that frozen R132 expression study the production S2 bytes were unchanged and no hidden outward correction was applied. The later candidate's explicit inclusive-cutoff repair has a separate identity and is not attributed to expression deletion. Equal projections do not imply identical presolve, native cuts, search paths or elapsed time, and do not make the entire \(C_G\) package redundant.

## C.4. Exact elimination of W, including its real bounds

In the active shared model \(W=W_{\rm SP}\) is continuous, has zero objective coefficient and is used by four MC rows, one SP cutoff and its own box. No other use is present in the qualified canonical scope. Preserve all \(W\)-free original rows, variable types and bounds, particularly \(g+\lambda P\le c\), which a cross-multiplied row cannot replace at \(S=0\).

For actual \(W\) bounds \(w_l,w_u\) and MC parameters \(s_l,s_u,p_l,p_u\), define

\[
L_0=w_l,\quad L_1=s_lP+p_lS-s_lp_l,\quad
L_2=s_uP+p_uS-s_up_u,
\]
\[
U_0=w_u,\quad U_1=s_uP+p_lS-s_up_l,\quad
U_2=s_lP+p_uS-s_lp_u.
\]

The original system is \(L_j\le W\le U_k\) and \(H_\Sigma+n\lambda W\le ncS\). For \(\lambda>0\), its complete projection is all nine compatibility rows \(L_j\le U_k\) and all three lower-cutoff rows \(H_\Sigma+n\lambda L_j\le ncS\). Necessity is immediate. Conversely, \(W=\max_jL_j\) satisfies every upper bound and the SP cutoff, proving sufficiency. This is standard one-variable Fourier-Motzkin elimination applied to this formulation, not a new linearization theorem or an exact continuous product identity.

Only after proving the same explicit nonnegative rectangle \(0\le s_l\le S\le s_u\), \(0\le p_l\le P\le p_u\), and that the actual \(W\) box is no tighter than the product box, may compatibility and box rows be removed. The true product \(SP\) is then an extension for MC feasibility. Since \(L_1-s_lp_l=s_l(P-p_l)+p_l(S-s_l)\ge0\) and \(w_l\le s_lp_l\), the constant lower plane is dominated. The two lower-plane cutoffs then suffice, with \(W=\max(L_1,L_2)\). Current inflated \(e\) can violate the tight physical \(P\) upper estimate; that estimate cannot simply be assumed to bound the whole epigraph.

For positive width \(s_u>s_l\), MC lower/upper pairings imply \(P\ge p_l\) and \(P\le p_u\) after cancellation. These consequences must survive projection. For example, \(s_l=1,s_u=2,p_l=0,p_u=1,S=1,P=2,H_\Sigma=0\) and sufficiently large \(c\) satisfy both lower-plane cutoffs, but \(L_2=3>U_2=2\), so no original \(W\) exists. Two cutoffs alone would incorrectly enlarge the domain.

When \(S\) is fixed, derive compatibility directly rather than dividing by its width. At \(S=0\), \(W=0\) need not imply \(P\le p_u\). The full pair system handles that case without adding an unauthorized \(P\) bound. When \(\lambda=0\), retain \(H_\Sigma\le ncS\) and every \(W\)-feasibility compatibility row; removing the whole block would again change its projection. Zero-width \(P\) and simultaneous degeneracy are also covered by the pair construction.

### Implemented research expression

The research writer reads the actual shared canonical row coefficients, normalizes their senses, includes the exact actual \(W\) box, and combines every lower/upper pair. There are three lower rows and four upper rows including the SP row: 12 projected rows. It retains even constant or duplicate compatibility rows. All remaining original rows, objective, bounds and integer types stay intact; only the \(W\) column and its rows are replaced. Its physical Start is mapped to the remaining actual columns and validated before use.

The independent checker reconstructs these combinations with exact rational arithmetic on source binary64 coefficients. It separately bounds the output coefficient-serialization residual over actual remaining-variable bounds. The candidate binary64 output is qualified as numerically consistent, not asserted to equal the exact rational projected matrix. `C_matrix_wording_addendum.json` makes this distinction explicit. Four saved interval/input configurations have equal canonical all-continuous LP objectives within the inherited \(10^{-7}\) policy. These finite observations check implementation and numerical behavior; they do not replace the general projection proof.

## C.5. Qualification and relation to costs

The research default-off writer and original E3 produce identical complete canonical LP bytes on the qualified small and medium fixtures, at a root interval and a positive lower endpoint. Actual S12 CLI runs bridge original E3 to research default-off, and validate independent H and full Start submission for both candidates. Each uses the legal inclusive-root LP then restored-integer MIP workflow. Default-off equivalence is a semantic/matrix bridge; the two executable byte strings are different and are never described as identical.

All 24 admitted C workflows are now sealed. Geometry deletion gives 2 Win, 4 Lose and 2 UNDETERMINED; full W projection gives 3 Win, 3 Lose and 2 UNDETERMINED against the same-build inclusive-root baseline. All 16 candidate/baseline comparisons have identical complete realized H, matching root intervals/cutoffs and actual native exposure. The continuous root objectives agree within the original numerical policy, while Work/nodes and complete costs vary in both directions. This supports mixed expression costs, not a stronger ideal relaxation or automatic production replacement. D remains the original frozen algorithm and its measurements do not come from this research build.

