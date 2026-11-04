# Independent preanalysis review for Round152

Reviewer: `/root/independent_review`, independent of the main implementation.
Date: 2026-11-04 (Asia/Shanghai). This is a mathematical/design admission,
not implementation qualification or approval of unobserved solver results.
No Optimize, enumeration, DP, compilation, producer or physical experiment
was invoked by this reviewer. File reads and theoretical review are excluded
from the experimental computation ledger under the task's accounting rule.

**Disposition: ADMIT the staged offline study, subject to the concrete checks
below.** No blocking mathematical defect was found in the proposed equations
(1)--(8). Production admission remains conditional on actual implementation
qualification, useful information beyond relevant old controls, and cost.

## 1. Reviewed sources and scope

The supplied complete goal and `WORKSPACE_POLICY.md` were read. The initial
goal copy had not yet appeared during the first read, so the original
`C:/Users/Administrator/Downloads/TailoredExact_Round152_Complete_Goal.md`
was read directly; the repository copy subsequently appeared.

Direct historical reads cover R133 `joint_objective_gap_note.md`, R135
`ap_math_and_history.md` and `final_report.md`, R138/R140/R141/R142/R146
`mathematical_analysis.md`, R104 `mathematical_algorithm.md`, the R105/R107
complete-study reports, the beginning and delivery portions of R106's report,
and R55 `penalty_cover_final_decision.json`. Sparse historical paths were read
with `git show HEAD:<path>` without changing the worktree. The current branch
inherits the R151 history; this review does not replace its fixed identities.
No AGENTS.md was found in the active tree by the filename search.

## 2. A useful exact reduction after AP

For fixed selector marginals s, define

    H(s) = sum_(i,y) h_i(y) s_iy,
    Gamma_D(s) = min_lambda sum_Y lambda_Y max(gamma_L,G(Y))

with exactly the same common-distribution constraints and R_D as Theta.
Every feasible common distribution satisfies

    sum_Y lambda_Y sum_i h_i(Y_i) = H(s).

Consequently **Theta_D(s) = H(s) + Gamma_D(s)** whenever the common-distribution
polytope is nonempty, and both relevant extended values are +infinity when it
is empty. This is an elementary decomposition, not a new general theorem.
It clarifies attribution: after AP, extra objective information concerns the
Gini epigraph over a jointly feasible integer distribution. The penalty is
already determined by the fixed marginals. This does not make penalty
irrelevant to optimizing the full model, where the marginals also change.

The pricing substitution pi=h+psi is exact:

    alpha_D(h+psi)
      = min_(Y in R_D) [max(gamma_L,G(Y)) - sum_i psi_i,Y_i].

Searching bounded residual potentials psi around the known AP contribution
can prevent a bounded master around pi=0 from spending most of its capacity
rediscovering AP. Fixing one potential per station to zero is harmless only
with the corresponding intercept translation. The pi=h direction is
AP plus a hard-resource integer Gini floor; it is different from the pi=0
original-objective scalar floor. Neither failed direction disproves the
entire epigraph family. At a full-model point with excess P_e above AP,
the relevant separation threshold is eta-H(s), not simply its g coordinate.

## 3. Validity, completion and scope

For every original integer completion, Y must belong to the declared
necessary oracle domain and g+P_e must dominate phi_D(Y). Thus a certified
pricing lower bound gives the stated support row by direct substitution.
This proof includes slack/nonminimal g and e: physical G below gamma_L is
legal when g is at least gamma_L. Imposing G>=gamma_L would break the proof.
G<=gamma_U is a necessary condition. Omitting the original objective cutoff
from the oracle enlarges the domain and is safe; supports already contracted
under that cutoff remain bound to their original scope.

Physical resource bounds must exclude the depot and follow loaded-return
conservation B-sum Q <= sum Y <= B, intersected safely with supported minima
and maxima. An observed fractional sum Y is not a resource bound, and
cumulative pickups are not bounded by Q. Ratios and weights must be the
actual model coefficients; omega already contains lambda in this task.

Rows proved on a parent domain can enter a compatible child. Reverse
transport from a strict child to a parent is not justified. A changed
potential requires new pricing or the explicit finite-state correction.
Potential coefficient changes require the maximum-per-station intercept
compensation stated in the goal, including coefficient deletion at import.
Negative potentials and negative pricing intercepts are legitimate and
must not be clipped to zero. Objective constants and all anchors belong in
the same identity/transport check.

## 4. Oracle bounds and denominator coverage

The bin model is a minimization relaxation. For an integer Y in a positive
bin, setting a_ij to its actual absolute difference and q to the least
legal value constructs the surrogate completion. Conversely its Gini-upper
row implies actual A<=n gamma_U S because A' >= A. Therefore its feasible
integer inventories obey the true upper-Gini condition, up to the existing
numerical qualification policy, and repricing each returned Y with the true
ratio objective gives a valid feasible pricing upper bound.

The objective lower bound is **the minimum over a complete bin cover**,
including unresolved/unvisited bins through a valid fallback bound. An
infeasible bin may be omitted only after a qualified infeasibility result.
A restricted dual-master intercept or a feasible inventory objective is
never substituted for a global pricing lower bound. The original objective
cutoff, if later added, would require checking the actual inventory against
that true condition before using it as a pricing upper witness.

The all-zero state, when supported and resource-feasible, is separate and
has cost gamma_L+sum h_i(0)-sum pi_i0. Positive coverage can start from a
conservative strictly positive supported ratio lower bound and end at a
conservative supported/resource upper bound; there is no need for an LCM
grid. Adjacent closed bins may overlap, which is safe. A gap at an endpoint
is not safe. The zero state must not be accidentally routed into a positive
bin through a feasibility tolerance.

The bound epsilon_b=g_max(1-l_b/u_b) concerns approximation of the true
Gini term at a fixed integer Y. It does not include the MILP optimization
gap. Save both quantities and the global pricing L/U. A time limit with
no useful bound is UNKNOWN; the safe fallback still preserves validity.
The unary hard-total DP is a relaxation of the full pricing domain when
it ignores bin/Gini conditions. Its result remains a valid lower bound,
even if its minimizing inventory is inadmissible for a true pricing upper.

## 5. Nonduplication and strong-reference design

AP is an established state-penalty expression. R135 already shows its ideal
projection relation to IND under stated bounds/aggregate-use assumptions
and mixed complete results, including K35 benefits and certification
slowdowns. R55's later cover DP was not opened; that is not an empirical
rejection of the cover idea. The hard-resource multiplier counterexample
is a design control, not a new strictness theorem.

R138 stock products and TC already close the old R133 J2/J3 objective gap.
R146 GD also closes the related zero/positive binary family. R140's full
threshold identity, integer count bounds and TC2, and R142's selected
count-product hull theorem must not be renamed as Round152 innovations.
In particular R142 establishes integrality for nested count-only selectors,
not for that block intersected with weighted stock or the original objective.
The latter boundary gives a legitimate remaining question.

A strong tiny example should expose a remaining correlation among several
positive/heterogeneous ratio levels or between weighted stock and counts,
after AP and relevant GD/TC/stock controls. A symmetric zero/one example
alone is an especially poor novelty witness. A joint feasible distribution
at the same marginals is needed to call a strict value difference an
objective-epigraph gap rather than a projection gap. A hand-built block
example should be labelled as such unless a complete exported-model
extension is actually verified; an exact finite small-domain LP is another
acceptable route under the task.

The three initial real domains have complementary roles: N-B35-S supplies
the current difficult shortage/resource-floor setting, K-35-U the known
surplus setting with old AP evidence, and N-C20-U the CPF-no-root-gain
positive-objective setting. This is a purposeful finite study, not a blind
holdout. Reuse old B and K35 AP only after matching objective, supports,
cutoff, all rows, bounds and semantics. Numerically close objectives do not
prove equivalence. Pay for only missing same-domain AP LPs; preserve all
original variables free. Add relevant GD/stock/count controls as the
observed mechanism warrants, recording which reference was actually used.

For attribution, the sequence is AP, pure hard-total projection diagnostic,
Gini-domain joint feasibility where needed, and the residual objective
epigraph support. A cut that merely excludes marginals with no common
resource-feasible distribution is useful projection information, but not
evidence of a finite Gamma gap. A nonzero-potential separation at an AP point
does not yet prove anything beyond GD/count until those applicable controls
are compared on the same model/domain.

## 6. Focused implementation admission checks

Before long pricing runs, the implementation should demonstrate on finite
small domains: actual weighted objective units; exact enumeration versus
pricing L/U; negative potential/intercept; gamma_L above physical G;
all-zero state; complete positive bin coverage; pointwise surrogate error;
and parent/child or changed-potential transport. Keep a deliberately
unresolved bin to verify it remains in the global minimum through its
fallback. These are semantic checks of a new oracle, not an invitation to
rewrite the project's numerical policy or repeat R151's repaired fixtures.

For one real model, read back every newly inserted row, verify retained old
matrix/bounds/objective identity and save complete free-LP feasibility and
quality. Potential construction, pricing and reoptimization need separate
times inside a once-charged outer receipt. One useful structural revision
may improve the limiting-bin lower bound or residual-potential search; a
small initial scalar floor is not a sufficient stopping reason.

No new production route/master decomposition is needed for this offline
object study. R104 compression preserves at most a declared root objective,
not all descendant bounds, and R105--107 show concrete master waiting/poor
route conversion in their tested architectures. Those results constrain
interpretation without mathematically ruling out this different oracle.
Complete algorithm claims require a later frozen, same-PE, own-H comparison
whose full costs include every auxiliary solve. This review admits no such
claim in advance.

## 7. Review completion

No mathematical blocker remains for small-domain qualification and the
staged real AP/oracle diagnostics. The decomposition in section 2 and the
attribution sequence in section 5 are recommended additions to the working
analysis. Implementation and final scientific evidence require a separate
review after they exist. All review edits are confined to this file; no
main implementation file, production entry, prior result, or Git commit was
changed by the reviewer.
