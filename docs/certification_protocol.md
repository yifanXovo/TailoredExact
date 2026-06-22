# Certification Protocol

This project distinguishes the original EBRP objective from fixed-cap and restricted-pool subproblems. A result is certified for the original problem only when all of the following hold:

- `status=optimal`.
- `gap=0`, with `lower_bound=upper_bound=objective` to numerical tolerance.
- `verifier_passed=true`; the independent verifier recomputes route feasibility, load feasibility, station feasibility, route duration, final inventories, `G`, `P`, and `G + lambda P`.
- `solves_original_objective=true`.
- The method-specific certificate closes the original objective, not just a diagnostic subproblem.

## Method Scopes

`gcap-frontier` is the main paper algorithm and is reported as `method_scope=original_bpc`, `is_bpc=true`. It solves the original objective only when the full Gini frontier is certified.

`tailored` is an auxiliary exact portfolio and is reported as `method_scope=original_compact`, `is_bpc=false`. It may use complete route-load enumeration on small cases or a strengthened compact fallback. Its success is not BPC success.

`cplex` with the plain baseline is reported as `method_scope=plain_cplex`, `is_bpc=false`. It is the benchmark compact exact MILP.

`gcap-cg`, `gcap-tree`, `gcap-branch`, `master`, `pricing`, `cuts`, `branching`, and restricted path/column pools are `subproblem` or `diagnostic` methods. They do not certify the original problem unless wrapped inside a complete full-frontier certificate.

## Full Frontier BPC Certificate

For `gcap-frontier`, `status=optimal` is valid only when:

- A feasible incumbent exists and passes the verifier.
- The covered Gini range includes the full improving range, currently `G in [0, min(incumbent_objective, (V-1)/V)]` unless a tighter valid range is proven.
- `frontier_covers_all_improving_gini_values=true` and `frontier_range_certificate_scope=original_full_improving_range`.
- Every interval is complete, empty, or certified by a valid lower bound at least as large as the incumbent.
- `unresolved_intervals=0`.
- `invalid_bound_intervals=0`.
- Every branch-price node used for a branch-price lower bound has exact pricing closure.
- The aggregated frontier lower bound reaches the incumbent objective.

The current JSON fields that demonstrate these conditions are:

- `method_scope`, `solves_original_objective`, `is_bpc`, `certificate_type`.
- `status`, `objective`, `lower_bound`, `upper_bound`, `gap`.
- `result_file`, `log_file`, and `stop_reason`.
- `verifier_passed`, `certified_original_problem`.
- `unresolved_intervals`, `invalid_bound_intervals`, `pricing_closed_nodes`, `open_nodes`.
- `bpc_workers`, `pricing_threads`, `parallel_frontier`, `parallel_nodes`, and `parallel_tasks` for threaded BPC runs.
- `wall_time_seconds` for elapsed wall time and `aggregate_worker_time_seconds` for summed worker activity; aggregate timing may exceed wall time under parallel BPC.
- `notes`, which include interval coverage, per-interval completion, valid lower bounds, and frontier summary.
- `gini_max_possible`, `relevant_gini_upper_for_improvement`, and `covered_gini_upper_bound` for Gini range audit.

For certified full-frontier runs, the top-level JSON fields are normalized to `lower_bound=upper_bound=objective` and `gap=0` after the full certificate closes within the frontier tolerance. The result may also report `raw_frontier_lower_bound_before_tolerance_normalization` and `certificate_tolerance` for auditability, while interval notes retain the per-interval lower-bound details.

Feasible incumbents may come from heuristics, compact auxiliary solves, or `--incumbent-json`. Imported or seeded routes must pass the independent verifier and may be used only as a warm start or incumbent cutoff. They do not contribute any lower-bound certificate, and they must not be reported as BPC success unless the full frontier conditions above also hold.

If `--gini-cap` truncates the frontier below `min(incumbent_objective,(V-1)/V)` without a separate bound-fathoming proof for the omitted range, the run is a capped diagnostic. It may close every requested interval and still have `certified_original_problem=false`.

`--movement-bound-audit true` computes relaxation bounds with and without movement-domain tightening and uses the larger valid value. This is a lower-bound audit and strengthening device, not a separate certificate. The relevant fields are `relaxation_lb_no_movement`, `relaxation_lb_with_movement`, `relaxation_lb_used`, `movement_audit_intervals`, `movement_audit_bound_improved_count`, and `movement_audit_bound_worse_count`.

Support-duration pricing pruning is exact only as a pricing pruning rule. A forbidden support subset may be used only when a metric-closure route-duration lower bound plus minimum handling time proves that no feasible route-load column can contain that subset. The fields `support_duration_cuts_generated`, `support_duration_pruned_labels`, and `support_duration_pruned_columns` are diagnostic/pricing efficiency fields; they never replace exact pricing closure.

BPC-owned incumbent route pools are heuristic upper-bound devices. Candidate columns with missing operation vectors are skipped before pool insertion or route-pool DFS use. This prevents address errors in incumbent generation and removes no lower-bound columns from the RMP or pricing certificate.

Verified incumbent route columns may be inserted into a fixed-interval restricted master even when the incumbent's true Gini value lies outside that interval. This is certificate-neutral because each inserted object is only a feasible route-load column. The incumbent itself is accepted only as an interval incumbent if its verified `G` lies in the interval.

Generic singleton and two-station pickup/drop warm-start columns are also certificate-neutral. They enlarge the restricted column pool but do not replace the exact pricing proof. A restricted-master result is still not a node certificate until exact pricing proves no missing negative-reduced-cost route-load column exists under the active branch and cut rows. The CLI option `--gcap-warmstart seed|sparse|full` controls this pool: `seed` uses only verified seed-route columns plus priced columns, `sparse` adds target-oriented singleton and pickup/drop pair quantities, and `full` enumerates all feasible one- and two-station operation quantities for the warm-start pool.

Adaptive interval splitting via `--frontier-refine-splits` is certificate-neutral: a parent interval may be replaced only by children that exactly cover the parent range. Children inherit the parent's valid lower bound and may receive stronger relaxation bounds. The final global lower-bound ledger must ignore replaced parents and account for every child interval.

Focused splitting via `--frontier-split-batch` is also certificate-neutral. It changes only which unresolved intervals are refined first, normally by lowest current lower bound. It does not remove intervals from the final ledger and cannot by itself certify the original problem.

Retry reserve via `--frontier-retry-reserve` is certificate-neutral. It stops adaptive splitting early to preserve wall time for branch-price retry. The final ledger must still account for every active interval, and no interval is certified merely because splitting stopped.

Best-bound branch node scheduling and best-bound frontier retry scheduling are also certificate-neutral. They spend finite runtime on the open branch node or unresolved interval with the smallest valid inherited lower bound. A retry tree may stop early when its valid open-node lower bound reaches the next unresolved interval's lower bound; that stopped interval remains unresolved and open nodes remain counted. A node or interval is counted as certified only when exact pricing closes the relevant branch-price tree, the interval is empty, or a valid lower bound reaches the incumbent objective.

Optional multi-column pricing via `--gcap-pricing-columns N` is certificate-neutral. It may add several negative route-load columns discovered during an exact pricing enumeration. Early negative stopping in this mode may be used only to add a column and continue column generation; it cannot certify a node. A branch-price node is closed only after exact pricing proves that no negative route-load column remains.

Closed-column dominance via `--column-dominance true --column-dominance-mode exact` is exact only under projection-equivalence conditions: same vehicle, same station mask, and same signed operation vector, with no path-dependent objective coefficient in the active master. If path-dependent terms are present, the implementation must use Pareto mode over duration, travel, and reduced/objective coefficient. Dominance changes only the route-load column representation and does not relax any certificate condition.

The inventory-ratio projection bound and incumbent penalty-budget domain tightening are valid only when their inventory intervals come from globally valid necessary conditions, not from an incomplete restricted column pool. Restricted-pool intervals may be logged as diagnostics but cannot certify an original BPC lower bound.

Reused columns from any frontier cache are certificate-neutral only because they are feasible route-load objects. They enlarge the restricted master but do not replace exact pricing closure for the current node duals. The current `--frontier-column-cache` switch is logged but the cache is intentionally disabled in certificate-producing runs.

Imported HGA/TGBC or other heuristic incumbents may provide only a verified upper bound. They must pass the independent verifier before they can update `upper_bound` or be used in incumbent cutoff, and they never provide a lower-bound certificate.

Optional initial frontier parallelism via `--parallel-frontier true --bpc-workers N` is certificate-neutral in the current build. It solves independent initial Gini intervals with a fixed incumbent copied before worker launch and merges interval records only after workers join, in deterministic interval order. The current queue is deterministic and ordered by proximity to the incumbent Gini value. Internal command-line CPLEX calls in restricted masters and inventory relaxations remain single-threaded. `--parallel-nodes` is accepted and logged but disabled; no branch-node parallel certificate is claimed.

Branch-closure pruning in pricing is certificate-neutral and exact. Required-together branches define station components that must be entirely present or absent in a final column. The pricing oracle may prune a partial route-load label when the required closure of its visited set would include a forbidden or disallowed station, violate a forbid-together branch, or cannot still visit required missing stations and return to the depot within the route time limit. The closure test removes only partial labels that cannot extend to any branch-feasible route-load column.

## Fixed Gini-Cap Subproblems

For a fixed cap or interval, the valid linearization is:

```text
G <= gamma iff H <= V * gamma * S
```

A fixed-cap tree can certify only its fixed-cap or fixed-interval subproblem. It is not a global certificate for `G + lambda P` unless all relevant Gini intervals are covered and aggregated by `gcap-frontier`.

The pricing oracle may use label-setting dynamic programming over elementary visited sets, last station, vehicle load, and total pickup, with Pareto dominance on reduced cost and travel time. This remains an exact pricing oracle because future feasibility and reduced-cost extensions depend only on these resources and the visited set; dominated labels cannot produce a better feasible completion.

Subset-row cuts use the valid set-packing inequality for odd station subsets `S`:

```text
sum_c floor(|A_c intersect S| / 2) z_c <= floor(|S| / 2).
```

The implementation separates triples and size-five subsets in the active restricted master and prices them with the same column coefficient. These cuts strengthen fixed-interval lower bounds but do not by themselves certify the original problem outside a complete frontier certificate.

Each interval also has the valid floor bound:

```text
objective = G + lambda P >= G >= interval_floor
```

This bound is now included in frontier lower-bound reporting. It does not close the low-G interval that starts at zero.

The frontier also uses a final-inventory pickup/route/Gini relaxation when it solves. This LP enforces station capacity bounds, no bike creation, exact station flow conservation

```text
pickup_i - drop_i + final_inventory_i = initial_inventory_i,
```

the depot-return capacity lower bound

```text
sum_i final_inventory_i >= sum_i initial_inventory_i - sum_k Q_k,
```

single-station operation capacity bounds

```text
pickup_i <= max_k Q_k * visit_i
drop_i <= max_k Q_k * visit_i,
```

and the operation-time pickup budget implied by

```text
operation_time_k = (tau_pick + tau_drop) * total_pickup_k,
```

and the interval Gini cap/floor. It also adds necessary route-reachability inequalities using singleton station cuts and subset station-visit cuts with shortest-path metric closures, so the cuts remain lower bounds on route travel. For `V<=12`, all station subsets are cut and final inventories, pickup/drop quantities, and visit indicators are integer. For larger instances the implementation caps subset size and keeps this relaxation continuous to control size.

The current interval relaxation also includes station-operation mode/projection rows:

```text
pickup_i + drop_i <= U_i * visit_i
pickup_i + drop_i >= visit_i
U_i = max(min(initial_i, Qmax), min(capacity_i - initial_i, Qmax)).
```

The upper row is valid because every original visited station has one operation mode: it either picks up bikes from the initial inventory or drops bikes into residual station capacity, and a single vehicle cannot operate more than `Qmax` bikes at that station. The lower row is a projection-strengthening convention for the inventory relaxation: a zero-operation station visit can be deleted without changing any final inventory, ratio, Gini term, or satisfaction penalty, and deletion can only make the route side easier. Therefore every projection-relevant original solution has an equivalent representation satisfying `pickup_i + drop_i >= visit_i`. These rows strengthen lower-bound relaxations but do not supply an incumbent or a complete BPC certificate by themselves.

For `V<=12` with a small vehicle count, the same relaxation also adds a complete route-mask duration/load assignment relaxation. For each vehicle, one binary mask is selected from the full set of travel-feasible station masks, station visits are assigned to selected masks, station pickup/drop quantities are assigned to vehicles, and each selected mask satisfies:

```text
shortest_depot_cycle(mask) + (tau_pick + tau_drop) * assigned_pickup <= T
assigned_drop <= assigned_pickup
assigned_pickup - assigned_drop <= Q_k.
```

This is a necessary-condition relaxation over all visit masks, not a restricted route-load solution pool. It can strengthen interval lower bounds or prove incumbent-cutoff infeasibility, but it does not replace the route-load branch-price certificate when an interval is not bound-fathomed.

The implementation must not use an incomplete route-mask list as if it were complete. Current certificate-producing runs enable complete route-mask enumeration only through the configured `--route-mask-max-v` threshold, defaulting to `12`; for larger `V`, route-mask rows are disabled unless a complete enumeration or a proved catch-all relaxation is implemented.

The relaxation minimizes a linear lower estimator of `G + lambda P`, so its optimum is a valid lower bound for every route-feasible solution in that interval. If the small integer relaxation hits a time limit, CPLEX's MIP best bound is still a valid lower bound for the integer relaxation, and therefore also a valid lower bound for the original interval.

With incumbent cutoff `UB` and interval floor `gamma_L`, the relaxation may add:

```text
P <= (UB - gamma_L) / lambda.
```

This is valid for proving the original interval because any excluded solution has objective `G + lambda P >= gamma_L + lambda P > UB`. The reported lower bound is then capped as `min(relaxation_bound, UB)`, which is a valid unconditional interval lower bound. If this cutoff relaxation is infeasible, the interval is bound-fathomed at `UB`; it is not claimed to be empty. If the unconditional relaxation is infeasible without a cutoff budget, the original interval is empty under necessary inventory/resource conditions and may be bound-fathomed.

When the relaxation uses the linear estimator `H/(V*S_upper)` for the Gini term, `S_upper` must be a valid upper bound on `sum_i r_i` for the same incumbent-improving relaxation domain. The implementation computes this bound with station capacities, the incumbent penalty budget when active, and the depot-return station-sum floor `sum_i final_inventory_i >= sum_i initial_inventory_i - sum_k Q_k`.

## Comparison Rule

Do not report a certified-optimal speedup unless both methods have `certified_original_problem=true`. If CPLEX times out with a positive gap, report:

```text
BPC certified in X seconds; CPLEX did not certify within Y seconds, final CPLEX gap = Z.
```

For the existing `results/compare_v10_m2_average.csv`, the correct wording is:

```text
tailored certified within 55.77s; CPLEX did not certify within 120.16s, final CPLEX gap = 0.0532958.
```

The CSV `speedup=2.1547` is not a certified-optimal speedup because CPLEX did not close.

## BPC-Owned Incumbents And Diagnostic Incumbents

A BPC-owned incumbent generator may be used in pure BPC runs only as an upper-bound source. The generated routes must pass the independent verifier before they can set `upper_bound` or an incumbent cutoff. They do not provide lower bounds and do not relax any certificate requirement.

The implemented pure-BPC incumbent modes include greedy route-load construction, fixed-seed randomized greedy starts, and exact load-decoded local search over station assignment and signed operation quantities. The local-search decoder fixes a vehicle's signed station operations and solves an exact dynamic program over visited mask, last station, and vehicle load before accepting a route. Current local-search neighborhoods include station relocate/resize and pairwise swap-style reassignment moves. The optional route-column pool master is a restricted incumbent master over already verified route columns; it is not a restricted-pool lower-bound certificate. A run using this pool is still globally optimal only if the full frontier certificate closes.

A run that imports a verified plain-CPLEX incumbent is a diagnostic incumbent-cutoff run. It may be useful to test whether the frontier lower-bound machinery can close around a strong incumbent, but it must not be reported as pure BPC performance and must not be compared as a BPC-vs-CPLEX speedup.

The final interval closure phase is certificate-preserving only when each focused interval is closed by exact pricing or bound-fathomed by a valid lower bound. If a focused pass leaves `open_nodes>0` or `unresolved_intervals>0`, the global BPC status remains not certified, regardless of incumbent quality.

Strengthened compact branch-and-cut runs are `method_scope=original_compact`, not BPC. They can certify the original problem when their compact MIP gap closes and the verifier passes, but their success must be reported as an auxiliary exact fallback result rather than a full-frontier route-load BPC certificate.

## Current Certified Target Instances

As of 2026-06-14, pure BPC has full original-problem certificates for:

- `test_data_V10_M2_average.txt`: `results/dyn4_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`.
- `test_data_V10_M1_average.txt`: `results/closure3600_v10_m1_average_strong_bpcseed.json`.
- `test_data_V12_M1_average.txt`: `results/closure7200_v12_m1_average_strong_bpcseed.json`.

All three have `status=optimal`, `gap=0`, `lower_bound=upper_bound=objective`, `unresolved_intervals=0`, `invalid_bound_intervals=0`, top-level `open_nodes=0`, and `verifier_passed=true`.

`test_data_V10_M2_low.txt` is not certified by pure BPC, but it is certified by the auxiliary strengthened compact fallback in `results/alt_strengthened_v10_m2_low_1200s.json`. This is an `original_compact` certificate, not a BPC certificate.

`test_data_V12_M2_average.txt` remains open. The current portfolio incumbent is `0.366168793171`, the current valid portfolio lower bound is `0.350523627890`, and the portfolio gap is about `0.0427266`.

## 2026-06-20 Round-2 Certificate Warnings

- Incomplete frontier `lower_bound` is now a valid progress metric from the interval ledger. It is not a certificate unless every relevant interval is closed, empty, or bound-fathomed and the minimum interval lower bound reaches the incumbent objective.
- Duplicate negative pricing projections cannot close a node. If pricing returns only negative columns that are already represented or dominance-filtered, the node remains unresolved unless exact pricing proves no missing negative projection exists.
- Movement-domain tightening is global only because it is based on route-duration/travel lower bounds, handling time, station inventory/space, and truck capacity. It must not be replaced by restricted-pool reachability data for certificate-producing bounds.
- Relaxation-cache reuse is valid only under an exact key match. Cached interval relaxations do not replace exact branch-price pricing closure.

## 2026-06-20 Round-3 Certificate Warnings

- Full BPC coverage is checked against `min(incumbent_objective,(V-1)/V)`, not against the incumbent objective alone. A capped `--gini-cap` run below this range is diagnostic unless omitted intervals are separately fathomed.
- Movement-bound audit may use the maximum of the no-movement and with-movement valid relaxation bounds. It is still only a lower-bound progress mechanism until the full frontier closes.
- Support-duration pruning can remove pricing labels only when metric-closure route-duration plus minimum operation time proves the support impossible. It does not replace exact pricing closure.
- The relaxation cache omits time budget from the key. Larger-budget requests after a cache hit are recomputed and logged as partial hits; the stronger valid bound is retained.
- BPC-owned incumbent pools skip malformed route-load candidates with missing operation vectors. These candidates are heuristic upper-bound candidates only, so skipping them cannot weaken a lower-bound certificate.

## 2026-06-21 Round-4 Certificate Warnings

- The strengthened support-duration rule uses
  `cycle_lb(S) + (pickup_time + drop_time) * ceil(|S|/2)`. It is valid only when
  `cycle_lb` is a non-overestimating route travel lower bound and station visits
  in certificate-producing columns imply nonzero operation. It is a pruning rule,
  not a closure certificate.
- Route-mask support-duration pruning may remove only masks whose entire support
  is impossible for the current vehicle by the same duration lower bound. The
  complete route-mask ledger must still cover every remaining relevant mask.
- Imported HGA-style incumbents, route JSON/CSV incumbents, compact seeds, and
  compact-CPLEX seeds are upper bounds only after the independent verifier
  accepts them. They may shrink the improving Gini range and cutoff domains, but
  they never provide lower-bound evidence.
- Focused min-LB retry changes only which unresolved interval receives more
  branch-price time. It does not remove intervals from the final ledger and does
  not certify a positive-gap run.
- The exact support-feasibility oracle remains disabled by default. No support
  cut may be generated from a timeout, sampled infeasibility, or heuristic route
  failure.

## 2026-06-21 Round-5 Certificate Warnings

- Focused min-LB retry changes only which unresolved frontier interval receives
  remaining branch-price time. It does not remove intervals from the ledger, and
  a positive-gap focused-retry result remains noncertified.
- The route-column pool incumbent master is a restricted primal heuristic. A
  verified route-pool solution may update `upper_bound`, but the restricted
  pool cannot provide a global lower-bound certificate.
- Interval tree surrogate metrics must not be confused with the original
  objective. Every integer candidate from an interval is verifier-checked and
  evaluated under `G + lambda P`; rejected candidates must carry a reason.
- Pickup-drop compatibility flow is a valid inventory-relaxation strengthening
  only when pairs are removed by a route-duration lower-bound proof. It is not
  an optimality certificate by itself, and if no pair is proven incompatible it
  may add audit statistics without improving the lower bound.
- The support-feasibility oracle remains optional and disabled in certificate
  runs for this pass. No heuristic or timed-out support failure may add a cut.

## 2026-06-21 Round-6 Certificate Warnings

- `--bpc-incumbent auto` and `--bpc-incumbent best-of-all` select the best
  independently verified route plan among bounded primal generators. The selected
  route set is an upper bound only. It may tighten cutoffs and domains but never
  supplies lower-bound evidence.
- The frontier route-column pool now harvests warm-start, priced, and integer
  leaf columns from BPC trees. The restricted route-pool incumbent master remains
  a primal heuristic over a subset of feasible columns. It cannot certify a lower
  bound, and failure to improve the incumbent proves nothing.
- Focused relaxation intensification is certificate-neutral. It reruns a valid
  relaxation on the current minimum-LB unresolved interval and keeps the maximum
  valid lower bound. If the frontier remains positive-gap, the result is still
  noncertified.
- Pickup-drop transfer-cap flow is a relaxation strengthening only. Pair caps
  must be derived from metric/travel lower bounds, handling time, truck capacity,
  pickup availability, and drop residual capacity. Heuristic route failures must
  not set a cap to zero.
- Time-to-gap progress logs are reporting aids. Longer runtime, a better
  incumbent, or a higher lower bound does not imply an original-problem
  certificate without full frontier closure and gap zero.

## 2026-06-21 Round-7 Certificate Warnings

- Periodic progress logs now include initial, interval, adaptive-split,
  focused-intensification, route-pool, and final checkpoints. They are
  convergence traces only. A decreasing trace does not certify the original
  problem.
- Adaptive interval splitting preserves certificates only when child intervals
  exactly cover the parent interval without gaps or overlaps. The active
  frontier lower bound is the minimum over leaf intervals.
- Route-mask operation-budget cuts require a non-overestimating depot-cycle
  travel lower bound and positive handling unit `pickup_time + drop_time`.
  If those conditions are not met, the cut must be disabled or relaxed.
- Focused intensification with splitting changes time allocation and interval
  partitioning only. It does not remove unresolved intervals from the final
  ledger.
- Time-limited relaxation or branch-price bounds may be reported as valid
  progress only when their solver status and lower-bound meaning are valid.
  They are not certificates unless the full frontier ledger closes and all
  exact-pricing requirements are satisfied.

## 2026-06-21 Round-8 Certificate Warnings

- Vehicle-indexed operation and transfer-flow rows strengthen the
  inventory/route-mask relaxation. They are valid lower-bound aids, not
  standalone certificates.
- Focus-only interval runs have certificate scope
  `diagnostic_interval_only`. They may close or tighten the selected interval
  but cannot certify the original problem unless the rest of the frontier ledger
  is also closed or validly fathomed.
- Regenerated V8/V10 instances are deterministic engineering benchmarks unless
  they are proven identical to historical source inputs. Do not compare them as
  historical paper targets.
- Bound-fathomed frontier certificates may have no branch-price tree closure
  rows. Exact pricing closure is required only for intervals whose certificate
  uses branch-price lower bounds; all bound-fathomed intervals must still have
  valid relaxation bounds, zero unresolved intervals, zero invalid intervals,
  zero open nodes, a verifier pass, and gap zero.
- Time-limited 1200s convergence rows remain noncertified when the frontier
  ledger has positive gap or unresolved intervals, regardless of gap decrease.

## 2026-06-21 Round-9 Certificate Warnings

- Focus-only interval runs can target an explicit Gini range or a leaf parsed
  from a previous frontier result. They report
  `focus_interval_certificate_scope=diagnostic_interval_only` and cannot certify
  the original problem unless their bounds are merged into a compatible full
  frontier ledger whose every relevant leaf is closed, empty, or validly
  fathomed.
- Imported focus-interval bounds are accepted only as lower-bound evidence for
  the covered interval. They are certificate-safe only when the instance,
  lambda/objective convention, Gini range, incumbent-cutoff meaning, and active
  route/load restrictions are compatible. If the import covers a subrange, the
  parent frontier leaf must be split without gaps or overlaps before using the
  imported bound.
- Final-inventory branching is exact because station final inventories are
  integer in every original feasible route-load solution; the two branches
  `Y_i <= floor(Y_i*)` and `Y_i >= ceil(Y_i*)` partition all integer
  completions of a fractional LP point.
- Operation-mode branching is exact because pricing and node column screening
  enforce the selected signed-operation restrictions. Forbid-pickup and
  forbid-drop children are search branches, not primal heuristics.
- Strong/reliability branch selection changes only which valid branch is explored
  first. It does not change the lower-bound certificate requirements. The
  current `strong` mode is a bounded scoring implementation, not a full
  child-LP strong-branching certificate.
- Positive-gap focus-only, imported-bound, or full-frontier runs remain
  noncertified even when they substantially improve the active lower-bound
  ledger.

## 2026-06-22 Round-10 Certificate Warnings

- Pricing closure requires exact pricing with no negative reduced-cost column
  under the current true RMP duals. If `pricing_completed_exactly=false`, if
  `pricing_remaining_negative_rc<0`, or if duplicate-negative projection
  blockage remains unresolved, then `pricing_closure_certified_exact` must be
  false.
- A valid inventory/route/Gini relaxation lower bound can still be reported for
  an interval whose pricing is not closed. That interval is not a
  pricing-closed BPC certificate unless exact pricing closure is separately
  proven.
- Frontier resume states are valid only after compatibility checks on instance,
  lambda, route duration, vehicle capacities, handling times, Gini interval, and
  active restrictions. A resume run that rebuilds from exported columns and
  bounds is certificate-neutral but does not certify anything by itself.
- Exact-CG continuation is exact only when the final RMP is verified by exact
  true-dual pricing. Extra pricing columns, multi-column output, and
  diversification are acceleration mechanisms, not closure evidence.
- Stabilized dual pricing is a column-discovery heuristic. It cannot be used as
  a node-closure certificate; final closure must use the true current RMP duals.
- Longer V12 runs and progress traces remain convergence diagnostics unless
  the full frontier ledger closes, all relevant exact-pricing requirements are
  satisfied, the verifier passes, and the final gap is zero.

## 2026-06-22 Round-11 Certificate Warnings

- Every frontier interval must report a certificate basis. Exact pricing
  closure is required only when the basis is `pricing_closed_bpc_tree`. It is
  not required for `gamma_floor_skip`, `incumbent_cutoff`, or
  `inventory_route_gini_relaxation_fathomed`, provided the non-pricing bound is
  valid and the interval is truly skipped or fathomed.
- The full result must report whether all active intervals are accounted for,
  whether any interval requires pricing closure, whether those closures are
  available, and the rejection reason when the run is not certified.
- Iterative frontier closure automates selecting the current minimum-LB
  unresolved leaf, focusing closure effort there, and updating the same ledger.
  It is a runtime allocation strategy, not a separate certificate.
- Open-node resume must distinguish exact tree continuation from warm restart.
  The current partial export stores interval metadata, lower bounds, column
  counts, and open-node counts, so it is reported as
  `open_node_state_resume_exact=false`.
- Final pricing verifier checkpoints are progress artifacts only. A checkpoint
  or time-limited verifier run cannot set `pricing_closure_certified_exact=true`
  unless true-dual exact pricing has completed with no negative reduced-cost
  column remaining.

## 2026-06-22 Round-12 Certificate Warnings

- `StationSet` is a representation change only. It is certificate-neutral when
  the same visited-station set is preserved, but any remaining integer-mask or
  all-subset feature must be guarded for large V.
- Relaxed ng-route/DSSR pricing cannot close a node unless DSSR has completed
  an exact proof or a separate true-dual exact final pricing verification has
  completed. If `dssr_incomplete` or a pricing time limit is reported, the run
  is not pricing-closed.
- Stabilized duals are column-discovery duals only. They may guide candidate
  generation, but closure and reduced-cost certificates must use the true RMP
  duals.
- External or HGA/TGBC incumbents are upper bounds only after independent
  route verification. They may improve pruning but never certify a lower bound.
- V50/V100 scalability rows are diagnostics unless the full original
  certificate protocol closes. Disabled all-subset route-mask relaxations must
  be listed in `unsupported_large_instance_features`, and no positive-gap or
  relaxed-pricing row may be labeled optimal.

## 2026-06-22 Round-13 Certificate Warnings

- A requested `hybrid` or `ng-dssr` BPC pricing row is certificate-valid only
  when every closure-relevant node either has completed DSSR exactness or a
  completed true-dual exact pricing verification with no negative reduced-cost
  column remaining.
- Fallbacks must be reported through `bpc_pricing_engine_fallbacks` and notes
  such as `pricing_engine_fallback_reason`. A silent fallback cannot support a
  paper certificate claim.
- Stabilized dual pricing is a BPC column-discovery accelerator only. Returned
  columns must be evaluated under true RMP duals before insertion, and
  stabilized pricing cannot close a node.
- Large-instance rows with disabled all-subset route-mask relaxations,
  incomplete DSSR, or diagnostic pricing scope must remain noncertified even
  if they produce useful incumbents or route columns.
- `large_lb_mode=inventory-only` and `movement-projection` may report valid
  global lower-bound progress. `column-pool-relaxation` over a subset of
  generated columns is restricted-pool diagnostic evidence unless exact pricing
  closure proves no missing columns.
- External/HGA incumbents and converted incumbent files are upper bounds only
  after independent route verification. Malformed or unverifiable files must be
  rejected without changing the incumbent.
