# Round153 preanalysis and review gate

The adopted goal is byte-identical to the supplied 29232-byte document;
SHA256 df131c38f9f9acdcc1c0dfccca9747f12367a34227208db863b605bdd8ab6c44.
On 2026-11-04 (Asia/Shanghai), origin/main is b2b940c1e517a72e226ec60fc49ff19651737632
and does not contain R152. Verified R152 head and temporary PR base are
ed058861e5eb094bc22d468a71a791bf558b51ac / codex/round152-resource-integer-objective.
PR214 is open, Draft, unmerged. The new branch is codex/round153-coupled-objective-hull.
No applicable AGENTS.md was found in the active tree or ancestors.
WORKSPACE_POLICY.md applies. Existing untracked history is retained; tracked
files were clean. The only observed preexisting Python process serves the
separate local-run-ui application; it is not a timed experiment.

## Design submitted for independent review

1. Read each complete R152 strongRN model and saved optimum. Generate both
   NC rows and all four TS rows through round145_math.joint_rows against the
   actual reciprocal bounds and supports. Use only implied finite caps:
   rn_h <= n*gamma_U follows from nonnegativity and rn_gini; rn_Y <= max(y)*U_t
   follows from its mass and inventory equalities. No argument that lowers
   auxiliary absolute values after adding NC is used.
2. Keep the original objective, all route/load/time variables and rows,
   cutoff, AP/GD/count/common-factor/RN/scaled-stock. Restore the eight qualified
   lifted rows, final full-support row and applicable scalar floor. First test
   old saved optima; free reoptimization is conditional on a violation or on
   missing qualified sandwich evidence. Transform total supports through the
   pricing identity psi=pi-h, retaining the original total rows and paying
   one-hot coefficient transport. Direct g does not replace the APoff floor.
3. Start a restricted master from valid old inventory witnesses. Add
   sum(lambda)=1, s=sum(lambda*v), g>=sum(lambda*f). All original x remain free.
   Legal columns use Fraction evaluation of actual binary64 coefficients;
   upward-rounded f is used in the Gini row. Any price bound correction must
   account for this upward column rounding before the full-domain dual claim.
   Empty/missing-column infeasibility will trigger Phase I or further legal
   seed construction, never an infeasibility claim for the full hull.
4. Extract the Lagrangian a, pi, beta>=0 with reduced cost
   beta*f-pi*v-a. Full-domain pricing generalizes the R152 normalized binary
   formulation to beta*f+sum(d), with d=-pi; the scalar floor uses beta=1,d=h.
   beta=0 still covers the hard resources, all states and Gupper. Separate
   valid zero state, negative prices, true-stock upper and lower are retained.
5. Compute a qualified dual lower using sign-repaired row multipliers and
   residual support on finite variable domains, including original Q. The
   convexity intercept correction max(0,a-Lm) occurs once. A true feasible RMP
   primal gives an upper on the strengthened LP value, never a physical BRP U.
   Current qualified Q lower can tighten the interval. Support rows preserve
   beta without division and use the goal's finite-domain coefficient transport.
6. Initially use absolute interval targets 1e-4 on the two 35-station roles
   and 1e-5 on N-C20, above inherited numerical uncertainty and below the
   relevant increment scale. Adapt to the observed bottleneck. No eight-row,
   six-price or .05-radius rule is a research stopping criterion. After an
   informative initial pass, deepen any important wide interval with available
   capacity; maintain an explicit quantitative stopping decision.
7. Independently screen the zero-potential floor relative to pure B. N-C20's
   existing near-zero upper is reused; K35 needs pricing against B. Production
   is conditional on demonstrated strength and a uniform affordable rule,
   not on the outcome of RN diagnostics. Preserve stable R137 throughout.

All experiments and necessary verification use the serial outer ledger,
115200-second total capacity, Seed 0 / Threads 1. Prior science is reused
without invented cost. Source snapshots precede each new run. No new timed
research beyond small qualification starts before a nonimplementer reviews
these formulas and the concrete interfaces. Packaging/authoring/build I/O
is recorded separately. Conditional complete arms retain the goal's capacity.

## Pending outcomes

Reference qualification, interface qualification, coupled intervals, targeted
deepening, floor decision, independent final review, fixed-science publication,
anonymous bounded recovery, Draft PR readback and workspace closeout remain.
