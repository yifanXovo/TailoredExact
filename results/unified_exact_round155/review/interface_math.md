# Interface and mathematical review before substantive loops

This review uses a separate arithmetic/reconstruction path. It is not described
as a review by an independent nonimplementer agent. The targeted executable
checks in round155_qualify.py must pass before loop admission is materialized.

The new basic-dual interface reads all current RMP row multipliers. Inequality
signs are repaired by the unchanged original-Q certificate routine; beta is
clamped consistently with the hull completion row. Potentials are free equality
multipliers. It computes each existing column's exact original price once,
sets a_K=min(alpha,min_K p(Y)), and applies the identical C_Q residual support
using only pre-column implied Q bounds. Neither a selected LP objective nor
native reduced costs are used as hull lower bounds.

The 1e-8 numerical completion margin belongs only to the RMP primal model. Its
RHS is excluded from C_Q. Full marginal equality, convexity, negative mass,
original model feasibility and true expected completion are checked before a
primal can improve the numerical LP upper. That upper is not a physical routing
incumbent. Older admissible uppers remain with their original witness chain.

Every returned inventory is reevaluated on the entire frozen scope. Exact
original price determines true reduced cost and ordering. A duplicate is never
counted as a new column. If the corrected ceiling satisfies C_Q+a_K>=zeta, an
existing column cannot satisfy p(Y)<zeta-C_Q; such a duplicate is a qualification
failure rather than progress. Positive or zero reduced-cost new incumbents can
also be retained without harming correctness. Adding columns always requires a
subsequent full RMP solve; a phase cannot discharge pending columns on the basis
of its old solution.

Pricing remains the inherited signed state-product residual and strengthened
cost product. The first rule inherits the qualified target callback; the second
uses the existing bounded oracle and 256-node stopping, returning its incumbent
pool. The compact adapter changes evidence storage only. It retains one complete
MPS, unchanged fixed rows, every changed coefficient/bound, exact row ordering,
native parameters, actual return and direction. Reconstruction must reproduce
the actual model semantics. Complete first/last models remain saved.

The lower is always C_Q+min(a_K,L_m). On the safe positive branch, residual ell
is divided by u when nonnegative and l when negative. Legal zero inventory is
combined by minimum and an inherited whole-domain price lower by maximum.
These operations are untouched. Each price lower belongs to its own direction;
only the resulting complete hull lowers are accumulated across directions.

All accumulated support rows are retained for a final original-free-Q replay.
A finite-support LP objective is never a complete-hull upper. No elapsed-time
component switch, role-conditioned rule, new routing/loading cut or production
helper change is introduced. Twelve-iteration screens assess implementations;
they cannot justify saturation of either full domain.
