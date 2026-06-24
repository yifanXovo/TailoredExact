# ExactEBRP Attempt Log

Date: 2026-06-10

All runs below used `lambda=0.15`, `T=3600`, `unit_pick_time=60`, `unit_drop_time=60`, and `threads=4` unless noted.

## Data and convention checks

- Parser reads the Hybrid GA text format.
- To match the current Hybrid GA parser, legacy weights with maximum value exactly `10.0` are scaled by `0.1`.
- Distances are rebuilt from `points` with speed factor `1.5`, matching `Instance_Generator.cpp`; serialized rounded distance matrices are used only when points are absent.
- The old `Solver_Exact_CPLEX.cpp` was inspected. It used a Gini product linearization but its duration expression counted station pickup/drop time and did not explicitly include final depot unloading. This project uses the exact conservation identity `travel + (tau_pick + tau_drop) * total_pickup <= T`.

## Route-load enumeration attempt

Implemented:

- Elementary route-load columns with signed operation vector `q_i`, pickup positive and drop negative.
- Vehicle load feasibility, station inventory feasibility, station-disjoint route supports, and route duration.
- Deduplication by operation vector with the shortest feasible route retained.
- Exact station-disjoint master search over final inventories when all columns are available.

Observed bottleneck:

- `test_data_V8_M2_average.txt`
- Initial DFS interleaving route extension and operation quantities exceeded the tool timeout and left a stale process.
- Refactored enumeration to separate route-order enumeration from operation assignment, but a 1-second diagnostic still generated about `1,447,154` deduplicated vehicle columns before completing vehicle 0.
- Temporarily allowed exhaustive materialized enumeration on `test_data_V8_M1_low.txt` to test whether a single-vehicle V=8 sample could close. It did not: the run returned `time_limit` after generating `49,993,115` deduplicated columns and `79,889,022` raw columns, with no certificate. The partial-column timeout path was then fixed so timed-out enumeration discards local partial columns instead of spending minutes converting and merging them after the limit.
- Conclusion: full materialized route-load enumeration is implemented but not currently competitive for these V=8 M2 generated samples. The portfolio therefore guards this mode by problem size and selects the strengthened compact exact fallback for V>=8 or M>=2.

Reason for abandonment as primary V=8 path:

- Column volume, not parser or master correctness.
- Continuing to materialize all route-load columns would risk memory blowup before producing a certificate.

## Inventory branch-search with exact route oracle

Implemented after the initial report:

- Branch over station final inventory values within `[max(0, initial_i-Qmax), min(C_i, initial_i+Qmax)]`.
- Use a valid partial lower bound from interval relaxations of `P` and the Gini numerator/denominator.
- At leaves, check exact route-load feasibility by partitioning active stations across vehicles and solving a Held-Karp-style load DP for each vehicle subset.
- If the tree exhausts, the certificate is non-compact and independent of CPLEX.

Observed bottleneck:

- `test_data_V8_M2_average.txt`
- A 20-second diagnostic did not close the tree: `46,694,400` inventory nodes and `1,186,561` route checks.
- A 2-second default probe was also too expensive relative to the benefit, so the automatic portfolio now runs this exact path only for `V<=7`. The V=8 diagnostic remains useful evidence for the next optimization step.
- Added a route-duration partition relaxation and explicit CLI probe controls. With `--inventory-probe-max-v 8 --inventory-probe-seconds 5`, `test_data_V8_M2_average.txt` processed `4,505,600` inventory nodes and `0` full route checks in `5.01334s`; it still did not exhaust the tree.
- Added an incumbent-backed proof mode: the strengthened compact solve supplies a feasible incumbent, then the inventory-route proof tree tries to exhaust. With `--inventory-probe-seconds 5`, the same V=8 instance processed `25,935,872` nodes and `0` full route checks in `5.00182s`; it still did not close.
- Applying the route-duration relaxation from the first active station rather than only larger supports did not materially improve the proof: a 5-second run processed `26,394,624` nodes and `0` route checks. The remaining bottleneck is objective-space branch volume, not route feasibility checking.
- Added incumbent-aware domain filtering, discrete suffix penalty lower bounds, and proof-domain instrumentation. A 2-second incumbent-backed run processed `9,814,016` proof nodes with `domain_values=314` and `max_domain_size=54`; it still did not close. Dynamic penalty child-pruning did not materially reduce the node rate in a 5-second run (`26,591,232` proof nodes).
- Added a valid Gini numerator "star" lower bound using the triangle inequality: if two ratio intervals are forced apart by gap `g`, then `H >= (V-1)g`. On the same V=8 instance, a 2-second proof run processed `11,862,016` nodes and still did not close; this did not materially change the bottleneck.
- Added a Lorenz/order-statistic interval lower bound for `H`: positive sorted-ratio coefficients use lower bounds on order statistics, and negative coefficients use upper bounds. This improved the 2-second V=8 incumbent-backed proof run to `7,208,960` proof nodes, but a 10-second run still did not close (`39,190,528` nodes, `0` route checks).
- Added suffix feasibility pruning for remaining net pickup/drop balance and minimum remaining pickup-time consumption, including child-level pruning before recursion. On the same V=8 incumbent-backed proof diagnostic, a 2-second run processed `9,568,256` nodes, `0` route checks, `domain_values=314`, and `max_domain_size=54`; the tree still did not close. This confirms that the current hard region is the broad objective/final-inventory domain before route feasibility is reached.
- Strengthened that suffix pruning into an exact dynamic-programming lower bound on remaining satisfaction penalty subject to remaining pickup capacity and required net pickup/drop balance. On `test_data_V8_M2_average.txt`, a 2-second incumbent-backed diagnostic still did not close (`9,224,192` nodes, `0` route checks). The bound is valid but not strong enough to change the bottleneck.
- Parallelized the inventory proof over disjoint root station-domain branches. With `threads=4`, `test_data_V8_M2_average.txt` processed `33,325,056` proof nodes in a 2-second incumbent-backed diagnostic, but still did not close and still reached `0` route checks.
- Reordered proof branching by descending ratio-interval width, then domain size, then weight, to tighten interval Gini bounds earlier. With `threads=4`, the same 2-second diagnostic processed `23,335,109` nodes and still did not close. On `test_data_V8_M1_high.txt`, a 30-second threaded incumbent-backed proof processed `329,596,928` nodes and still did not close.
- Added a suffix DP for the maximum feasible remaining ratio sum `S` under the same pickup-capacity and net-balance relaxation used by the penalty suffix bound. This tightens the Gini denominator in partial nodes. On `test_data_V8_M2_average.txt`, a 2-second threaded diagnostic processed `16,992,410` nodes and still did not close.
- Added dynamic ratio-interval tightening from the residual satisfaction-penalty budget implied by `P < incumbent/lambda`. On the same 2-second diagnostic, it processed `17,139,866` nodes and still did not close, so the effect was neutral on this sample.

## Exact pricing oracle

Implemented after the initial report:

- Added `include/Column.hpp`, `include/Pricing.hpp`, and `src/Pricing.cpp`.
- The pricing oracle enumerates elementary route-load columns exactly for one vehicle, including integer pickup/drop choices, load feasibility, station capacity feasibility, and the operation-time identity `duration = travel + (tau_pick + tau_drop) * pickup`.
- For each fixed route sequence, the operation subproblem is now solved by an exact dynamic program over `(position, load, pickup_total)` instead of naive recursive quantity enumeration. Because reduced cost is linear in the signed station operations, keeping only the best operation vector for a fixed route is exact for pricing.
- The oracle accepts generic visit and operation dual coefficients and returns the best reduced-cost column plus an exact `complete` flag. This is a reusable BPC component, but it is not yet connected to a full restricted master / branch-price tree.
- Added `--method pricing` as a diagnostic CLI path. It minimizes one-column route duration with nonnegative reduced-cost pruning, reconstructs the selected route, and runs the independent verifier.
- `test_data_V8_M2_average.txt`: pricing diagnostic completed for both vehicles in `0.0000991s`, generated `6` route candidates after DP pricing, and selected route `[0,5,0]` with pickup `1`, pricing reduced cost/duration `196.179910901`.
- `test_data_V10_M2_average.txt`: pricing diagnostic completed for both vehicles in `0.0000348s`, generated `6` columns, and selected route `[0,4,0]` with pickup `1`, pricing reduced cost/duration `207.156335011`.
- Added Ryan-Foster child-node restrictions to exact pricing:
  - `forbid_together_pairs` rejects columns containing both branch stations.
  - `require_together_pairs` rejects columns containing exactly one of the branch stations.
- Added `--method pricing-branch` as a diagnostic CLI path. It prices under both child restrictions for pair `(1,2)`, using high non-branch station visit costs so the required-together child must produce a column containing both stations.
- `test_data_V8_M2_average.txt`: required-together pricing produced a column containing both stations with reduced cost `627.195774064`; forbidden-together pricing produced a column not containing both, reduced cost `400.005618817`; output `results/v8_m2_average_pricing_branch_diag.json`.
- `test_data_V10_M2_average.txt`: required-together pricing produced a column containing both stations with reduced cost `735.174209169`; forbidden-together pricing produced a column not containing both, reduced cost `590.183901371`; output `results/v10_m2_average_pricing_branch_diag.json`.

## 3-subset-row cut separator

Implemented after the initial report:

- Added `include/Cuts.hpp` and `src/Cuts.cpp`.
- The separator implements the valid row cut `sum_c floor(|A_c intersect S|/2) z_c <= 1` for every station triple `S`.
- Added `--method cuts` as a diagnostic CLI path. It builds a feasible fractional pair-column triangle with `z=0.5` on each pair, then runs the separator.
- `test_data_V8_M2_average.txt`: diagnostic columns on triple `(1,2,4)` produced `lhs=1.5`, `rhs=1`, violation `0.5`; output `results/v8_m2_average_cuts_diag.json`.
- `test_data_V10_M2_average.txt`: diagnostic columns on triple `(1,2,3)` produced `lhs=1.5`, `rhs=1`, violation `0.5`; output `results/v10_m2_average_cuts_diag.json`.
- Integrated the separator into the fixed-Gini branch-price restricted master. Cut rows are local to each node; after a violated triple is added, the restricted master is re-solved before pricing. Active cut duals are passed to exact pricing as a term for any column covering at least two stations in the triple, preserving the pricing certificate.

## Ryan-Foster co-route branching

Implemented after the initial report:

- Added `include/Branching.hpp` and `src/Branching.cpp`.
- The scanner computes `sum_{c containing both i,j} z_c` for every station pair and selects a fractional pair for Ryan-Foster branching.
- Added `--method branching` as a diagnostic CLI path. It builds feasible pair columns with `z=0.5`, then reports the selected pair and the two child branches `together=0` and `together=1`.
- `test_data_V8_M2_average.txt`: diagnostic columns on pairs `{1,2}` and `{1,4}` produced candidate pair `(1,2)` with together value `0.5`; output `results/v8_m2_average_branching_diag.json`.
- `test_data_V10_M2_average.txt`: diagnostic columns on pairs `{1,2}` and `{1,3}` produced candidate pair `(1,2)` with together value `0.5`; output `results/v10_m2_average_branching_diag.json`.

## Restricted column master

Implemented after the initial report:

- Added `include/Master.hpp` and `src/Master.cpp`.
- The reusable master solver exactly searches an integer set-packing master over a supplied route-load column pool: at most one column per vehicle, station-disjoint masks, exact final-inventory aggregation, and exact `G + lambda P` evaluation.
- Added `--method master` as a diagnostic CLI path. It builds all feasible one-stop pickup columns for every vehicle, solves the restricted master exactly, reconstructs selected routes, and runs the independent verifier.
- `test_data_V8_M2_average.txt`: one-stop pool had `212` columns, exact restricted master processed `9,314` states, selected pickups at stations `4` and `7`, objective `0.653759267174`; output `results/v8_m2_average_master_diag.json`.
- `test_data_V10_M2_average.txt`: one-stop pool had `396` columns, exact restricted master processed `34,984` states, selected pickups at stations `6` and `5`, objective `0.638754695152`; output `results/v10_m2_average_master_diag.json`.

## Root column-generation diagnostic

Implemented after the initial report:

- Added `include/ColumnGeneration.hpp` and `src/ColumnGeneration.cpp`.
- The diagnostic solves a small required-pair coverage LP over route-load columns, extracts CPLEX LP duals, calls exact pricing, adds negative reduced-cost columns, and repeats until exact pricing proves no missing negative reduced-cost column for that diagnostic LP.
- Added `--method cg` as a CLI path. This is a root LP column-generation plumbing test, not an EBRP optimality certificate.
- `test_data_V8_M2_average.txt`: initial one-stop LP objective `999.101328019`; exact pricing added two pair columns with reduced cost `-371.905553955`; the second LP closed at objective `627.195774064` with best pricing reduced cost about `-2.1e-10`; output `results/v8_m2_average_cg_diag.json`.
- `test_data_V10_M2_average.txt`: initial one-stop LP objective `1214.80299246`; exact pricing added two pair columns with reduced cost `-479.628783296`; the second LP closed at objective `735.174209169` with best pricing reduced cost about `-1.5e-10`; output `results/v10_m2_average_cg_diag.json`.

## Fixed-Gini-cap EBRP root master diagnostic

Implemented after the coverage column-generation diagnostic:

- Added `--method gcap-cg`.
- The restricted LP master now has actual EBRP root-master rows: vehicle-use rows, station-disjoint visit rows, final-inventory equations `Y_i + sum_c q_{ic} z_c = Y_i^Initial`, ratio equations, satisfaction absolute-deviation rows, pairwise Gini numerator rows, and the fixed-cap linearization `H <= V * gamma * S`.
- The LP objective is `lambda * P`; the diagnostic reports the fixed-cap surrogate `gamma + lambda*P` in notes and bound fields. The top-level JSON objective still refers to the independently verified reported route solution.
- If `--gini-cap` is omitted, the diagnostic uses the empty-solution Gini plus a tiny tolerance as a feasible cap.
- CPLEX LP duals from the inventory rows are passed to exact route-load pricing as operation coefficients; visit and vehicle duals are passed as fixed route-support coefficients.
- Identical vehicle capacities reuse one pricing proof per iteration when only the additive vehicle-row dual changes; the best column is cloned to the matching vehicle with the adjusted reduced cost.
- This is a continuous root-LP/pricing diagnostic. It is not an integer EBRP optimality certificate.

Smoke-test result:

- `testdata/examples/gcap_smoke_V4_M1.txt`: root column generation closed in `0.226061s`.
- It ran `3` pricing calls, left `2` active columns in the restricted master, processed `2,548` pricing states after operation DP, and proved best reduced cost `0`.
- Output: `results/gcap_smoke_v4_m1_gcap_cg.json`.

V8 benchmark diagnostic:

- `test_data_V8_M2_average.txt`, default cap `gamma=0.538075`.
- The initial fixed-cap LP solved with `lambdaP=0.310809904547`, `S=5.17550764756`, and `H=22.2785098827`.
- After replacing naive operation enumeration with DP and reusing identical-vehicle pricing, the fixed-cap root LP closed in `7.4304519s`.
- It ran `7` actual pricing oracle calls, left `12` active columns in the restricted master, processed `325,276,126` pricing states, and proved best reduced cost about `2.17e-18`.
- The fixed-cap LP surrogate bound closed at `gamma + lambdaP = 0.714138632029`.
- Output: `results/v8_m2_average_gcap_cg_diag.json`.

V10 benchmark diagnostic:

- `test_data_V10_M2_average.txt`, default cap `gamma=0.58115`.
- The initial fixed-cap LP solved with `lambdaP=0.19344374735`, `S=15.7514384168`, and `H=91.5395507517`.
- Exact pricing did not close in a 60-second run: `8,842,985` route states and `2,755,641,957` operation DP states for the first vehicle.
- Best observed reduced cost was negative (`-0.0827812`), so no root LP certificate is claimed.
- Output: `results/v10_m2_average_gcap_cg_diag.json`.

Reason this is not yet the main exact path:

- V8 fixed-cap root closure is now available, but it is a continuous LP certificate only; the integer master/tree is still not closed by BPC.
- V10 pricing remains too large without stronger route-level dominance, route-order lower bounds under duals, or a compact single-route pricing MIP proof fallback.

## Fixed-Gini-cap Ryan-Foster branch probe

Implemented after fixed-cap root column generation:

- Added `--method gcap-branch`.
- The fixed-cap LP writer now supports Ryan-Foster branch restrictions:
  - `together=0` filters any column containing both branch stations and passes the pair to pricing as `forbid_together_pairs`.
  - `together=1` filters columns containing exactly one branch station, adds the equality row `sum_c containing both z_c = 1`, and passes the row dual into pricing as a pair coefficient.
- `PricingDuals` now supports pair coefficients that are added when both stations are present in a priced column.
- The branch probe closes the root fixed-cap LP, selects one fractional co-route pair with the existing Ryan-Foster scanner, and then attempts to close both child LP/pricing relaxations from the root column pool.
- This is one branch level, not a full integer branch-price tree.

Smoke-test result:

- `testdata/examples/gcap_smoke_V4_M1.txt`: root and both child relaxations closed in `1.0075024s`.
- Selected pair `(1,2)` with together value `0.75`; forbid and require child bounds both closed at `0.250000001`.
- Output: `results/gcap_smoke_v4_m1_gcap_branch.json`.

V8 benchmark diagnostic:

- `test_data_V8_M2_average.txt`: root and both child relaxations closed in `14.7525764s`.
- Selected Ryan-Foster pair `(1,8)` with together value `0.642857142857`.
- Root fixed-cap LP bound was `0.714138632029`.
- `together=0` child closed at `0.714411385506`.
- `together=1` child closed at `0.714554806346`.
- The verified empty-route incumbent for the diagnostic cap is `0.848885378453`, so the one-level branch bound gap is `0.158412426883`.
- Output: `results/v8_m2_average_gcap_branch.json`.

## Fixed-Gini-cap branch-price tree diagnostic

Implemented after the one-level branch probe:

- Added `--method gcap-tree` and `--max-nodes`.
- The tree maintains an open-node queue, solves each node with the fixed-cap LP/pricing loop, and branches in this order:
  - Ryan-Foster co-route pair branch.
  - Station served/unserved branch when no fractional co-route pair remains.
  - Final inventory interval branch when station service is integral but a `Y_i` value is fractional.
- Presolve-infeasible CPLEX LP nodes are now detected from the CPLEX log even when no `.sol` file is written, and are fathomed.
- Pricing now supports `forbidden_station_mask` so station-unserved child nodes are enforced inside the exact pricer.
- If all station service, co-route pairs, and final inventories are integral but residual `z` variables remain fractional, the tree now attempts route-integer reconstruction. It first searches the current node column pool, then falls back to exact route-order enumeration for the signed operation vector implied by the projected final inventory.
- If pricing returns a negative reduced-cost column already present in the restricted master, the diagnostic treats the node as closed with an explicit bounded-variable degeneracy note because no new column is available to add.
- Added an initial fixed-cap incumbent from the empty-route solution only when the empty solution satisfies the supplied cap. Nodes with closed LP bounds no better than a valid incumbent are fathomed.
- Added phase-I column generation for cap-infeasible restricted masters. Phase I adds artificial inventory and Gini-cap slack, prices real route-load columns from phase-I duals, and switches back to the original fixed-cap master only when artificial use reaches zero.
- Added `--gcap-seed-cplex` as an explicit diagnostic warm-start option. The compact solution is used only as a verified incumbent and seed route-column pool; the fixed-cap branch-price tree must still close with exact pricing.
- Added `--gini-floor` as an interval lower-bound primitive. The tree adds `H >= V*floor*S` and reports the valid lower-bound metric `floor+lambda*P`. Because `h_ij` can be slack under a floor, route incumbents are accepted only when the independent verifier confirms true `G` is inside the requested interval.

Smoke-test result:

- `testdata/examples/gcap_smoke_V4_M1.txt`: fixed-cap tree exhausted all open nodes in `2.0121208s`.
- It solved `9` nodes, branched `4` times, pruned `2` nodes by incumbent bound, found `1` reconstructed route-integer leaf, and ended with `0` open nodes.
- Fixed-cap surrogate lower bound and best integer surrogate both closed at `0.250000001`.
- The reconstructed route verifies true objective `0` with final station inventories all equal to target.
- Status is `gcap_tree_complete` for the fixed-cap surrogate tree.
- Output: `results/gcap_smoke_v4_m1_gcap_tree.json`.

V8 benchmark diagnostic:

- `test_data_V8_M2_average.txt` with `--max-nodes 15`: solved `13` branch-price nodes in `24.1877689s`.
- Every solved node closed with exact pricing.
- The tree exhausted its open nodes after incumbent-bound pruning: `6` branch nodes, `6` nodes pruned by bound, `1` reconstructed route-integer leaf, `0` projected leaves, and `0` open nodes.
- The fixed-cap surrogate lower and upper bounds closed at `0.714554806346`.
- The reconstructed routes verify true EBRP objective `0.544866745544`, `G=0.368387414104`, and `P=1.17652887627`.
- Status is `gcap_tree_complete` for the fixed-cap surrogate tree. This is still not a full EBRP objective certificate because it does not search all Gini caps.
- Output: `results/v8_m2_average_gcap_tree15.json`.

Lower-cap correctness check:

- `testdata/examples/gcap_smoke_V4_M1.txt` with `--gini-cap 0.05` now starts without the empty-route incumbent because the empty solution has `G=0.25`.
- Phase I generates cap-feasible real columns, reaches zero artificial use, and the fixed-cap tree closes in `1.8407275s`.
- The run solves `5` branch-price nodes, uses `17` columns and `17` pricing calls, and closes fixed-cap surrogate bounds at `0.05`.
- The reconstructed route verifies true objective `0`.
- Output: `results/gcap_smoke_v4_m1_gcap_tree_lowcap.json`.

Exact interval lower-bound check:

- `testdata/examples/gcap_smoke_V4_M1.txt` with `--gini-floor 0.05 --gini-cap 0.05` exhausts the interval tree in `1.8113638s`.
- It solves `11` branch-price nodes, uses `44` columns and `29` pricing calls, and reports `gcap_interval_bound_complete`.
- The interval lower-bound metric closes at `0.05`, but no route-integer incumbent verifies inside the exact interval.
- The all-target reconstructed route has true `G=0`, so it is rejected as an interval incumbent and kept only as a lower-bound leaf. This fixed an earlier overclaim where the floor row could be satisfied by slack `h_ij`.
- Output: `results/gcap_smoke_v4_m1_gcap_interval_lowcap.json`.

V8 incumbent-gamma cap-point check:

- Unseeded `test_data_V8_M2_average.txt` with `--gini-cap 0.129169959908 --max-nodes 31` now progresses through phase I instead of failing at root, but does not close: `31` nodes solved, `20` open nodes, `672` columns, `155` pricing calls, no route-integer incumbent, runtime `48.0609237s`.
- Seeded exact-interval run with `--gcap-seed-cplex --gini-floor 0.129169959908 --gini-cap 0.129169959908 --max-nodes 127` closes the interval tree in `45.4876689s`.
- The CPLEX seed took `4.41209s`, produced verified objective `0.31908731186`, `G=0.129169959908`, `P=1.26611567968`, and supplied `2` seed route columns.
- The interval branch-price tree solved `29` nodes, branched `14` times, pruned `9` nodes by incumbent bound, generated `595` columns, made `121` exact pricing calls, and exhausted all open nodes.
- Interval lower-bound and incumbent metrics both closed at `0.31908731186`; the independently verified route objective is also `0.31908731186`.
- This is an exact cap-point/interval certificate, not a full weighted-objective BPC certificate, because lower-Gini tradeoffs still require a gamma-frontier proof.
- Output: `results/v8_m2_average_gcap_interval_optgamma_seed127.json`.

## Gamma-frontier diagnostic

Implemented:

- Added `--method gcap-frontier`.
- The diagnostic obtains a verified incumbent, covers `G in [0, incumbent_objective]` with `--frontier-intervals`, runs the fixed-Gini interval branch-price tree on each interval, and aggregates valid interval lower bounds.
- It reports `optimal` only if every relevant interval is closed or fathomed by a valid interval lower bound above the incumbent, and the aggregated lower bound reaches the incumbent objective. Open intervals can therefore be certified by bound when their inherited/closed-node lower bound is already high enough.
- Added a stronger valid frontier node objective: `g_lb + lambda*P` with `g_lb >= floor` and `g_lb >= H/(V*S_max)`. `S_max` is computed from station-bike conservation and active inventory upper branches. In incumbent-cutoff mode, `S_max` is further tightened for potentially improving solutions by the exact final-inventory DP implied by `P <= (incumbent_objective-floor)/lambda`; this is used only to prove that no solution below the verified incumbent remains.
- Added adaptive retry passes. After the coarse frontier pass, unresolved intervals are retried with the remaining wall time and a larger local node cap. Closed intervals with no route-integer incumbent are treated as empty and do not lower the aggregated frontier bound.

Smoke frontier result:

- `testdata/examples/gcap_smoke_V4_M1.txt` with `--frontier-intervals 1 --max-nodes 63` closes in `1.6859s`.
- The frontier covers `[0,0.49]`, solves `13` branch-price nodes, generates `62` columns, and makes `43` exact pricing calls.
- It finds the all-target route, verifies objective `0`, and reports `optimal` because the closed lower bound is also `0`.
- Output: `results/gcap_smoke_v4_m1_frontier.json`.

V8 frontier result:

- `test_data_V8_M2_average.txt` with `--frontier-intervals 2 --gcap-seed-cplex --max-nodes 31` does not close in `86.2828s` after the strengthened lower estimator.
- The verified incumbent is the compact-seeded route with objective `0.31908731186`, `G=0.129169959908`, and `P=1.26611567968`.
- Aggregated lower bound improves to `0.257212959552`, so the frontier gap is `19.3910%`.
- Interval `[0,0.159544]`: not closed, lower bound `0.257213`, incumbent metric `0.283159`, `31` nodes solved, `6` open nodes.
- Interval `[0.159544,0.319087]`: not closed, but its lower bound is valid and above the incumbent (`0.341031 > 0.319087`), so it is bound-certified despite `32` open nodes.
- Certification summary: `closed_intervals=0`, `bound_certified_intervals=1`, `unresolved_intervals=1`. The remaining bottleneck is the low-Gini interval, not the upper half of the incumbent Gini range.
- Output: `results/v8_m2_average_gcap_frontier2_seed.json`.

Larger and adaptive frontier probes:

- `--frontier-intervals 2 --max-nodes 127`: certified both intervals in `130.6828s`, but only proved lower bound `0.283158881228`, giving gap `11.2597%`; output `results/v8_m2_average_gcap_frontier2_seed127.json`.
- `--frontier-intervals 4 --max-nodes 63`: certified all four intervals in `202.4401s`; interval `[0,0.0797718]` is empty, `[0.0797718,0.159544]` closes at lower bound `0.283159`, and the two upper intervals are bound-certified. The same `0.283158881228` global lower bound remains; output `results/v8_m2_average_gcap_frontier4_seed63.json`.
- Cut-enabled `--frontier-intervals 4 --max-nodes 63`: added `31` 3-subset-row cuts and certified all four intervals in `210.9904s`, but the global lower bound was unchanged at `0.283158881228`. Cuts appeared only in the already bound-certified upper intervals, so this did not address the limiting incumbent-neighborhood bound. Output: `results/v8_m2_average_gcap_frontier4_seed63_cuts.json`.
- Incumbent-cutoff and adaptive frontier run: `--frontier-intervals 8 --max-nodes 255 --time-limit 900 --gcap-seed-cplex` reports `optimal` for `test_data_V8_M2_average.txt` in `568.6657s`. The verified incumbent has objective/lower/upper bound `0.31908731186`, `G=0.129169959908`, `P=1.26611567968`, and gap `0`. The run solves `291` branch-price nodes, generates `5,678` active columns across interval solves, makes `896` exact pricing calls, and closes all eight relevant intervals after one adaptive retry of `[0.119658,0.159544]`. Output: `results/v8_m2_average_gcap_frontier8_adaptive_cutoff.json`.
- Targeted one-interval checks confirm the adaptive certificates: `[0.0797718,0.119658]` closes empty/bound-complete in `134.2480s` with `53` nodes, and `[0.119658,0.159544]` closes bound-complete in `215.4795s` with `167` nodes. Outputs: `results/v8_m2_average_gcap_frontier_interval_079_119_cutoff1023.json` and `results/v8_m2_average_gcap_frontier_interval_119_159_cutoff1023.json`.
- Attempted to use the same adaptive BPC/frontier path on `test_data_V8_M1_high.txt` because the plain compact baseline is slow there. It did not close in `239.3928s`: incumbent/objective `0.571697257514`, lower bound `0.52667698786`, gap `7.8748%`, `26` branch-price nodes, `158` columns, and `102` pricing calls. Seven of eight intervals were certified; interval `[0.214386,0.285849]` remained open with `15` nodes after the first adaptive retry. Output: `results/v8_m1_high_gcap_frontier8_adaptive_cutoff.json`.
- The remaining BPC issue is performance and scaling, not V8 correctness on this sample: the closed frontier is much slower than the compact strengthened fallback and still depends on a compact CPLEX seed for its incumbent.

## CPLEX command-line integration

Implemented:

- Compact MILP LP writer in C++.
- CPLEX command script with `set threads <N>`, `set timelimit <seconds>`, and `mipgap=1e-8`.
- XML `.sol` parser and independent route/objective verifier.
- Unique CPLEX work directory per run to avoid interactive overwrite prompts.

Issues fixed:

- Windows quoting for `cplex.exe` under `Program Files`.
- Stale `.sol` parsing after CPLEX overwrite prompt.
- Plain baseline initially allowed simultaneous pickup and drop at a station; mode constraints are now enforced in both plain and strengthened variants.
- Time-limited CPLEX best bound is parsed from the CPLEX log.

## Historical compact-fallback benchmark runs

These early rows compare the tailored compact/portfolio fallback against plain CPLEX. They are not BPC results and must not be reported as full Gini-frontier route-load BPC speedups.

### V=8 M2 average

- File: `Hybrid GA/testdata/Smallnetwork2/test_data_V8_M2_average.txt`
- Tailored portfolio: optimal, objective `0.319087311860`, time `4.3472609s`.
- Plain CPLEX baseline: optimal, objective `0.319087311860`, time `7.8434418s`.
- Compact-fallback runtime ratio: `1.8042262x`.
- Output: `results/compare_v8_m2_average.csv`.
- Current rebuilt executable rerun with `threads=8`: tailored compact portfolio optimal in `2.4877399s`, plain CPLEX optimal in `5.6400034s`, compact-fallback runtime ratio `2.2671194x`; output `results/compare_v8_m2_average_current.csv`.

### V=8 M2 low

- File: `Hybrid GA/testdata/Smallnetwork2/test_data_V8_M2_low.txt`
- Tailored portfolio: optimal, objective `2.18621359223`, time `0.6106639s`.
- Plain CPLEX baseline: optimal, objective `2.18621359223`, time `0.4491078s`.
- Compact-fallback runtime ratio: `0.7354419x`.
- Output: `results/compare_v8_m2_low.csv`.

### V=8 M2 high

- File: `Hybrid GA/testdata/Smallnetwork2/test_data_V8_M2_high.txt`
- Tailored portfolio: optimal, objective `0.359576511323`, time `1.793211s`.
- Plain CPLEX baseline: optimal, objective `0.359576511323`, time `1.3301467s`.
- Compact-fallback runtime ratio: `0.7417681x`.
- Output: `results/compare_v8_m2_high.csv`.

Median V=8 M2 compact-fallback runtime ratio over these three runs is below 1 because two instances are already easy for the plain compact model. This historical block is not evidence of BPC speedup.

### Additional V=8 M1 checks

- `test_data_V8_M1_low.txt`: tailored optimal in `0.3466798s`, plain CPLEX optimal in `0.1823147s`, compact-fallback runtime ratio `0.5258879x`.
- `test_data_V8_M1_average.txt`: tailored optimal in `0.3021317s`, plain CPLEX optimal in `0.285843s`, compact-fallback runtime ratio `0.9460874x`.
- `test_data_V8_M1_high.txt`: tailored optimal in `4.0203748s`, plain CPLEX optimal in `51.3915582s`, compact-fallback runtime ratio `12.7827779x`.
- Outputs:
  - `results/compare_v8_m1_low.csv`
  - `results/compare_v8_m1_average.csv`
  - `results/compare_v8_m1_high.csv`

### V=10 M2 average

- File: `Hybrid GA/testdata/Smallnetwork2/test_data_V10_M2_average.txt`
- Tailored portfolio: optimal, objective `0.463263009179`, time `55.6407158s`.
- Plain CPLEX baseline: not certified at `120.1633254s`, incumbent `0.463263009179`, lower bound `0.43854431231`, gap `5.3357804%`.
- Output JSON:
  - `results/v10_m2_average_tailored.json`
  - `results/v10_m2_average_cplex_plain.json`
- Comparison CSV: `results/compare_v10_m2_average.csv`.

## Current bottlenecks

- The strongest current certified path is the strengthened compact exact fallback, not a closed route-load BPC tree.
- Full route-load enumeration needs compressed dominance/frontier storage or pricing-based branch-price search before it can serve as the primary V=8 M2 engine.
- The Gini product linearization still drives a difficult MIP bound in the plain baseline; subset route-duration cuts and symmetry help substantially on V=10 M2 average.
- The inventory branch-search now has valid objective and route-duration lower bounds, but its remaining search tree is still too broad for V=8 M2.
- Next useful pruning work should target stronger lower bounds on the objective over final-inventory boxes, not faster route DP.
- Incumbent-aware filtering leaves hundreds of discrete station values on V=8 M2 average, so the next bound likely needs a box-level Gini/P relaxation rather than stationwise penalty filtering.
- The triangle-inequality Gini star bound is valid but not strong enough by itself on the tested V=8 M2 average instance.
- The Lorenz/order-statistic bound helps, but V=8 M2 still needs a stronger box-level relaxation or a different search split.
- Suffix pickup/drop feasibility pruning and the pickup/net-aware penalty DP are valid and cheap, but they did not materially change the V=8 proof bottleneck.
- Root-level parallelism scales proof throughput, but even hundreds of millions of nodes do not close the current V=8 proof tree; stronger objective-space bounds are still required.
- The exact pricing oracle is now available as a compiled module, can enforce Ryan-Foster child restrictions, and now uses an exact operation DP for each fixed route.
- The 3-subset-row separator is now available as a compiled module; it still needs integration into the column master relaxation.
- Ryan-Foster co-route branch candidate selection is now available as a compiled module; pricing restrictions for the child nodes still need to be enforced in the BPC tree.
- The restricted integer column master is now available as a compiled module. It proves pool optimality for supplied columns, but a full BPC certificate still needs a restricted LP/dual loop and exact pricing closure.
- A CPLEX-backed root LP/dual/pricing loop is available for both a simple coverage diagnostic and a fixed-Gini-cap EBRP root master. The remaining BPC work is to integrate the fixed-cap master, cuts, pricing, and branching into an integer branch-price tree.
- The fixed-Gini-cap V8 M2 root LP closes in `7.43s`; V10 M2 still times out in first pricing after `60s`, so route-level pricing dominance is the next scaling bottleneck.

## Method-scope cleanup and paper BPC reruns

Date: 2026-06-11.

Changes:

- Added explicit result metadata to JSON/CSV output: `method_scope`, `solves_original_objective`, `is_bpc`, `certificate_type`, `stop_reason`, `verifier_passed`, `unresolved_intervals`, `invalid_bound_intervals`, `pricing_closed_nodes`, `open_nodes`, and `certified_original_problem`.
- Changed `ExactEBRPCompare` CSV output to long format, one method per row, so compact fallback and plain CPLEX rows cannot be confused with BPC rows.
- Added the valid interval lower bound `objective >= G >= gamma_floor` to fixed-Gini interval/tree reporting and the full frontier aggregation.
- Wrote `docs/certification_protocol.md`, `docs/paper_bpc_algorithm_report.md`, `docs/paper_bpc_algorithm_report.tex`, and `docs/experiment_table.csv`.

Fresh runs:

- `results/paper_bpc_v8_m2_average_frontier.json`: `gcap-frontier`, `status=optimal`, objective/LB/UB `0.31908731186`, gap `0`, verifier passed, unresolved intervals `0`, runtime `574.1946168s`.
- `results/paper_cplex_v8_m2_average_plain.json`: plain CPLEX, `status=optimal`, same objective, gap `0`, runtime `31.9968276s`.
- `results/paper_bpc_v10_m2_average_frontier_boundfloor.json`: `gcap-frontier`, `status=gcap_frontier_not_closed`, incumbent `0.474319271743`, valid LB `0`, gap `1`, unresolved intervals `4`, runtime `183.4153072s`.
- `results/paper_cplex_v10_m2_average_plain.json`: plain CPLEX, `status=not_certified`, incumbent `0.470083906899`, LB `0.42753772088`, gap `0.0905076421353`, runtime `120.0841327s`.
- `results/paper_tailored_v10_m2_average.json`: auxiliary strengthened compact fallback through `tailored`, `status=not_certified`, incumbent `0.463263009179`, LB `0.4505216778`, gap `0.0275034507977`, runtime `120.1211124s`.

Outcome:

- The full frontier BPC currently certifies at least one V=8 instance, but it is slower than the plain compact CPLEX benchmark on the fresh V8 M2 average run. This does not support a BPC speedup claim.
- The V10 frontier does not close. The main unresolved bottleneck is the low-G interval starting at zero; the newly added interval-floor bound helps higher intervals but cannot lift the global lower bound while the first interval remains open.
- The previous `results/compare_v10_m2_average.csv` is still only a compact-fallback benchmark result: tailored compact certified within `55.77s`; CPLEX did not certify within `120.16s`, final gap `0.0532958`. The reported runtime ratio is not a certified-optimal speedup.

Next exact BPC work:

- Add a valid low-G interval lower bound for `lambda P`, likely through a final-inventory box relaxation.
- Integrate 3-subset-row cuts into the active fixed-cap master.
- Cache exact pricing labels across adjacent frontier intervals and Ryan-Foster sibling nodes.
- Add route-resource lower bounds before the exact operation DP in pricing.

## Final-inventory pickup/Gini relaxation bound

Date: 2026-06-11.

Change:

- Added `include/Bounds.hpp` and `src/Bounds.cpp`.
- Implemented a resource relaxation lower bound using operation-time conservation and total pickup budget.
- Implemented a final-inventory pickup/Gini LP relaxation for each frontier interval. It enforces station capacity bounds, no bike creation, total pickup budget, and the interval Gini cap/floor, then minimizes a valid linear lower estimator of `G + lambda P`.
- Wired this relaxation into `gcap-frontier` before each branch-price interval solve. If the relaxation is infeasible, the interval is validly bound-fathomed. If it solves, its lower bound is combined with the branch-price lower bound.

Validation:

- `results/inventory_relax_smoke_gcap_frontier.json`: smoke instance remains `status=optimal`, `certified_original_problem=true`.
- `results/paper_bpc_v10_m2_average_frontier_inventoryrelax_180s.json`: V10 M2 average remains not closed, but the valid lower bound improves from `0.0415096260643` to `0.2028316526`; gap improves from `0.912485896026` to `0.572373157316`; unresolved intervals drop from `4` to `3`.
- Interval 0 `[0,0.11858]` is bound-fathomed before branch-price by relaxation infeasibility.
- Interval relaxation lower bounds now reported in notes:
  - interval 1 `[0.11858,0.23716]`: `0.202832`
  - interval 2 `[0.23716,0.355739]`: `0.305901`
  - interval 3 `[0.355739,0.474319]`: `0.402055`

Outcome:

- This is aligned with the paper BPC path because it strengthens full-frontier lower bounds without using a restricted route pool or compact-route certificate.
- It still does not certify V10. The active global bottleneck is now interval 1, where pricing/tree closure still fails before the cap.

## Route-reachability cuts inside the final-inventory relaxation

Date: 2026-06-11.

Change:

- Added continuous station-visit indicators to the final-inventory relaxation.
- Added singleton route-duration cuts: each changed station must fit within one vehicle route's minimum depot round trip plus its pickup operation.
- Added pair and triple route-reachability cuts using shortest-path metric closure distances and exact small-subset route partition travel lower bounds. These are necessary conditions for route feasibility and therefore valid for lower-bound certification.
- Tested a finer 16-interval frontier cover.

Validation:

- `results/routecut_smoke_gcap_frontier.json`: smoke instance remains `status=optimal`.
- `results/paper_bpc_v10_m2_average_frontier_routecuts_75s.json`: V10 M2 average lower bound improved to `0.305900633685`; unresolved intervals dropped to `2`.
- `results/paper_bpc_v10_m2_average_frontier_routecuts_8int_120s.json`: V10 lower bound improved to `0.319141241222`.
- `results/paper_bpc_v10_m2_average_frontier_routecuts_16int_180s.json`: V10 lower bound improved to `0.348786195706`, gap `0.26465944674`; intervals 0-8 are bound-fathomed as relaxation-infeasible and interval 15 is bound-fathomed by relaxation lower bound.

Outcome:

- The route-cut relaxation materially improves the full-frontier BPC bound and moves the active bottleneck to interval 9 `[0.266805,0.29645]`.
- V10 is still not closed. The result remains `gcap_frontier_not_closed`, `certified_original_problem=false`, with six unresolved intervals.

## All-subset route relaxation and finer V10 frontier cover

Date: 2026-06-11.

Change:

- Generalized the final-inventory route-reachability relaxation from singleton/pair/triple cuts to subset route cuts.
- For `V<=12`, the implementation precomputes exact small-subset route partition lower bounds over all station subsets using shortest-path metric travel costs and up to `M` routes. For larger instances it caps subset size to avoid an oversized LP.
- Kept the cuts as necessary route-feasibility conditions, so they strengthen only valid lower bounds for full-frontier certification.
- Tested both 16-interval and 32-interval V10 frontier covers.

Validation:

- `results/routecut_all_smoke_gcap_frontier.json`: smoke instance remains `status=optimal`.
- `results/paper_bpc_v10_m2_average_frontier_routecuts_all_16int_120s.json`: all-subset cuts with the same 16-interval cover did not improve over the subset-size-5 result; LB stayed `0.348786195706`.
- `results/paper_bpc_v10_m2_average_frontier_routecuts_all_32int_240s.json`: the 32-interval cover improves the valid V10 BPC lower bound to `0.361674025004`, with incumbent/UB `0.474319271743`, gap `0.237488235141`, runtime `243.1346681s`, `unresolved_intervals=11`, and `certified_original_problem=false`.
- Intervals 0-17 are bound-fathomed by relaxation infeasibility; intervals 29-31 are bound-fathomed by relaxation lower bounds above the incumbent. The active global bottleneck is interval 18 `[0.266805,0.281627]`.

Outcome:

- The finer frontier cover gave a real full-BPC lower-bound improvement, but V10 remained uncertified at that point.
- The branch-price tree still contributes little on the unresolved mid-G intervals; the current progress is coming from valid final-inventory/route/equity lower bounds rather than exact pricing closure.

## Verified external incumbent import for frontier cutoff

Date: 2026-06-11.

Change:

- Added `--incumbent-json <path>` for `gcap-frontier`.
- The option reads routes from the project's own JSON result format, independently verifies route feasibility and objective, and accepts the routes only if they improve the incumbent.
- The imported incumbent is logged as a warm start/cutoff only. No lower-bound certificate is inherited from the source result, so compact fallback success is still not counted as BPC success.
- Added `--gcap-seed-time-limit <seconds>` to allow explicit control of the optional compact CPLEX seed time when `--gcap-seed-cplex` is used.
- Added `--frontier-refine-splits <N>` for optional adaptive Gini-interval splitting. Child intervals inherit the parent valid lower bound, then solve their own final-inventory/route/Gini relaxation; replaced parent intervals are skipped in the final ledger so the child cover remains exact.

Validation:

- `results/incumbent_json_smoke_frontier.json`: short V10 smoke run accepted `results/paper_tailored_v10_m2_average.json` as an external incumbent, verifier passed, and the output remained `gcap_frontier_not_closed`.
- `results/paper_bpc_v10_m2_average_frontier_external_incumbent_32int_240s.json`: imported incumbent objective/UB `0.463263009179`, `G=0.345161450961`, `P=0.787343721456`; run LB `0.361305350521`, gap `0.220085905064`, runtime `242.7465303s`, `unresolved_intervals=10`, `invalid_bound_intervals=0`, `certified_original_problem=false`.
- Intervals 0-18 are bound-fathomed by relaxation infeasibility; intervals 29-31 are bound-fathomed by relaxation lower bounds above the incumbent. The active bottleneck is interval 19 `[0.275062,0.289539]`.
- `results/frontier_refine_smoke_v10.json`: coarse 4-interval smoke with one adaptive split improved the run lower bound from the parent interval's `0.301720` to `0.317874`, confirming that child relaxation bounds are included in the final ledger.
- `results/paper_bpc_v10_m2_average_frontier_refine16_external_240s.json`: 16-interval cover plus one adaptive split pass reproduced the 32-interval imported-incumbent bound with fewer initial intervals: LB `0.361305350521`, UB `0.463263009179`, gap `0.220085905064`, runtime `242.7527628s`, `unresolved_intervals=10`, `certified_original_problem=false`.
- The adaptive run proves infeasibility below `G=0.275062` and bound-fathoms the high-Gini tail above `G=0.419832`; the active bottleneck is child interval `[0.275062,0.289539]`.

Outcome:

- The better incumbent tightened the full-frontier cover and improved the reported V10 incumbent and gap, but the BPC frontier remained uncertified at that point.
- Combining the separate valid BPC lower-bound run (`0.361674025004`) with this verified incumbent gives a best-known BPC gap of about `0.21929`, still not a certificate.
- Adaptive splitting is useful as a more targeted way to reproduce the uniform finer-grid bound, but by itself it does not fix the branch-price closure bottleneck in the mid-Gini intervals.

## Integer final-inventory relaxation and MIP best-bound fallback

Date: 2026-06-11.

Change:

- Strengthened the final-inventory pickup/route/Gini relaxation for `V<=12` by making final inventories, pickup/drop quantities, and visit indicators integer.
- Kept all-subset route cuts for `V<=12`; larger instances still use the continuous relaxation with capped subset size.
- Added a parser for CPLEX `Current MIP best bound` in the relaxation log. If the small integer relaxation hits a time limit, the MIP best bound is used as a valid lower bound for the relaxation and therefore for the original interval.

Validation:

- `results/frontier_integer_relax_smoke_v10.json`: first integer-relaxation smoke accepted the model, improved the coarse V10 lower bound to `0.333486284217`, but lost some bounds when MIP relaxations hit time limit before the best-bound fallback existed.
- `results/frontier_integer_relax_bound_smoke_v10.json`: with best-bound fallback, the same coarse smoke improved LB to `0.38303720536`, gap `0.173175501237`, and reduced unresolved intervals to `2`; verifier passed, `certified_original_problem=false`.
- `results/frontier_integer_relax_smoke_v4.json`: smoke frontier instance remained `status=optimal`, objective `0`, runtime `4.5152s`.
- `results/paper_bpc_v10_m2_average_frontier_integer_refine16_external_240s.json`: V10 M2 average with imported incumbent, 16 intervals, one adaptive split pass, integer final-inventory relaxation, and MIP best-bound fallback reached LB `0.429870019678`, UB `0.463263009179`, gap `0.0720821408996`, runtime `240.9288738s`, `unresolved_intervals=4`, `invalid_bound_intervals=0`, `certified_original_problem=false`.
- The run proves infeasibility below `G=0.318493` and bound-fathoms the high-Gini tail above `G=0.376401`. The active bottleneck is child interval `[0.318493,0.33297]`, with relaxation LB `0.429870`.

Outcome:

- At the time of that run, this was the strongest paper-BPC V10 bound and a substantial improvement over the previous `0.361305350521` bound.
- V10 remained uncertified in that run because four mid-Gini intervals were unresolved and the branch-price tree did not close them before the cap.

## Station-flow conservation, depot-return capacity, and cutoff relaxation

Date: 2026-06-11.

Change:

- Added exact per-station conservation to the final-inventory relaxation:
  `pickup_i - drop_i + final_inventory_i = initial_inventory_i`.
- Added the aggregate depot-return capacity lower bound:
  `sum_i final_inventory_i >= sum_i initial_inventory_i - sum_k Q_k`.
- Added incumbent-cutoff relaxation mode for frontier intervals. For interval floor `gamma_L` and incumbent `UB`, any solution with `P > (UB-gamma_L)/lambda` cannot improve the incumbent. The relaxation may therefore add this penalty budget, tighten the Gini denominator upper bound for incumbent-improving candidates, and report `min(relaxation_bound, UB)` as a valid unconditional lower bound.
- Updated relaxation notes to expose `station_flow_conservation`, `depot_return_capacity`, `incumbent_cutoff_bound`, `penalty_budget`, and `s_upper`.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_cutoff_bound_smoke_v4_final.json`: smoke frontier instance remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed, `certified_original_problem=true`.
- `results/paper_bpc_v10_m2_average_frontier_cutoff_refine2_external_360s.json`: V10 M2 average with imported incumbent, 16 intervals, two adaptive split passes, integer final-inventory relaxation, all-subset route cuts, station-flow conservation, depot-return capacity, and cutoff relaxation reached LB `0.434363176405`, UB `0.463263009179`, gap `0.0623832082465`, runtime `361.116497s`, `unresolved_intervals=8`, `invalid_bound_intervals=0`, `certified_original_problem=false`.

Outcome:

- The cutoff relaxation made interval fathoming more explicit in the logs: several intervals are now reported as having no incumbent-improving solution under the valid penalty budget.
- The numeric V10 lower bound did not improve over the previous two-split integer-relaxation run; the active bottleneck remains child interval `[0.318493,0.325732]` with relaxation LB `0.434363176405`.
- V10 remained uncertified in that run because eight mid-Gini child intervals remained unresolved and no branch-price tree closure was obtained before the time cap.

## Station operation-capacity cuts and focused frontier splitting

Date: 2026-06-11.

Change:

- Added the valid station operation-capacity cuts to the final-inventory interval relaxation:
  `pickup_i <= max_k Q_k * visit_i` and `drop_i <= max_k Q_k * visit_i`.
- Added frontier scheduling controls:
  `--frontier-split-batch <N>` refines only the lowest-bound unresolved intervals first,
  `--frontier-retry-passes <N>` controls adaptive branch-price retry passes, and
  `--frontier-retry-nodes <N>` caps retry tree nodes when retries are enabled.
- Kept the certificate ledger unchanged: child intervals replace parents only when they exactly cover the parent, and unresolved children remain counted.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_station_opcap_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/frontier_focused_refine_smoke_v4.json`: V4 smoke with focused splitting and no adaptive retries remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/paper_bpc_v10_m2_average_frontier_opcap_refine3_external_240s.json`: V10 M2 average with operation-capacity cuts and three split passes reached LB `0.437982418664`, UB `0.463263009179`, gap `0.054570708247`, runtime `240.9552927s`, `unresolved_intervals=14`, `certified_original_problem=false`.
- `results/paper_bpc_v10_m2_average_frontier_focused_refine6_external_240s.json`: focused splitting with `--frontier-split-batch 1 --frontier-retry-passes 0` reached the same LB `0.437982418664` in `209.2928106s`, with `unresolved_intervals=9`.
- `results/paper_bpc_v10_m2_average_frontier_focused_refine10_external_360s.json`: deeper focused splitting reached LB `0.43961899847`, UB `0.463263009179`, gap `0.0510379854224`, runtime `311.3770673s`, `unresolved_intervals=12`, `invalid_bound_intervals=0`, `certified_original_problem=false`.

Outcome:

- The operation-capacity cuts and focused splitting improved the best current V10 BPC lower bound from `0.434363176405` to `0.43961899847`.
- This is still not a global certificate. The run remains `gcap_frontier_not_closed`, with 12 unresolved child intervals and no exact branch-price closure on the active mid-Gini region.
- Focused splitting is useful for improving the global lower bound under a time cap, but it increases the number of unresolved children. The next exact step must close or bound-fathom these children, not merely split them further.

## Station-sum-aware Gini denominator bound

Date: 2026-06-11.

Change:

- Tightened the `S_upper` computation used by the Gini lower estimator `H/(V*S_upper)` in the final-inventory relaxation.
- The denominator-bound DP now enforces the depot-return station-sum floor:
  `sum_i final_inventory_i >= sum_i initial_inventory_i - sum_k Q_k`.
- The relaxation notes now include `min_station_bikes=<value>` so this part of the bound certificate is auditable.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_station_sum_floor_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/paper_bpc_v10_m2_average_frontier_station_sum_floor_refine10_external_360s.json`: V10 M2 average with focused splitting and station-sum-aware `S_upper` reported LB `0.43961899847`, UB `0.463263009179`, gap `0.0510379854224`, runtime `307.6852241s`, `unresolved_intervals=12`, `invalid_bound_intervals=0`, `certified_original_problem=false`.

Outcome:

- This change improves the mathematical tightness and audit trail of the Gini lower estimator, but it did not improve the numeric V10 lower bound on the current focused run.
- V10 remained uncertified in that run. The active bottleneck was exact closure or valid bound-fathoming of the unresolved mid-Gini child intervals.

## Exact label-setting pricing, warm-start columns, and generalized subset-row cuts

Date: 2026-06-11.

Change:

- Added an exact label-setting route-load pricing path for guarded small/medium instances. Labels are keyed by visited station set, last station, vehicle load, and total pickup, with Pareto dominance on reduced cost and travel time. The older exhaustive route plus operation DP remains as a fallback.
- Added verified incumbent route columns to every fixed-interval restricted master as feasible warm-start columns, even when the incumbent's Gini value is outside the interval. The incumbent itself is still accepted only when its verified Gini value lies in the interval.
- Added generic singleton and two-station pickup/drop warm-start route-load columns with hash-based duplicate detection.
- Generalized subset-row cuts from triples to odd station subsets, currently separating size 3 and 5 cuts in the active fixed-interval master. Pricing uses the same coefficient `floor(|A_c intersect S|/2)`.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_labelpricing_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/frontier_warmstart_hash_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed, with the larger warm-start pool.
- `results/cuts_after_subsetrow_change.json`: existing cuts diagnostic still completed after the generalized cut data model change.
- `results/v10_bottleneck_labelpricing_tree.json`: direct V10 interval `[0.322113,0.323922]` improved from the old exhaustive pricing behavior but still did not close within 120 seconds.
- `results/v10_bottleneck_warmstart_hash_tree.json`: the same direct interval closed as `gcap_interval_bound_complete` in `7.2777046s`, with `pricing_closed_nodes=1`, `open_nodes=0`, and exact pricing at the root. This is a fixed-interval subproblem certificate, not a full original-problem certificate.
- `results/paper_bpc_v10_m2_average_frontier_label_warmstart_360s.json`: full V10 frontier with label pricing, warm-start columns, generalized subset-row cuts, 16 intervals, 10 focused split passes, and no retry reached LB `0.43961899847`, UB `0.463263009179`, gap `0.0510379854224`, runtime `261.6949606s`, `pricing_closed_nodes=6`, `cuts_added=2`, `unresolved_intervals=12`, `certified_original_problem=false`.
- `results/paper_bpc_v10_m2_average_frontier_label_warmstart_split10_retry_600s.json`: full V10 frontier with 10 focused split passes and one retry pass reached LB `0.4405602007`, UB `0.463263009179`, gap `0.0490063053378`, runtime `597.1742812s`, `pricing_closed_nodes=35`, `open_nodes=20`, `cuts_added=2`, `unresolved_intervals=9`, `certified_original_problem=false`.

Outcome:

- Exact pricing is materially stronger and faster on the formerly visible interval `[0.322113,0.323922]`; that interval can now be bound-fathomed in isolation.
- At this point in the run history, the best V10 BPC lower bound improved from `0.43961899847` to `0.4405602007`, reducing the valid BPC gap from `0.0510379854224` to `0.0490063053378`.
- V10 remained uncertified. The then-visible global bottleneck was around child interval `[0.325732,0.327541]`, with nine unresolved intervals in the full frontier ledger.
- `results/paper_bpc_v8_m2_average_frontier_label_warmstart_900s.json`: current-code V8 M2 average BPC remained `status=optimal`, objective/LB/UB `0.31908731186`, gap `0`, verifier passed, `pricing_closed_nodes=308`, `cuts_added=4`, runtime `779.2751898s`. This preserves the V8 certificate but is slower than the earlier `574.1946168s` BPC run, mainly because the broad generic warm-start pool increases restricted master size.

## Sparse warm-start control

Date: 2026-06-11.

Change:

- Added `--gcap-warmstart seed|sparse|full`.
- `seed` keeps only verified seed-route columns plus columns generated by exact pricing.
- `sparse` adds target-oriented singleton and pickup/drop pair quantities.
- `full` preserves the previous exhaustive one- and two-station warm-start pool.
- The default is `sparse` to avoid the full-pool restricted-master blowup while retaining the interval-closing columns that seed-only lacks.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_sparse_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/v10_bottleneck_sparse_tree.json`: direct interval `[0.322113,0.323922]` closed as `gcap_interval_bound_complete` in `7.0557021s`, with `pricing_closed_nodes=1`, `open_nodes=0`, and only `618` columns.
- `results/v10_bottleneck_seedonly_tree.json`: the same interval with `--gcap-warmstart seed` did not close within `120s`, ending `gcap_tree_not_closed`, `open_nodes=1`, and `columns=16`.
- `results/paper_bpc_v8_m2_average_frontier_sparse_900s.json`: current-code V8 M2 average BPC remained `status=optimal`, objective/LB/UB `0.31908731186`, gap `0`, verifier passed, runtime `745.9169507s`, `columns=28930`, `pricing_closed_nodes=306`, `cuts_added=4`.
- `results/paper_bpc_v10_m2_average_frontier_sparse_split10_retry_600s.json`: full V10 frontier matched the previous best LB `0.4405602007` and gap `0.0490063053378`, with runtime `597.2573421s`, `unresolved_intervals=8`, `pricing_closed_nodes=36`, `open_nodes=19`, `cuts_added=4`, and only `24560` columns.

Outcome:

- Sparse warm-start became the best default at this point: it preserved the useful fixed-interval closure and V10 lower bound while reducing column counts by roughly two orders of magnitude compared with full warm-start.
- It did not solve the global V10 certificate. The then-active bottleneck remained unresolved mid-Gini child intervals, especially around `[0.325732,0.327541]`.
- V8 remained certified but not competitive with CPLEX. Sparse warm-start improved over full warm-start on V8; a later current-code seed-only rerun was slower than sparse.

## Best-bound branch and frontier retry scheduling

Date: 2026-06-11.

Change:

- Changed fixed-interval branch-price tree node selection from FIFO to best inherited lower bound. This is a search-order change only; an LP node bound is still used only after exact pricing closure.
- Changed frontier retry ordering to process unresolved intervals by missing/invalid lower bound first, then by smallest valid interval lower bound.
- Changed frontier retry budgeting to spend the remaining retry wall time on one best-bound interval at a time. This is intended to move the global BPC lower-bound ledger under a time cap instead of spreading time thinly over intervals that do not control the global bound.

Validation:

- Rebuilt `build/ExactEBRP.exe` with `g++`.
- `results/frontier_bestbound_single_retry_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/paper_bpc_v8_m2_average_frontier_seed_900s.json`: current-code seed-only V8 M2 average BPC remained certified with objective/LB/UB `0.31908731186`, gap `0`, verifier passed, runtime `833.4219356s`, `columns=5510`, and `pricing_closed_nodes=286`. This is slower than the sparse current-code run, so sparse remains the default.
- `results/v10_bottleneck_325732_327541_bestbound_tree.json`: direct interval `[0.325732,0.327541]` closed as `gcap_interval_bound_complete` in `47.9211891s`, with `pricing_closed_nodes=3`, `nodes=3`, `columns=1664`, and exact pricing closure.
- `results/paper_bpc_v10_m2_average_frontier_bestboundretry_sparse_split10_retry_600s.json`: full V10 frontier with best-bound retry improved the valid BPC lower bound to `0.440727746455`, UB `0.463263009179`, gap `0.048644640901`, runtime `601.7613255s`, `unresolved_intervals=7`, `pricing_closed_nodes=29`, `open_nodes=9`, `columns=18820`, and `certified_original_problem=false`.
- `results/v10_bottleneck_327541_329351_bestboundretry_tree.json`: direct interval `[0.327541,0.329351]` closed in `46.9939288s`.
- `results/v10_bottleneck_329351_332970_bestboundretry_tree.json`: direct interval `[0.329351,0.332970]` closed in `155.0890644s`, with `nodes=11`, `columns=5372`, and `pricing_calls=32`.
- `results/v10_bottleneck_332970_336590_bestboundretry_tree.json`: direct interval `[0.332970,0.336590]` did not close in `146.6973873s`; pricing hit the time limit at a branch node after `730361` route states and `29884158` operation states. The valid interval lower bound was `0.444303569057`, but the fixed-interval tree remained open.
- `results/paper_bpc_v10_m2_average_frontier_bestboundretry_sparse_split10_retry_1000s.json`: a longer full V10 run did not improve the best ledger. It ended with LB `0.440523809035`, UB `0.463263009179`, gap `0.0490848604219`, runtime `1000.0175797s`, `unresolved_intervals=9`, and `certified_original_problem=false`. Extra time was consumed by a broad unresolved interval before the narrow mid-Gini children were fully retried.

Outcome:

- Best-bound retry gives a modest but valid full-frontier V10 improvement over the prior sparse 600s run: LB `0.4405602007` to `0.440727746455`, gap `0.0490063053378` to `0.048644640901`, and unresolved intervals `8` to `7`.
- V10 remained uncertified in that run. The full-frontier bottleneck moved from `[0.325732,0.327541]` to `[0.329351,0.332970]` in the best 600s ledger, but direct diagnostics showed that `[0.332970,0.336590]` was the next harder pricing bottleneck.
- The 1000s attempt shows that longer wall time alone is not enough; the frontier needs stronger interval lower bounds or pricing-state pruning on the mid-Gini region.

## Branch-closure pricing pruning and split-batch refinement

Date: 2026-06-11.

Change:

- Added exact branch-closure pruning to the label-setting pricer. Required-together branches define station components that must be fully present or absent in a final column. A partial label is pruned only if its required closure would include a forbidden/disallowed station, violate a forbid-together branch, or fail a route-time lower bound for visiting required missing stations and returning to the depot.
- Added target lower-bound early stopping to fixed-interval retry trees. In frontier retry, a tree may return incomplete once its valid lower bound reaches the next unresolved interval's lower bound. The stopped interval remains unresolved and open nodes remain counted.
- Evaluated `--frontier-split-batch 2` so the frontier refines two low-bound unresolved intervals per split pass instead of only one.

Validation:

- Rebuilt `build/ExactEBRP.exe`.
- `results/frontier_branchclosure_smoke_v4.json` and `results/frontier_targetlb_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/v10_bottleneck_329351_332970_branchclosure_tree.json`: direct interval `[0.329351,0.332970]` closed in `122.929871s`, improved from `155.0890644s` before branch-closure pruning.
- `results/v10_bottleneck_332970_336590_branchclosure_tree.json`: direct interval `[0.332970,0.336590]` closed in `162.113089s`; before branch-closure pruning, the same diagnostic did not close in `146.6973873s`.
- `results/v10_bottleneck_336590_340209_branchclosure_tree.json`: direct interval `[0.336590,0.340209]` still did not close in `169.4504922s`, with valid lower bound `0.449494459053`, `open_nodes=11`, and a pricing time limit after `630540` route states and `21648954` operation states in the active node.
- `results/paper_bpc_v10_m2_average_frontier_branchclosure_sparse_split10_retry_600s.json`: full V10 frontier with branch-closure pruning reached LB `0.440822509746`, UB `0.463263009179`, gap `0.0484400847645`, runtime `600.0646591s`, `unresolved_intervals=7`, `pricing_closed_nodes=33`, `open_nodes=9`, and `certified_original_problem=false`.
- `results/paper_bpc_v10_m2_average_frontier_targetlb_branchclosure_sparse_split10_retry_600s.json`: target-LB retry gave the same LB `0.440822509746`, gap `0.0484400847645`, runtime `601.782948s`, and remained uncertified.
- `results/paper_bpc_v10_m2_average_frontier_targetlb_branchclosure_sparse_split10_retry_900s.json`: longer 900s run was worse because retry time was spent on a broad unresolved interval; LB `0.440548050725`, gap `0.0490325322859`, `certified_original_problem=false`.
- `results/paper_bpc_v10_m2_average_frontier_branchclosure_splitbatch2_600s.json`: split-batch=2 produced the best current V10 BPC ledger: LB `0.441244588296`, UB `0.463263009179`, gap `0.0475289855808`, runtime `600.0338103s`, `unresolved_intervals=12`, `pricing_closed_nodes=33`, `open_nodes=13`, and `certified_original_problem=false`.
- Narrow child diagnostics after the split-batch=2 run:
  `results/v10_bottleneck_325732_326637_branchclosure_tree.json` closed `[0.325732,0.326637]` in `39.1627303s`;
  `results/v10_bottleneck_326637_327541_branchclosure_tree.json` closed `[0.326637,0.327541]` in `39.2233941s`;
  `results/v10_bottleneck_324827_325279_branchclosure_tree.json` closed `[0.324827,0.325279]` in `6.3318674s`.

Outcome:

- Branch-closure pruning materially improved exact fixed-interval closure on V10 mid-Gini children, including converting `[0.332970,0.336590]` from a direct timeout into a closed interval diagnostic.
- The best full V10 frontier lower bound improved from `0.440727746455` to `0.441244588296`, reducing the valid BPC gap from `0.048644640901` to `0.0475289855808`.
- The full original problem is still not certified. Split-batch=2 raises the lower bound by creating many narrow children, but it also leaves `12` unresolved intervals. The next improvement should combine this splitting with a retry queue that closes the newly narrow low-Gini children before spending time on broad intervals.

## Dynamic retry and reduced-refinement scheduling probes

Date: 2026-06-11.

Change:

- Changed the frontier retry loop to rebuild the unresolved-interval queue after each retry and process the current lowest valid lower bound dynamically.
- Deferred an interval for the remainder of the current retry pass only when a retry neither closed the interval nor improved its valid lower bound.
- Tested whether fewer split passes would start exact interval retries earlier and convert the direct fixed-interval closures into a stronger full-frontier ledger.

Validation:

- Rebuilt `build/ExactEBRP.exe`.
- `results/frontier_dynamicretry_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/paper_bpc_v10_m2_average_frontier_dynamicretry_branchclosure_splitbatch2_600s.json`: dynamic retry matched the best split-batch lower bound but did not improve it. It ended with LB `0.441244588296`, UB `0.463263009179`, gap `0.0475289855808`, runtime `600.0013516s`, `unresolved_intervals=12`, `pricing_closed_nodes=33`, `open_nodes=13`, and `certified_original_problem=false`.
- `results/paper_bpc_v10_m2_average_frontier_dynamicretry_branchclosure_splitbatch2_refine8_600s.json`: reducing refinement from ten to eight split passes also matched the best lower bound, with LB `0.441244588296`, gap `0.0475289855808`, runtime `601.7563383s`, `unresolved_intervals=10`, `pricing_closed_nodes=32`, `open_nodes=13`, and `certified_original_problem=false`.
- `results/paper_bpc_v10_m2_average_frontier_dynamicretry_branchclosure_splitbatch2_refine5_fixedinc_600s.json`: reducing refinement to five split passes let the retry close broader child `[0.325732,0.327541]`, but the final ledger was weaker: LB `0.440822509746`, UB `0.463263009179`, gap `0.0484400847645`, runtime `600.9733919s`, `unresolved_intervals=7`, `pricing_closed_nodes=33`, `open_nodes=12`, and `certified_original_problem=false`.
- `results/paper_bpc_v10_m2_average_frontier_dynamicretry_branchclosure_splitbatch2_refine5_600s.json`: an initial probe used a missing incumbent JSON path and therefore covered a weaker incumbent objective `0.77459416785`. This run is retained only as a configuration error diagnostic and is not comparable to the current V10 frontier table.

Outcome:

- Dynamic retry is certificate-neutral and did not damage correctness, but it did not improve the V10 global lower-bound ledger under the 600s cap.
- In the pre-route-mask run, fewer split passes traded a smaller unresolved-interval count for a weaker valid global lower bound. At that time, the best V10 BPC/frontier record was `results/paper_bpc_v10_m2_average_frontier_branchclosure_splitbatch2_600s.json`.
- The active bottleneck is not just queue order. The next useful algorithmic change is stronger lower bounds or state pruning for the mid-Gini branch-price nodes, especially around `[0.336590,0.340209]`, plus reusable column/label state across related intervals.

## Optional multi-column exact pricing probe

Date: 2026-06-11.

Change:

- Added `--gcap-pricing-columns <N>`, default `1`.
- When `N>1`, a completed exact label-setting pricing pass may return up to `N` negative route-load columns instead of only the single best column. These are columns found during exact pricing enumeration; they are added to the restricted master but do not change pricing closure conditions.
- Early negative stopping is allowed only in this optional mode, only for V>=10 non-phase-I pricing, and only to add a column. It is never used to certify node closure. If an early negative column is already present, the code reruns exact pricing before any closure claim.
- The expensive completion reduced-cost lower-bound pruning was left disabled by default after testing because its state-count reduction did not offset overhead on the V10 bottleneck.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_pricing_option_default_smoke_v4.json`: default full-frontier V4 smoke remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/v10_bottleneck_336590_340209_multicol_option_300s_tree.json`: with `--gcap-pricing-columns 4`, the formerly hard direct interval `[0.336590,0.340209]` closed as `gcap_interval_bound_complete` in `265.699s`, with `nodes=35`, `pricing_closed_nodes=35`, `open_nodes=0`, `columns=13926`, `pricing_calls=124`, and `cuts_added=4`.
- Earlier same-code diagnostic `results/v10_bottleneck_336590_340209_multicol_tree.json` did not close in `185.702s`, but improved the valid interval tree lower bound to `0.453441824253`, with `nodes=23`, `open_nodes=9`, and `cuts_added=4`.
- Full V10 frontier diagnostic `results/paper_bpc_v10_m2_average_frontier_multicol_splitbatch2_600s.json` remained not certified and was worse than the best default ledger: LB `0.44116081605`, UB `0.463263009179`, gap `0.0477098164353`, runtime `601.2543931s`, `unresolved_intervals=14`, and `certified_original_problem=false`.

Outcome:

- Multi-column exact pricing is a valid optional subproblem accelerator for difficult fixed intervals, and it closes `[0.336590,0.340209]` where the earlier 169s branch-closure diagnostic timed out.
- It is not promoted as the default full-frontier configuration because the 600s original-objective V10 ledger worsened slightly under the tested split-batch schedule.
- In that pre-route-mask test set, the main V10 BPC/frontier result remained not certified, and the best full-frontier row was `results/paper_bpc_v10_m2_average_frontier_branchclosure_splitbatch2_600s.json`.

## Frontier retry reserve scheduling probe

Date: 2026-06-11.

Change:

- Added `--frontier-retry-reserve <seconds>`, default `0`.
- When set, adaptive interval splitting stops once the remaining global wall time reaches the reserve, so the frontier has a protected budget for branch-price retry. This changes only time allocation; interval coverage, valid bounds, and exact-pricing closure requirements are unchanged.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_retry_reserve_default_smoke_v4.json`: default V4 full-frontier smoke remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/v10_bottleneck_325732_326637_current_tree.json`: direct fixed interval `[0.325732,0.326637]` still closes as `gcap_interval_bound_complete` in `39.3859s`, with `nodes=3`, `pricing_closed_nodes=3`, `open_nodes=0`, `columns=1664`, and `pricing_calls=7`.
- `results/paper_bpc_v10_m2_average_frontier_retryreserve120_splitbatch2_600s.json`: reserve `120s` matched the best full-frontier lower bound but did not improve it. It ended with LB `0.441244588296`, UB `0.463263009179`, gap `0.0475289855808`, runtime `600.8140797s`, `unresolved_intervals=12`, `pricing_closed_nodes=34`, `open_nodes=12`, and `certified_original_problem=false`.
- `results/paper_bpc_v10_m2_average_frontier_retryreserve220_splitbatch2_600s.json`: reserve `220s` stopped splitting earlier and weakened the ledger. It ended with LB `0.441055697175`, gap `0.0479367261462`, runtime `601.7986828s`, `unresolved_intervals=5`, `pricing_closed_nodes=34`, `open_nodes=12`, and `certified_original_problem=false`.

Outcome:

- Retry reserve is certificate-neutral and useful for diagnosing time allocation, but the tested reserves did not supersede the best V10 full-frontier ledger.
- `120s` gave the same global lower bound and one fewer open node than the best pre-route-mask run; `220s` left fewer unresolved intervals but a weaker lower bound because it stopped splitting before that low-Gini child ledger was created.
- In that pre-route-mask retry-reserve test set, the full original V10 problem remained uncertified. The best full-frontier row was `results/paper_bpc_v10_m2_average_frontier_branchclosure_splitbatch2_600s.json`.

## Route-mask relaxation closes V10 frontier

Date: 2026-06-12.

Change:

- Strengthened the final-inventory pickup/route/Gini interval relaxation with a complete small-instance route-mask duration/load assignment relaxation for `V<=10` and small vehicle counts.
- Each vehicle chooses at most one binary visit mask from the full set of travel-feasible station masks. Station visits are assigned to selected masks, pickup/drop quantities are assigned to vehicles, and each route satisfies the necessary conditions `cycle(mask) + (tau_pick+tau_drop)*pickup <= T`, `drop <= pickup`, and `pickup-drop <= Q_k`.
- Added `--frontier-relax-seconds <seconds>` to control the CPLEX time budget for each frontier inventory relaxation. The default behavior is unchanged when the option is not supplied.
- Added route-mask activity to inventory-bound notes as `route_mask_duration_load_relaxation=true`.
- For certified full-frontier outputs, normalized top-level `lower_bound` and `upper_bound` to `objective` after the full certificate closes within the `1e-7` certificate tolerance.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_route_mask_relax_smoke_v4.json`, `results/frontier_routemask_relax_option_smoke_v4.json`, and `results/frontier_routemask_final_smoke_v4.json`: V4 smoke frontier remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed.
- `results/paper_bpc_v10_m2_average_frontier_routemask_probe_180s.json`: V10 frontier with route-mask relaxation reached LB `0.460292993037`, UB `0.463263009179`, gap `0.00641107984764`, with `2` unresolved intervals in `180.0059s`. This was not certified.
- `results/paper_bpc_v10_m2_average_frontier_routemask_relax20_refine8_600s.json`: with `--frontier-relax-seconds 20` and 8 split passes, V10 reached LB `0.462870775074`, gap `0.000846676936301`, `5` unresolved intervals, `16` pricing-closed nodes, `11` open nodes, `10846` columns, and `12` subset-row cuts in `600.4989s`. This was still not certified.
- `results/paper_bpc_v10_m2_average_frontier_routemask_relax20_refine14_1000s.json`: with a 180s retry reserve, V10 reached LB `0.46323023803`, gap `0.0000707398353043`, `2` unresolved intervals, `34` pricing-closed nodes, `14` open nodes, `17345` columns, and `12` subset-row cuts in `998.3256s`. This was still not certified.
- `results/paper_bpc_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: removing the retry reserve and allowing continued splitting certified the full original V10 frontier. Final status is `optimal`, objective/LB/UB `0.463263009179`, gap `0`, `unresolved_intervals=0`, `invalid_bound_intervals=0`, `open_nodes=0`, verifier passed, runtime `1006.3825s`, `28` branch-price nodes, `26` pricing-closed nodes, `12615` columns, `76` pricing calls, and `12` cuts.
- `results/paper_bpc_v8_m2_average_frontier_routemask_relax20_900s.json`: V8 M2 average also remained certified with route-mask relaxation. Final status is `optimal`, objective/LB/UB `0.31908731186`, gap `0`, `unresolved_intervals=0`, `invalid_bound_intervals=0`, `open_nodes=0`, verifier passed, runtime `648.2557s`, `189` branch-price nodes, `186` pricing-closed nodes, `19158` columns, `498` pricing calls, and `23` cuts.
- `results/paper_cplex_v10_m2_average_plain_1200s.json`: matching plain CPLEX benchmark under the existing baseline code path, which writes `set threads` from the CLI default, found the same incumbent but did not certify within `1200.1490s`. Final LB was `0.45189466907`, UB `0.463263009179`, gap `0.0245397104541`, nodes `864089`, verifier passed for incumbent.

Outcome:

- The route-mask duration/load relaxation is the decisive BPC improvement for V10 M2 average. It turns the full Gini-frontier route-load BPC from a `4.75%` 600s gap into a certified original-problem result.
- On V8 M2 average, the same relaxation improves the current-code certified BPC runtime from `745.9169s` to `648.2557s`, reduces columns from `28930` to `19158`, and reduces pricing calls from `782` to `498`. It remains much slower than the plain CPLEX V8 benchmark (`31.9968s`).
- Correct benchmark wording: BPC certified in `1006.38s`; plain CPLEX did not certify within `1200.15s`, final CPLEX gap `0.0245397`.
- Do not report a certified-optimal speedup for this pair because CPLEX did not close. The valid claim is a BPC certificate versus a CPLEX benchmark failure under the tested cap.

## Certificate audit and safe initial-frontier parallelism

Date: 2026-06-12.

Change:

- Audited the V10 M2 average BPC certificate artifact and wrote `docs/v10_bpc_certificate_audit.md` plus `results/v10_bpc_certificate_audit.json`.
- Wrote the route-mask duration/load relaxation proof in `docs/route_mask_bound_proof.md`.
- Wrote the thread audit in `docs/threading_audit.md` plus `results/threading_audit.json`.
- Added result JSON fields `result_file`, `log_file`, `bpc_workers`, `pricing_threads`, `parallel_frontier`, `parallel_nodes`, `parallel_tasks`, `pricing_time_seconds`, `master_time_seconds`, `bound_time_seconds`, and `route_mask_time_seconds`.
- Added CLI switches `--bpc-workers`, `--pricing-threads`, `--parallel-frontier`, and `--parallel-nodes`.
- Implemented opt-in parallelism for the initial independent Gini frontier interval pass. Workers use a fixed incumbent copied before launch; the frontier ledger is merged after join in deterministic interval order. Internal CPLEX restricted-master and route-mask bound solves remain `set threads 1`.
- Added thread-id suffixes to command-line CPLEX work directories to avoid collisions under parallel workers.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/frontier_parallel_smoke_v4.json`: parallel-frontier smoke with `bpc_workers=2` remained `status=optimal`, objective/LB/UB `0`, gap `0`, verifier passed, and `certified_original_problem=true`.
- `results/repro_seq_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: rebuilt sequential V10 M2 average reproduction certified the original problem with objective/LB/UB `0.463263009179`, gap `0`, verifier passed, runtime `1003.5294s`, `nodes=28`, `columns=12613`, `pricing_calls=75`.
- `results/parallel4_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: 4-worker initial frontier parallelism certified the same original problem in `595.8748s`, with `nodes=6`, `columns=3304`, `pricing_calls=14`.
- `results/parallel8_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: 8-worker run certified in `590.3490s`.
- Superseded previous scheduler result `results/parallel12_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: 12-worker run certified in `586.7605s`. The later dynamic-queue series should be used for current worker-scaling claims.
- `results/parallel12_v8_m2_average_frontier_routemask_relax20_900s.json`: V8 M2 average BPC certified in `444.4004s`, improving the earlier route-mask sequential `648.2557s`, but still slower than plain CPLEX.
- `results/current_cplex_v8_m2_average_plain_120s.json`: V8 M2 plain CPLEX certified in `31.4133s`.
- `results/parallel12_v8_m1_high_frontier_routemask_300s.json`: hard V8 BPC did not close in `301.4560s`, with incumbent `0.571697257514`, LB `0.571334638406`, gap `0.000634285197725`, `unresolved_intervals=5`, and `open_nodes=16`.
- `results/current_cplex_v8_m1_high_plain_300s.json`: hard V8 plain CPLEX certified in `89.8469s`.
- `results/parallel12_v10_m1_average_frontier_routemask_300s.json`: additional V10 BPC did not close in `300.0285s`, with incumbent `0.840116598684`, LB `0.491857533692`, gap `0.414536584014`, `unresolved_intervals=23`, and `open_nodes=33`.
- `results/current_cplex_v10_m1_average_plain_300s.json`: matching V10 M1 average plain CPLEX certified in `62.8087s` with objective `0.49262512358`.
- `results/parallel12_v12_m1_average_frontier_300s.json`: V12 stress BPC did not close in `301.4595s`, with incumbent `0.798129616416`, LB `0.65433719971`, gap `0.180161735323`, `unresolved_intervals=7`, and `open_nodes=7`.
- `results/current_cplex_v12_m1_average_plain_300s.json`: matching V12 M1 average plain CPLEX certified in `9.2388s` with objective `0.690938574743`.

Outcome:

- The V10 M2 BPC certificate artifact is present and valid. The rebuilt sequential run reproduces the certificate.
- Initial frontier parallelism is safe and useful on V10 M2 average. This previous scheduler reduced wall time from `1003.53s` sequential to `586.76s` with 12 workers; the later dynamic-queue section supersedes it for current worker-scaling claims.
- The speedup saturates after 4 workers, so remaining time is dominated by route-mask bound solves and sequential adaptive/retry phases.
- BPC is still not broadly superior to CPLEX: V8 M2 remains slower, V8 M1 high does not close within 300s, and the V10 M1/V12 M1 stress runs are not competitive.
- Current paper reporting must state BPC certified V10 M2 while CPLEX did not certify within 1200s; it must not call this a certified-optimal speedup because CPLEX did not close.

## Implementation proof consistency and expanded stress tests

Date: 2026-06-12.

Change:

- Wrote `docs/implementation_proof_consistency.md`.
- Added clarified timing fields: `wall_time_seconds` and `aggregate_worker_time_seconds`. `runtime_seconds` remains wall time for compatibility.
- Changed `route_mask_time_seconds` so it accumulates only bound calls whose notes include `route_mask_duration_load_relaxation=true`; V12 runs now correctly report zero route-mask time.
- Replaced round-robin initial frontier worker assignment with a deterministic dynamic queue ordered by proximity to the incumbent Gini value.
- Updated `docs/paper_bpc_algorithm_report.md`, `docs/paper_bpc_algorithm_report.tex`, `docs/certification_protocol.md`, `docs/threading_audit.md`, `docs/experiment_table.csv`, `docs/bpc_parallel_table.csv`, and `docs/bpc_ablation_table.csv`.

Implementation/proof audit:

- Route-mask rows match the proof: one mask per vehicle, station assignment/disjointness, operation linking, per-vehicle duration, drop-before-pickup aggregate condition, and return-load capacity.
- Incumbent cutoff logic remains a valid no-improving-solution certificate.
- Gini cap/floor and linear lower estimator are valid lower-bound rows.
- The subset route cuts are valid for V12 and for larger instances with capped subset size. For subset `S`, the extra `( |S|-1 ) L(S)` RHS slack keeps the row valid when only a proper subset of `S` is visited.

V10 M2 worker series with dynamic queue:

- `results/dynseq_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: certified, objective/LB/UB `0.463263009179`, wall `997.7916s`, aggregate worker `997.6165s`, nodes `26`, columns `11921`, pricing calls `71`.
- `results/dyn4_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: certified, wall `589.0030s`, aggregate worker `701.3822s`, nodes `6`, columns `3302`, pricing calls `13`.
- `results/dyn8_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: certified, wall `588.6499s`, aggregate worker `706.4414s`.
- `results/dyn12_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: certified, wall `589.1565s`, aggregate worker `718.6533s`.
- `results/dyn16_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`: certified, wall `589.4532s`, aggregate worker `730.8302s`.

Additional V10 samples:

- `results/dyn4_v10_m1_average_frontier_300s.json`: BPC did not close. Incumbent `0.840116598684`, LB `0.491857533692`, gap `0.414536584014`, unresolved intervals `23`, open nodes `33`, wall `300.2743s`.
- `results/current2_cplex_v10_m1_average_plain_300s.json`: plain CPLEX certified objective `0.49262512358` in `63.3175s`.
- `results/dyn4_v10_m2_low_frontier_300s.json`: BPC did not close. Incumbent `1.06046656248`, LB `0.818955`, gap `0.22774085579`, unresolved intervals `22`, open nodes `30`, wall `301.3069s`.
- `results/current2_cplex_v10_m2_low_plain_300s.json`: plain CPLEX did not certify within `300.0874s`, incumbent `0.824301313135`, LB `0.79305072817`, gap `0.0379116040057`.

V12 stress tests:

- `results/dyn4_v12_m1_average_frontier_300s.json`: BPC did not close. Incumbent `0.798129616416`, LB `0.65431157845`, gap `0.180193836951`, unresolved intervals `7`, open nodes `7`, route-mask time `0`, wall `321.0857s`.
- `results/current2_cplex_v12_m1_average_plain_300s.json`: plain CPLEX certified objective `0.690938574743` in `9.2284s`.
- `results/dyn4_v12_m2_average_frontier_300s.json`: BPC did not close. Incumbent `0.748216664422`, LB `0.318414548361`, gap `0.574435369457`, unresolved intervals `21`, open nodes `21`, route-mask time `0`, wall `300.2952s`.
- `results/current2_cplex_v12_m2_average_plain_300s.json`: plain CPLEX did not certify within `300.2167s`, incumbent `0.365626842595`, LB `0.30496945226`, gap `0.165899718697`.

Outcome:

- Dynamic queue scheduling is stable but does not improve beyond the prior parallel frontier pass in a material way. Four BPC workers are the best practical setting on V10 M2 because 8/12/16 workers have similar wall time and higher aggregate worker time.
- BPC remains paper-valid but not robust: additional V10 and V12 samples did not close, and CPLEX often has much better incumbents.
- The immediate bottleneck is BPC incumbent quality plus interval lower-bound strength, not just worker count.

## Failure diagnosis, V12 complete masks, and incumbent-cutoff reruns

Date: 2026-06-13.

Change:

- Added `--route-mask-max-v <V>` to the main and compare CLIs. The default is `12`.
- Extended the route-mask duration/load relaxation from complete `V<=10` masks to complete `V<=12` masks. For `V>12`, route-mask rows remain disabled unless complete enumeration or a proved catch-all relaxation is added.
- Added per-interval note timing for new BPC runs: inventory-bound time, branch-price pricing time, and restricted-master time.
- Wrote `docs/bpc_failure_diagnosis.md` and regenerated `docs/bpc_interval_diagnostics.csv`.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/v10_m1_average_frontier_cplexinc_300s.json`: BPC with the verified CPLEX incumbent used only as an incumbent/cutoff did not certify, but improved the run from UB `0.840116598684`, LB `0.491857533692`, gap `0.414536584014`, unresolved `23` to UB `0.49262512358`, LB `0.491379983572`, gap `0.00252756091483`, unresolved `6`.
- `results/v10_m2_low_frontier_cplexinc_300s.json`: BPC with the verified CPLEX incumbent used only as an incumbent/cutoff did not certify, but improved the run from UB `1.06046656248`, LB `0.818955`, gap `0.22774085579`, unresolved `22` to UB `0.824301313135`, LB `0.815505108904`, gap `0.0106711030187`, unresolved `9`.
- `results/v12_m1_average_frontier_routemask12_300s.json`: complete V12 route masks were active and valid. BPC did not certify; LB improved from `0.65431157845` to `0.676058339622`, gap improved from `0.180193836951` to `0.152946682198`, route-mask aggregate time was `584.8788439s`.
- `results/v12_m2_average_frontier_routemask12_300s.json`: complete V12 route masks were active and valid. BPC did not certify; LB improved from `0.318414548361` to `0.35462778729`, gap improved from `0.574435369457` to `0.526035967718`, unresolved intervals dropped from `21` to `16`, route-mask aggregate time was `330.6678775s`.

Outcome:

- Complete V12 route-mask relaxation is mathematically safe and strengthens bounds, but it is too expensive and too weak to certify the current V12 stress samples by itself.
- The failed V10 cases are mostly incumbent-quality failures before warm start. With verified incumbents, the remaining issue is tight interval lower-bound/branch closure.
- No new load-order cut was added. The current diagnostics show the need for support/load-order pattern logging before a valid general cut can be derived.

## 2026-06-13: BPC-Owned Incumbents And Final Closure

Implemented a pure BPC-owned greedy route-load incumbent generator. It builds feasible route-load columns, solves a tiny disjoint-column incumbent master, and accepts only independently verified incumbents. This is an upper-bound generator only; it does not contribute lower bounds.

Results:

- V10 M1 average, BPC-owned greedy: UB 0.530951906115, G 0.279844464926, P 1.67404960793, LB 0.492245890617, gap 0.0728992872093, not certified.
- V10 M1 average, BPC-owned final closure post-patch: UB 0.530951906115, LB 0.491050395584, gap 0.0751508942187, 10 unresolved intervals, not certified. The final closure scheduler deferred each no-progress interval.
- V10 M2 low, BPC-owned greedy: UB 0.85951781114, G 0.69967781114, P 1.0656, LB 0.81840839255, gap 0.0478284662137, not certified.
- V10 M2 low, BPC-owned final closure post-patch: UB 0.85951781114, LB 0.812818153149, gap 0.0543323912381, 11 unresolved intervals, not certified. All focused closure passes stayed open below cutoff.
- V12 M1 average, BPC-owned greedy with complete V12 masks: UB 0.706835352191, LB 0.682746237839, gap 0.0340802342114, not certified.
- V12 M2 average, BPC-owned greedy with complete V12 masks: UB 0.415847367966, LB 0.35040372464, gap 0.157374191512, not certified.

A pricing/portfolio incumbent mode was tested briefly but produced very large column pools and was unstable on V10 M2 low. It is not used in reported pure BPC comparisons.

Load/order diagnostics decoded representative route-mask relaxation solutions in `docs/load_order_diagnostics.csv`. The sampled supports were aggregate-feasible under pickup-before-drop ordering, so no valid load-order cut was added. The next cut attempt should require exact route-support infeasibility certificates from the oracle layer.

## 2026-06-14: Local/Pool Incumbents, Station-Operation Cuts, And Alternative Compact Prototype

Change:

- Added a BPC-owned exact load-feasible route decoder for fixed signed station operations. It solves a DP over `(visited mask,last station,load)` and rebuilds a route only when travel plus `(tau_pick+tau_drop)*pickup` satisfies the route time limit.
- Added local-search incumbent generation over station assignment and signed operation quantities. The accepted routes are independently verified.
- Added a restricted verified route-column pool incumbent master. This is an upper-bound source only and is not used as a lower-bound certificate.
- Added station-operation mode/projection rows to the interval inventory relaxation:
  `p_i+d_i <= U_i v_i` and `p_i+d_i >= v_i`.
- Kept the pricing/portfolio incumbent mode disabled for reported pure-BPC runs after a short instability test produced very large route-column pools on V10 M2 low.
- Regenerated `docs/experiment_table.csv`, `docs/bpc_interval_diagnostics.csv`, and `docs/load_order_diagnostics.csv`.
- Updated `docs/paper_bpc_algorithm_report.md`, `docs/paper_bpc_algorithm_report.tex`, `docs/certification_protocol.md`, `docs/bpc_failure_diagnosis.md`, and `docs/implementation_proof_consistency.md`.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe`.
- `results/campaign_v10_m1_average_pool_bounds_1200s.json`: pure BPC with BPC-owned local/pool incumbent and station-operation cuts did not certify, but reached UB `0.49262512358`, LB `0.492491573593`, gap `0.000271098612489`, verifier passed, wall `1200.412453s`, unresolved intervals `3`.
- `results/campaign_v10_m2_low_pool_bounds_1200s.json`: pure BPC did not certify, UB `0.831494993816`, LB `0.82040601031`, gap `0.0133361999628`, verifier passed, wall `1200.6103071s`, unresolved intervals `18`.
- `results/campaign_v12_m1_average_pool_bounds_1200s.json`: pure BPC did not certify, UB `0.695790527408`, LB `0.690860456292`, gap `0.00708556802962`, verifier passed, wall `1200.6407274s`, unresolved intervals `15`.
- `results/campaign_v12_m2_average_pool_bounds_1200s.json`: pure BPC did not certify, UB `0.404618571401`, LB `0.35052362789`, gap `0.133693674327`, verifier passed, wall `1200.5869506s`, unresolved intervals `14`.
- Auxiliary strengthened compact branch-and-cut prototype:
  `results/alt_strengthened_v10_m1_average_300s.json` certified V10 M1 in `166.3435737s`;
  `results/alt_strengthened_v10_m2_low_300s.json` did not certify V10 M2 low in `300.1125986s`, gap `0.0208733129296`;
  `results/alt_strengthened_v12_m1_average_300s.json` certified V12 M1 in `123.3197084s`.

Outcome:

- At this stage, before the later final-closure campaign, no pure-BPC global optimality certificate had been obtained beyond V10 M2 average.
- At least three failed pure-BPC samples had their gaps reduced by more than 50% relative to the latest BPC-owned results: V10 M1 average, V10 M2 low, and V12 M1 average.
- V10 M1 now has an optimum-level pure-BPC incumbent but remains uncertified because three narrow Gini intervals have open branch-price nodes.
- V10 M2 low still needs both a better pure-BPC incumbent and stronger interval lower bounds.
- V12 M1 is close but route-mask/Gini bound solves dominate runtime.
- V12 M2 remains structurally weak; low-Gini route-mask relaxations often time-limit and the pure-BPC incumbent is still far worse than the plain CPLEX incumbent.
- The strengthened compact prototype is a useful auxiliary exact fallback for M1 cases, but it is not BPC and is not reported as BPC success.

## 2026-06-14: Final Closure Campaign, Strong Incumbents, And Portfolio Decision

Change:

- Added fixed-seed randomized greedy incumbent starts under `--bpc-incumbent random|strong`.
- Extended the BPC-owned local search with pairwise swap-style reassignment moves after the relocate/resize pass.
- Wrote `docs/station_operation_cut_proof.md` for the station-operation relaxation rows `p_i+d_i <= U_i v_i` and `p_i+d_i >= v_i`.
- Ran serious final-closure campaigns for the near-closed pure-BPC cases and added a missing auxiliary compact V12 M2 row for the portfolio comparison.

Validation:

- Rebuilt `build/ExactEBRP.exe` and `build/ExactEBRPCompare.exe` with `g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic`.
- `results/closure3600_v10_m1_average_strong_bpcseed.json`: pure BPC certified V10 M1 average, objective/LB/UB `0.49262512358`, gap `0`, verifier passed, `unresolved_intervals=0`, `invalid_bound_intervals=0`, `open_nodes=0`, wall `641.0843535s`. The run used BPC-owned strong incumbent generation and a prior pure-BPC artifact as a seed; it did not use a CPLEX incumbent.
- `results/closure3600_v12_m1_average_strong_bpcseed.json`: pure BPC did not certify V12 M1 average after `3622.6885415s`; UB `0.695790527408`, LB `0.690938092526`, gap `0.00697398813461`, verifier passed, 26 unresolved intervals, 34 open nodes.
- Strong incumbent smoke diagnostics:
  `results/incstrong_smoke_v10_m1_average.json` UB `0.504336402086`;
  `results/incstrong_smoke_v10_m2_low.json` UB `0.830839158085`;
  `results/incstrong_smoke_v12_m1_average.json` UB `0.695790527408`;
  `results/incstrong_smoke_v12_m2_average.json` UB `0.375567618892`.
- `results/alt_strengthened_v12_m2_average_300s.json`: auxiliary strengthened compact branch-and-cut did not certify V12 M2 average in `300.2093801s`; UB `0.366168793171`, LB `0.25818922713`, gap `0.29489013825`.

Outcome:

- A new pure-BPC certificate was obtained beyond V10 M2 average: V10 M1 average.
- Pure BPC currently certifies two target instances: V10 M2 average and V10 M1 average.
- V12 M1 remains a pure-BPC near miss; the lower bound is almost at the compact optimum, but the BPC incumbent remains above it and open branch-price nodes remain in tiny intervals around `G=0.47045`.
- At this stage, V10 M2 low and V12 M2 average remained open for pure BPC. Strong BPC-owned incumbents improved their UBs, especially V12 M2, but lower-bound closure was still weak.
- The recommended paper algorithm at this stage was a tailored exact portfolio: full Gini-frontier route-load BPC first, then strengthened compact branch-and-cut as an exact fallback.

## 2026-06-14: Portfolio Consolidation And V12 M1 BPC Closure

Change:

- Audited the new V10 M1 pure-BPC certificate in `docs/v10_m1_bpc_certificate_audit.md` and `results/v10_m1_bpc_certificate_audit.json`.
- Added `docs/portfolio_protocol.md`, `docs/portfolio_benchmark_table.csv`, `docs/portfolio_certificate_audit.md`, and `results/portfolio_certificate_audit.json`.
- Ran a deeper V12 M1 pure-BPC closure pass with 24 initial intervals, 24 adaptive split passes, larger retry trees, complete V12 route-mask bounds, BPC-owned strong incumbent search, and a 7200s cap.
- Ran a longer strengthened compact fallback on V10 M2 low.

Validation:

- `results/closure7200_v12_m1_average_strong_bpcseed.json`: pure BPC certified V12 M1 average, objective/LB/UB `0.690938574743`, gap `0`, verifier passed, `unresolved_intervals=0`, `invalid_bound_intervals=0`, top-level `open_nodes=0`, wall `5280.7002047s`.
- `results/v12_m1_bpc_certificate_audit.json`: accepted the V12 M1 BPC certificate. The audit notes that one retry tree was incomplete after finding the improved incumbent; the final proof is the fully bound-certified frontier ledger, not a restricted-tree certificate.
- `results/alt_strengthened_v10_m2_low_1200s.json`: auxiliary strengthened compact fallback certified V10 M2 low, objective/LB/UB `0.824301313135`, gap `0`, verifier passed, wall `938.1947592s`. This is an original compact certificate, not BPC.
- `results/alt_strengthened_v10_m2_average_300s.json`: auxiliary strengthened compact standalone run did not certify V10 M2 average, but improved compact LB to `0.45611584972`.

Outcome:

- Pure BPC now certifies three target instances: V10 M2 average, V10 M1 average, and V12 M1 average.
- The tailored exact portfolio certifies four target instances: the three pure-BPC certificates plus V10 M2 low through compact fallback.
- V12 M2 average remains open. Current portfolio UB is `0.366168793171`, LB is `0.350523627890`, gap about `0.0427266`.
- No compact fallback result is reported as BPC, and no positive-gap result is reported as optimal.

## 2026-06-20: Route-Load BPC Dominance And Projection Bounds

Change:

- Added `ColumnPool` for exact-safe closed route-load column dominance.
- Added CLI controls `--column-dominance`, `--column-dominance-mode`, `--projection-bound`, `--penalty-domain-tightening`, and `--frontier-column-cache`.
- Added inventory-ratio interval projection lower bound and incumbent penalty-budget domain tightening.
- Filtered multi-column pricing output before RMP insertion while preserving exact-pricing closure requirements.
- Added dominance compression for BPC-owned route-column incumbent pools.
- Added proof documentation in `docs/optimization_proofs.md`.
- Added optimization update results under `results/optimization_update/`.

Validation:

- CMake was unavailable, so both executables were rebuilt with the fallback `g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic` commands.
- V4 smoke diagnostics ran for pricing, pricing-branch, cuts, branching, master, cg, gcap-cg, gcap-tree, and gcap-frontier.
- `results/optimization_update/raw/ablation_v4_full.json`: full BPC smoke certified the original V4 instance with objective/LB/UB `0`, gap `0`, verifier passed, `unresolved_intervals=0`, `invalid_bound_intervals=0`.
- `results/optimization_update/raw/stress_v12_m1_average_full_60s.json`: V12 stress smoke did not certify in 60s; UB `0.393080018005`, LB `0`, gap `1`, verifier passed. This is a noncertified diagnostic stress row only.

Outcome:

- The new optimizations preserve the existing V4 certificate in smoke ablations.
- The short V12 stress run shows the new stats and lower-bound hooks working, but it is not a certificate.
- Frontier column cache, route-support infeasibility cuts, and HGA/TGBC incumbent import remain TODOs.

## 2026-06-20: Frontier Ledger, Safe Duplicate Pricing, And Movement Domains

Change:

- Fixed incomplete `gcap-frontier` reporting so top-level lower bounds come from the minimum valid interval lower bound instead of defaulting to zero.
- Added duplicate-negative pricing safeguards: duplicate or dominance-filtered negative projections leave a node unresolved unless exact pricing proves closure.
- Clarified dominance statistics with separate enumeration, dominance input/kept/removed, existing-projection removal, and RMP insertion counters.
- Added globally valid movement-reachable final-inventory domain tightening.
- Added deterministic best-bound initial frontier scheduling and exact-key interval relaxation caching.
- Added `dominance-test` diagnostic for artificial duplicate/different projection pools.

Validation:

- CMake was unavailable; rebuilt both executables with the fallback `g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic` commands.
- Smoke diagnostics passed on `testdata/examples/gcap_smoke_V4_M1.txt` for `pricing`, `pricing-branch`, `cuts`, `branching`, `master`, `cg`, `gcap-cg`, `gcap-tree`, `gcap-frontier`, and `dominance-test`.
- V4 ablation variants all preserved the BPC certificate with objective/LB/UB `0`.
- V12 M1/M2 average 60s stress ablations remained noncertified. V12 M1 improved-full reported a valid top-level lower bound `0.24680708541` instead of zero; V12 M2 remains a lower-bound hard case.

Outcome:

- No new original-problem certificate was obtained in this short round-two pass.
- The existing V4 smoke certificate is preserved.
- V8 and V10 source input files were not present locally; only V12 reference candidates were available for stress ablations.
- Plain CPLEX benchmark runs were skipped in this pass; CPLEX was used only by the inventory/route/Gini relaxation when available.
# 2026-06-20 Round-3 Frontier/Incumbent Safety Pass

- Implemented Gini frontier range audit fields and certificate gating against `min(incumbent objective,(V-1)/V)`.
- Added movement-bound audit mode, support-duration pricing pruning, relaxation-cache partial-hit/recompute counters, incumbent import metadata, and expanded JSON/CSV reporting.
- Captured a Windows access violation (`-1073741819`) in V12 M1 BPC-owned `pricing/portfolio` incumbent modes. Debug gdb trace identified `src/main.cpp:1393` reading `col.q[i]` from a malformed incumbent-pool candidate. Fixed by rejecting empty/undersized operation vectors before incumbent pool insertion/use. Post-fix repros exit cleanly.
- CMake was unavailable; built with the documented `g++` fallback.
- Smoke diagnostics passed on `testdata/examples/gcap_smoke_V4_M1.txt`, including `pricing`, `pricing-branch`, `cuts`, `branching`, `master`, `cg`, `gcap-cg`, `gcap-tree`, `gcap-frontier`, `dominance-test`, and `support-pruning-test`.
- Runnable local source instances found for this pass: V4 smoke and V12 regenerated candidates. V8/V10 source text files were not present in this checkout, so round-three ablation reruns for V8/V10 were skipped rather than fabricated.
- V4 smoke remains certified. V12 M1/M2 average remain noncertified in short ablations; improved_full gives modest lower-bound progress only.
- Raw outputs and summaries are in `results/optimization_update_round3/`.

# 2026-06-21 Round-4 Support-Duration And Incumbent Pass

- Started from merged `main` at `db20932d1690cb842bb5cabdc95f13e7bb7b81ad` and preserved pre-existing untracked round-three artifacts.
- Strengthened support-duration pricing pruning from one operation to the exact-safe `ceil(|S|/2)` pickup lower bound.
- Applied the same support-duration infeasibility test to complete route-mask relaxation mask filtering with vehicle-specific allowed masks and route-mask removal statistics.
- Added route JSON/CSV and HGA-style incumbent import plumbing, compact/compact-CPLEX seeding modes, and import diagnostics. Imported incumbents are verifier-gated upper bounds only.
- Added focused retry metadata for unresolved minimum-LB frontier intervals. The pass is certificate-neutral and does not remove intervals from the ledger.
- `--support-feasibility-oracle` is exposed but remains disabled by default; no heuristic support infeasibility cuts were added.
- CMake was unavailable; both executables were rebuilt with the documented `g++` fallback.
- Smoke diagnostics passed on `testdata/examples/gcap_smoke_V4_M1.txt`: `pricing`, `pricing-branch`, `cuts`, `branching`, `master`, `cg`, `gcap-cg`, `gcap-tree`, `gcap-frontier`, `dominance-test`, `support-pruning-test`, `route-mask-support-test`, and `incumbent-import-test`.
- V4 smoke remains certified with objective/LB/UB `0`.
- V12 M1 average best local seed in this pass was compact-CPLEX, UB `0.366157179488`; this is a verified seeded/hybrid upper bound, not pure BPC performance.
- V12 M2 average best local seed was BPC-owned portfolio/strong, UB `0.759438494406`.
- Short V12 ablations remained noncertified: improved_full V12 M1 gap `0.244343576775`; improved_full V12 M2 gap `0.223640060515`.
- Real V4/V12 support-duration and route-mask support counts were zero. Synthetic diagnostics demonstrate the strengthened rule on constructed cases where the old one-operation rule cuts nothing.
- All smoke, incumbent-audit, and ablation commands exited `0`; no captured log contained memory/address error signatures.
- Runnable local source inputs for V8/V10 were not found in this checkout; only historical logs/results were present.
- Raw outputs and summaries are in `results/optimization_update_round4/`.

Remaining TODOs:

- Find or regenerate compatible V8/V10 input files for the current parser so round-four ablations can cover the historical target cases.
- Add an exact support-feasibility oracle only if it can prove small-support infeasibility without timeouts or heuristics.
- Investigate stronger V12 lower bounds; support-duration pruning did not remove real V12 masks in this pass.

# 2026-06-21 Round-5 Focused Retry, Route-Pool Incumbents, And Compatibility Flow

- Started from merged `main` at `68fe5fb3ac0f8b2bbcffa65b962902db60f58e8a` and preserved the pre-existing untracked round-three raw JSON artifacts.
- Fixed focused min-LB retry execution so `--frontier-focused-min-lb-retry true` can spend remaining time on the unresolved relevant interval with the current minimum valid lower bound even when final closure is disabled.
- Added a frontier route-column pool and true-objective restricted route-column incumbent master. The master is verifier-gated and updates only the upper bound; it never contributes lower-bound evidence.
- Added interval integer-candidate auditing under the true `G + lambda P` objective with accepted/rejected candidate counts and rejection reasons.
- Added pickup-drop compatibility flow variables to the inventory/route/Gini relaxation. Pairs are removed only when directed metric-closure duration bounds prove pickup-before-drop infeasibility. On the two regenerated V12 instances, all pairs remained compatible.
- CMake was unavailable; both executables were rebuilt with the documented `g++` fallback commands.
- Smoke diagnostics passed on `testdata/examples/gcap_smoke_V4_M1.txt`: `pricing`, `pricing-branch`, `cuts`, `branching`, `master`, `cg`, `gcap-cg`, `gcap-tree`, `gcap-frontier`, `dominance-test`, `support-pruning-test`, `route-mask-support-test`, `incumbent-import-test`, `route-pool-incumbent-test`, and `pickup-drop-compat-flow-test`.
- V4 `gcap-frontier` remains certified with objective/LB/UB `0`, `unresolved_intervals=0`, `open_nodes=0`, and verifier passed.
- V12 M1 average best incumbent audit row was BPC-owned `local/pool/portfolio/strong`, UB `0.369698924539`. The short ablation rows with compact-style seed remained at UB `0.382683045935`, LB `0.258804234390`, gap `0.323711261476`.
- V12 M2 average best incumbent audit row was BPC-owned `strong/portfolio`, UB `0.759438494406`. The best short ablation lower bound was `0.587614408090`, gap `0.226251483934`.
- Focused retry executed in unresolved V12 rows, including V12 M1 `focused_retry_only` and `improved_full_long`, and V12 M2 focused variants. It did not make valid lower-bound progress before the short time caps.
- Route-pool incumbent diagnostics were verified, but the pool did not beat the best V12 BPC-owned seeds in this pass.
- All round-five smoke, incumbent-audit, and V12 ablation commands exited `0`; captured logs were scanned for address/access-violation, segmentation, `bad_alloc`, out-of-memory, and Windows access-violation signatures, with no hits.
- Plain CPLEX benchmark runs were skipped in this pass. CPLEX-style compact seeds appear only as labeled upper-bound sources where requested.
- Runnable local source inputs for V8/V10 were not found in this checkout; only historical logs/results were present.
- Raw outputs and summaries are in `results/optimization_update_round5/`.

Remaining TODOs:

- Strengthen V12 lower bounds beyond compatibility flow; the conservative compatibility test found zero incompatible pairs on the regenerated V12 inputs.
- Improve BPC-owned route-pool harvesting so the restricted pool can beat local/strong incumbents on V12.
- Implement exact support-feasibility cuts only after an exact no-timeout oracle is available; the switch remains disabled for certificate runs.
- Restore or regenerate compatible V8/V10 text inputs for current-parser ablation coverage.
## 2026-06-21 Round 6: Auto Incumbents, Route-Pool Harvesting, Focused Intensification, Transfer Caps

Implemented:

- `--bpc-incumbent auto` / `best-of-all` verified incumbent portfolio selection.
- Export of warm-start, priced, and integer-leaf BPC columns into the global route-column pool.
- Per-vehicle route-pool caps and dominance-preserving pool insertion statistics.
- Focused relaxation intensification for the current global-min-LB unresolved frontier interval.
- Quantity-aware pickup/drop transfer caps in the compatibility-flow relaxation.
- `--progress-log` / `--progress-interval-seconds` reporting; round-six traces were final-checkpoint oriented and were superseded by the periodic round-seven implementation.
- `pickup-drop-transfer-cap-test` diagnostic.

Tests:

- Built with direct `g++` fallback because CMake is not installed.
- Ran V4 diagnostics for pricing, pricing-branch, cuts, branching, master, cg, gcap-cg, gcap-tree, gcap-frontier, dominance-test, support-pruning-test, route-mask-support-test, incumbent-import-test, route-pool-incumbent-test, pickup-drop-compat-flow-test, and pickup-drop-transfer-cap-test. All exited `0`; V4 gcap-frontier remains certified with objective `0`.
- Ran V12 M1/M2 incumbent audit for greedy, local, pool, pricing, portfolio, strong, compact, compact-cplex, auto, and route-pool rows. All exited `0`.
- Ran V12 M1/M2 ablations for round5_baseline, auto_incumbent_only, route_pool_fixed_only, transfer_cap_flow_only, focused_intensification_only, improved_full, and improved_full_300s. All exited `0`.
- Scanned captured logs for address/access-violation, segmentation, `bad_alloc`, out-of-memory, and sanitizer signatures; none were found.

Best local V12 rows:

| Instance | Variant | UB | LB | Gap | Time (s) | Certified? |
|---|---|---:|---:|---:|---:|---|
| V12 M1 average | improved_full_300s | 0.367765009974 | 0.281531929781 | 0.234478750980 | 304.42 | no |
| V12 M2 average | improved_full_300s | 0.719065249476 | 0.585987841514 | 0.185070003118 | 292.15 | no |

Observations:

- Auto incumbent selection used verified candidates only. V12 M2 selected the BPC-owned portfolio/strong incumbent over weaker compact-CPLEX output. V12 M1 selected a compact tailored seed in the 300s production row because it verified and was slightly better than the BPC-owned candidates.
- Route-pool harvesting is working when interval trees execute: 300s V12 rows collected thousands of raw columns. Some 60s rows collected few columns because the short cap ended before substantial tree production.
- Focused intensification executed but did not close V12 intervals.
- Transfer-cap flow produced many capacity-limited compatible pairs, but did not by itself close either V12 average instance.
- No new original-problem certificate was obtained. V12 M1 and V12 M2 remain noncertified with positive gaps.

Skipped/limited:

- V8/V10 source `.txt` files were not present in this checkout, so those reruns were skipped.
- Plain CPLEX benchmark was skipped in this pass.
- 1200s V12 runs were not run locally because the required smoke, incumbent audit, and 60/300s ablation matrix already consumed substantial wall time; exact reproduction commands are saved in `results/optimization_update_round6/commands.md`.

Next TODOs:

- Periodic progress checkpoints were implemented in round seven; continue using them for long-run convergence diagnosis.
- Investigate why focused intensification often improves little despite additional relaxation time.
- Add a stronger lower-bound source for the V12 minimum-LB intervals; transfer caps and route-pool incumbents are not enough.

## 2026-06-21 Round 7: Adaptive Splitting, Operation Budgets, And Periodic Progress Traces

Implemented:

- Periodic `--progress-log` checkpoints with an initial empty-incumbent row,
  after-seed row, interval relaxation/tree rows, adaptive split rows, route-pool
  rows, and final summary.
- Adaptive splitting of unresolved global-min-LB Gini frontier intervals, with
  exact child coverage and inherited valid parent lower-bound floors.
- Route-mask operation-budget cuts in the route-mask relaxation using
  non-overestimating depot-cycle lower bounds and the operation-time
  conservation identity.
- Focused intensification metadata for split-triggered child processing and
  operation-budget use.

Tests:

- CMake was unavailable; both executables built with the documented `g++`
  fallback.
- V4 smoke diagnostics were run for pricing, pricing-branch, cuts, branching,
  master, cg, gcap-cg, gcap-tree, gcap-frontier, dominance-test,
  support-pruning-test, route-mask-support-test, incumbent-import-test,
  route-pool-incumbent-test, pickup-drop-compat-flow-test,
  pickup-drop-transfer-cap-test, route-mask-operation-budget-test, and
  adaptive-frontier-split-test.
- V4 `gcap-frontier` remained certified with objective `0`, gap `0`, and
  `certified_original_problem=true`.
- V12 M1/M2 ablations were run for 60s rows plus final 300s improved rows.

Best local V12 rows:

- V12 M1 improved_full_300s: UB `0.366563817616`, LB `0.279082208580`, gap
  `0.238653148053`; noncertified.
- V12 M2 improved_full_300s: UB `0.719065249476`, LB `0.595725069580`, gap
  `0.171528494787`; noncertified.

Convergence behavior:

- V12 M1 300s improved through incumbent quality and adaptive child processing,
  but left one unresolved interval.
- V12 M2 300s improved the lower bound from `0.583173497560` in the 60s
  baseline to `0.595725069580`; operation-budget cuts and adaptive splitting
  both contributed to the active lower-bound ledger.
- 1200s commands were prepared but not run locally because the smoke plus V12
  60s/300s suite consumed about 31 minutes of wall time.

Safety:

- All executed commands exited with code `0`.
- Captured logs were scanned for AddressSanitizer, access violation,
  segmentation, `bad_alloc`, out-of-memory, `-1073741819`, `3221225477`, and
  STATUS_ACCESS_VIOLATION signatures; none were found.
- Plain CPLEX was skipped, so no CPLEX comparisons or speedup claims are made.

Remaining TODOs:

- Run the prepared V12 1200s commands during a longer unattended slot.
- Investigate V12 M1 lower-bound sensitivity where operation-budget cuts did
  not improve short-run relaxation bounds.
- Evaluate route-mask operation budgets with vehicle-indexed pickup linking and
  exact small-support feasibility cuts, still requiring exact infeasibility
  proofs.

## 2026-06-21 Round 8: Vehicle-Indexed Relaxation And Focus Runs

Implemented:

- Vehicle-indexed route-mask operation relaxation with `y_{k,i}`, `p_{k,i}`,
  and `d_{k,i}` linked to route-mask variables, station disjointness, aggregate
  final inventories, vehicle pickup/drop balance, depot-return capacity, and
  mask operation-budget cuts.
- Vehicle-indexed pickup-drop transfer flow with `f_{k,i,j}` and depot-unload
  variables linked to vehicle route masks and safe duration/capacity transfer
  caps.
- Focus-only interval diagnostics through `--frontier-focus-only` and
  `--frontier-focus-interval-id auto`; results are explicitly diagnostic
  interval bounds, not original-problem certificates.
- Deterministic V8/V10 parser-compatible engineering benchmark generator under
  `scripts/generate_reference_instances.py` with generated inputs and manifest
  in `reference/generated/`.
- Reporting fix for bound-fathomed frontier certificates: exact pricing closure
  is required only when branch-price tree intervals contribute to the lower
  bound. Bound-fathomed-only certificates still require zero gap, full frontier
  coverage, zero unresolved/invalid intervals, zero open nodes, and verifier
  pass.

Tests:

- CMake was unavailable; both executables built with the documented `g++`
  fallback.
- V4 smoke diagnostics were run for pricing, pricing-branch, cuts, branching,
  master, cg, gcap-cg, gcap-tree, gcap-frontier, dominance-test,
  support-pruning-test, route-mask-support-test, route-mask-operation-budget-test,
  incumbent-import-test, route-pool-incumbent-test,
  pickup-drop-compat-flow-test, pickup-drop-transfer-cap-test,
  vehicle-indexed-relaxation-test, vehicle-indexed-transfer-flow-test, and
  adaptive-frontier-split-test.
- V4 `gcap-frontier` remained certified with objective `0`, gap `0`, and
  `certified_original_problem=true`.
- V12 M1/M2 round-eight ablations were run for round7 baseline, vehicle-indexed
  ops only, vehicle transfer flow only, focus interval only, improved_full,
  and improved_full_300s. V12 M2 improved_full_1200s was also run.

Best local V12 rows:

- V12 M1 improved_full_300s: UB `0.368581603155`, LB `0.284563809518`, gap
  `0.227948961416`; noncertified.
- V12 M2 improved_full_1200s: UB `0.719065249476`, LB `0.689651961258`, gap
  `0.0409048945689`; noncertified. The same UB/LB/gap appeared by the 300s
  row, so the 1200s run did not add valid lower-bound progress.

Focus-only interval outcome:

- V12 M1 selected interval `0`, range `[0,0.184291]`, and closed that interval
  diagnostically with interval LB `0.368581603155`.
- V12 M2 selected interval `0`, range `[0,0.372737]`, and closed that interval
  diagnostically with interval LB `0.745474506024`.
- These are interval-only diagnostics and do not certify the original problem.

V8/V10 restoration/generation:

- Historical runnable V8/V10 `.txt` inputs were not found in this checkout.
  Deterministic generated engineering benchmarks were created for V8_M2_average,
  V10_M1_average, V10_M2_average, and V10_M2_low.
- Generated V10_M2_average certified in `23.21s` with objective
  `0.0601270957314`; generated V10_M2_low certified in `23.54s` with objective
  `0.163171713361`.
- Generated V8_M2_average and V10_M1_average remained positive-gap 60s
  diagnostics. These generated cases are not historical paper targets.

Safety:

- Captured logs were scanned for AddressSanitizer, access violation,
  segmentation, `bad_alloc`, out-of-memory, `-1073741819`, `3221225477`, and
  STATUS_ACCESS_VIOLATION signatures; none were found.
- Plain CPLEX was skipped, so no CPLEX comparisons or speedup claims are made.

Remaining TODOs:

- Run V12 M1 improved_full_1200s when local time is available.
- Investigate why V12 M2 reaches the same lower bound by 300s and 1200s under
  vehicle-indexed transfer flow.
- Compare the generated V8/V10 engineering benchmarks with historical data if
  the original `.txt` sources are recovered.
- Consider exact small-support feasibility cuts only with a proof-producing
  oracle; heuristic support failures remain unusable as cuts.

## 2026-06-21 Round 9: Inventory Branching And Focus-Interval Closure

Implemented:

- Explicit focus targeting through `--frontier-focus-range`,
  `--frontier-focus-from-result`, and `--frontier-focus-leaf-id`, so diagnostic
  runs can target active unresolved adaptive leaves from a previous ledger.
- Compatible focus-bound import through `--frontier-import-interval-bound`,
  including active-leaf splitting when the imported range covers a strict
  subrange.
- Final-inventory branching rows in the branch-price tree, with pricing dual
  contributions through each column's signed inventory-change vector.
- Operation-mode branching restrictions for forbid-pickup and forbid-drop
  child nodes, enforced in pricing and node column screening.
- Branch-selection reporting for Ryan-Foster, inventory, operation-mode, and a
  bounded `strong` scoring mode. The current `strong` implementation is a search
  heuristic, not full child-LP strong branching.

Tests:

- CMake was unavailable; both executables built with the documented `g++`
  fallback.
- V4 smoke diagnostics were run for pricing, pricing-branch, cuts, branching,
  master, cg, gcap-cg, gcap-tree, gcap-frontier, dominance-test,
  support-pruning-test, route-mask-support-test, route-mask-operation-budget-test,
  incumbent-import-test, route-pool-incumbent-test,
  pickup-drop-compat-flow-test, pickup-drop-transfer-cap-test,
  vehicle-indexed-relaxation-test, vehicle-indexed-transfer-flow-test,
  adaptive-frontier-split-test, inventory-branching-test, and
  operation-mode-branching-test.
- V4 `gcap-frontier` remained certified with objective `0`, gap `0`, and
  `certified_original_problem=true`.
- V12 M2 focus-only `[0.465922,0.512514]` ran for 300s and improved that
  interval lower bound from `0.496993274667` to `0.689652394993`, but did not
  close the interval.
- V12 M1 focus-only `[0.230364,0.276436]` ran for 300s and improved that
  interval lower bound from `0.234802392857` to `0.330637007941`, but did not
  close the interval.
- A full V12 M2 frontier run imported the compatible V12 M2 focus bound,
  accepted one imported interval bound, and ended with UB `0.719065249476`,
  LB `0.712948394993`, gap `0.008506675142`, one unresolved interval, and no
  certificate.
- A corrected `--frontier-focus-from-result` diagnostic parsed the full-import
  ledger and selected the unresolved leaf `[0.489218,0.512514]`; it kept LB
  `0.712948394993` and remained diagnostic/noncertified.
- A full V12 M1 300s run ended with UB `0.369698924539`, LB
  `0.282149235152`, gap `0.236813481393`, two unresolved intervals, and no
  certificate.
- Generated V8/V10 engineering benchmark 60s runs completed for V8_M2_average,
  V10_M1_average, V10_M2_average, and V10_M2_low. All remained positive-gap
  diagnostics under the short budget and are not historical paper targets.

Safety:

- All executed commands exited with code `0`.
- Captured logs were scanned for address/access-violation, segmentation,
  `bad_alloc`, out-of-memory, `fatal`, and related memory/error signatures; none
  were found.
- Plain CPLEX was skipped, so no CPLEX comparisons or speedup claims are made.
- The V12 M2 1200s focus/import commands were not run in this pass because the
  smoke, generated V8/V10, V12 focus, branch-selection, and V12 full 300s suite
  consumed the available local run budget. Commands are recorded in
  `results/optimization_update_round9/commands.md` for unattended reproduction.

Remaining TODOs:

- Run V12 M2 focus-only and full imported-bound 1200s rows during a longer
  unattended slot.
- Upgrade the bounded `strong` selector to true child-LP/CG strong branching if
  the runtime budget can support it.
- Add deeper compatibility hashing for imported interval-bound reuse across
  independent command invocations.
- Investigate the remaining V12 M2 leaf `[0.489218,0.512514]`, which controls
  the full-import 300s gap after the focus-bound split.

## 2026-06-22 Round 10: Exact-CG Continuation And Pricing-Closure Audit

Implementation:

- Added strict pricing-closure status fields. Incomplete pricing, duplicate
  negative projection blockage, or remaining negative reduced cost now forces
  `pricing_closure_certified_exact=false`.
- Added frontier state export/resume metadata. Open nodes are not serialized in
  this build; resumed interval runs rebuild the exact tree from compatible
  interval metadata, incumbent scalar data, and generated-column counts.
- Added exact-CG continuation controls and reporting fields. The implementation
  uses the existing tree/CG machinery with larger iteration and multi-column
  pricing budgets.
- Added dual-stabilization CLI/reporting. Smoothing is recorded but true-dual
  pricing is used for certificate safety; actual stabilized discovery remains a
  TODO.
- Added `pricing-closure-audit-test` and `resume-state-test` smoke diagnostics.

Results:

- V4 `gcap-frontier` remains certified with objective `0`.
- V12 M2 exact-CG focus `[0.489218,0.512514]`, 300s: UB
  `0.719065249476`, LB `0.712948394993`, gap `0.008506675142`,
  `pricing_closure_status=pricing_time_limit`, not certified.
- V12 M2 resume from exported state, 300s: compatible state loaded with 1107
  columns and interval LB `0.712948394993`; the resumed run reproduced the same
  LB/UB/gap and remained noncertified.
- V12 M2 full frontier importing the focus result, 300s: imported bound
  accepted, UB `0.719065249476`, LB `0.657495783410`, gap
  `0.085624310327`, `pricing_closure_status=negative_columns_remaining`, not
  certified.
- V12 M1 full frontier importing the round-nine focus result, 300s: imported
  bound accepted, UB `0.375405784113`, LB `0.330637`, gap `0.119254380214`,
  not certified. Other intervals still control full closure.

Safety:

- CMake was unavailable; fallback g++ builds succeeded for `ExactEBRP.exe` and
  `ExactEBRPCompare.exe`.
- All smoke and V12 commands exited with code `0`.
- Logs in `results/optimization_update_round10/logs` were scanned for memory,
  address, access-violation, segmentation, `bad_alloc`, fatal, and Windows
  access-violation code signatures. No matches were found.
- Plain CPLEX was skipped. No CPLEX speedup or certificate comparison is made.

Remaining TODOs:

- Serialize live BPC open nodes for stronger resume, or document exact limits
  for every resume-mode result.
- Implement actual dual-stabilized column discovery, followed by exact true-dual
  final pricing verification.
- Run V12 M2 exact-CG focus and full imported/resumed frontier at 1200s or
  3600s in an unattended slot.

## 2026-06-22 Round 11: Iterative Closure And Pricing Verifier

Implementation:

- Added interval-level `interval_certificate_basis`,
  `interval_requires_pricing_closure`, `interval_pricing_closure_available`,
  `interval_bound_valid`, and `interval_bound_source_list` reporting.
- Added full-result certificate-basis fields and rejection reasons. BPC
  optimality now also requires any pricing-closure obligations reported by the
  interval bases to be satisfied.
- Added iterative frontier closure over the current minimum-LB unresolved leaf.
  It refreshes relaxation bounds, runs focused exact-CG/tree continuation,
  checkpoints pricing verifier state, and updates the same full ledger.
- Added partial open-node state export/resume metadata. This is explicitly
  reported as warm restart (`open_node_state_resume_exact=false`) until live
  node-local queues are serialized.
- Added final pricing-verifier checkpoint/resume plumbing and smoke diagnostics
  for pricing verifier, iterative closure, and certificate-basis audit.

Results:

- V4 `gcap-frontier` remains certified with objective `0`; every interval is
  reported as `gamma_floor_skip`, so pricing closure is not required.
- V12 M2 iterative reserved 300s targeted `[0.465922,0.489218]` and
  `[0.489218,0.512514]`. Bounds did not improve; UB `0.719065249476`, LB
  `0.689651961258`, gap `0.040904894569`, not certified.
- V12 M1 multi-focus import 300s accepted one compatible focus bound and reached
  UB `0.368581603155`, LB `0.34466673345`, gap `0.064883514261`, not
  certified.
- V12 M1 iterative lite 300s executed two iterative rounds and remained open
  with UB `0.369698924539`, LB `0.330637007941`, gap `0.105658723910`.
- V12 M2 resume 60s loaded compatible state metadata and one saved open-node
  count; it is reported as partial warm restart, not exact open-node resume.

Safety:

- CMake was unavailable; fallback g++ builds succeeded for both executables.
- All V4 smoke and V12 round-eleven commands exited with code `0`.
- Round-eleven logs were scanned for memory/address/access-violation,
  segmentation, `bad_alloc`, fatal, and Windows access-violation code
  signatures. No matches were found.
- Plain CPLEX was skipped. No CPLEX speedup or certificate comparison is made.

Remaining TODOs:

- Serialize true live BPC open-node queues, including node-local RMP columns and
  active cuts.
- Complete a resumable true-dual route-load pricing verifier; current
  checkpointing is conservative and does not certify incomplete pricing.
- Run V12 M2 and V12 M1 iterative closure at 1200s/3600s in an unattended slot.

## 2026-06-22 Round 12: Scalable Pricing And Large-Instance Support

Implementation:

- Added a `StationSet` abstraction with compact and dynamic backends, stable
  serialization, equality, subset/intersection operations, popcount, iteration,
  and hashing. Route-load columns and dominance keys now preserve dynamic
  station sets, avoiding projection-key collapse when V exceeds integer-mask
  capacity.
- Added large-instance reporting fields and guards. For V>32, all-subset
  route-mask enumeration is disabled in large-instance mode unless a certifying
  replacement is available; affected rows are diagnostic only.
- Added hybrid/ng-DSSR pricing options and a scalable pricing diagnostic path.
  DSSR currently inserts only verified elementary route-load columns and
  reports `dssr_incomplete` unless final exact verification completes.
- Implemented smooth/box dual-stabilized column discovery for ng-DSSR ranking
  and operation choice. Returned columns are still evaluated with true duals,
  and closure remains true-dual only.
- Added `--external-incumbent`, `--external-incumbent-format`, and
  `--export-incumbent`. A synthetic route JSON import passed the independent
  verifier; a malformed route was rejected.
- Extended `scripts/generate_reference_instances.py` with deterministic
  V20/V50/V100 engineering scalability cases. Python was unavailable locally,
  so equivalent parser-compatible files were generated with a PowerShell
  fallback and recorded in `reference/generated/manifest.csv`.

Results:

- CMake was unavailable; fallback g++ builds succeeded for `ExactEBRP.exe` and
  `ExactEBRPCompare.exe`.
- V4 smoke diagnostics all exited `0`, including `station-set-test`,
  `ng-dssr-pricing-test`, `dssr-exactness-test`,
  `dual-stabilization-test`, `external-incumbent-test`, and
  `large-instance-mode-test`. V4 `gcap-frontier` remains certified with
  objective `0`.
- V12 M2 `gcap-frontier` hybrid-flag 300s remained noncertified:
  UB `0.719065249476`, LB `0.689651961258`, gap `0.0409048945689`,
  `unresolved_intervals=3`.
- V12 M1 `gcap-frontier` hybrid-flag 300s remained noncertified:
  UB `0.368581603155`, LB `0.330636509913`, gap `0.102948961415`,
  `unresolved_intervals=2`.
- V12 M2 pricing exact-label and ng-DSSR diagnostics both completed with exact
  no-negative status on the diagnostic pricing oracle. These are not original
  problem certificates.
- V70 and V100 generated inputs parsed and ran large-instance diagnostics with
  dynamic `StationSet`; no mask overflow, access violation, `bad_alloc`, or
  memory/address error was observed in the captured logs.
- V20/V50/V100 hybrid pricing rows are scalability diagnostics only and report
  incomplete DSSR closure.

Safety:

- No positive-gap row is reported as optimal.
- Plain CPLEX was skipped. No CPLEX speedup or certificate comparison is made.
- Full frontier internals still use the established exact-label BPC pricing
  path; the new ng-DSSR engine is currently exercised through pricing
  diagnostics and is not yet a certifying replacement inside every BPC tree.

Remaining TODOs:

- Thread pricing-engine options through all BPC/tree column-generation entry
  points so hybrid ng-DSSR can accelerate frontier closure, followed by exact
  true-dual verification.
- Complete DSSR exactness refinement for larger V instead of reporting
  `dssr_incomplete`.
- Add a memory profiler or OS-level peak memory measurement; current
  `memory_peak_estimate_mb` is a deterministic data-structure estimate.
- Run V12 M2 and V12 M1 closure with hybrid pricing after it is fully wired
  into BPC tree pricing.

## 2026-06-22 Round 13: Production Hybrid Pricing In BPC

Implementation:

- Threaded `PricingOptions` through gcap-CG, gcap-tree, gcap-frontier,
  focused closure, and iterative closure so explicit `--pricing-engine hybrid`
  requests reach BPC pricing calls.
- Changed explicit hybrid/ng-DSSR requests to use the scalable pricing engine
  on V12 as well as larger instances. Small V rows still require exact final
  verification before any pricing-closure claim.
- Added BPC pricing-engine counters for requested/used engine, fallback count,
  nodes using hybrid/ng-DSSR/exact-label, DSSR incomplete nodes, and final
  verifier calls.
- Strengthened DSSR reporting with neighborhood mode, initial/final memory,
  repeated-station events, no-negative-relaxed-route status, and true-dual
  final-verification time.
- Threaded smooth/box stabilization into BPC pricing as column-discovery duals;
  all inserted columns remain true-dual checked.
- Added `--large-lb-mode` with global `inventory-only` and
  `movement-projection` lower-bound diagnostics, while keeping restricted
  column-pool evidence diagnostic.
- Added `scripts/convert_hga_incumbent.py` for route JSON, CSV, and simple
  legacy-text incumbent conversion. The solver still verifies every imported
  route plan independently.

Results:

- CMake was unavailable; fallback `g++` build succeeded.
- V4 smoke diagnostics exited `0`. V4 `gcap-frontier` remains certified with
  objective `0` under exact-label and under explicit hybrid with exact final
  verification.
- V12 M2 focus exact-label 300s: UB `0.780792889928`, LB `0.712948394993`,
  gap `0.086891793983`, noncertified.
- V12 M2 focus hybrid 300s and hybrid smooth 300s matched the same LB/UB, used
  hybrid with no fallback, found elementary negative columns, and remained
  noncertified because DSSR closure was incomplete.
- V12 M2 full frontier 300s: exact-label and hybrid both remained nonclosed
  with LB about `0.684222130220`, UB `0.780792889928`, gap about `0.12368`.
- V12 M1 full frontier 300s: exact-label LB `0.338980588720`; hybrid smooth
  LB `0.334782317080`; both remained noncertified.
- V20 generated hybrid frontier 300s ran through the BPC hybrid path and
  remained nonclosed: UB `1.13623075045`, LB `0.368133269885`, gap `0.6760`.
- V50/V100 generated hybrid pricing diagnostics ran without memory/address
  error signatures and correctly reported incomplete DSSR/time-limit status.
- V4 export/re-import incumbent matched verifier expectations. A malformed V50
  external incumbent was rejected with no incumbent update.

Safety:

- No positive-gap row is reported as optimal.
- Relaxed DSSR rows with incomplete exactness are noncertified.
- No access violation, segmentation fault, `bad_alloc`, out-of-memory, ASan, or
  fatal exception signature was found in the captured round-thirteen logs.
- Plain CPLEX was skipped. No CPLEX speedup or certificate comparison is made.

Remaining TODOs:

- Make DSSR refinement prove exactness on more BPC nodes instead of stopping
  after finding elementary negative columns that require final exact closure.
- Add a production final exact pricing verifier that can complete on the V12
  hard intervals under hybrid-discovered columns.
- Strengthen nonzero global lower bounds for V50/V100 without all-subset
  route-mask enumeration.
- Add OS-level peak-memory measurement in addition to deterministic memory
  estimates.

## 2026-06-22 Round 14: Two-Track Relaxed Route-Load BPC

Implementation:

- Added route-load column classification fields for elementary feasible columns
  and ng-relaxed lower-bound columns.
- Included column kind in dominance projection keys so lower-bound-only
  relaxed representatives cannot replace elementary feasible representatives.
- Threaded `--column-tracks`, `--relaxed-columns-in-rmp`,
  `--relaxed-columns-max-per-pricing`, `--rmp-column-space`,
  `--dssr-close-relaxed-pricing`, and `--large-relaxed-rmp` through pricing
  options and result output.
- Added conservative two-track hybrid pricing: relaxed RMP columns are created
  only from verified elementary projections; non-elementary relaxed routes
  remain rejected until projection feasibility is proven.
- Added relaxed-RMP certificate fields and ng-relaxed pricing closure fields.
  Relaxed-RMP objectives are certificate-valid only when ng-relaxed pricing
  closes.
- Filtered relaxed columns from route-pool incumbent insertion, route-pool DFS
  selection, route export, and BPC leaf route reconstruction.
- Added smoke diagnostics:
  `two-track-column-test`, `relaxed-rmp-test`,
  `relaxed-pricing-closure-test`,
  `relaxed-column-incumbent-safety-test`, and
  `large-relaxed-rmp-test`.
- Added a UB sanity guard for large-instance lower-bound diagnostics: a
  computed lower bound above a verified incumbent UB is rejected as invalid
  evidence.

Results:

- CMake was unavailable; fallback `g++` build succeeded for
  `ExactEBRP.exe` and `ExactEBRPCompare.exe`.
- V4 smoke diagnostics exited `0`. V4 `gcap-frontier` remained certified with
  objective `0` under exact-label and under two-track hybrid.
- V12 M2 focus exact-label 300s and two-track 300s both remained nonclosed:
  UB `0.780792889928`, LB `0.712948394993`, gap about `0.08689`.
- V12 M2 full frontier 300s improved from exact-label LB
  `0.684003547210` to two-track LB `0.710571053706`, still noncertified.
- V12 M1 full frontier 300s changed from exact-label LB `0.337454471060` to
  two-track LB `0.337666891430`, still noncertified.
- V20 generated two-track frontier 300s ran and remained nonclosed:
  UB `1.13623075045`, LB `0.372692167178`.
- V50/V100 generated relaxed-RMP diagnostics ran without crashes. Their
  movement-projection fallback exceeded the verified empty-route UB and was
  therefore rejected; rows remain diagnostic with LB `0`.
- No access violation, segmentation fault, `bad_alloc`, out-of-memory, ASan,
  or fatal `ExactEBRP error` signature was found in round-fourteen logs.
- Plain CPLEX was skipped.

Remaining TODOs:

- Implement projection-safe non-elementary relaxed route columns so relaxed
  RMPs can materially strengthen lower bounds beyond elementary projections.
- Complete ng-relaxed pricing closure over the selected relaxed state space
  without relying on elementary exact closure.
- Integrate a stronger scalable large-instance global LB that does not exceed
  verified incumbents and does not require all-subset route masks.
- Add OS-level peak-memory measurement.
## 2026-06-22 - Round 15: Projection-Safe Relaxed-RMP CG

- Implemented projection-safe non-elementary ng-relaxed route-load columns for
  the lower-bound RMP.  The validator checks net inventory projection, load
  trajectory, station final capacity, depot unload, route duration, branch
  projection, and operation-mode projection before relaxed columns are inserted.
- Added relaxed-RMP CG controls and reporting:
  `--allow-non-elementary-relaxed-columns`, `--relaxed-projection-strict`,
  `--ng-relaxed-closure`, `--relaxed-rmp-cg`,
  `--frontier-relaxed-rmp-cg`, and `--large-relaxed-rmp-cg`.
- V4 exact and two-track frontier rows remain certified at objective 0.
- V12 M2 exact full 300s ended at LB 0.702420, UB 0.780793, gap 0.100377.
  V12 M2 two-track relaxed-RMP CG inserted relaxed columns but remained
  noncertified at LB 0.681925, UB 0.780793, gap 0.126625.
- V12 M1 exact and two-track rows both remained noncertified at LB 0.325981,
  UB 0.386764, gap 0.157159; the two-track row inserted 8 non-elementary
  relaxed columns.
- Generated V20 remained noncertified with LB 0.359196, UB 1.136231, gap
  0.683871.  Generated V50/V100 relaxed-RMP CG rows were diagnostic with
  incomplete ng-relaxed pricing closure and zero valid global relaxed LB.
- No original-problem certificate was obtained beyond the V4 smoke instance.
  CPLEX was skipped.
- TODO: implement a stronger complete ng-relaxed label enumeration/checkpoint
  routine for V20+; improve large-instance relaxed column generation so V50/V100
  produce nonzero diagnostic relaxed-RMP trajectories; investigate why V12 M2
  two-track relaxed columns did not improve the full frontier lower bound.

## 2026-06-23 - Round 16: Paper Algorithm Consolidation

- Added production presets: `paper-bpc-core`, `paper-exact-portfolio`,
  `paper-bpc-experimental`, and `diagnostic-large`.
- Added `RunConfigSnapshot` and option-consistency audit fields so JSON, CSV,
  progress traces, notes, and certificate audits use the same resolved options.
  Results with mismatched active options are diagnostic and cannot certify.
- Added verified incumbent archive scanning. Only reconstructable route plans
  that pass the independent verifier can update the incumbent; objective-only
  rows are ignored.
- Added instance scope/hash/source fields to separate smoke, regenerated
  engineering, historical target, and large diagnostic rows.
- Ran V4 smoke diagnostics successfully. V4 frontier remains certified at
  objective 0 under production presets.
- V12 M1 `paper-bpc-core` 300s: UB 0.368581603155, LB 0.336357248340, gap
  0.087428006550, noncertified.
- V12 M2 `paper-bpc-core` 300s: UB 0.719065249476, LB 0.698710208326, gap
  0.028307641296, noncertified.
- V12 M1 `paper-exact-portfolio`: BPC row remained noncertified at UB
  0.368581603155/LB 0.337408507830; compact companion row remained
  noncertified at UB 0.357200583208/LB 0.321514225010.
- V12 M2 `paper-exact-portfolio`: BPC row remained noncertified at UB
  0.719065249476/LB 0.698710208326; compact companion row remained
  noncertified at UB 0.752394062701/LB 0.572735131170.
- Generated V8/V10/V20 paper-core rows and V50/V100 diagnostic-large rows ran
  and are labeled regenerated/diagnostic, not historical targets.
- Result-integrity audit reported zero failures. No new certificate was
  obtained beyond V4.
- TODO: recover or locate historical V8/V10/V20 sources for paper-comparable
  runs; run the full 300s ablation matrix on a longer compute budget; decide
  whether compact fallback should be automated in a single executable portfolio
  command rather than represented by companion rows.

## 2026-06-25 - Paper-Core Certificate Safety Pass

- Narrowed the paper-facing algorithm scope to GF-RL-BPC:
  `--method gcap-frontier --algorithm-preset paper-bpc-core`.
- Tightened `paper-bpc-core` so it uses exact-label elementary-column BPC and
  disables compact fallback certificates, hybrid/ng-DSSR, two-track relaxed
  RMP, large diagnostic modes, focus-only shortcuts, imported focus bounds,
  frontier resume, and iterative closure automation.
- Added `scripts/audit_bpc_certificate.py` with self-tests for incomplete
  pricing, duplicate negative-column blockage, partial frontier coverage,
  disabled route-mask enumeration used as certifying, and original optimality
  without `certified_original_problem=true`.
- Added a JSON output guard so original-problem `status=optimal` is not emitted
  unless the full certificate audit proves `certified_original_problem=true`.
- V4 paper-core smoke remains certified at objective 0 and passes the external
  certificate audit.
- V12 M1 Average 60s paper-core baseline:
  UB 0.357200583208, LB 0.178600291604, gap 0.5, unresolved intervals 2,
  controlling interval `4:[0.1786,0.238134]`, noncertified.
- V12 M2 Average 60s paper-core baseline:
  UB 0.719065249476, LB 0.359532624738, gap 0.5, unresolved intervals 2,
  controlling interval `4:[0.359533,0.479377]`, noncertified.
- Current plateau diagnosis is preliminary: both 60s rows are still controlled
  by gamma-floor child intervals after relaxation time, not by a fully traced
  branch-price pricing-closure plateau.
- TODO: add per-node and per-pricing-call trace output; run 300s/1200s V12 M1
  and V12 M2 paper-core rows; run plain compact CPLEX only as same-instance
  benchmark evidence.

## 2026-06-25 - Paper-Core Plateau Trace Artifact

- Added `bpc_trace_json` and `bpc_interval_trace_csv` result fields.
- `paper-bpc-core` runs with an output path now emit
  `*.trace.json` and `*.intervals.csv` next to the result JSON.
- The trace schema `paper_bpc_core_plateau_trace_v1` records the active
  frontier interval ledger, controlling interval, runtime bucket summary, and
  aggregate tree/pricing counters.
- Early zero-objective certificates now emit a minimal trace artifact so V4
  smoke certificates have the same audit trail.
- `scripts/audit_bpc_certificate.py` skips trace JSON artifacts by detecting
  top-level `trace_schema`; it audits only solver result JSON.
- V4 paper-core smoke still certifies objective 0 and passes the certificate
  audit. V12 M1 20s trace validation remains noncertified, as expected.
- Current limitation: branch-price node and pricing-call trace are still
  aggregate-only (`branch_price_node_trace_available=false`,
  `pricing_call_trace_available=false`). The next implementation step is
  instrumentation inside `ColumnGeneration.cpp`/`Pricing.cpp`.

## 2026-06-25 - Paper-Core Interval Trace Refinement

- Extended the interval trace ledger with real per-interval aggregate counters
  from branch-price tree runs: `bpc_nodes`, `generated_columns`, `cuts`,
  `pricing_calls`, `pricing_time_seconds`, `rmp_solve_time_seconds`, and
  `relaxation_time_seconds`.
- Added a distinct plateau reason,
  `tree_not_started_before_time_limit_or_reserve`, so queued unresolved leaves
  are not confused with branch-price trees that started and remain open.
- Rebuilt with the documented fallback g++ command and reran:
  - V4 paper-core smoke: certified objective 0, audit passed.
  - V12 M1 60s: UB 0.357200583208, LB 0.178600291604, gap 0.5,
    controlling interval `4:[0.1786,0.238134]`,
    reason `tree_not_started_before_time_limit_or_reserve`, noncertified.
  - V12 M2 60s: UB 0.719065249476, LB 0.359532624738, gap 0.5,
    controlling interval `4:[0.359533,0.479377]`,
    reason `tree_not_started_before_time_limit_or_reserve`, noncertified.
- Full certificate audit over `results/paper_bpc_core/raw` reports
  five solver JSON rows and zero failures.
- Current diagnosis: the 60s V12 rows are controlled by gamma-floor child
  intervals not yet expanded by BPC; the immediate bottleneck is relaxation
  time and frontier scheduling before the controlling leaf, not a pricing
  closure contradiction inside an explored tree.

## 2026-06-25 - Paper-Core Node/Pricing Trace Instrumentation

- Added structured branch-price node trace fragments in
  `runGiniCapBranchPriceTreeDiagnostic`.
- Added structured pricing-call trace fragments in the fixed-Gini column
  generation loop. Each pricing call records vehicle id, dual summary,
  requested/used pricing engine, reuse flag, generated columns, returned
  negative columns, route/operation state counts, support-pruning totals, best
  reduced cost, exact-completion flag, early-negative-stop flag, elapsed time,
  and unfinished-state count on timeout.
- `paper_bpc_core_plateau_trace_v1` now embeds `branch_price_nodes` and
  `pricing_calls` arrays when a branch-price tree starts for an interval.
- V8 generated tree-trace probe (`regen_V8_M2_average`, 60s diagnostic config)
  validates the trace path with 53 node trace objects and 100 pricing-call
  trace objects; the result remains noncertified and audit-safe.
- V12 M1/M2 60s rows were rerun with the current trace schema. Their
  node/pricing arrays are empty because the controlling leaves still do not
  reach a branch-price tree before the time/reserve stop.
- Full certificate audit over `results/paper_bpc_core/raw` reports six solver
  JSON rows and zero failures.

## 2026-06-25 - Paper-Core 300s Plateau Audit

- Reran V12 M1 and V12 M2 regenerated Average candidates with
  `--method gcap-frontier --algorithm-preset paper-bpc-core`, 300s time limit,
  exact-label elementary-column BPC, progress logs, interval CSV traces, and
  branch-node/pricing-call JSON traces.
- V12 M1 300s: UB 0.357200583208, LB 0.268414876140, gap 0.248559804329,
  unresolved intervals 2, open nodes 5, noncertified. The controlling interval
  `4:[0.1786,0.238134]` is a queued adaptive-split leaf; explored BPC nodes
  remain unresolved because pricing did not close.
- V12 M2 300s: UB 0.719065249476, LB 0.577560696100, gap 0.196789586869,
  unresolved intervals 2, open nodes 4, noncertified. The controlling interval
  `4:[0.359533,0.479377]` is queued with an inventory/route/Gini relaxation
  lower bound; explored BPC nodes also stop with `pricing_did_not_close`.
- The trace now gives actionable bottleneck evidence: started V12 branch-price
  nodes are dominated by exact-label pricing state explosion. Representative
  calls enumerate millions of route states and hundreds of millions of
  operation states, return negative columns, and therefore cannot certify
  pricing closure.
- Full certificate audit over `results/paper_bpc_core/raw` reports eight solver
  JSON rows and zero failures. Only the V4 smoke row is certified; V8/V12 rows
  are correctly labeled noncertified.
- TODO: run 1200s paper-core rows when local budget allows and investigate
  certificate-safe pricing pruning before making any paper-level V12 closure
  claim.

## 2026-06-25 - Completion-LB Pricing Pruning Diagnostic

- Implemented exact-label completion lower-bound pruning and exposed it as
  `--pricing-completion-lb-pruning`.
- The pruning is certificate-safe: it only skips a pricing label when a
  true-dual reduced-cost lower bound proves no feasible completion can improve
  the current best priced column. It is not used as a node-closure shortcut.
- Added `completion_lb_pruned_labels` to pricing results, BPC/tree aggregates,
  solver JSON, and per-pricing-call trace records.
- Rebuilt with the documented fallback g++ command.
- Validation:
  - V4 paper-core smoke remains certified at objective 0.
  - V12 M2 60s paper-core remains noncertified and controlled by a queued leaf;
    completion pruning does not trigger because that short run still does not
    reach the controlling BPC pricing plateau.
  - V8 generated tree-trace probe records
    `completion_lb_pruned_labels=9559313` at result level and remains
    noncertified/audit-safe.
- V12 M1 300s with pruning reaches the same LB/gap as the baseline and reduces
  captured operation states from about 1.48B to 1.11B in the branch-price
  pricing-call trace.
- V12 M2 300s with pruning remains noncertified and produces a weaker LB than
  the baseline in this row because the controlling split leaf keeps an inherited
  parent lower bound. The pruning is therefore not enabled by default in
  `paper-bpc-core`.
- Full certificate audit over `results/paper_bpc_core/raw` reports fourteen
  solver JSON rows and zero failures.
- TODO: investigate why the M2 controlling split leaf does not recover the
  stronger inventory/route/Gini relaxation lower bound before spending BPC
  time elsewhere.

## 2026-06-25 - Compatibility-Flow Relaxation Ordering

- Found a certificate-safe scheduling bottleneck in the inventory/route/Gini
  relaxation audit path. With pickup/drop compatibility enabled, the solver
  previously solved the compatibility-flow model before the no-compatibility
  model, then kept the larger valid lower bound. Some low-Gini V12 child
  intervals are already cutoff-fathomed by the easier no-compatibility model,
  so solving the compatibility model first could consume the remaining
  frontier budget and leave sibling split intervals with only an inherited
  parent lower bound.
- Changed the relaxation ordering to solve the no-compatibility model first.
  If that valid relaxation already cutoff-fathoms the interval, the
  compatibility-flow model is skipped. Otherwise both models are still solved
  and the maximum valid lower bound is used, preserving certificate semantics.
- Validation:
  - V4 paper-core smoke remains certified at objective 0.
  - V12 M1 300s remains noncertified with the same LB/gap as before
    (`LB=0.268414876140`, `UB=0.357200583208`, gap `0.248559804329`).
  - V12 M2 300s improves materially:
    `LB=0.692627421486`, `UB=0.719065249476`, gap `0.036766938758`.
    The previous 300s paper-core row had `LB=0.577560696100`, gap
    `0.196789586869`.
  - The new V12 M2 plateau is no longer the split child
    `[0.359532624738,0.479376832984]`; both low/mid children are now
    bound-fathomed by valid no-compatibility relaxation bounds. The remaining
    unresolved leaves are `[0.479376832984,0.599221041230]` and
    `[0.599221041230,0.719065249476]`, both at LB `0.692627421486`.
- Full certificate audit over `results/paper_bpc_core/raw` now covers
  seventeen solver JSON rows and zero failures.
- TODO: focus the next paper-core optimization on the new high-Gini plateau
  around `[0.479376832984,0.719065249476]`; V12 M2 remains noncertified.

## 2026-06-25 - Split-Before-Tree Frontier Scheduling

- Added `--frontier-split-before-tree` and enabled it in the
  `paper-bpc-core` preset. The option defers initial branch-price trees on
  broad adaptive-splittable intervals so child intervals can receive valid
  relaxation bounds before the solver spends most of its time in exact-label
  BPC pricing.
- The change is certificate-neutral: a deferred parent is not certified or
  counted in the final ledger after replacement; children exactly cover the
  parent interval and remain unresolved unless they are empty, validly
  bound-fathomed, or closed by exact branch-price pricing.
- Validation:
  - V4 paper-core split-before-tree smoke remains certified at objective 0.
  - V12 M2 non-split 1200s is noncertified and demonstrates the scheduling
    regression: `LB=0.469117173935`, `UB=0.719065249476`, gap
    `0.347601383495`, two unresolved intervals, twelve open nodes, and pricing
    time about 873s.
  - V12 M2 split-before-tree 300s is noncertified but improves the best valid
    paper-core lower bound to `LB=0.696966843140`, `UB=0.719065249476`, gap
    `0.0307321294594`, with two unresolved intervals and two open nodes.
- Full certificate audit over `results/paper_bpc_core/raw` now covers twenty
  solver JSON rows and zero failures.
- TODO: run a 1200s split-before-tree row and continue diagnosing the remaining
  high-Gini unresolved leaves. V12 M2 remains noncertified.

## 2026-06-25 - V12 M1 Paper-Core 1200s Plateau Trace

- Ran V12 M1 Average with `paper-bpc-core` for 1200s under the current
  split-before-tree scheduling.
- Result remains noncertified: `UB=0.357200583208`,
  `LB=0.332675660948`, gap `0.0686586848205`,
  `unresolved_intervals=2`, `open_nodes=2`,
  `invalid_bound_intervals=0`.
- The run improves over the earlier 300s paper-core LB
  `0.268414876140`, but still does not close the original problem.
- Runtime decomposition shows the remaining bottleneck clearly:
  pricing `896.6435636s`, master `79.5333302s`, bound/relaxation
  `211.0970326s`.
- Active unresolved leaves are `[0.223250364505,0.238133722139]`, still queued
  without a BPC tree, and `[0.238133722139,0.297667152674]`, which has open
  BPC nodes.
- Trace evidence includes 27 branch-price node summaries and 40 pricing-call
  summaries. The largest exact-label pricing calls enumerate roughly 7.07M
  route states and 299.9M operation states, so the next algorithmic target is
  certificate-safe pricing/branch closure rather than another side algorithm.
- Full certificate audit now covers twenty-one paper-core solver JSON rows and
  reports zero failures.
