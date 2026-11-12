# GI-TBC: mathematical objects and mechanism interpretation

This maintained companion explains the physical, inventory, relaxation and complete-method objects used in the current paper. It preserves the earlier exact arguments and integrates the archived-source three-Seed evidence. Production source/PE identities and document-build identities are separate in the [source manifest](../unified_exact_round165/source_manifest.json).

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


## Structural evidence for the stage choice

This synthesis uses the maintained R137 physical model and numerical policy.
It is an explanation of existing results and the R163 confirmation, not a new
general hull theorem or a claim that all future structural strengthening fails.
The exact fixed-commit/member/SHA identities are in [the inherited source map](../unified_exact_round164/historical_source_map.json).

| Existing conclusion | Evidence identity | R163 increment | What does not follow |
|---|---|---|---|
| Empty departure, unique nonzero one-way service, prefix loads, loaded return and unloading have an objective-preserving integer-model correspondence. Integer inventory plus unique assignment/direction implies service integrality. | R137 paper §3.1 and model/algorithm appendices A.1–A.7; R100 lineage retained there | Check the same contracts in all new complete arms; integrate their role in the paper | The A/B shared-state links are not extra premises of implicit integrality, nor a full vehicle-route hull |
| Local inventory/count/product information can be strict while complete outcomes are mixed. STOCK retains important K20 certificate gains; RN and joint projection retain useful selected LP/physical results. | R138 final report; R140 final decision; R143 mathematical analysis; R145 final report | Keep the positive structural and certificate evidence while testing only the already frozen E+ | A separated old optimum proves neither an increase after free reoptimization nor a complete-method advantage |
| Standalone GD has selected hard-role U gains and explicit L/time tradeoffs; further known-role confirmation and propagation do not support a broad replacement claim. | R147, R150 and R151 final reports | Preserve both directions in the algorithm-selection discussion | A relative-gap gain does not erase a worse U or L; the selected R147 result is not unseen-data confirmation |
| Full integer inventory objective information differs from marginal penalty and service convexification. Free inventory-hull value gains and finite pricing plateaus are real. | R133 fixed-positive-total objective-gap note; R152 offline final report; R154 mathematical analysis/final report; R155 final report | State the hierarchy of objects and avoid reopening the same plateau | Even complete service compatibility does not convexify the integer objective epigraph; a restricted stock pool is not a full-hull value upper |
| R154 proof-only E can raise qualified proof L while leaving formal Native and raw AM inputs as designed. Uniform RN16384 E+ improves the exposed RX35 proof L relative to E by .013789522987126268. | R154 complete placement panel; R156 final report and complete-arm table | Six prospective archived-source configurations, three methods, all paid costs; E+ is the sole enhancement candidate | Identical formal inputs do not guarantee identical finite-time trajectories or U; small remaining inventory precision does not identify the whole physical gap |
| Inventory levels and necessary integer resources need not have physical realizations. Several family exclusions and new resource uppers are finite, scoped results; physical neighborhood gains did not survive the complete method. | R157–159 final reports; R160 final report | Use them to delimit the next question, with no new resource or neighborhood candidate | Excluding a finite near-optimal family is not a global physical lower bound; UNKNOWN is not infeasibility |
| RN replacement on the full physical carrier preserves integer objectives but changes the continuous objective module. Neither tested RN variant beats its OLD control in the prescribed finite study. | R161 formulation and final report | Close the current replacement chain in the stage account | Integer equivalence is not a continuous-relaxation ordering or runtime theorem |
| NB35 full-Q adds .000187249791616 beyond STOCK and the finite projection retains about 87%; RX35 freely remixes to the same qualified value. PC loses U against both controls on both complete primary roles, with equal proof L and no certificate. | R162 fixed science `fb087d7d9a3eef5bbff250487639d89b6e794739`; LP/projection reports and six complete arms | Reuse the closed result without rerunning old producers; distinguish it from the new 18-arm confirmation | The 5348-term row is not sparse because it is one row. The duration ablation proves necessity conditional on the rest of Q, not time-alone sufficiency. A small continuous-Q increment is not an upper bound on the integer physical gap |

### 1. Physical and objective correspondence

For a fleet with integer stock, let `p_ki,d_ki` be its nonnegative service
quantities. Unique assignment and binary direction set one of them to zero.
Inventory balance then fixes the other to `|b_i-Y_i|`, an integer. The shared
M-B/VD-P movement and visit equations strengthen the fractional representation;
they are not needed for that integer implication. Empty departure gives
nonnegative prefix load and return `R_k=P_k-D_k` in `[0,Q_k]`. Conservation is

\[
 \sum_iY_i=B-\sum_kR_k,\qquad
 \max(0,B-\sum_kQ_k)\le\sum_iY_i\le B.
\]

Handling including final unloading is
`tp*P_k + td*(D_k+R_k)=(tp+td)*P_k`. Prefix capacity does not bound cumulative
pickups by `Q_k`. Depot stock is outside both objective terms. R137 Appendix A
supplies the two objective-preserving maps, connectivity, ordered supply and
support assumptions. They continue to govern each R163 physical U.

The model variable `g` is an epigraph of true ratio-Gini, not an assertion
`g=G_true` at every feasible completion. For `S=sum_i Y_i/D_i>0`, it satisfies
`g>=G_true`; for `S=0` the convention is `G_true=0`. A tight extension recovers
the original physical objective. A nonminimal feasible epigraph must not be
silently replaced by the true-Gini graph when proving a model extension.

### 2. Comparable domains and incomparable expressions

Fix one input, objective coefficients, original physical horizon, supported
inventories, epigraph interval and cutoff. Write

\[
 \phi_I(Y)=\max\{\gamma_L,G_{\rm true}(Y)\}
       +\lambda\sum_i\omega_i|Y_i/D_i-1|,
 \qquad G_{\rm true}(Y)\le\gamma_U.
\]

This is the actual inventory-helper objective and domain. In particular it
does **not** require `G_true>=gamma_L`. The legal `S=0` stock is evaluated with
`G_true=0` and objective `gamma_L+penalty`. A zero floor is information and cost,
not a reason to change the input or candidate. A missing/unqualified source
retains the independent B proof information under the frozen fallback.

Let `X_P^epi` be the full physical epigraph domain, including the common
interval and cutoff. Let `Y_I` be the inventory necessary domain above,
including supported stocks and valid total bounds. If an integer resource
domain `Y_R` has a proved embedding of every full physical fleet and retains
these same premises, then

\[
 \pi_Y(X_P^{\rm epi})\subseteq Y_R\subseteq Y_I,
 \qquad \min_{Y_I}\phi_I\le\min_{Y_R}\phi_I\le
             \min_{X_P^{\rm epi}}J.
\]

These arrows express the stated embedding premises. They do not identify
every historical resource model with `Y_R`, or transfer numerical optima
between different cutoffs, intervals, old auxiliaries or coefficients.

For R162's exactly matched OLD/OLD+STOCK/full-Q extension, the proved lifting
and projection support continuous containment in that fixed old space.
The RN **addition** in R143 and the RN **replacement** in R161 are distinct
objects. R161 removes the registered old objective-consumer closure; integer
equivalence alone supplies no inclusion arrow between its continuous
relaxation and OLD. Values from unrelated old LPs cannot order these domains.
An objective-value interval is likewise not a polyhedral inclusion.

The existing [four-station derivation](https://github.com/yifanXovo/TailoredExact/blob/de01e8fb27a954d031abac5fe99442d6c8d29d44/results/unified_exact_round133/joint_objective_gap_note.md) distinguishes the objects. It has initial stock (2,1,0,0), equal targets/weights 1, capacities 2, vehicle capacities (1,2), coincident points and 60-second pickup/drop. Its 240/360-second horizons define two complete tiny domains. Here `lambda_hat=5404319552844595/36028797018963968` is the exactly loaded binary64 coefficient near .15, without division of the penalty by four.
Its full service hull has LP value `lambda_hat`; its original integer optimum
is `1/4+lambda_hat` at the actually loaded coefficient. The exact gap is `1/4`
on the fixed positive total `sum Y=3`. At the loaded coefficient R133 also
minimizes over all legal loaded-return totals to prove the same global integer
value; the physical problem is not restricted to this slice. A variable denominator is unnecessary
for that example, and the proof is not a global Jensen claim for ratio-Gini.
It is inherited evidence, not a newly manufactured counterexample.

### 3. Coverage, qualification and finite return

For one region, a qualified lower `ell` on its cutoff-restricted domain
`J<=c` combines with the excluded complement to give `min(ell,c)`. Bounds on
the **same** domain combine by maximum. Bounds on a covering **union** combine
by minimum, with complete coverage and every scope/cutoff premise checked.
An infeasible restricted source closes its region only through its qualified
domain and cutoff complement. A child must be contained in the source's
interval, support and cutoff scope. R133's inclusive-cutoff repair and R134's
independent exact-zero rule remain separate proof policies.

Proof-only placement takes the maximum of applicable root-floor information
and a leaf's qualified raw search information before the covering minimum.
It installs no total-objective Native row, raw AM bound, hint, Start or new
branching rule. It still pays to obtain the root model, DP/RN result and
qualification, inside that arm's one total deadline. Paid helper time,
remaining Native time and legitimate earlier certification can alter finite
trajectories and physical U even when the intended formal expressions agree.

If a native source is rejected, actual final qualification discards its dependent proof conclusions and conservatively restores the unresolved physical domain with the independent nonnegative bound and its own verified U. This is the implemented global fallback, not a generic online revocation/resumption mechanism; the frozen scheduler itself accumulates same-unit bounds monotonically. An exact zero physical fleet can independently certify; a
small positive floating objective cannot. Positive Native/outer certificates
retain the actual floating-point source and numerical qualification contract;
they are not all exact rational certificates.

The controller's fixed depth/width limits bound its refinement structure.
Finite actions and the global deadline give a finite implementation return,
possibly OPEN. Successful exact terminal solves of a bounded finite integer
domain, together with complete coverage, give the corresponding ideal
finite-proof conclusion. Depth/width limits alone neither prove all terminal
sources nor guarantee a certificate before a wall-clock cap.

### 4. What a small inventory gap can explain

For a common **global** objective and scope, suppose

\[
 L_I\le f_I^*\le U_I,\qquad f_I^*\le f_P^*\le U_P.
\]

Then the standard identity is

\[
 U_P-L_I=(U_P-f_P^*)+(f_P^*-f_I^*)+(f_I^*-L_I).
\]

Only the last term is bounded by `U_I-L_I`. The first is incumbent
suboptimality and the second is the relaxation-to-physics difference.
R156's small same-inventory-scope remainder limits further precision gains
from the same scalar floor on that scope; it does not allocate the entire
remaining complete gap to physical coupling. Its local cutoff/interval
source must first pass the coverage contract before any global use.
R162's small continuous-Q value gain is not an upper bound on the integer
physical gap. This identity organizes the evidence; it is not a new theorem.

### 5. Five evidence levels

1. Separation of an old point shows missing information at that point.
2. Free matched LP reoptimization tests objective-value information.
3. A paid Native call tests that information against its solve/construction cost.
4. A complete own-H method tests U, proof L, certification and all paid work.
5. Frozen new configurations test the selected complete method beyond its development inputs.

R138–162 reach different levels, with positive and negative results retained.
R163 supplies the fifth level for frozen E+ against B and cold P, on six new
configurations from already archived sources. All six become exposed after
this study. They are neither new cities nor independent observed demand.

## Within-input solver-Seed evidence

The later Seed confirmation repeats frozen B and cold P on those six exposed
mathematical inputs. Gurobi Seeds1/2 are additional observations; the qualified
R163 Seed0 runs retain their historical measured identities. The H seed stays
20260626, and every B run recomputes and pays its own complete startup. A
common Gurobi Seed label does not couple two different models to an identical
random trajectory.

For configuration \(i\) and Seed \(s\), report

\[
 \Delta U_{i,s}=U_{B,i,s}-U_{P,i,s},\qquad
 \Delta L_{i,s}=L_{B,i,s}-L_{P,i,s}.
\]

Negative \(\Delta U\) and positive \(\Delta L\) favor B on different
endpoints. The existing numerical qualification scale applies; retaining a
signed gap does not remove the obligation to report both directions. Each
U still requires that run's complete physical fleet, and each L or certificate
requires that run's applicable original-problem source/coverage. No cross-Seed
minimum U and maximum L are assembled into a new run or certificate.

Medians and ranges of the three paired differences describe within-input
observations. They are neither additional endpoint observations nor a sample
of eighteen independent new inputs. No general success probability,
significance statement or best-Seed method follows. Certificate-time
differences remain restricted to the explicitly counted same-input,
same-Seed joint-CERT intersection; OPEN budget use is not a certificate time.
E+ has no new Seed runs in this confirmation, so its earlier gains retain
their measured scope rather than inheriting B/P robustness.

The preregistered offline primal target is
\(u_{\rm ref}(i)=\min\{U_{B,i,0},U_{P,i,0}\}\), using the two original
qualified physical upper endpoints. It is a known feasible target and need
not be optimal. It enters no model, Start, cutoff or stopping rule. Saved
journal fleets can show target attainment only at their trustworthy saved
availability clocks; the original wrapper overhead gives conservative paid
clock bounds when it is not isolated. A final witness without a saved first
event supplies only an upper bound. No observed attainment within the window
is right-censored evidence, not a proof of unattainability, and later
verification cannot be used as the production discovery clock.

Saved C35 fleets distinguish witnessed incumbent suboptimality from the
unresolved global proof gap. Assignment, relative order and service amounts
can all differ at once. A fixed unserved-station penalty is only a necessary
objective term, and a target inventory point must still satisfy the original
route time, empty departure, every prefix capacity and loaded-return rules.
Neither observation supplies a restricted-domain optimum, single-operator
causality or a complete-method feedback benefit. These are evidence and
interpretation conventions; no additional general theorem or optimizer is
introduced.

## Completed finite-Seed interpretation

The completed six-input readback gives eighteen within-input B/P pairs,
including six historical Seed0 pairs. C35 has ΔU signs +/−/− and ΔL signs
+/+/+; its median ΔU is descriptive and cannot erase the adverse Seed0
fleet. B35/X35 have ΔU<0 and ΔL>0 in all three observations but no own
certificate. B20's differences within the frozen 1e-7 scale are equivalent
endpoints, with three independently paid joint-CERT comparisons.

These are numerical observations under the original source, exact-zero and
inclusive-cutoff qualification; they change no physical equivalence,
epigraph/S=0 convention or coverage theorem. The complete own-run values
and all target-availability intervals are in the
[finite evidence tables](../unified_exact_round164/reports/seed_evidence.md).
