# One feasible fixed-level adjustment: pre-execution review

Status: the repaired level_interfaces_v4 passed. Both version2 level
attempts have now closed with unresolved selected-candidate limits: K35 after18
price/feedback cycles, NC20 after1. No large-domain level gain is claimed.
Their remaining substantive capacities are retained; see
level_stop_and_remaining_capacity.md. The K35 basic
phase closed normally at a reviewed checkpoint after112 iterations and1606
new columns, all with maximum recorded weight <=1e-10, in3244.787604100071
outer seconds. Its original remaining deep capacity is retained for this
adjustment. Its checkpoint readback, full214-support free-Q replay and
separate support readback all passed. The source-bound v4 level admission
and level_deep_plan_v2.json supersede the earlier candidate cap below.

The matched screens and the first 101 completed K35 deep iterations gave no
material interval gain or new-column weight above 1e-10. The deep phase had
35,507 columns at that observation, versus 34,052 at its start. This is evidence
to prepare a different selector, not evidence that the full hull is exhausted.
The present candidate is the single C3 adjustment, uniformly defined for both
domains. No instance-specific center or solver parameter grid is proposed.

## Mathematical reconstruction

For the actual finite RMP, write its original variables as x and nonnegative
inventory weights as lambda. The unchanged matrix is A x + B lambda with
mixed row senses, original explicit bounds l <= x <= u, and objective c'x+k.
The selector uses row multipliers pi with the corresponding signs, lower-bound
multipliers s >= 0, and upper-bound multipliers t <= 0. Its constraints are

    A' pi + s + t = c,
    B' pi <= 0,
    b' pi + l' s + u' t >= zeta + 1e-7 - k.

Only existing finite explicit bounds receive a multiplier. The lambda
inequality is exactly the result of eliminating its nonnegative lower-bound
multiplier. Its coefficients are read from the actual written column,
including the inherited upward completion coefficient. Every new column adds
its inequality; no original variable or row is removed or fixed. This model
is kept in memory throughout the phase. The inherited AP-based L1 center and
beta-center 1 define a secondary minimization objective. No potential radius
or box is added.

The nominal level cushion is a candidate-selection aid. The complete original
Q residual calculation excludes the artificial completion margin and convexity
RHS exactly as before. The candidate's actual ceiling must separately satisfy
C_Q + min(alpha, min_K p(Y)) >= zeta, using exact binary64 fractions and true
completion costs. The nominal dual objective, L1 objective, solver status,
and nominal feasibility are never substituted for this gate or a hull bound.

## Computational rule and exits

The current optimal RMP Pi/RC values supply a full selector primal start.
Native residuals are checked and saved; a warm start is not itself a proof.
All matrix edits precede PStart assignment. The obsolete selector solution
basis is discarded while its model is retained, so the current RMP point is
used with primal simplex, LPWarmStart=1. Seed=0, Threads=1, IterationLimit=2000
and a 120s offline call ceiling are fixed uniformly. A returned point with
Status2,7,9 can be accepted if complete numerical selector feasibility and
the exact original-Q/true-column ceiling both pass. L1 optimality is optional.
A failed call stops this phase with an explicit unresolved-candidate result;
it is not repeated indefinitely or interpreted as a bound.

The stage fixes zeta=(retained L+retained U)/2. The unchanged bounded residual
oracle uses tau=zeta-C_Q, NodeLimit256, PoolSolutions20 and the original price
conversion. A true p(Y)<tau returns a new negative column and continues the
same level. A whole-domain L_m>=tau establishes the lower-side exit. Only a
qualified complete original-Q primal with U<zeta establishes the upper-side
exit. After either certified exit, the next midpoint is formed. A phase
allowance, selector failure or undecided price leaves the level unresolved.

Each accepted candidate preserves full multipliers, complete selector point,
warm point, corrected certificate and original-price direction. First/last
selector and master models are saved. Intermediate selector matrices are
reconstructible from the fixed original matrix, current accumulated inventory
columns, fixed AP centers and recorded level RHS. Existing incrementally
reconstructible full-domain pricing evidence is unchanged.

## Targeted readback and actual outcomes

The separate checker transposes every actual primal coefficient, reconstructs
every dual variable bound and row, and compares a saved selector model. A
two-site enumerated domain checks a fixed-level strict counterexample,
deduplication, persistent addition of its inequality, subsequent full-primal
upper exit and full-enumeration lower exit. A real zero-iteration return checks
the limited-status interface without assuming it has a feasible solution.
An unavailable-level call must not become a hull bound. Existing signed
residual and complete-domain qualifications are inherited, not rerun as a grid.
This is independent arithmetic/model readback, not a nonimplementer-agent
review. Actual large-domain results still require their own final readback.

The first actual check, level_interfaces_v1, failed in the checker after its
two selector calls: Gurobi's accepted1e100 infinity sentinel was compared
directly with IEEE infinity returned on MPS readback. The saved model has
the expected FR/MI bounds. The repair canonicalizes only infinite bound
representations in the independent comparator; the selector, finite matrix,
level rule and certificates did not change. The failed outer cost was
0.5594974001869559s and its raw evidence/source snapshot are retained.

level_interfaces_v2 passed in0.4143294000532478 outer seconds. The real
IterationLimit0 call returned Status7/SolCount0 and was rejected, rather than
being invented into a feasible candidate. The ordinary selected candidate
passed all matrix and true-ceiling checks; at level.6 its new (1,1) inventory
had exact price-1/4 and entered the next full RMP with weight1, reducing the
qualified numerical upper from.7000000100000001 to.5000000099999999. The
level stayed fixed until that upper exit. Reusing the model with all three
legal columns passed exact reconstruction and the full-enumeration lower
exit at level.49. A requested unavailable level.8 returned Status3; only the
already saved complete primal, never that status, supplied an upper. These
are interface checks, not performance predictions for K35 or NC20.

## Actual large-start diagnosis and bounded repair

K35_feasible_level_deep_v1 closed without any price call or new column. Its
saved warm point had maximum constraint violation6.212998865384733e-14 and
zero bound violation. Native explicitly reported3172 superbasic variables
and used all2000 iterations in0.53s before a solution was available. Status7,
SolCount0 was correctly rejected; the complete outer cost61.94101840001531s
also includes the actual RMP, construction, readback evidence and output.
This is a start-conversion limit, not evidence that a feasible level is absent.

The same selector now uses IterationLimit=NumVars+2000, with the same120s call
ceiling. This is one model-sized deterministic allowance, not a parameter
grid or a promise that L1 optimization completes. The AP center, dual-domain
constraints, original Q, pricing and proof exits are unchanged. The initial
actual selector has49514 variables and47846 rows, so its revised allowance
is51514 iterations. level_interfaces_v3 checked this rule; after recording
the matrix discrepancy below, level_interfaces_v4 checked the final source.
Both passed. The current source-bound admission is level_admission_v4.

Independent actual-matrix readback exposed two tiny original RHS values
that Native omitted when they became coefficients in the nominal level row:

    pi_26755: -6971857329068129/10141204801825835211973625643008
    pi_26756: -8310899805071699/5070602400912917605986812821504

The first two large readbacks failed rather than silently accepting these
differences (fees9.12887019990012s and9.528721800073981s). The final reader
identifies and preserves omissions only on this nominal candidate-selection
row, requires each to be below1e-13, and requires exact equality of every
dual-domain equation, lambda inequality and bound. The selector records the
same exact omitted coefficients and, when a point exists, their contribution.
The nominal level is therefore explicitly a search aid; all original RHS
terms remain in exact C_Q and the unrelaxed true C_Q+a_K>=zeta gate. No hull
bound is obtained from the shortened nominal row. This preserves the prior
certificate policy without a new general numeric test grid.

K35_level_initial_readback_v3 passed in11.250085799954832s with zero Optimize.
The repaired K continuation inherits its closed first attempt and retains
25493s outer capacity; NC retains28800s. Both use the same rule. Old plans,
failed readbacks and actual source versions remain immutable references.

The first allocation writer also rejected itself as an unclosed fee
(prepare_level_deep_v1,0.4823491000570357s; no Optimize). It was repaired to
allow only its own metered parent label, reject any other unclosed fee, and
reserve its own remaining allowance. The replacement plan writer passed.
This guard repair did not alter any experimental algorithm or waive serial
execution. All failed and successful fees remain in the outer ledger.

Gurobi's documentation supports the specified start mechanism and reset
semantics; feasibility and performance remain empirical checks here:
[LPWarmStart](https://docs.gurobi.com/projects/optimizer/en/13.0/reference/parameters.html#parameterlpwarmstart),
[PStart](https://docs.gurobi.com/projects/optimizer/en/13.0/reference/attributes/variable.html#attrpstart),
[Model.reset](https://docs.gurobi.com/projects/optimizer/en/13.0/reference/python/model.html#Model.reset),
[limited statuses](https://docs.gurobi.com/projects/optimizer/en/13.0/reference/numericcodes/statuscodes.html).
This is an application of existing dual stabilization and midpoint ideas,
not a claim of a new general column-generation method.
