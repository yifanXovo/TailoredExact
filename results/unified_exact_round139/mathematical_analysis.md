# Placement of inventory-product consistency rows

Round139 extends the accepted Round138 resource-product study. Its object is
the location of four valid rows, not a new RLT construction or a claim that
LP strength orders complete algorithm performance. The stable method remains
Round137 GI-TBC. The legacy Round138 switch continues to mean both locations.

Let D specify an actual inventory-support domain, a Gini interval [alpha,beta],
physical parameters and the original objective. X_D denotes its integer feasible
completions, R_D the continuous formulation, and C_D the four inventory RLT rows
using these exact endpoints. At integer selectors the product variables satisfy
Z_i = g Y_i; applying the shared inventory sum bounds to that common factor gives
the valid rows. This argument does not require auxiliary g to equal the true
Gini of Y. Thus

\[
X_D\subseteq R_D\cap C_D\subseteq R_D,\qquad X_D\cap C_D=X_D,
\quad L_D^{base}\le L_D^{stock}\le z_D^*.
\]

The continuous-domain and integer-domain claims remain those of Round138;
they are not strengthened to unspecified projected polytopes here. The four
uniform placements 00/base, 11/both, 10/LP-only and 01/MIP-only all preserve
integer feasibility and the original objective. An outer LP strengthened with
stock rows and a native MIP without those rows is exact under the same proof
policy. The converse is also exact. “Outer LP” means explicit controller
relaxations; a native MIP includes its own root LP and search relaxations.

The paid model often includes f <= c. Its returned lower bound ell_(D,c)
belongs to that restricted domain. Decomposing D into f <= c and f >= c gives

\[
L_D^{LP}=\min\{\ell_{D,c},c\}.
\]

If the improvement domain is infeasible, its contribution is +infinity and the
complement supplies c. The existing R120/R134 evidence and numerical policies
qualify this bound; changing placement neither relaxes their residual limits
nor invents a new certificate. Valid same-domain evidence combines as

\[
L_D=\max\{L_D^{LP},L_D^{MIP},L_D^{inherited}\}.
\]

A bound whose source domain contains the target domain can be inherited by
the target. A child cannot supply a parent bound without a complete cover.
The frontier takes the minimum of its valid obligations and cutoff complements.
An external LP contribution stays distinct from a native MIP returned bound.
The implementation retains the unchanged NativeEvidenceJournal qualification
path and complete-frontier ledger.

For finite feasible children, current AM uses d=max(U-Lp,epsilon),
ri=clip((Li-Lp)/d,0,1), eta=min(rl,rr), mu=(rl+rr)/2 and S_AM=eta*mu.
It first checks a strict improvement in the weakest child. Without one, the
parent enters exact-close; the threshold comparison is reached only afterwards.
Even with nonnegative strengthening deltas at parent and children,

\[
(L_i+\Delta_i)-(L_p+\Delta_p)
 =(L_i-L_p)+(\Delta_i-\Delta_p).
\]

Consequently stronger LPs need not raise the marginal child gain, AM score, or
frequency of splits/targets. The denominator also changes. This is a property
of the existing controller and its formulation input, not a new general AM
theorem. K20 is an actual example: BASE (Lp,Ll,Lr) =
(0.195149152441,0.196078259949,0.540770654572) selects native-target with
S_AM about 0.00047847; BOTH uses
(0.204590439178,0.204590439178,0.540770654572) and selects exact-close at
the no-strict test. Tau remains .08 in every placement comparison.

Asymmetric placement requires a real matrix transition. Round139 verifies the
old immutable artifact, discards the retained native model, and rebuilds using
the unchanged V2 writer with the declared role. A fresh path/SHA/signature
identifies the matrix. Same-domain LP evidence and its original SHA remain;
cutoff-epoch changes keep the existing invalidation policy. Integer requests
are intercepted before native scope construction, so both target and terminal
consume the declared matrix. Model rebuild and lost reuse are paid complete
method costs. No basis/tree transfer across changed matrices is claimed.

Four-grid interventions expose joint changes to control and native execution.
They do not provide an additive decomposition of runtime. Earlier solver state,
Start processing and rebuild differences remain part of each complete method.
Open certificate time is null. Rounded native incumbent logs are diagnostic
model objectives, not independently validated intermediate physical upper
bounds; controller trace publication time is not solver discovery time.

Independent preflight: review/preflight.md. Actual qualification, registered
positions and complete outcome summaries are reported separately. No statement
here presumes a winning placement or licenses instance-specific dispatch.
