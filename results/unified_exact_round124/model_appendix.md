# Appendix A. Complete model, scoped strengthening and proof obligations

This appendix is the single maintained model specification for the manuscript. It transcribes the frozen writer, including constraints sometimes redundant for integer solutions. It does not replace the implemented model by a different vehicle-routing formulation. Equations are mathematical real-arithmetic expressions; A.7 states the separate numerical implementation boundary. Source locations refer to production snapshot 355eefd2be3fe5651195681faf7b3a63ee4032f8 [@frozenImplementation].

## A.1 Sets, data and variables

Let \(N=\{1,\ldots,n\}\) be service stations, \(N_0=N\cup\{0\}\), \(K=\{1,\ldots,m\}\), and \(A=\{(i,j)\in N_0^2:i\ne j\}\). Depot 0 is absent from every inventory, ratio, weight and Gini sum. Vehicle indexing is shifted by one relative to source indices \(0,\ldots,M-1\). All vehicle-indexed formulas hold for each \(k\in K\); all station formulas hold for each \(i\in N\), unless otherwise stated.

Station capacity \(C_i\) and initial inventory \(b_i\) are integers with \(0\le b_i\le C_i\); target inventory \(D_i\) is a positive integer no larger than \(C_i\). The parser's depot capacity/stock fields do not provide departure supply. Vehicle capacity \(Q_k>0\) is integer. A vehicle starts empty and returns to the same depot, possibly loaded. Travel time \(\tau_{ij}=\|v_i-v_j\|_2/1.5\) uses the serialized planar coordinates. The route horizon is \(T\); unit pickup/drop times are \(t_p,t_d\), with \(h=t_p+t_d\). Penalty multiplier \(\lambda\ge0\) and station weights \(\omega_i\ge0\) are data; the study uses \(\lambda=.15\), positive weights and \(t_p=t_d=60\). No inventory floor is imposed by the compatibility field min_ratio.

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

## A.5 Actual F0 strengthening

The root/interval package is configured by PaperK1AmSf.cpp, then inherited by the frozen complete preset. The following rows are retained, not newly proposed. “Global” means independent of the true-G interval on the fixed physical input; cutoffs still have their own scope. “Local” means its stated interval/inventory/cutoff domain.

First compute inventory domains by intersecting \([0,C_i]\) with physical reachability. Set

\[
M_{ki}=\begin{cases}
\max(0,\min(Q_k,\lfloor(T-\tau_{0i}-\tau_{i0})/h\rfloor)),&T\ge\tau_{0i}+\tau_{i0},\ h>0,\\
Q_k,&h=0,\ T\ge\tau_{0i}+\tau_{i0},\\
0,&\text{otherwise}.
\end{cases}
\]

The largest feasible pickup/drop at a singly served station is bounded by \(\max_k\min(b_i,M_{ki})\) and \(\max_k\min(C_i-b_i,M_{ki})\), respectively. These give \(\underline y_i\ge b_i-\max_k\min(b_i,M_{ki})\), \(\bar y_i\le b_i+\max_k\min(C_i-b_i,M_{ki})\).

For a finite current cutoff \(c\), lower Gini endpoint \(\alpha\), positive \(\lambda,\omega_i\), define \(B_P=(c-\alpha)/\lambda\). A physical improving point has \(|Y_i/D_i-1|\le B_P/\omega_i\), giving the additional integer bounds \(D_i(1-B_P/\omega_i)\le Y_i\le D_i(1+B_P/\omega_i)\). The writer uses outward integer rounding with \(10^{-9}\) guards and skips weights at or below its \(10^{-12}\) test. Negative/empty domains invoke the saved infeasibility path rather than manufacturing states. Canonical propagation uses the original two passes; no stronger fixed-point algorithm is substituted.

For the resulting domains let \(\underline r_i=\underline y_i/D_i,\ \bar r_i=\bar y_i/D_i\), \(\underline S=\sum_i\underline r_i,\ \bar S=\sum_i\bar r_i\),
\(\underline e_i=\min_{r\in[\underline r_i,\bar r_i]}|r-1|\),
\(\bar e_i=\max(|\underline r_i-1|,|\bar r_i-1|)\),
\(\underline P=\sum_i\omega_i\underline e_i,\ \bar P=\sum_i\omega_i\bar e_i\).
These are physical-extension bounds. In particular, the SP envelopes may remove nonminimal epigraph completions; they preserve \(e_i=|r_i-1|\). This does not silently replace all native \(e_i\) bounds by new bounds.

| Family and indices | Actual mathematical row/bound | Scope and validity |
|---|---|---|
| Inventory conservation, fleet | \(\sum_i b_i-\sum_kQ_k\le\sum_iY_i\le\sum_i b_i\) | Global; each return load is in \([0,Q_k]\). |
| Movement reachability, \(i,k\) | Domain construction above; \(z_{ki}=0\) if \(\tau_{0i}+\tau_{i0}+h>T\) | Global physical part; any nonzero visit requires at least one unit of pickup somewhere and its handling. |
| Visit/inventory, \(i\) | \(-b_i\sum_kz_{ki}\le Y_i-b_i\le(C_i-b_i)\sum_kz_{ki}\) | Global, follows from unique service and inventory balance. |
| Global handling, fleet | \(h\sum_{ki}p_{ki}\le mT\) | Global, sum of route-time constraints after dropping nonnegative travel. |
| Transfer compatibility, \(k,j\) | \(d_{kj}\le\sum_{i\ne j:\ \tau_{0i}+\tau_{ij}+\tau_{j0}+h\le T}p_{ki}\) | Global; every delivered unit has a prior pickup on that vehicle; metric shortcut gives the necessary ordered tour. |
| Support duration, \(k,W,\ \lvert W\rvert=2,3\) | If \(\tau(W)+h\lceil\lvert W\rvert/2\rceil>T\), \(\sum_{i\in W}z_{ki}\le\lvert W\rvert-1\); otherwise \(h\sum_{i\in W}p_{ki}+B_{kW}\sum_{i\in W}z_{ki}\le T-\tau(W)+B_{kW}\lvert W\rvert\) | Global; \(\tau(W)\) is the shortest depot cycle through the pair/triple; \(B_{kW}=T+\tau(W)+h\max(1,\sum_{i\in W}\bar p_{ki})\) safely deactivates the conditional row. |
| Direct Gini cap/floor, interval | \(n\alpha S\le H_\Sigma\le n\beta S\) | Local; the physical extension has \(H_\Sigma=A=nG_{\rm true}S\). |
| Pairwise spread, \(i<j\) | \((n-1)H_{ij}\le n\beta S\) | Local; \(A\ge(n-1)\lvert r_i-r_j\rvert\) by summing triangle inequalities through other stations. |
| Fixed and variable centering, \(i<j\), both signs | \(\pm(r_i-r_j)\le n\beta\bar S/(n-1)\), \((n-1)\,\pm(r_i-r_j)\le n\beta S\) | Local, same triangle bound; shared factory uses projected pairs, not a newly chosen center variable. |
| Required movement, \(i\) | \(\sum_k(d_{ki}-p_{ki})\ge\underline y_i-b_i\) if positive; reverse sign and \(b_i-\bar y_i\) for required pickup | Local where tightened inventory bounds are local; necessary balance consequences. |
| Verified incumbent row | \(g+\lambda P\le c\), actual \(c=U_{\rm epoch}-\epsilon_{\rm writer}\) | Factory registers “Global”, meaning whole current cutoff model; it is not valid for all physical objectives above c. Actual epsilon/cutoff remains call-bound. |
| Objective lower estimator | \(H_\Sigma+n\bar S\lambda P\le n\bar S c\) | Local cutoff; \(A/(n\bar S)\le G_{\rm true}\), including the zero-sum convention by direct extension. |
| Penalty lower bound/closure | \(P\ge\underline P\); implemented numerical impossible row if \(\alpha+\lambda\underline P\ge c-10^{-9}\) | Local; floor is exact in ideal arithmetic, while the impossible-row guard has the numerical qualification in A.7. |
| SP product estimator | Four envelopes below and \(H_\Sigma+n\lambda W_{SP}-ncS\le0\) | Local cutoff; take the physical extension \(W_{SP}=SP\). |
| Interval/inventory/deviation bounds | \(g\in[\alpha,\beta]\), valid \(Y\) domains; \(e_i\le\max(0,B_P/\omega_i)\) when activated | Local where based on cutoff/Gini; global reachability intersections remain global facts. |

Support enumeration loops vehicles, increasing station pairs, then triples. It considers at most 50000 subsets in that deterministic order, shared across the vehicle loop; the maximum size is 3. \(\tau(W)\) uses the explicit pair/triple cycle formula, not an added optimization solve in this manuscript task. Enumeration truncates strengthening only; it never truncates original feasibility or proof coverage.

For \(S\in[\underline S,\bar S]\) and physical \(P\in[\underline P,\bar P]\), the SP rows are

\[
\begin{aligned}
W_{SP}&\ge\underline S P+\underline P S-\underline S\underline P,\\
W_{SP}&\ge\bar S P+\bar P S-\bar S\bar P,\\
W_{SP}&\le\bar S P+\underline P S-\bar S\underline P,\\
W_{SP}&\le\underline S P+\bar P S-\underline S\bar P.
\end{aligned}\tag{A17}
\]

These standard McCormick envelopes [@mccormick1976] follow by expanding the four nonnegative rectangle products. They are relaxations for continuous \(SP\), unlike the exact integer-selected \(gY_i\) block. The product estimator follows from \(F\le c\) after multiplying by \(nS\); the original objective row remains, especially at \(S=0\).

If an interval bit model is used, the factory's ordinary binary-product envelopes are \( \alpha b\le w\le\beta b,\ g-\beta(1-b)\le w\le g-\alpha(1-b)\). They are skipped in the active VD-P writer. Diagnostic S buckets, GS products, receiver/source covers, subset Gini envelopes, local-Q cuts, user/lazy cuts and custom branching priorities are not silently included. Equal-capacity symmetry may order vehicles by nonincreasing visit count \(\sum_i z_{ki}\ge\sum_i z_{k+1,i}\); heterogeneous capacities do not receive that order. Permuting identical vehicles preserves an original solution. It is not an instance-dependent algorithm selector.

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

Lemmas A1–A4 concern ideal exact arithmetic and valid mathematical domains. Stored matrices use binary64 arithmetic and Gurobi 13.0.2. Native FeasibilityTol and OptimalityTol are \(10^{-6}\), IntFeasTol \(10^{-5}\), requested MIPGap/MIPGapAbs zero; retained evidence closure uses \(10^{-7}\). A qualified result is a numerical certificate under this policy, not a rational exact proof.

In particular, the implemented guard \(\alpha+\lambda\underline P\ge c-10^{-9}\) can serialize \(0\le-1\) while a mathematical point satisfies \(c-10^{-9}\le F<c\). Therefore it is numerical closure, not strict infeasibility of every arbitrarily small improver. Its local cutoff discrepancy does not supply a bound on accumulation of all native arithmetic errors; \(10^{-9}<10^{-7}\) alone proves no such global guarantee. This manuscript changes neither guard nor tolerance. No new contradiction with the stated numerical evidence policy was found; claims of error-free rational certification are excluded.

Every numerical original-problem certificate additionally requires a physically verified own U, qualified complete source/return chains and cover, normal lifecycle completion, and the inherited signed-gap test. Tiny signed gaps are reported unchanged. A same-domain counterexample revokes its source and dependent pruning; an independent fleet can remain valid, but floor zero or a good U cannot repair invalid proof dependencies. Source-reduced results are separately labelled and get no dependent nonzero certificate credit.

The single total process deadline guarantees finite execution of this implementation, not certification within every finite window. The finite physical space and ideal complete search do not imply a linear forecast from the remaining gap.

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

The source is public at the fixed [implementation snapshot](https://github.com/yifanXovo/TailoredExact/tree/355eefd2be3fe5651195681faf7b3a63ee4032f8). The finite production_identity authority records all 216 bindings. Line locations aid review; they do not replace derivations. This appendix supplies constraint groups and validity premises without claiming every engineering identifier as a mathematical contribution.
