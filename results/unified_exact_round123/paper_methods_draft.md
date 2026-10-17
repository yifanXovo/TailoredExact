# A complete frozen inventory–routing method with scoped numerical certification

## Problem and physical objective

We consider a static redistribution problem on service stations \(i=1,\ldots,V\), with depot 0 excluded from all inventory, target-ratio and weight sums. Station \(i\) has integer capacity \(C_i\), initial inventory \(b_i\), and target \(0<D_i\le C_i\). Vehicle \(k\) has capacity \(Q_k\) and physical route horizon \(T\). Each vehicle leaves the depot empty, follows one depot-to-depot route, and may return loaded. A station is either unserved or receives exactly one nonzero, unidirectional, integer service from one vehicle. With pickup and delivery quantities \(p_{ki},d_{ki}\ge0\), final inventory is

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\qquad 0\le Y_i\le C_i.
\tag{1}
\]

Every route prefix, including the last return, has load in \([0,Q_k]\). Let \(P_k=\sum_i p_{ki}\), \(D_k^{\rm drop}=\sum_i d_{ki}\), and \(R_k=P_k-D_k^{\rm drop}\ge0\) be the return load. Travel time is the Euclidean distance between the serialized points divided by 1.5. With pickup and drop handling times \(t_p,t_d\), the route-duration constraint is

\[
\sum_{(i,j)\text{ on route }k}\frac{\|x_i-x_j\|_2}{1.5}
 +t_pP_k+t_d(D_k^{\rm drop}+R_k)
 =\operatorname{travel}_k+(t_p+t_d)P_k\le T.
\tag{2}
\]

The equality follows from empty departure and nonnegative return load. It accounts for depot unloading. Capacity is a bound on simultaneous load, so repeated pickups separated by deliveries may have \(P_k>Q_k\). The input field `min_ratio` introduces no additional inventory floor. Summing (1) gives \(\sum_iY_i+\sum_kR_k=\sum_i b_i\); station inventory alone need not be conserved. These semantics are implemented by the original Parser, Evaluator and compact-model resource block [M1–M3].

Define \(r_i=Y_i/D_i\), \(S=\sum_i r_i\), and \(A=\sum_{i<j}|r_i-r_j|\). The physical objective is

\[
G_{\rm true}(Y)=\begin{cases}A/(VS),&S>0,\\0,&S=0,\end{cases}
\qquad
F(Y)=G_{\rm true}(Y)+\lambda\sum_i\omega_i|r_i-1|.
\tag{3}
\]

Weights and \(\lambda\) are nonnegative; the studied inputs have positive service-station weights and \(\lambda=.15\). The penalty is a two-sided relative deviation from target, rather than observed rental or return failure demand. Travel is constrained by (2); it is not an additional term minimized by (3). The zero-denominator convention retains the penalty. Because ratios are nonnegative, \(A\le(V-1)S\), so \(0\le G_{\rm true}\le(V-1)/V\) when \(S>0\); at \(S=0\), the same nonnegativity remains valid. The executable evaluates each proposed fleet using (1)–(3), independently of its native auxiliary objective [M1,M2].

## Exact inventory products and implicit service integrality

The routing core uses binary route arcs, visit assignments \(z_{ki}\), and directions \(m_{ki}\), with flow/connectivity constraints, unique service \(\sum_kz_{ki}\le1\), inventory balance, and prefix-load and duration constraints. For \(\bar p_{ki}=\min(b_i,Q_k)\) and \(\bar d_{ki}=\min(C_i-b_i,Q_k)\), its protected service rows include

\[
0\le m_{ki}\le z_{ki},\quad
0\le p_{ki}\le\bar p_{ki}m_{ki},\quad
0\le d_{ki}\le\bar d_{ki}(z_{ki}-m_{ki}),\quad
p_{ki}+d_{ki}\ge z_{ki}.
\tag{4}
\]

The individual quantity bounds are consistent with simultaneous capacity; they do not bound cumulative route pickup. Integer inventory and load variables and binary routing/state variables are retained. ENS-C declares pickup and delivery integer. The frozen M-B reference declares these quantities continuous while retaining (1), (4), unique assignment and all original resource rows [M3,M4].

**Lemma 1 (implicit quantity integrality).** If initial and final inventories are integer, each station has at most one binary vehicle assignment, and the direction and service rows (4) hold, every pickup and delivery quantity is integer even if declared continuous.

*Proof.* An unassigned vehicle has \(z_{ki}=0\), hence \(m_{ki}=p_{ki}=d_{ki}=0\). At the unique assigned vehicle, \(m_{ki}=1\) forces \(d_{ki}=0\), and (1) gives \(p_{ki}=b_i-Y_i\in\mathbb Z\). If \(m_{ki}=0\), pickup is zero and delivery equals \(Y_i-b_i\in\mathbb Z\). The last row of (4) excludes a zero operation at a visited station. Zero directional bounds and heterogeneous capacities require no division and cause no exception. Thus relaxing only the quantity declarations preserves the integer feasible solutions and their objectives. This local proof does not assert that all continuous relaxations have identical convex hulls. It does not extend to fractional inventories or assignments, split service, or simultaneous pickup and delivery. Integer load is retained in the implementation but is not an additional premise of this proof. ∎

For a valid finite inventory domain \(\mathcal Y_i\subseteq\{0,\ldots,C_i\}\), the VD-P representation uses binary \(s_{iy}\) and continuous \(q_{iy}\):

\[
\sum_{y\in\mathcal Y_i}s_{iy}=1,\quad
Y_i=\sum_yys_{iy},\quad
a s_{iy}\le q_{iy}\le b s_{iy},\quad
\sum_yq_{iy}=g,\quad Z_i=\sum_yyq_{iy}.
\tag{5}
\]

Here \([a,b]\) is the model's current Gini interval and \(g\) is its native epigraph variable, named `G` in the saved matrix. The model also has \(r_i=Y_i/D_i\), \(e_i\ge|r_i-1|\), \(H_{ij}\ge|r_i-r_j|\), and

\[
V\sum_i Z_i/D_i\ge\sum_{i<j}H_{ij},\qquad
f=g+\lambda\sum_i\omega_i e_i.
\tag{6}
\]

**Lemma 2 (product exactness and objective-preserving embedding).** At integer selectors, (5) enforces \(Z_i=gY_i\). Every physically feasible fleet whose true Gini and objective satisfy the current interval and cutoff has an extension with \(g=G_{\rm true}\), \(e_i=|r_i-1|\), \(H_{ij}=|r_i-r_j|\), and \(f=F\), provided the inventory domains and strengthening preserve that fleet.

*Proof.* Exactly one inventory state is selected. The bounds in (5) set all other \(q\)'s to zero and their sum sets the selected one to \(g\). This proves the product identity. Conversely select the physical inventory, place \(g\) at that state, and use its actual route, quantities and loads. Equations (1), (2), (4)–(6) then hold with equality in the physical objective block. At \(S=0\), all ratios and pair differences are zero; \(g=0\) realizes the stipulated convention whenever the obligation includes true Gini0. For an arbitrary integer completion with \(S>0\), (6) implies \(g\ge G_{\rm true}\), so \(f\ge F\); at \(S=0\), \(g\ge0=G_{\rm true}\) suffices. ∎

An arbitrary native \(g\) is therefore not the fleet's true Gini. In particular, a model with \(g\in[a,b]\) may contain an inflated-g completion of a physical fleet with \(G_{\rm true}<a\). The proof needs objective-preserving embeddings of the physical points assigned to that obligation; it does not infer physical interval membership from every auxiliary completion. A local native objective or an inventory vector alone is not a physical upper bound. Full fleet decoding and replay remain necessary. The exactness in Lemma 2 concerns the inventory-product block and admissible integer embeddings, not the convex hull of the route-coupled relaxation.

M-B retains two existing state/service rows per station:

\[
\sum_k(p_{ki}+d_{ki})=\sum_{y\in\mathcal Y_i}|b_i-y|s_{iy},\qquad
\sum_kz_{ki}=1-s_{i,b_i}.
\tag{7}
\]

If the initial inventory is outside the proved domain, the missing state is interpreted as zero, not added artificially. Under unique one-way service the left side of the first row is \(|b_i-Y_i|\), and an integral state selects precisely that value. The station is served exactly when \(Y_i\ne b_i\), because (4) excludes a nonzero visit at unchanged inventory. This proves (7) valid for original integer solutions. The rows can strengthen the relaxation; neither is needed for Lemma 1, and validity does not guarantee a strict bound gain or reduced native search time. The independent ENS-Q switch remains false [M3,M4].

## Inherited strengthening and model domains

Each scoped model retains the frozen F0 families, not a new family selected for the long study. Their validity is conditional on their declared domains. We summarize the mathematical reasons rather than treating an implementation's `passed` field as a proof. Inventory conservation follows from nonnegative returns. A metric route visiting station \(i\) travels at least \(t_{0i}+t_{i0}\); together with (2) and individual capacity this yields the inherited movement/reachability domains. For a true-G interval lower endpoint \(a\) and actual cutoff \(c\), any admitted fleet satisfies \(\lambda\omega_i|Y_i/D_i-1|\le c-a\). With positive weight this supplies safe integer inventory bounds after conservative rounding; a zero weight supplies no such tightening. Absolute-deviation bounds follow from the resulting inventory intervals.

The remaining interval rows admit direct physical embeddings. True \(G\in[a,b]\) implies \(VaS\le A\le VbS\). The triangle inequality gives \((V-1)|r_i-r_j|\le A\), hence the pairwise spread and range-centering consequences of \(A\le VbS\). Bounds on \(S\), inventory and penalty permit ordinary McCormick envelopes for the auxiliary products: the exact physical product lies in each envelope. If \(S\le\bar S\), \(A/(V\bar S)+\lambda P\le F\le c\) implies the objective estimator \(A+V\bar S\lambda P\le V\bar S c\). The alternative SP estimator follows by multiplying \(F\le c\) by \(VS\), with a physical extension \(W_{SP}=SP\); the explicit original objective row is retained, including at \(S=0\). Minimum movement, support-duration and transfer-compatibility rows use necessary pickup/drop, metric tour-duration and source/sink capacities, so the exact physical route satisfies them. The factory registers global versus interval-local scopes explicitly [M5].

These arguments establish why such rows may preserve the required physical embeddings; the actual writer, bounds, cutoffs, numeric tolerances and finite family selection remain part of the implementation contract. Static support enumeration is limited to subsets of size at most 3 and at most 50000 generated subsets. Omitting ungenerated valid strengthening does not omit a route-feasibility constraint or a proof obligation. No new user cut, lazy constraint, projection cut, branch priority or heuristic is introduced here. A row derived for a child domain is not promoted to an unrelated parent or sibling merely because its label is familiar.

Exact row validity and the implementation's numerical closure must also be separated. If a valid local penalty floor is \(\underline P\), every physical point in a true-G interval beginning at \(a\) satisfies \(F\ge a+\lambda\underline P\). The existing writer may close the cutoff region when this quantity is at least \(c-10^{-9}\), by adding an infeasible row [M5, lines 739–752]. In exact arithmetic this condition can omit a point with \(c-10^{-9}\le F<c\); the maximum omitted improvement relative to that cutoff is \(10^{-9}\). It therefore belongs to the inherited floating numerical closure policy, rather than a theorem that every serialized matrix preserves every arbitrarily small exact improvement. Lemma 2's exact embedding applies when its domain/strengthening premise holds; numerical closure and all other native arithmetic are reported under the original \(10^{-7}\) evidence policy. No rational exact feasible-set or optimality claim is made for a matrix closed only by that numerical guard. This observation changes no row, tolerance, source endpoint or production lower bound.

## The complete M-B algorithm

Every M-B and ENS-C arm first pays for the same finite startup procedure H. It combines joint insertion construction with 24 fixed orders under Seed 20260626 and the constructive 25th seed, fully decodes each using `nGreedyLU_RA_compact_full` in compaction mode1, applies guided strict descent, and then alternates the inherited insertion/quantity/R76 closure with the union of R78 balanced relocation and R83 equal-net block exchange. Neutral accepted union moves strictly improve the complete sorted-duration tuple. The bounded decoded-order cache and deterministic ties remain. The outer incumbent store accepts objective improvements using its original threshold, so a neutral change inside H need not become a later native Start [M6].

There are finitely many route orders, assignments and integer quantities. Strict objective descent and strictly improving duration-tuple moves cannot cycle among these physical states; the absolute work deadline can terminate H earlier. Such termination or neighborhood closure supplies a legal own fleet, not original-problem optimality. A verified zero objective can close against \(F\ge0\) under the inherited zero policy. Otherwise the same complete interval controller is invoked on all roles; the method never dispatches different algorithms by role name, inventory regime, scale, elapsed time, Work or stagnation.

An obligation records its Gini interval, immutable complete model identity, inventory domain, actual objective cutoff \(c\), call and epoch, scoped lower evidence and unresolved status. The initial improving domain is \(0\le G_{\rm true}\le\min((V-1)/V,U)\), since \(F\ge G_{\rm true}\) and an own physical \(U\) is available. The complement cannot improve \(U\) and remains explicitly represented in the lower-bound argument. LP requests relax the actual saved integer VType array of that model; before an integer request, the captured original types are restored. A relaxed feasible objective is not a lower certificate unless the appropriate native optimal/dual-bound and lifecycle evidence qualifies it. MIP requests use the restored integer domain and may return a qualified bound while remaining open. Unknown or unreturned work is not silently substituted for a returned proof [M7,M8].

For the parent bound \(B_p\), own \(U\), and two qualified child LP bounds \(b_0,b_1\), the original AM rule sets

\[
\Delta=\max\{U-B_p,\max(\varepsilon,10^{-12})\},\quad
v_j=\operatorname{clip}((b_j-B_p)/\Delta,0,1),\quad
\eta=\min(v_0,v_1),\quad\mu=(v_0+v_1)/2,
\tag{8}
\]

and uses \(\eta\mu\) against threshold 0.08 with its original scale-dependent comparison tolerance. Original child-infeasibility handling commits both children while retaining the proved empty half. No strict child-disjunction improvement invokes complete parent MIP; sufficient score commits an atomic midpoint split; a smaller positive improvement requests a parent bound target and then requeues the obligation. Frontier targets are justified by other relevant covering obligations. K0=1, midpoint subdivision, maximum depth 8 and width threshold\(10^{-4}\) are fixed. A depth/width limit triggers complete MIP or an open retained obligation; it does not itself prove closure. A mathematical bound target can interrupt a native request without changing the single total deadline or discarding the unresolved domain.

Before an integer request, an eligible own verified fleet may be mapped to every actual model column, including empty vehicles and auxiliaries. Eligibility is checked against the current interval/cutoff using its true Gini. The complete mapped vector is checked against rows, bounds, types and objective, then submitted and read back. Mapping, submission, API acceptance and a later native incumbent are separate observations. A globally valid fleet outside a target leaf need not provide that leaf with an exact-g Start. Absence of such a Start is compatible with a sound global upper bound. Starts and H never supply lower-bound proofs.

```text
FrozenMB(instance, physical parameters, one absolute process deadline):
  parse the original instance; create an empty own evidence store
  run the complete independently paid H while work time remains
  replay accepted full fleets and retain the own physical incumbent U
  if the inherited verified-zero rule closes against F >= 0: seal and return
  initialize a complete cover of all possible strict improvers under U
  while a relevant obligation exists and work time remains:
    choose the original controlling obligation, preserving every sibling
    build/reuse only its identity-bound full VD-P/F0 model and current epoch
    obtain the original paid, returned LP evidence for required domains
    apply the original AM decision (8):
      keep/requeue the parent, request its mathematical bound target,
      launch complete MIP, or replace the parent atomically by both children
    for each actually requested MIP:
      restore original VTypes; clear explicit old Starts
      map/check/submit/read back an eligible own complete Start, if one exists
      optimize only within the same remaining absolute work deadline
      replay proposed physical fleets before updating U
      qualify returned bounds only on their exact model/domain/cutoff
    close only obligations justified by admitted proofs; retain all others
  finalize the full cover, native cleanup and mandatory output; seal producer
  perform independent post-seal physical/model/scope/clock verification
  report final-fleet U, qualified full-cover L and numerical status
```

Cold P-GRB instead solves the complete original canonical compact formulation from scratch, without H or another method's Start, cutoff, bound, tree or cache. ENS-C follows the same integrated procedure with its original integer quantity declarations and without M-B's A/B rows. These are three complete methods, each paying its own online work.

## Scoped lower bounds and complete numerical certification

**Lemma 3 (cutoff complement).** Suppose a qualified returned LP/MIP bound \(\ell\) applies to physical points with \(G_{\rm true}\in I\) and \(F\le c\), through Lemma 2's embedding. Then \(\min(\ell,c)\) is a bound for every physical point with true Gini in \(I\).

*Proof.* Points in the cutoff set have \(F=f\ge\ell\). Points outside it have \(F>c\). The minimum bounds both sets. An infeasibility proof excludes only the cutoff set and leaves \(c\) as the unconditional regional floor. Thus a bound 1 from a model cut off at .5 cannot exclude an original feasible point of value .6 outside that cutoff. ∎

If several qualified bounds concern the same domain they may be combined by maximum. Transfer to a new obligation requires that the proved domain contain that obligation and that the cutoff or its complement be handled. A bound on a child cannot certify an uncovered parent; a sibling's larger bound cannot replace a smaller unresolved bound. Models sharing a leaf name can differ by cutoff or epoch; identity requires the actual matrix SHA and scope. Calls in a reused logfile are paired with their actual byte spans, immutable models, settings, Start and returns [M8].

**Lemma 4 (coverage invariant).** Maintain a complete cover of all possible improving true-G values and an analytic complement. For each covering unit \(I\), retain a valid unconditional regional floor \(\beta_I\), including its cutoff complement. Then

\[
L=\min\{U,\;\min_{I\text{ in the complete cover}}\beta_I\}
\tag{9}
\]

is a lower bound for the original optimum, with the initial non-improving complement represented by \(U\).

*Proof.* An original feasible point either lies in the analytic complement, where its objective is at least the applicable complement floor, or has true Gini in a covering unit. Lemma 3 bounds it in that unit. Taking the minimum is valid for their union. At initialization, \(F\ge G_{\rm true}\) justifies the outside-Gini complement. A midpoint split replaces \([a,b]\) only after both closed children \([a,m]\) and \([m,b]\), their proofs and cutoffs are registered atomically. They cover the parent, including the shared endpoint. Keeping an unresolved parent preserves the same invariant. Qualified closure preserves its proved floor in the cover; a scheduling decision or a native target does not delete an obligation. Induction proves (9). ∎

A native terminal OPTIMAL/INFEASIBLE status consequently supplies local information, not a whole-problem certificate. An original numerical certificate additionally requires an own physically verified \(U\), complete qualified model/return and coverage chains, lifecycle completion, and the inherited signed-gap closure test at\(10^{-7}\). Requested native MIPGap and MIPGapAbs are zero; FeasibilityTol and OptimalityTol are\(10^{-6}\), and IntFeasTol is\(10^{-5}\). These are floating-point numerical certificates under that policy. Exact rational checks of stored coefficients establish algebraic facts about those coefficients; they do not turn Gurobi's floating-point optimization into a rational exact certificate.

A proved same-domain lower-bound counterexample revokes its source and dependent search/closure. An independent physical fleet can remain valid, but a good own upper bound or the analytic zero floor cannot repair incorrect pruning. Source-reduced physical/open results are reported separately and receive no dependent nonzero certificate credit. Ordinary time limits and missing finite incumbent/bound information are retained as open or censored observations, with unevaluable pairs where needed, rather than filled from historical routes.

The method uses a finite physical search space and bounded scheduled requests under one process deadline; this is distinct from obtaining an optimality certificate in that window. Physical horizon\(T\) constrains each route, while computational cap constrains the complete method's online production. In Round123 these values are 10800 and 18000 seconds, respectively. The original 30-second native shutdown reserve remains. No proof time is inferred from an open cap or from a percentage gap.

Trajectory availability also requires a clock scope. Existing committed observations use the supervisor's GetTickCount64 elapsed clock, while the complete producer duration uses QueryPerformanceCounter. The offline reader preserves the raw times and converts availability to a conservative arm-origin upper time using the native-end/wrapper-wall origin and recorded wall-origin pairs. The fixed 1-second presentation envelope and failed-alignment behavior were declared in `observation_clock_contract.json` before the first 3600-second formal checkpoint. This changes neither the producer clocks nor any solver tolerance, deadline or observation frequency. An unqualified alignment leaves prefix values unknown until sealing. At each requested checkpoint the table uses the last already available legal fleet and qualified bound, with the historical minimum in a separate descriptive column. A finished arm contributes one actual endpoint; later requested points have no invented computation or backfilled API bound.

## Two offline qualifications of the present evidence

The D1 candidate is not part of the Round123 experiment and is no longer under selection. Its two R122 V35 instances nevertheless admit a useful exact boundary statement. The original model has \(f=g+\lambda\sum_i\omega_i e_i\ge g\), with nonnegative \(e_i\), positive penalty coefficients and actual ObjCon 0. For \(g\in[a,b]\), midpoint \(m\), and side floors \(\beta_0\le a,\beta_1\le m\), any original point, including a fractional LP point, extends with binary \(h=0\) when \(g\le m\) and \(h=1\) otherwise. Its unchanged objective satisfies the appropriate side floor. Because the extension only adds rows, its projection onto the original variables equals the original feasible set.

There is a stronger continuous-extension result. The lower interval link gives \(g\ge a(1-h)+mh\), so for every \(h\in[0,1]\),

\[
f\ge g\ge a(1-h)+mh\ge\beta_0(1-h)+\beta_1h.
\tag{10}
\]

Thus the conditional objective row is redundant over the whole D0 continuous extension under these premises. For actual serialized rows \(g\ge A+Dh\) and \(f\ge B+Eh\), the sufficient check is \(A\ge B\) and \(A+D\ge B+E\), with actual ObjCon restored when forming the complete-f row. Both endpoints suffice because the difference is affine in \(h\). Round123 parses both complete saved V35 models and checks these inequalities with exact decimal fractions and exact fractions of the original native binary64 readback, including outward link rounding. The margins at\(h=1\) are about\(10^{-7}\); the actual rational values and complete matrix identities are retained in `mathematics/d1_redundancy.json` and the finite saved-model evidence. No new native LP is solved. These facts do not negate R120's nonredundancy in its original extended space, establish universal D1 redundancy, explain a particular runtime loss, or imply unchanged solver search after adding selectors/links.

For PB-C50-S, the service-station totals are \(B=\sum b_i=495\) and \(\sum D_i=562\), a shortage 67; total vehicle capacity 120 is not an external supply. By conservation and nonnegative return, \(\sum Y_i\le B\), hence \(\sum_i|Y_i-D_i|\ge67\). With \(\delta=\min_i\lambda\omega_i/D_i>0\),

\[
F\ge\lambda\sum_i\omega_i|Y_i/D_i-1|\ge67\delta>0.
\tag{11}
\]

The decimal interpretation gives \(\delta=592593/160000000\) and bound 0.24814831875. A tighter explanatory inventory relaxation drops routing, loads, duration and Gini, retains integer \(0\le Y_i\le C_i\) and \(\sum Y_i\le B\), and minimizes weighted absolute deviations. Any surplus \(Y_i>D_i\) can be reduced to target, decreasing the positive penalty and preserving feasibility. If the remaining total is below\(B\), increase a deficit inventory until the total reaches\(B\); this is possible because every target fits its capacity and \(\sum D_i>B\). Every such increase decreases penalty. An optimum therefore exists with \(0\le Y_i\le D_i\) and \(\sum Y_i=B\). Writing \(u_i=D_i-Y_i\) gives

\[
L_{\rm pen}=\min\left\{\sum_i(\lambda\omega_i/D_i)u_i:
u_i\in\{0,\ldots,D_i\},\;\sum_i u_i=67\right\}.
\tag{12}
\]

Allocating deficit units in nondecreasing unit cost is optimal: an allocation using a more expensive available unit while leaving a cheaper unit unused can be improved by exchanging one unit. Greedy allocation gives 0.26064825 in decimal arithmetic; an independent exact dynamic program agrees. `mathematics/positive_objective.json` also retains exact real interpretations of the parsed binary64 inputs, their small differences from decimal arithmetic and a directly rounded binary64 evaluation. Both explanatory bounds are weaker than the existing qualified R122 global bounds; neither is a discovered production strengthening or an injected bound. They establish that any eventual complete certificate on this role must be nonzero, without predicting whether or when the open proof gap will close.

## Implementation and contribution scope

The frozen complete method is the project's composition of a physical model, exact inventory representation, service-state formulation, paid constructive/neighborhood startup, and a coverage-preserving controller around scoped native solves. Gurobi provides its standard LP/MIP machinery, presolve, cuts and branching under unchanged defaults. Multistart search, local exchange, MIP Starts, McCormick envelopes, implicit integrality and cutoff complementation are standard mathematical/algorithmic ideas; their use here is not a claim of a new general branch-and-cut theory. This draft makes no uncompleted literature novelty claim. Attribution of the separate components' computational effects requires appropriate controls, and is not inferred merely from an integrated-method win.

The implementation identity is source-before-native `355eefd2be3fe5651195681faf7b3a63ee4032f8`, PE SHA256 `5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba`, and Gurobi13.0.2 DLL SHA256 `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`. All 216 production-source bindings are checked. ENS-C stays the project default; frozen M-B is the existing paper reference, with no claim of instancewise ENS dominance. R122 remains COMPLETE/BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION. The present methods statement incorporates its final specification and R120/R121 mathematical boundary clarifications without promoting D1, D0 or the stopped MB-PC family.

| Source key | Concrete implementation or evidence authority |
|---|---|
| M1 | [Result.cpp objective evaluator](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/Result.cpp#L109); [Parser.cpp](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/Parser.cpp#L175) |
| M2 | [Evaluator.cpp complete fleet replay](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/Evaluator.cpp#L34) |
| M3 | [CplexBaseline.cpp actual compact writer](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/CplexBaseline.cpp#L816), service rows around1827–1876 and VD-P/A/B around2970–3060; the filename is not a claim of a different backend |
| M4 | [Round98StateService.hpp](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/include/Round98StateService.hpp); [R100 mathematical derivation](https://github.com/yifanXovo/TailoredExact/blob/f3363d9ddede2725496e4a3e0466bbf4d1cec089/results/unified_exact_round100/mathematical_algorithm.md) |
| M5 | [IntervalRowFactory.cpp scope/domain and row formulas](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/IntervalRowFactory.cpp#L391); inherited F0/specification in R122 `paper_algorithm_spec.md` and R118 `paper_algorithm_spec.md` |
| M6 | [HgaTgbcRunner.cpp](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/HgaTgbcRunner.cpp), `Round73JointInsertion.cpp`, `Round76PhysicalClosure.cpp`, `Round78BalancedRelocation.cpp`, `Round83BlockExchange.cpp`, and R122 full-H records |
| M7 | [PaperExternalGiniTree.cpp AM and coverage controller](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/PaperExternalGiniTree.cpp#L1018); [ProcessPhaseLedger.cpp single work deadline](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/ProcessPhaseLedger.cpp#L39) |
| M8 | [GurobiBaseline.cpp scoped requests/types/returns](https://github.com/yifanXovo/TailoredExact/blob/355eefd2be3fe5651195681faf7b3a63ee4032f8/src/GurobiBaseline.cpp#L1968), `MipStartMapping.cpp`; R120 `mathematical_contract.md`; R122 call-scoped audit in `round122_evidence.py` and `round118_call_logs.py` |
| M9 | This round's exact-fraction algebra and finite saved-model checks: `round123_math_prior.py`, `mathematics/d1_redundancy.json`, `mathematics/positive_objective.json`; final/history-U regression: `round123_precontract.py` and `qualification/general_history_regression.json` |
