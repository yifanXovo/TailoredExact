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

The last row uses the same budget activation tests as A19. The floor follows station by station from the distance to 1 in (A21); the original e upper bound is retained and the budget row intersects it. \(\alpha+\lambda\underline P>c\) proves ideal cutoff infeasibility. The implementation instead tests \(\alpha+\lambda\underline P\ge c-10^{-9}\), writes an impossible row, and uses its numerical closure policy. In particular equality to c is not strict infeasibility of the non-strict cutoff set. A.7 explicitly limits this claim. The factory's “Global” metadata on the incumbent row means the entire current model, not all physical objectives at every cutoff.

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

Lemmas A1–A4 concern ideal exact arithmetic and valid mathematical domains. Stored matrices use binary64 arithmetic and Gurobi 13.0.2. Native FeasibilityTol and OptimalityTol are \(10^{-6}\), IntFeasTol \(10^{-5}\), requested MIPGap/MIPGapAbs zero; retained evidence closure uses \(10^{-7}\). A qualified result is a numerical certificate under this policy, not a rational exact proof.

In particular, the implemented guard \(\alpha+\lambda\underline P\ge c-10^{-9}\) can serialize \(0\le-1\) while a mathematical point satisfies \(c-10^{-9}\le F<c\). Therefore it is numerical closure, not strict infeasibility of every arbitrarily small improver. Its local cutoff discrepancy does not supply a bound on accumulation of all native arithmetic errors; \(10^{-9}<10^{-7}\) alone proves no such global guarantee. This manuscript changes neither guard nor tolerance. No new contradiction with the stated numerical evidence policy was found; claims of error-free rational certification are excluded.

Every numerical original-problem certificate additionally requires a physically verified own U, qualified complete source/return chains and cover, normal lifecycle completion, and the post-seal signed-gap test −1e−7≤U−L≤1e−7. Appendix B.4.1 fully distinguishes that policy, the one-sided native function and the own-zero/source-reduced branches. Tiny signed gaps are reported unchanged. A same-domain counterexample revokes its source and dependent pruning; an independent fleet can remain valid, but floor zero or a good U cannot repair invalid proof dependencies. Source-reduced results are separately labelled and get no dependent nonzero certificate credit.

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
