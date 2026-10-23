# Mathematical analysis of the frozen model and research expressions

## 1. Physical semantics and comparison space

Only service stations enter inventory, target deviation and Gini sums. A vehicle starts empty, follows a depot-closed route and can return loaded. Each station receives at most one nonzero, one-direction service. Inventory, vehicle assignment and the original integer route/load structure retain their parser/writer/Evaluator meanings. Prefix loads and each individual operation obey Q; cumulative pickup need not be at most Q. Physical T and computational caps are different quantities.

For every physical fleet,

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad
R_k=\sum_i(p_{ki}-d_{ki})\in[0,Q_k],\quad
\sum_iY_i=\sum_i b_i-\sum_kR_k.
\]

Returning bicycles are unloaded and counted in handling. Consequently

\[
t_p\sum_i p_{ki}+t_d(\sum_i d_{ki}+R_k)
=(t_p+t_d)\sum_i p_{ki}.
\]

Replacing the last pickup sum by Q, fixing total final inventory to its initial value, supplying bicycles externally at the depot, or allowing split station service would change the model.

Write r_i=Y_i/D_i, S=sum_i r_i, A=sum_{i<j}|r_i-r_j| and

\[
P_{true}=\sum_i\omega_i|r_i-1|,\qquad
G_{true}=\begin{cases}A/(nS)&S>0,\\0&S=0,\end{cases}
\qquad F=G_{true}+\lambda P_{true}.
\]

The native epigraph variables satisfy e_i>=|r_i-1|, P=sum_i omega_i e_i, and g is also an epigraph variable. Arbitrary native points can inflate P and g. Tight physical completion gives their original objective; that embedding, interval coverage and cutoff complement are essential to a global bound.

Fix the same input, actual variable domains, G interval, cutoff c, objective and retained structure. For a stated common coordinate vector xi, A dominates B if proj_xi(P_A) is a subset of proj_xi(P_B). Strictness requires a strict projected witness. Equivalence requires both inclusions, normally by auxiliary reoptimization. A difference with old auxiliaries fixed is not a physical/target-objective projection difference. Four questions remain distinct: preservation of physical solutions; projection strength; the current objective LP optimum; complete solve cost.

## 2. Local inventory products and service linking

Let the finite allowed inventory set have minimum L and maximum U. The convex hull of (g,y,gy), g in [alpha,beta], y in that set, equals the McCormick hull over [alpha,beta] x [L,U]. Every state line lies in the rectangle hull, while the four corner graph points belong to the state union. The rectangle hull is their convex hull, proving both inclusions. This standard isolated-block statement includes no service, penalty or routing links; it does not establish whole-model equality or VD-P dominance over a correct four-plane aggregate MC block.

VD-P uses sum_y s_iy=1, Y_i=sum_y y s_iy, alpha s_iy<=q_iy<=beta s_iy, sum_y q_iy=g and Z_i=sum_y y q_iy. Its retained A/B and inventory rows imply

\[
\sum_kp_{ki}=\sum_y(b_i-y)^+s_{iy},\quad
\sum_kd_{ki}=\sum_y(y-b_i)^+s_{iy},\quad
\sum_kz_{ki}=\sum_{y\ne b_i}s_{iy}.
\]

These shared state weights tie expected movement and assignment to inventory. They do not describe the full BRP hull. With binary assignment and direction, unique service and integer Y, p and d are implicitly integer directly: at an unserved station both vanish; at the unique served vehicle only one direction can be positive and the inventory equation sets it to the integer absolute change. A/B is therefore not necessary for this particular integer-solution argument. Deleting binary direction would require a different theorem.

## 3. Projection of the three geometry row families

Delete only H-spread, variable-S centering and fixed-S centering. Keep all H absolute-value lower bounds, individual bounds, total cap/floor, original Gini epigraph, scalar/SP estimators, cutoff, real domains and domain-generation rules. For n>=2 the ideal three families are

\[
(n-1)H_{ij}\le n\beta S,\quad
\pm(n-1)(r_i-r_j)\le n\beta S,\quad
\pm(r_i-r_j)\le n\beta\bar S/(n-1).
\]

Let H_sum=sum H_ij. The retained original epigraph is H_sum<=n sum_i Z_i/D_i. Nonnegative states and q_iy<=beta s_iy give Z_i<=beta Y_i, hence H_sum<=n beta S. Triangle inequalities give A>=(n-1)|r_i-r_j|: for each third station t, |r_i-r_t|+|r_t-r_j|>=|r_i-r_j|, together with the pair itself; unused pair distances are nonnegative. Thus both centering families follow from the retained inequalities and S<=Sbar.

### Root interval

When alpha=0, replace every H_ij by |r_i-r_j|. This decreases the sum, respects its upper bounds and all individual upper bounds under the audited conditions, and the floor reduces to nonnegativity. The new H satisfies H-spread and leaves all non-H variables and the objective unchanged. Reverse inclusion follows by adding constraints. Thus projecting away all H gives equal LP sets and equal ideal LP objective values. Because H is continuous, the same extension preserves any remaining integer restrictions.

### Positive lower endpoint

Assume 0<=alpha<=beta, r_i>=0, S<=Sbar; individual H upper bounds U_ij=c_i+c_j with c_i>=0 and r_i<=c_i; and outside the deleted families H appears only in absolute lower bounds, individual bounds, a total floor/cap and other uniform total upper bounds. H has zero objective coefficient and no additional individual positive lower bounds or nonuniform linear uses.

Fix every non-H variable in a feasible point of the deletion model. Put d_ij=|r_i-r_j|, A=sum d_ij, L=n alpha S and t=n beta S/(n-1). Let B be the smallest retained total upper bound, including the implied n beta S. Feasibility gives

\[
T^*=\max(A,L)\le\min(B,\sum U_{ij}).
\]

The triangle argument gives d_ij<=t. Let U'_ij=min(c_i+c_j,t). With C=sum c_i>0, f(c)=sum_{i<j}min(c_i+c_j,t) is concave on the nonnegative simplex of sum C. Express c=sum_i(c_i/C)Ce_i. Concavity then gives

\[
\sum U'_{ij}=f(c)\ge(n-1)\min(C,t)
=\min(\sum U_{ij},n\beta S)\ge T^*.
\]

If sum U'>A, set theta=(T*-A)/(sum U'-A) and H'_ij=d_ij+theta(U'_ij-d_ij). Then 0<=theta<=1; every individual bound and spread bound holds, sum H'=T*<=B, and the floor holds. The centering rows already follow without H. All non-H variables and their objective remain unchanged. If the denominator vanishes, T*=A and H'=d suffices. If C=0, all c,r,S,A,L vanish and H'=0. If S=0, nonnegative ratios vanish and H'=0. For n=1 none of these three families is generated. This proves both projected inclusions, including the nonzero-floor case in which setting H=d alone can fail.

### Actual-model application and numerical boundary

The current shared canonical factory generates the named three families, and the frozen paper profile disables local/subset nonuniform H uses. The Cplex writer sets H upper bounds to fl(C_i/D_i+C_j/D_j), with zero H objective coefficients. The independent reviewer inspected an actual saved S12 S2R matrix: 66 H bounds, five uniform full-H rows and 198 individual-H rows. W appears in five rows, as required below. This is a canonical-model result, not a theorem about arbitrary native node cuts.

The exact additive upper-bound hypothesis concerns real algebra. In the saved S12 matrix, 41 of 66 serialized H bounds differ from the exact rational sum of the two serialized r upper bounds at roughly 1e-16. Therefore the ideal theorem is not asserted as strict rational equality for every serialized floating matrix. Necessary actual coefficient/domain checks and extension residuals accompany the research comparisons. The production S2 bytes are unchanged; no hidden outward correction is applied. Equal projections do not imply identical presolve, native cuts, search paths or elapsed time, and do not make the entire C_G package redundant.

## 4. Exact elimination of W_SP, including its real bounds

In the active shared model W is continuous, has zero objective coefficient and is used by four MC rows, one SP cutoff and its own box. No other use is present in the qualified canonical scope. Preserve all W-free original rows, variable types and bounds, particularly g+lambda P<=c, which a cross-multiplied row cannot replace at S=0.

For actual W bounds w_l,w_u and MC parameters s_l,s_u,p_l,p_u define

\[
L_0=w_l,\quad L_1=s_lP+p_lS-s_lp_l,\quad
L_2=s_uP+p_uS-s_up_u,
\]
\[
U_0=w_u,\quad U_1=s_uP+p_lS-s_up_l,\quad
U_2=s_lP+p_uS-s_lp_u.
\]

The original system is L_j<=W<=U_k and H_sum+n lambda W<=ncS. For lambda>0 its complete projection is all nine compatibility rows L_j<=U_k and all three lower-cutoff rows H_sum+n lambda L_j<=ncS. Necessity is immediate. Conversely, W=max_j L_j satisfies every upper bound and the SP cutoff, proving sufficiency. This is standard one-variable Fourier-Motzkin elimination applied to this formulation, not a new linearization theorem or an exact continuous product identity.

Only after proving the same explicit nonnegative rectangle s_l<=S<=s_u, p_l<=P<=p_u, and that the actual W box is no tighter than the product box, may compatibility and W-box rows be removed. The true SP is then an extension for MC feasibility. Since L_1-s_lp_l=s_l(P-p_l)+p_l(S-s_l)>=0, the constant lower plane is dominated. The two lower-plane cutoffs then suffice, with W=max(L_1,L_2). Current inflated e can violate the tight physical P upper estimate; that estimate cannot simply be assumed to bound the whole epigraph.

For positive width s_u>s_l, MC lower/upper pairings imply P>=p_l and P<=p_u after cancellation. These consequences must survive projection. Example: s_l=1,s_u=2,p_l=0,p_u=1,S=1,P=2,H_sum=0 and sufficiently large c satisfies both lower-plane cutoffs but L_2=3>U_2=2, so no original W exists. Two cutoffs alone would incorrectly enlarge the domain.

When S is fixed, derive compatibility directly rather than dividing by its width. At S=0, W=0 need not imply P<=p_u. The full pair system handles that case without adding an unauthorized P bound. When lambda=0, retain H_sum<=ncS and every W-feasibility compatibility row; removing the whole block would again change its projection. Zero-width P and simultaneous degeneracy are also covered by the pair construction.

### Implemented research expression

The research writer reads the actual shared canonical row coefficients, normalizes their senses, includes the exact actual W box, and combines every lower/upper pair. There are three lower rows and four upper rows including the SP row: 12 projected rows. It retains even constant or duplicate compatibility rows. All remaining original rows, objective, bounds and integer types stay intact; only the W column and its rows are replaced. Its physical Start is mapped to the remaining actual columns and validated before use.

The independent checker reconstructs these combinations with exact rational arithmetic on source binary64 coefficients. It separately bounds the output coefficient-serialization residual over actual remaining-variable bounds. The candidate binary64 output is qualified as numerically consistent, not asserted to equal the exact rational projected matrix. `C_matrix_wording_addendum.json` makes this distinction explicit. Four saved interval/input configurations have equal canonical all-continuous LP objectives within the inherited 1e-7 policy. These finite observations check implementation and numerical behavior; they do not replace the general projection proof.

## 5. Qualification and relation to costs

The research default-off writer and original E3 produce identical complete canonical LP bytes on the qualified small and medium fixtures, at a root interval and a positive lower endpoint. Actual S12 CLI runs bridge original E3 to research default-off, and validate independent H and full Start submission for both candidates. Each uses the legal inclusive-root LP then restored-integer MIP workflow. Default-off equivalence is a semantic/matrix bridge; the two executable byte strings are different and are never described as identical.

C cost diagnostics remain required after these qualifications. Their known-role panel, two Seeds and three same-build expressions are frozen separately. D remains the original frozen algorithm, and its measurements do not come from this research build. Native process differences can be reported without claiming a stronger ideal LP relaxation.

## 6. Joint structure: definitions and unresolved obligations

For finite complete necessary service sets R_k in v_k=(p_ki,d_ki,z_ki), let P_sep=(product_k conv R_k) intersect unique service and let H_joint be the convex hull of jointly unique integer selections of one plan per vehicle. Every joint integer selection belongs to the separated product and unique-service rows; convexity proves H_joint subset P_sep. This elementary inclusion alone is not new and proves neither strictness after current theta/rank/routing constraints nor an objective increment.

On a common lifted space define B_ref as the actual current S2 continuous model plus those same single-vehicle hulls and the explicitly chosen historical theta/rank structures. Define B_joint=B_ref intersect H_joint. Any strict physical/objective claim must permit all other auxiliaries to reoptimize and provide a full B_ref extension. Distinct single-vehicle travel/resource domains cannot silently be exchanged across the comparison.

For H_k=conv R_k, h_k(a)=max_{v in R_k} a'v, and E_k v=z_k, every point of P_sep satisfies

\[
\sum_k w_k'v_k\le\sum_i\mu_i+\sum_k h_k(w_k-E_k'\mu),\qquad\mu\ge0.
\]

Indeed, bound each (w_k-E_k'mu)'v_k by its support value, sum, and apply sum_k z_ki<=1. Recombining the same single-vehicle support functions and linear unique-service rows cannot separate such a point. A genuinely joint support value Psi(w)=max{sum w_k'v_k: v_k in R_k, unique service} can do so only if its valid upper bound is below the separated value. Feasible plans and restricted column subsets provide lower bounds on this maximization, unsuitable as cut right-hand sides. Necessary service hulls remain distinct from complete physical route hulls.

The required bounded exact tiny comparison, its precise theta/event-rank space, witnesses or obstacles, costs and step-2 admission decision will be recorded in `joint_structure_note.md`. No structural or objective improvement is presumed while that required step remains outstanding.
