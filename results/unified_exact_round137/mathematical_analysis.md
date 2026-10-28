# GI-TBC: stage definitions and mechanism interpretation

This is a consolidation of the accepted method and the precise Round137
comparisons. It introduces no TC/AP, joint-support or route-oracle candidate.
The production source, PE and complete argv identities are frozen separately.

## Physical model and effective objective weight

Vehicles depart empty and may return loaded. At most one vehicle performs a
nonzero, one-way operation at a station. Inventory and route-prefix capacity
remain integer physical quantities; the depot is excluded from the objective.
With final station inventory and return load,

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad
R_k=\sum_i(p_{ki}-d_{ki})\in[0,Q_k],\quad
\sum_iY_i=\sum_ib_i-\sum_kR_k.
\]

Return unloading gives total handling time
\((t_p+t_d)\sum_i p_{ki}\) for vehicle \(k\). Prefix capacity does not imply
a cumulative-pickup bound of \(Q_k\).

Put \(r_i=Y_i/D_i\), \(S=\sum_i r_i\),
\(A=\sum_{i<j}|r_i-r_j|\), \(P=\sum_i\omega_i|r_i-1|\).
For \(S>0\), \(G=A/(nS)\); at \(S=0\), \(G=0\).
For \(\Omega=\sum_i\omega_i>0\),

\[
P_{\rm avg}=P/\Omega,\qquad \rho=\lambda\Omega,\qquad
F=G+\lambda P=G+\rho P_{\rm avg}.
\]

B1 fixes \(\lambda=.15\). B2 fixes \(\rho=1\). B3 changes only
\(\rho\in\{.5,1,2\}\) within two prospectively fixed physical configurations.
Fixed effective weight controls total penalty scale; it does not remove
relative-weight, geographic, fleet or inventory differences between inputs.

For serialized shortage \(s=\sum_iD_i-\sum_ib_i>0\), all weights
positive, and \(\lambda>0\) (equivalently \(\rho>0\)), let
\(a=\min_i\omega_i/D_i>0\). Then

\[
P\ge a\sum_i|D_i-Y_i|
\ge a\left|\sum_iD_i-\sum_iY_i\right|\ge as,
\qquad F\ge\lambda as=\rho as/\Omega>0.
\]

The last inequality uses nonnegative return load. It applies equally to P,
PS and GI-TBC, and to every physical \(T\). It is the established shortage
construction, not a new theoretical contribution or a guarantee of difficulty.
The actual serialized arrays, rather than an intended regime label, establish
the eight B2 floors. B3 floors scale with the actual \(\rho\).

For fixed remaining physical data and \(T_1\le T_2\), every route feasible
under \(T_1\) is feasible under \(T_2\); hence
\(X(T_1)\subseteq X(T_2)\) and
\(F^*(T_2)\le F^*(T_1)\). This says nothing about search-time monotonicity
or about finite-budget feasible upper and qualified lower endpoints.

## Shared states and A/B deletion

GI-TBC retains the accepted finite inventory-state products, M-B service
representation, VD-P, pair-only support, complete own H and interval controller.
The A/B equations link the same inventory mixture to total movement and visits:

\[
\sum_k(p_{ki}+d_{ki})=\sum_y|b_i-y|s_{iy},\qquad
\sum_k z_{ki}+s_{i,b_i}=1,
\]

where an unavailable state contributes zero. Deleting exactly these two
equations per station leaves integer \(b_i,Y_i\), unique assignment, binary
direction, nonnegative quantities and the original nonzero-service and balance
constraints. At its sole service vehicle, pickup direction gives
\(p=b_i-Y_i\in\mathbb Z,d=0\); delivery gives
\(d=Y_i-b_i\in\mathbb Z,p=0\). Thus implicit quantity integrality does
not rely on A/B, and deletion does not require retyping pickup/delivery.
The existing R100 proof and original inventory-domain boundary treatment apply.

## Four conditional comparisons

| Comparison | Mathematical/process change | What its complete cost can support | Boundary |
|---|---|---|---|
| GI-TBC-R | Accepted post-R130 inclusive full strengthened root (`s2-root`), complete own H; remove outer probe/target/split scheduling | Conditional contribution of the outer control package | Not the old unqualified R127 MD; not a separate physical model |
| GI-TBC minus A/B | Delete only the two shared movement/visit equations per station | Value/cost of linking inventory mixtures to service in the remaining formulation | Quantity integrality and physical service remain |
| GI-TBC minus C_R | Omit ordered supply compatibility and pair-support cover/conditional handling group | Resource-group relaxation effect and complete-search cost | Keep pair-only; do not select old MR and restore triples |
| GI-TBC minus C_G | Omit existing spread/centering/objective-estimator rows and their dedicated W_SP/r_min/r_max helpers | Geometry/objective-group effect conditional on the remaining formulation | Retain original inventory/S/P domains, core state products and physical rows; no global Cuts=0 |

For the same initial domain, objective and cutoff, deleting valid inequalities
can only decrease or preserve the ideal relaxation lower bound. Dedicated
auxiliaries may be reoptimized; they are not fixed to the full model's solution.
This feasible-set statement neither orders native runtime/Work/nodes nor orders
the final endpoints of independently evolving finite-budget searches.
The four contrasts estimate conditional contributions; they do not yield
additive percentages of total speed-up. A component may cost time, replace
information supplied elsewhere or be unexposed on a finite role.

The finite zero-Optimize K15 export check established exact default-off equality
to accepted R135 and duplicate-preserving row deletion: 30 A/B rows, 240 C_R rows,
and 531 C_G rows plus its three dedicated auxiliaries. All shared variable
bounds/types and objective were identical. These are one-fixture structural
checks; complete per-call audits and physical mappings remain required.

## AM rule and experimental interpretation

For finite valid child LP evidence, the actual controller uses

\[
\begin{aligned}
\Delta&=\max\{U-b,\max(\epsilon,10^{-12})\},\\
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
The prior R47/R52 decision supports the default .08; the bounded current study
compares .04/.08/.16 without per-instance selection.

The new explicit research CLI sets the first-class `split_threshold` after
presets. The historical `round47_c6_adaptive_mass_tau` field is not substituted
for that control. Actual readback is checked before evidence qualification.
Offline replay can describe different actions at observed states, but cannot
reuse the original post-divergence trajectory as a runtime counterfactual.
The score estimates gap-normalized two-sided bound improvement, not remaining
complete proof cost.

## Scope of prior evidence

R132 already provides twelve new inputs, cross-source evidence, formulation
strictness and projection analysis. R133 gives a fixed-denominator
original-objective gap; variable denominator alone cannot explain all failures.
R134 TC and R135 AP supply completed mathematical and mixed/negative runtime
evidence. The AP aggregate can strengthen a root while producing a weaker final
dual endpoint in complete search; it remains off. These studies keep their
actual source versions and denominators. Round137 does not relabel their runs
as current measurements or present their questions as previously unstudied.

Main Seed0 results, preselected Seed1 checks and any later diagnostic repeats
have distinct denominators. Matching baselines are shared only with the same
input, physical T, weight, Seed, cap and actual algorithm configuration. Two
Seeds are finite checks, not an estimated runtime distribution. Open runs keep
null certificate times; the cap is not an observed solve time. Both-certified
time comparisons use the declared max(10s,10% of the faster time) rule alongside
the actual values, with the intersection denominator stated explicitly.
