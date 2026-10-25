# Vehicle labels, integer inventory and the tiny joint-objective gap

The finite Round132 service-coordinate separation remains valid. Its J2 witness
also has a simpler explanation: a conflict between **specified vehicles** competing
for the same donors. Adding the complete service joint hull still leaves the
current continuous objective at the displayed value 0.15. The integer original
optimum is displayed as 0.40. The gap is exactly 1/4 under the actual loaded
binary64 coefficient, by the primal and analytic proofs below. These statements
are about the two complete tiny universes, not a new full-size separator.

## Fixed evidence and arithmetic

The sole computational dependency is the 213,859-byte
[Round132 tiny carrier](https://github.com/yifanXovo/TailoredExact/blob/52b02252ba47e8228b73e071d6ed692385a4f816/results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip),
SHA256 `d2e55d7ae5fcaf5bb0c9d39a489b589006f3a29eb350b167fd790ad399a0aac1`.
`scripts/round133_joint_check.py` reads only the named J2/J3 members and uses the
Python standard library, with no solver import, Optimize, compilation, extra
directions or native sensitivity run. `math/exact_joint_receipt.json` binds the
carrier, every consumed member and the checker. The original carrier is unchanged.

J2 has four service stations, initial stocks b=(2,1,0,0), target D_i=1, capacities
C_i=2, weights omega_i=1 and vehicle capacities Q=(1,2). All points coincide.
Pickups and drops each cost 60 seconds. Empty departure and legal loaded return
give handling 120 times total pickups; the time horizon is 240 seconds per vehicle.
J3 differs only in its 360-second horizon. Inventory is integer in the original
problem, with values 0,1,2 and no positive minimum-ratio constraint. Every variable
type is explicitly relaxed for the LP comparison. Depot stock and deviation do
not enter the objective.

The retained objective is g+lambda_hat sum_i e_i, with

\[
\widehat\lambda=\frac{5404319552844595}{36028797018963968}.
\]

There is no division of the penalty by four. At a tight physical completion this
is G_true+lambda_hat sum_i |Y_i-1|. The ideal decimal coefficient 3/20 and the
exact rational value of the loaded binary64 coefficient are different objects.
The original native result was a numerical observation; the exact finite primal
and analytic lower-bound verification is new in this round.

## 1. A simple vehicle-labelled incompatibility

**Proposition 1.** In the complete J2 or J3 integer universe, with zero-based
vehicle and one-based station indices,

\[
d_{0,3}+d_{1,2}\le 1.
\]

Each term is an integer at most one: the first is limited by Q_0=1, and the
second by station 2's remaining capacity C_2-b_2=1. If vehicle 1 delivers to
station 2, it occupies that station. Empty departure requires it to pick up
from station 1, because only stations 1 and 2 initially contain bicycles and
one-way service rules out also picking up at station 2. Vehicle 1 therefore
occupies both possible donor stations. Unique nonzero service prevents vehicle
0 from picking up at either donor, so it cannot deliver to station 3. This proves
the inequality. It uses the **complete** four-station domain and cannot be moved
to a larger instance after deleting outside donors.

The checker independently enumerates every single-car service vector and tests
every ordering until it finds a prefix-feasible order. It recovers 11/23 plans
and all 59 disjoint J2 joint fleets, and 11/30 plans and all 66 J3 joint fleets.
The exact maximum of the simple left side is one in both universes. This is
complete for the service projection; it is not a list of every route permutation.
No cumulative-pickup-at-most-Q premise is used.

The original J2 strict reference witness has d_0,3=1 and d_1,2=1/2, hence simple
activity 3/2. Its individual car mixtures are mix0[3]=mix0[6]=1/2 and
mix1[0]=mix1[13]=1/2. The complete saved auxiliary extension passes all 558 rows
and 225 variable bounds of the **actual loaded** reference matrix, with zero
rational equality residual and no inequality or bound violation. The original
24-dimensional support evidence remains: exact activity 15/2 exceeds the exact
maximum 7 over all 59 fleets. The simpler inequality supplements that evidence.

The strict witness has inventory (1,1,1,0). Vehicle 0 can legally pick up one
bicycle at station 1 and deliver it to station 3, while vehicle 1 stays idle,
realizing exactly that inventory in 120 seconds. Consequently the saved point
proves a strict **service-coordinate** distinction, not a strict inventory
projection distinction. It supplies a vehicle-labelled compatibility condition
missing from this reference; it does not establish a new general quantity-hull
family. The 64 directions per case, 256 in total, are not a complete facet search.
The 32 event controls are checks of already known rows.

## 2. Exact LP value and what the joint hull convexifies

Every plan in a single-vehicle hull has return
R_k=sum_i(p_ki-d_ki)>=0. Convex combinations preserve this inequality. Summing
the inventory balance therefore gives sum_i Y_i<=sum_i b_i=3. The epigraph rows
give e_i>=1-Y_i and g>=0, so

\[
\sum_i e_i\ge4-\sum_iY_i\ge1,
\qquad f_{\rm model}\ge\widehat\lambda.
\]

The checker also identifies and exact-matches the actual loaded rows used by
this lower bound: the sum-Y upper bound, each r_i=Y_i equality, each e_i+r_i>=1
row, and the nonnegative lower bound on G. Thus this is an exact algebraic
lower bound on these serialized LPs, without promoting a numerical dual vector.

The saved complete joint LP points attain it: Y_i=r_i=3/4, e_i=1/4, g=0.
Checking **all** rows and bounds using exact rational arithmetic gives:

| Case | Complete joint rows | Variable bounds | Nonzero equality residuals | Violations | Exact objective |
|---|---:|---:|---:|---:|---|
| J2 | 583 | 284 | 0 | 0 | lambda_hat |
| J3 | 583 | 298 | 0 | 0 | lambda_hat |

Legal slack is allowed; not all inequalities have to be tight. This exact result
uses the rational interpretation of the actual loaded binary64 matrix. It does
not assert exact equality of separately rounded ideal matrices or verify an
unobserved MIP tree.

For J2 the saved joint column indices 22,33,38,49 each have weight 1/4. Their
inventories and original physical objectives are:

| Inventory | G_true | P_true | Original physical objective |
|---|---:|---:|---|
| (0,2,1,0) | 7/12 | 3 | 7/12+3 lambda_hat |
| (2,0,0,1) | 7/12 | 3 | 7/12+3 lambda_hat |
| (0,0,2,1) | 7/12 | 3 | 7/12+3 lambda_hat |
| (1,1,0,1) | 1/4 | 1 | 1/4+lambda_hat |

Their inventory average is (3/4,3/4,3/4,3/4). The first three columns are displayed
as about 1.0333333, not 0.40. In J3 the saved mixture uses inventories
(1,0,0,2), (1,0,2,0), (1,2,0,0), (0,0,2,1) with weights 1/4,1/8,3/8,1/4;
it has the same uniform inventory average and each column has G=7/12,P=3.
The carrier preserves the exact routes and service quantities of both mixtures.

Convexifying feasible service vectors preserves linear service compatibility.
It does not convexify the original integer **objective epigraph**. Recomputing
Gini and absolute deviation at an average inventory can cost less than averaging
the costs at the integer inventories. All these columns have the fixed positive
total inventory tau=3, so a changing denominator is not needed for this gap.
On this fixed-total slice the Gini denominator is constant; convexity of the
sum of absolute differences explains the direction of the decrease. No global
convexity or Jensen claim is made for variable-denominator Gini.

## 3. Integer inventory lower bound and original optimum

**Balancing lemma (standard discrete convexity).** Suppose D_i=D>0, Y_i are
nonnegative integers, and tau=sum_i Y_i>0. Let q=floor(tau/n) and m=tau-nq.
Then, on the larger inventory domain that ignores routing and capacities,

\[
A\ge\frac{m(n-m)}D,
\qquad G_{\rm true}\ge\frac{m(n-m)}{n\tau}.
\]

If the largest inventory a and smallest inventory b satisfy a-b>=2, replace
them by a-1,b+1. Their mutual absolute distance decreases by two. For every
third integer value t between the extrema, |a-t|+|b-t| does not increase under
this operation. This follows directly by considering t<=b, b<=t<=a and t>=a,
or by convexity of absolute value. Thus the pairwise numerator never increases.
The sum of squares strictly decreases, so repeated transfers terminate at a
balanced vector: n-m entries q and m entries q+1. Exactly m(n-m) pairs differ
by one. Dividing by D and by nS=n tau/D proves the claim. Capacities and routes
may prevent attainment but cannot invalidate a lower bound obtained on this
larger domain. This is a self-contained standard balancing proof, not a claimed
new majorization theorem.

If all weights equal omega>=0, the same transfer does not increase the symmetric
convex penalty, hence

\[
P_{\rm true}\ge\omega[(n-m)|q/D-1|+m|(q+1)/D-1|].
\]

For integer D the two adjacent balanced levels cannot strictly straddle D, so
the expression simplifies to omega |tau-nD|/D. The formula is not directly
valid for heterogeneous targets or weights. For tau=0 the stipulated convention
is G=0 and P=n omega.

Loaded return means tau is not fixed at the initial total B. Conservation gives
tau=B-sum_k R_k, with R_k in [0,Q_k]. A global necessary bound must minimize
over a safe superset of possible **integer** totals, for example
max(0,B-sum Q)<=tau<=B, further restricted only by separately proved facts.
It must not assume all vehicles return empty.

**Proposition 2.** For the original J2/J3 problem and any nonnegative penalty
coefficient lambda, its exact physical optimum is

\[
F^*_{\rm IP}=\min\{4\lambda,\tfrac14+\lambda\}.
\]

Indeed the only possible integer totals are tau=0,1,2,3. The lemma gives:

| tau | G lower bound | P lower bound | Objective lower bound |
|---:|---:|---:|---|
| 0 | 0 | 4 | 4 lambda |
| 1 | 3/4 | 3 | 3/4+3 lambda |
| 2 | 1/2 | 2 | 1/2+2 lambda |
| 3 | 1/4 | 1 | 1/4+lambda |

For lambda>=0 the middle two expressions exceed the last by 1/2+2 lambda and
1/4+lambda, respectively, so cannot improve either endpoint minimum. The
tau=3 bound is attained by the legal one-unit station1-to-station3 transfer,
with inventory (1,1,1,0) and duration 120. The tau=0 bound is attained by vehicle
0 picking up station2's one bicycle and returning loaded, and vehicle1 picking
up station1's two bicycles and returning loaded: durations 120 and 240,
respectively, with Q=(1,2). Both fleets are legal in J2 and J3. These matching
lower and upper bounds prove the formula, including S=0.

The transition is lambda=1/12. Since lambda_hat>1/12, the loaded-coefficient
conclusions are F*_LP=lambda_hat and F*_IP=1/4+lambda_hat, with gap exactly 1/4.
For ideal decimal lambda=3/20 these are exactly 3/20 and 2/5. The loaded IP
value is 14411518807585587/36028797018963968 and is displayed approximately
as 0.40. The general-lambda original physical proof does not assert that every
parameter-dependent S2 strengthening/cutoff has been rebuilt and verified for
all lambda. There was no new native sensitivity experiment.

## 4. Relation to existing project mechanisms

All historical files below were read directly, not inferred from their names.
Their immutable blob identities are listed in `math/history_sources.json`.

| Existing mechanism and directly read source | What it already covers | Relation and limit of this explanation |
|---|---|---|
| R55 `station_state_exactness_proof.md`, at `06b4c0634cbb85d3440be88511c736dd3282fdc9` | VD-J reconstructs ratio and the state-weighted minimum penalty in addition to VD-P products. | State-weighted penalty is already known. Its exclusion of one old mixture alone would not prove full-objective improvement with all auxiliaries free. This round does not reimplement it. |
| R55 `penalty_budget_validity.md`, `penalty_cover_validity.md`, `penalty_cover_dp_design.md`, `penalty_cover_final_decision.json` | Strict-improver penalty budget, multiple-choice cover validity and exact integer-scale DP were implemented/tested. | The VD-J prerequisite failed; live development and confirmation counts are both zero. This is **not** evidence that the cover mechanism was empirically ineffective. |
| R98 `mathematical_algorithm.md` | A/B shares inventory-state movement/visits; theta links vehicle and station-state marginals with capacity eligibility. | These rows are explicitly in B_ref and the strict full-reference point passes them. Marginal consistency is distinct from joint donor compatibility. No new state-linkage claim is made. |
| R101 `mathematical_algorithm.md` | Events are `(i,sign,q)`, one distinct station per set, projected on original inventory selectors. Small-support ranks and large-support matching/Hall use capacity and necessary travel/handling with outside supply retained. | The J2 inequality fixes the service vehicles. The saved strict witness has a realizable inventory projection, so unlabeled inventory-event cuts cannot exclude that inventory. B_ref already includes all 80 exact-domain station-event rank rows. |
| R103 `mathematical_algorithm.md`, `capability_table.md` | Full necessary single-car support/member pricing and alternative mixtures; unique-access multipliers cannot separate a point already in the same hull intersection. | Complete joint support differs from recombining the same independent supports. Strict service separation and current complete-objective gain remain separate; no R105–107 architecture is reopened. |
| Historical inventory DP, `docs/algorithm_report.md` (frontier objective and inventory probe sections); R90 `lp_g_split_implementation_handoff.md` and `lp_g_g3_decision.md` | Inventory penalty-budget DP and suffix bounds were already explored; LP-G changes a split proposal using the current parent LP G and retains complete coverage, not a new inventory epigraph. | A balancing explanation does not establish nonredundancy against existing DP/objective bounds. Old numerical outcomes do not decide a new common-projection comparison. |
| R114 `claim_policy.md` and `final_report.md`; R118 `positive_objective_proof.md` / `scripts/round118_math.py` | R114 documents source revocation and independent nonnegative floor0. The positive stock-deficit floor and bulk greedy penalty relaxation are explicitly documented at R118 and carried into R132. | The task's shorthand “R114 stock-deficit floor” should not conflate those two provenance layers. Positive shortage floors and state penalty links are existing ideas, not new here. |
| R120 `mathematical_contract.md` | Qualified child bounds plus cutoff complements define a scalar disjunctive objective envelope in G. | This is a conditional envelope of inherited source bounds, not the full integer-inventory objective hull; it depends on their qualification. No hidden solver-tree verification follows from its algebra. |

The direct source paths above are under their named `results/...` round directories
at the Round132 immutable study lineage, except the explicit R55 pin. No historical
campaign or new production matrix was restored for this comparison. The explanation
suggests investigating integer inventory with its original objective epigraph, but
does not establish that it dominates the existing mechanisms or is the main cause
of difficult real instances.

## 5. Gates for later research; no implementation this round

An integer-inventory objective envelope should first demonstrate nonredundancy
on the same complete model and common projection with every noncomparison
auxiliary free. It then needs a valid treatment of unequal D_i and omega_i,
variable tau, S=0, inventory capacities and route resources. An actual difficult
root/leaf must show useful original-objective lower-bound gain at affordable cost.
The equal-target lemma alone does not authorize an instance-specific production
shortcut or a repetition of the existing penalty/DP studies.

A joint support direction over a subset I needs a valid **upper** bound on the
maximization over the entire station universe N:

\[
\sum_{k,i\in I} w_{ki}^{\mathsf T}v_{ki}\le\widehat\Psi_N(w).
\]

A restricted-column maximum or a feasible maximizing fleet supplies a lower
bound on that maximization and cannot be used as the cut RHS. An outside-station
relaxation may aggregate pickups/deliveries P^O_k,D^O_k while preserving

\[
\sum_{i\in I}(p_{ki}-d_{ki})+P^O_k-D^O_k=R_k\in[0,Q_k],
\quad (t_p+t_d)(\sum_{i\in I}p_{ki}+P^O_k)+\underline t_k\le T_k.
\]

It also needs valid shared outside-stock and reception bounds. Zero travel is
a safe lower bound; stronger travel claims need proof. Outside aggregation is
a relaxation interface, not a fictitious physical station. Cumulative pickup
is not capped by Q. Before solving such a support problem, prove that every
complete fleet maps into the relaxation. Only then investigate a support
difference and original-objective increment. No real-role LP, oracle, cut
separator or production matrix was run or admitted in this round's E task.

These results complete the finite E interpretation. They preserve the previous
negative objective results and the full-universe gate rather than creating a
new algorithm or claiming full-size performance from a tiny example.
