# Accepted corrected S0/F0 CPLEX algorithm contract

## Authority and discrepancy resolution

The accepted behavior is the corrected stable S0 production path, not the
older external schedulers. It is established jointly by the current
`chooseGlobalGiniSplit` implementation, the shared interval-row factory, the
Round 23 corrected-S0 manifests and official commands, and the current
certificate tests. These sources agree on the contract below.

The apparent discrepancy with C2 is intentional: C2 creates an initial set of
four external leaves and requires complete child-LP lookahead benefit before a
split. Corrected S0 instead starts from the complete root and recursively
branches at the remaining equal-partition breakpoints; after those breakpoints
are exhausted it performs unconditional adaptive midpoint branching. C3
follows S0. It records both the contract's four initial intervals and its one
initial externally scheduled root.

## Improving range and incumbent

- The maximum possible Gini value is `(V-1)/V`.
- The upper endpoint relevant to improvement is
  `min(independently verified incumbent objective, (V-1)/V)`.
- The lower endpoint is zero for official uncapped runs.
- An explicit user cap that truncates the relevant upper endpoint makes the
  range partial and cannot produce an original-problem certificate.
- The same-run HGA incumbent is independently verified and supplies only a
  valid upper bound. It never supplies a lower bound.
- The objective cutoff row is the original objective at the verified upper
  bound with epsilon exactly zero.

## Structural Gini tree

- Initial equal intervals: 4.
- Native/root representation: one complete root, recursively split first at
  the median remaining initial breakpoint. For four intervals this produces
  the root midpoint, then the left and right quarter breakpoints.
- Split factor: 2.
- Adaptive split point: interval midpoint.
- Adaptive eligibility: after the two initial-partition levels, split when
  adaptive depth is less than 8 and interval width is greater than `1e-4`
  (with the source's `1e-12` comparison guard).
- Terminal rule: no remaining initial breakpoint and either adaptive depth 8
  has been reached or the minimum-width rule blocks another split.
- A structurally eligible, LP-valid, non-pruned leaf splits unconditionally.
  Child infeasibility and child LP improvement are not prerequisites.
- Children exactly cover the parent and may meet only at the accepted shared
  boundary. Parent replacement is atomic.
- Each child inherits the complete valid parent LP lower bound until its own
  complete LP is selected and solved.

## Selection, pruning, and terminal exact solve

- S0 uses native best-bound processing. C3 preserves the mathematical rule by
  selecting the minimum valid external-leaf lower bound.
- C3's preregistered structural tie order is: smaller width, greater depth,
  lower endpoint, upper endpoint, deterministic leaf ID.
- A complete interval LP may close the leaf only as infeasible or prune it
  when its valid lower bound cannot improve the verified incumbent under the
  `1e-7` certificate tolerance. An LP result is never integer optimality.
- A terminal interval is solved as the complete original fixed-interval F0
  MIP with exact zero relative and absolute MIP gaps.
- A terminal MIP is launched at most once and runs to native optimality,
  native infeasibility, or interruption by the remaining global process
  deadline.
- Returned incumbents are independently verified before the global upper
  bound changes.

## F0 formulation and accepted rows

Connectivity-flow formulation F0 resolves to `round20-current`. No variable is
added to encode the outer interval tree.

Six global paper-safe families:

1. `inventory_conservation`
2. `movement_reachability_domains`
3. `visit_inventory_linking`
4. `global_handling_capacity`
5. `support_duration`
6. `transfer_compat`

Nine interval-local paper-safe families:

1. `direct_gini_cap_floor`
2. `interval_tight_mccormick`
3. `objective_estimator_cutoff`
4. `penalty_lb_closure`
5. `gini_spread`
6. `required_movement`
7. `low_gini_centering`
8. `variable_s_centering`
9. `sp_product_estimator`

The interval bound and verified-incumbent objective row are separately tagged
contract mechanics. The authoritative row factory version is
`round19_v2_projected_centering`.

## Native settings and certificate

Corrected S0 uses one CPLEX thread, traditional search, presolve off for the
continuous custom-G branch contract, parent-copy child estimates,
full-inherited-pack attachment, deferred local-row timing, no native MIP
start, F0 `round20-current`, and exact zero gaps. Default native ordinary cuts,
heuristics, probing, and compact-variable branching remain solver-owned.

Strict certification requires complete improving-range coverage, exact and
atomic parent-child coverage, valid monotone inherited/LP/MIP lower bounds,
every relevant leaf closed, an independently verified global incumbent,
global LB/UB agreement within `1e-7`, and complete model/environment lifecycle
and feasibility-consistency gates.
