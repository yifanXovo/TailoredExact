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
