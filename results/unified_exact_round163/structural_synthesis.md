# Structural evidence for the stage choice

This synthesis uses the maintained R137 physical model and numerical policy.
It is an explanation of existing results and the R163 confirmation, not a new
general hull theorem or a claim that all future structural strengthening fails.
The exact fixed-commit/member/SHA identities are in `historical_source_map.json`.

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

## 1. Physical and objective correspondence

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

## 2. Comparable domains and incomparable expressions

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

The existing R133 four-station example is enough to distinguish the objects.
Its full service hull has LP value `lambda_hat`; its original integer optimum
is `1/4+lambda_hat` at the actually loaded coefficient. The exact gap is `1/4`
on the fixed positive total `sum Y=3`. At the loaded coefficient R133 also
minimizes over all legal loaded-return totals to prove the same global integer
value; the physical problem is not restricted to this slice. A variable denominator is unnecessary
for that example, and the proof is not a global Jensen claim for ratio-Gini.
It is inherited evidence, not a newly manufactured counterexample.

## 3. Coverage, qualification and finite return

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

If a source is rejected, dependent closures are revoked and the unresolved
physical domain is restored with the independent nonnegative bound and its
own verified U. An exact zero physical fleet can independently certify; a
small positive floating objective cannot. Positive Native/outer certificates
retain the actual floating-point source and numerical qualification contract;
they are not all exact rational certificates.

The controller's fixed depth/width limits bound its refinement structure.
Finite actions and the global deadline give a finite implementation return,
possibly OPEN. Successful exact terminal solves of a bounded finite integer
domain, together with complete coverage, give the corresponding ideal
finite-proof conclusion. Depth/width limits alone neither prove all terminal
sources nor guarantee a certificate before a wall-clock cap.

## 4. What a small inventory gap can explain

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

## 5. Five evidence levels

1. Separation of an old point shows missing information at that point.
2. Free matched LP reoptimization tests objective-value information.
3. A paid Native call tests that information against its solve/construction cost.
4. A complete own-H method tests U, proof L, certification and all paid work.
5. Frozen new configurations test the selected complete method beyond its development inputs.

R138–162 reach different levels, with positive and negative results retained.
R163 supplies the fifth level for frozen E+ against B and cold P, on six new
configurations from already archived sources. All six become exposed after
this study. They are neither new cities nor independent observed demand.
