# ExactEBRP Algorithm Report

Date: 2026-06-11

Scope note: this is a historical engineering report for the whole ExactEBRP portfolio. The paper algorithm is the full Gini-frontier route-load BPC documented in `docs/paper_bpc_algorithm_report.md`. Speedups reported below for `tailored` are compact/portfolio results unless explicitly labeled `gcap-frontier`; they are not BPC speedups and must not be cited as BPC success.

## Problem Statement and Data Assumptions

The project solves the Equity-aware Bike Repositioning Problem with stations `1..V` and depot `0`. Each vehicle starts empty at the depot, visits an elementary station sequence, performs one nonzero pickup or drop at each visited station, returns to the depot, and unloads remaining bikes. Station visits are disjoint across vehicles.

The parser supports the Hybrid GA sample format and the reference regenerated sample format. For compatibility with the old project, two conventions are currently used:

- Legacy weights with maximum `10.0` are scaled by `0.1`, matching `Instance_Generator.cpp`.
- If coordinates are present, distances are rebuilt from points with speed factor `1.5`, matching the old loader.

The old compact CPLEX source did not explicitly count final depot unloading in the route duration expression. This implementation uses the model specification identity:

`duration_k = travel_k + (tau_pick + tau_drop) * total_pickup_k`.

For the requested tests, `tau_pick=tau_drop=60`, so handling time is `120 * total_pickup`.

## Objective

For final inventory `Y_i`, define `r_i = Y_i / target_i`.

`H = sum_{i<j} |r_i-r_j|`, `S = sum_i r_i`, and `G = H / (V*S)`.

The penalty is `P = sum_i w_i |r_i - 1|`.

The objective is:

`min G + lambda * P`.

All reported objectives are independently recomputed in the JSON verification block from the reconstructed routes and operations.

## Implemented Formulations

### Compact CPLEX MILP

The compact MILP uses:

- Binary arc variables `x[k,i,j]`.
- Binary visit variables `z[k,i]`.
- Integer pickup/drop variables `p[k,i]`, `d[k,i]`.
- Binary pickup/drop mode variables so a station cannot both pick up and drop off on the same visit.
- Integer load variables and MTZ order variables.
- Integer final inventory variables `Y_i`.
- Continuous ratio, absolute deviation, and pairwise Gini numerator variables.
- Binary expansion of `Y_i` and McCormick variables for `G * Y_i`, matching the old product-linearization strategy.

The plain baseline includes the corrected operation-time conservation and pickup/drop mode constraints. The strengthened fallback additionally includes:

- Subset route-duration cuts using Held-Karp depot-cycle lower bounds for all subsets when `V<=12`.
- Simple symmetry cuts for identical vehicle capacities.

The CPLEX integration is command-line based, not Concert-linked, because the available build toolchain is MinGW while the local CPLEX C++ libraries are MSVC-oriented. The generated CPLEX script sets `threads`, `timelimit`, and `mipgap`.

### Route-Load Enumeration Mode

A route-load column is a complete feasible vehicle route and signed operation vector. The implementation enumerates elementary route orders, assigns bounded integer operations along each order, checks load and duration feasibility, and deduplicates columns by operation vector while retaining the shortest route.

If all route-load columns are materialized, the integer master is solved exactly by dynamic programming over station masks and final inventory vectors. This is a valid exhaustive-column certificate.

Current limitation: on `test_data_V8_M2_average.txt`, the enumerator generated about `1.45M` deduplicated vehicle columns in a 1-second diagnostic before completing vehicle 0. A V8 M1 materialization test on `test_data_V8_M1_low.txt` also failed to certify after generating about `50.0M` deduplicated columns. The timeout path now discards partial columns instead of merging them after interruption. The portfolio therefore guards full materialized enumeration and selects the strengthened compact exact fallback for `V>=8` or `M>=2`. This is not claimed as a closed branch-price certificate.

### Exact Pricing Oracle

The project now includes `include/Pricing.hpp` and `src/Pricing.cpp`, an exact one-vehicle route-load pricing oracle. It enumerates elementary station sequences, enforces vehicle load and station inventory bounds, uses the operation-time identity, and returns the best reduced-cost column for generic visit and operation dual coefficients. For each fixed route sequence, the integer pickup/drop subproblem is solved by an exact DP over `(position, load, pickup_total)`, which is exact because reduced cost is linear in the signed station operations.

`--method pricing` exercises this oracle as a diagnostic by minimizing one-column route duration with safe nonnegative-cost pruning and then independently verifying the selected route. On `V8 M2 average`, this completed for both vehicles in `0.0000991s` and selected route `[0,5,0]` with pickup `1` and duration `196.179910901`. On `V10 M2 average`, it completed in `0.0000348s` and selected route `[0,4,0]` with pickup `1` and duration `207.156335011`.

The pricing options now also support Ryan-Foster child restrictions. `forbid_together_pairs` rejects columns containing both branch stations; `require_together_pairs` rejects columns containing exactly one branch station. `--method pricing-branch` verifies both restrictions. On `V8 M2 average`, required-together pricing for pair `(1,2)` returns a column containing both stations with reduced cost `627.195774064`, while forbidden-together pricing returns a column not containing both with reduced cost `400.005618817`. On `V10 M2 average`, the corresponding reduced costs are `735.174209169` and `590.183901371`.

This is a required BPC building block. It is now connected to root LP diagnostics, including a fixed-Gini-cap EBRP master, but it is not yet inside a closed integer branch-price tree.

### 3-Subset-Row Cuts

The project now includes `include/Cuts.hpp` and `src/Cuts.cpp`. For every station triple `S`, the separator checks:

`sum_c floor(|A_c intersect S|/2) z_c <= 1`.

This cut is valid for the set-packing route-load master because at most one selected integer column can cover two or more stations from a three-station set without violating station disjointness. `--method cuts` exercises the separator on a feasible fractional pair-column triangle. On `V8 M2 average`, it finds triple `(1,2,4)` with `lhs=1.5`, `rhs=1`, violation `0.5`. On `V10 M2 average`, it finds triple `(1,2,3)` with the same violation.

The fixed-Gini branch-price master now separates these cuts dynamically at each node. Active cut duals are passed to pricing as an added reduced-cost term for columns containing at least two stations from the cut triple, so a priced node remains a valid full-column LP certificate.

### Ryan-Foster Branching

The project now includes `include/Branching.hpp` and `src/Branching.cpp`. For every station pair `(i,j)`, the scanner computes:

`sum_{c containing both i,j} z_c`.

If this value is fractional, the Ryan-Foster branch is:

`sum_{c containing both i,j} z_c = 0`

or

`sum_{c containing both i,j} z_c = 1`.

`--method branching` exercises the scanner on feasible fractional pair columns. On `V8 M2 average`, it selects pair `(1,2)` with together value `0.5` from diagnostic columns `{1,2}` and `{1,4}`. On `V10 M2 average`, it selects pair `(1,2)` with together value `0.5` from diagnostic columns `{1,2}` and `{1,3}`. This verifies the branching candidate logic; `--method pricing-branch` separately verifies that the pricing oracle can enforce the two child-node restrictions.

### Restricted Column Master

The project now includes `include/Master.hpp` and `src/Master.cpp`. The master solver exactly searches a supplied route-load column pool with:

- at most one selected column per vehicle,
- station-disjoint route masks,
- exact final-inventory aggregation from signed `q_i`,
- exact `G + lambda P` objective evaluation.

`--method master` builds all feasible one-stop pickup columns for each vehicle and solves that restricted integer master. On `V8 M2 average`, the one-stop pool has `212` columns; the exact restricted master processes `9,314` states, selects pickups at stations `4` and `7`, and verifies objective `0.653759267174`. On `V10 M2 average`, the pool has `396` columns; the master processes `34,984` states, selects pickups at stations `6` and `5`, and verifies objective `0.638754695152`.

This is a pool-optimal certificate for the supplied columns. It is not a global EBRP certificate unless the supplied column pool is the full feasible route-load set or a branch-price tree proves no missing improving columns.

### Root Column Generation Diagnostic

The project now includes `include/ColumnGeneration.hpp` and `src/ColumnGeneration.cpp`. `--method cg` solves a small required-pair coverage LP over route-load columns, extracts CPLEX LP duals, calls the exact pricing oracle, adds negative reduced-cost columns, and repeats until pricing proves no negative reduced-cost column for that diagnostic LP.

On `V8 M2 average`, the initial one-stop LP objective is `999.101328019`; exact pricing adds two pair columns with reduced cost `-371.905553955`; the second LP closes at objective `627.195774064` with best pricing reduced cost about `-2.1e-10`. On `V10 M2 average`, the initial LP objective is `1214.80299246`; pricing adds two pair columns with reduced cost `-479.628783296`; the second LP closes at objective `735.174209169` with best pricing reduced cost about `-1.5e-10`.

This verifies CPLEX LP solve, dual extraction, exact pricing, column insertion, and pricing closure for a simple master. It is not an EBRP optimality certificate because the diagnostic master is a required-pair coverage LP rather than the full EBRP equity master.

### Fixed-Gini-Cap Root Master Diagnostic

`--method gcap-cg` replaces the coverage-only LP with an EBRP-shaped continuous restricted master. The LP includes vehicle-use rows, station-disjoint visit rows, inventory equations, ratio equations, absolute satisfaction-deviation rows, pairwise Gini numerator rows, and the valid fixed-cap row:

`H <= V * gamma * S`.

The LP objective is `lambda * P`; the diagnostic reports `gamma + lambda*P` as a fixed-cap surrogate in notes and bound fields. CPLEX duals from inventory equations are passed to exact route-load pricing as signed operation coefficients, while vehicle and visit duals become fixed route-support coefficients. If `--gini-cap` is omitted, the command uses the empty-solution Gini plus a tiny tolerance so the initial LP is feasible. When `--gini-floor` is supplied, the LP also adds `H >= V*floor*S` and reports the valid interval lower-bound metric `floor + lambda*P`. Because the pairwise `h_ij` variables are lower envelopes for absolute differences and can be slack under a floor, the floor row is used only for lower bounds; any route incumbent is accepted only after the independent verifier confirms its true `G` lies inside the requested interval. When the restricted master is infeasible because the current column pool cannot satisfy the cap/floor rows, a phase-I master adds artificial inventory and Gini slack, minimizes their sum, prices real route-load columns from the phase-I duals, and switches back to the original master only after all artificial variables are zero. Identical vehicle capacities reuse one pricing proof per iteration when only the additive vehicle-row dual changes.

On `testdata/examples/gcap_smoke_V4_M1.txt`, this root LP closes in `0.226061s`: three pricing calls, two active master columns, `2,548` pricing states after operation DP, and best reduced cost `0`. This validates the full LP/dual/pricing/add-column loop on a tractable instance.

On `V8 M2 average`, the fixed-cap root LP now closes in `7.4304519s`. It uses `7` actual pricing oracle calls, leaves `12` active columns in the restricted master, processes `325,276,126` pricing states, and proves best reduced cost about `2.17e-18`. The fixed-cap LP surrogate closes at `gamma + lambdaP = 0.714138632029`.

On `V10 M2 average`, the same diagnostic does not close in `60s`: the first pricing call reaches `8,842,985` route states and `2,755,641,957` operation DP states, with best observed reduced cost `-0.0827812`.

This is still not an integer EBRP certificate. It is a root-LP pricing component that needs branch-price integration and stronger V10 pricing dominance before it can replace the compact fallback.

### Fixed-Gini-Cap Ryan-Foster Branch Probe

`--method gcap-branch` adds the first branch-price tree component on top of the fixed-cap root master. It closes the root fixed-cap LP, uses the Ryan-Foster scanner to select a fractional co-route station pair, and then attempts to close both child LP/pricing relaxations.

For a `together=0` child, columns containing both branch stations are filtered and pricing receives the pair as a forbidden-together restriction. For a `together=1` child, columns containing exactly one branch station are filtered, the LP adds `sum_c containing both z_c = 1`, and the dual of that row is passed to pricing as a pair coefficient. This makes branch restrictions active in both the restricted master and the exact pricing oracle.

On `testdata/examples/gcap_smoke_V4_M1.txt`, the probe closes root and both child relaxations in `1.0075024s`. It selects pair `(1,2)` with together value `0.75`; both child bounds close at `0.250000001`.

On `V8 M2 average`, the probe closes root and both child relaxations in `14.7525764s`. It selects pair `(1,8)` with together value `0.642857142857`; the root bound is `0.714138632029`, the `together=0` child bound is `0.714411385506`, and the `together=1` child bound is `0.714554806346`. Against the verified empty-route incumbent `0.848885378453`, the one-level branch bound gap is `0.158412426883`.

This is still not a full integer BPC certificate: only one branch level is closed. It verifies the branch-row/pricing-dual mechanics needed for a complete tree.

### Fixed-Gini-Cap Branch-Price Tree Diagnostic

`--method gcap-tree` extends the one-level probe into an open-node diagnostic tree. Each node solves the fixed-cap restricted LP by column generation with exact pricing. Branching currently uses:

- Ryan-Foster co-route pair branching.
- Station served/unserved branching when no fractional co-route pair remains.
- Final-inventory interval branching when station service is integral but some `Y_i` is fractional.

The implementation also detects CPLEX presolve-infeasible node LPs from the log when no `.sol` file is written. It starts with the empty-route fixed-cap incumbent only when the empty solution satisfies the supplied Gini cap and, if present, Gini floor; otherwise it starts without an incumbent and uses the phase-I master above to generate cap-feasible columns. With `--gcap-seed-cplex`, the diagnostic may also use a verified compact CPLEX solution only as a warm-start incumbent and route-column seed; the branch-price tree still has to close with exact pricing for a fixed-cap or interval certificate. If all station service, co-route pair values, and final inventories are integral but residual `z` values are fractional, the diagnostic now attempts to reconstruct an actual route-integer selection. The fallback reconstruction builds the signed operation vector implied by the integral projected inventory, enumerates feasible route orders for each vehicle/subset, and partitions active stations across vehicles.

On `testdata/examples/gcap_smoke_V4_M1.txt`, the fixed-cap tree exhausts all open nodes in `2.0121208s`: `9` nodes solved, `4` branch nodes, `2` nodes pruned by bound, `1` reconstructed route-integer leaf, `0` projected leaves, and `0` open nodes. The fixed-cap surrogate lower and upper bounds close at `0.250000001`; the reconstructed route reaches final inventory `[5,5,5,5]`, so the independently verified true EBRP objective is `0`.

On the same smoke instance with a stricter supplied cap `--gini-cap 0.05`, the initial restricted master is infeasible because the empty solution has `G=0.25`. Phase I generates real route columns, reaches zero artificial variables, and the fixed-cap tree closes in `1.8407275s` with `5` branch-price nodes, `17` columns, `17` pricing calls, fixed-cap surrogate bounds both equal to `0.05`, and the same verified true objective `0`.

With the exact interval `--gini-floor 0.05 --gini-cap 0.05`, the smoke instance exhausts the interval tree in `1.8113638s` with `11` branch-price nodes, `44` columns, and `29` pricing calls. It reports `gcap_interval_bound_complete`: the valid interval lower-bound metric is `0.05`, but no route-integer incumbent verifies inside the exact interval. The all-target route has true `G=0`, so it is correctly rejected as an interval incumbent and kept only as a lower-bound leaf.

On `V8 M2 average` with `--max-nodes 15`, the diagnostic exhausts its open nodes in `24.1877689s` after incumbent-bound pruning: `13` nodes solved, `6` branch nodes, `6` nodes pruned by bound, `1` reconstructed route-integer leaf, `0` projected leaves, and `0` open nodes. The fixed-cap surrogate lower and upper bounds close at `0.714554806346`. The reconstructed routes independently verify with true EBRP objective `0.544866745544`, `G=0.368387414104`, and `P=1.17652887627`.

On `V8 M2 average` at the compact incumbent exact interval `--gini-floor 0.129169959908 --gini-cap 0.129169959908 --gcap-seed-cplex --max-nodes 127`, the interval tree closes in `45.4876689s`: `29` branch-price nodes, `14` branched nodes, `9` nodes pruned by the seeded incumbent, `595` columns, and `121` exact pricing calls. The interval lower-bound metric and incumbent metric both close at `0.31908731186`, and the seed routes independently verify the same true EBRP objective `0.31908731186` with `G=0.129169959908` and `P=1.26611567968`.

This is still a cap/interval diagnostic. Its bound fields are for either `gamma + lambda*P` in cap mode or `floor + lambda*P` in interval mode, while `objective/G/P` are recomputed for the reconstructed route solution. The incumbent-gamma interval run is a strong cap-point certificate but not a full weighted-objective BPC proof, because solutions with lower `G` and different `P` require a closed gamma-frontier or another valid objective-space bound.

### Gamma-Frontier Diagnostic

`--method gcap-frontier` wraps the interval tree above. It obtains a verified incumbent, covers `G in [0, incumbent_objective]` with `--frontier-intervals` intervals, solves each interval with exact-pricing branch-price trees, and aggregates the interval lower bounds. It reports `optimal` only when every relevant interval is either closed or fathomed by a valid interval lower bound above the incumbent, and the minimum interval lower bound reaches the verified incumbent. Since `G >= incumbent_objective` cannot improve the incumbent objective, covering this range is sufficient for a global weighted-objective proof.

The frontier master now uses a stronger valid linear Gini lower estimator. For each interval it adds `g_lb >= floor` and `g_lb >= H/(V*S_max)`, where `S_max` is a station-bike-conservation upper bound on `sum_i r_i` tightened by active inventory upper branches, and minimizes `g_lb + lambda*P`. In incumbent-cutoff mode, `S_max` is tightened further by an exact final-inventory DP under the necessary condition `P <= (incumbent_objective-floor)/lambda` for any improving solution. This does not remove feasible improving integer solutions from the proof: if a solution could beat the incumbent, it satisfies that penalty budget, and the resulting `g_lb` remains no larger than its true Gini term. Closed intervals with no route-integer incumbent are treated as empty and do not reduce the aggregated lower bound.

The frontier driver also has adaptive retries. After the coarse interval pass, it reruns only unresolved intervals with the remaining wall time and a larger local node cap. This made the previously manual incumbent-neighborhood checks reproducible from one CLI command.

On `testdata/examples/gcap_smoke_V4_M1.txt`, the regression run over `[0,0.49]` reports `optimal` in `4.5195s`: `25` branch-price nodes, `115` columns, and `63` pricing calls. It finds the all-target route, independently verifies objective `0`, and the nonnegativity of both objective terms closes the global proof.

On `V8 M2 average` with `--frontier-intervals 2 --gcap-seed-cplex --max-nodes 31`, the strengthened frontier still does not close, but the lower bound improves from `0.185101` to `0.257212959552` and the reported gap drops to `19.3910%`. The low-Gini interval `[0,0.159544]` has `6` open nodes; the high-Gini interval `[0.159544,0.319087]` is bound-certified with lower bound `0.341031 > 0.319087`.

With `--frontier-intervals 2 --max-nodes 127`, the two intervals are fully certified in `130.6828s`, but the aggregated lower bound is only `0.283158881228`, so this is `gcap_frontier_bound_complete`, not optimal. With `--frontier-intervals 4 --max-nodes 63`, every interval is also certified in `202.4401s`; the first interval is empty, the middle interval closes, and the upper two intervals are bound-certified, but the same `0.283158881228` lower bound remains. With dynamic 3-subset cuts enabled, the same four-interval run adds `31` cuts and finishes in `210.9904s`; the upper two intervals receive cuts, but the global lower bound remains `0.283158881228`.

With incumbent-cutoff `S_max` tightening and adaptive retries, `V8 M2 average` now has a full weighted-objective route-load BPC/frontier certificate. The command `--frontier-intervals 8 --max-nodes 255 --time-limit 900 --gcap-seed-cplex` reports `optimal` in `568.6657s`, with verified objective/lower/upper bound all equal to `0.31908731186`, `G=0.129169959908`, `P=1.26611567968`, and gap `0`. The run solves `291` branch-price nodes, generates `5,678` active columns across interval solves, makes `896` exact pricing calls, and closes all eight intervals after one adaptive retry of `[0.119658,0.159544]`. Output: `results/v8_m2_average_gcap_frontier8_adaptive_cutoff.json`.

This is the first full-objective V8 BPC/frontier certificate in the project. It is exact, but not yet fast: it is much slower than the strengthened compact fallback and still uses compact CPLEX only to provide a verified incumbent seed.

### Inventory Branch-Search Mode

The project also includes a non-compact exact branch-search over station final inventories. It branches over every allowed integer final inventory value, uses interval lower bounds on `P` and `G`, and checks complete candidates with an exact route-load feasibility oracle.

The route oracle partitions active stations across vehicles and solves a Held-Karp-style DP over `(subset,last)` states, where the load after a subset is determined by the signed operation vector. This exactly proves whether a route order exists with load in `[0,Q]` and duration within `T`.

If this search exhausts its tree, it is a valid tailored exact certificate. It also includes a valid route-duration partition relaxation based on shortest depot cycles for station subsets, a triangle-inequality Gini numerator lower bound, a Lorenz/order-statistic interval lower bound for `H`, suffix pickup/drop feasibility pruning, a suffix DP that lower-bounds remaining satisfaction penalty subject to remaining pickup capacity and required net pickup/drop balance, and a suffix DP that upper-bounds feasible remaining `S` for the Gini denominator. The proof can split root station-domain branches across `--threads`. In current benchmarks, a 20-second diagnostic on `V8 M2 average` did not close (`46.7M` branch nodes). The Lorenz bound improved the 2-second incumbent-backed diagnostic to `7.2M` nodes, but a 10-second run still did not close (`39.2M` nodes). After threaded root splitting and feasible-`S` tightening, a 2-second incumbent-backed run still did not close (`17.0M` nodes, `0` route checks, `314` station-domain values). Dynamic penalty-budget interval tightening was neutral (`17.1M` nodes). The automatic portfolio therefore only enables this path for `V<=7` while retaining it for future optimization. Explicit diagnostics can be run with `--inventory-probe-max-v 8 --inventory-probe-seconds <seconds>`.

## Tailored Portfolio Flow

`--method tailored` currently runs:

1. Run inventory branch-search automatically for small guarded cases (`V<=7`, `M<=2`, `Q<=31`).
2. Size guard for materialized route-load enumeration.
3. If guarded out, solve the strengthened compact exact fallback with CPLEX.
4. Parse the CPLEX solution.
5. Independently verify routes, operation quantities, final inventories, `G`, `P`, and objective.
6. Report `optimal` only when a complete exact search or CPLEX reports optimality and verification passes.

This provides a certified exact portfolio result, but the current speedup comes from globally valid compact strengthening rather than from a closed BPC implementation.

## Build and Run

CMake project files are provided. In this environment `cmake` was not on PATH, so the verified build used:

```powershell
& 'D:\msys64\ucrt64\bin\g++.exe' -std=c++17 -O2 -Wall -Wextra -Iinclude src/main.cpp src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp -o build/ExactEBRP.exe
& 'D:\msys64\ucrt64\bin\g++.exe' -std=c++17 -O2 -Wall -Wextra -Iinclude src/compare_main.cpp src/Parser.cpp src/Evaluator.cpp src/Result.cpp src/Bounds.cpp src/TailoredExact.cpp src/Pricing.cpp src/Cuts.cpp src/Branching.cpp src/Master.cpp src/ColumnGeneration.cpp src/CplexBaseline.cpp src/Logger.cpp -o build/ExactEBRPCompare.exe
```

Example commands:

```powershell
./build/ExactEBRP.exe --method tailored --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 60 --log logs/v8_m2_average_tailored.log --out results/v8_m2_average_tailored.json
./build/ExactEBRP.exe --method cplex --plain-baseline --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V10_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 120 --log logs/v10_m2_average_cplex_plain.log --out results/v10_m2_average_cplex_plain.json
./build/ExactEBRPCompare.exe --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V10_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 120 --out results/compare_v10_m2_average.csv
./build/ExactEBRP.exe --method tailored --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 60 --inventory-probe-max-v 8 --inventory-probe-seconds 5 --log logs/v8_m2_average_inventory_probe5.log --out results/v8_m2_average_inventory_probe5.json
./build/ExactEBRP.exe --method pricing --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 10 --out results/v8_m2_average_pricing_diag.json
./build/ExactEBRP.exe --method pricing-branch --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 10 --out results/v8_m2_average_pricing_branch_diag.json
./build/ExactEBRP.exe --method cuts --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 10 --out results/v8_m2_average_cuts_diag.json
./build/ExactEBRP.exe --method branching --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 10 --out results/v8_m2_average_branching_diag.json
./build/ExactEBRP.exe --method master --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 10 --out results/v8_m2_average_master_diag.json
./build/ExactEBRP.exe --method cg --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 30 --out results/v8_m2_average_cg_diag.json
./build/ExactEBRP.exe --method gcap-cg --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 10 --out results/gcap_smoke_v4_m1_gcap_cg.json
./build/ExactEBRP.exe --method gcap-cg --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 30 --out results/v8_m2_average_gcap_cg_diag.json
./build/ExactEBRP.exe --method gcap-cg --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V10_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 60 --out results/v10_m2_average_gcap_cg_diag.json
./build/ExactEBRP.exe --method gcap-branch --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 20 --out results/gcap_smoke_v4_m1_gcap_branch.json
./build/ExactEBRP.exe --method gcap-branch --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 90 --out results/v8_m2_average_gcap_branch.json
./build/ExactEBRP.exe --method gcap-tree --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 60 --max-nodes 63 --out results/gcap_smoke_v4_m1_gcap_tree.json
./build/ExactEBRP.exe --method gcap-tree --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 60 --gini-cap 0.05 --max-nodes 63 --out results/gcap_smoke_v4_m1_gcap_tree_lowcap.json
./build/ExactEBRP.exe --method gcap-tree --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 60 --gini-floor 0.05 --gini-cap 0.05 --max-nodes 63 --out results/gcap_smoke_v4_m1_gcap_interval_lowcap.json
./build/ExactEBRP.exe --method gcap-tree --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 120 --max-nodes 15 --out results/v8_m2_average_gcap_tree15.json
./build/ExactEBRP.exe --method gcap-tree --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 180 --gini-floor 0.129169959908 --gini-cap 0.129169959908 --gcap-seed-cplex --max-nodes 127 --out results/v8_m2_average_gcap_interval_optgamma_seed127.json
./build/ExactEBRP.exe --method gcap-frontier --input testdata\examples\gcap_smoke_V4_M1.txt --lambda 0.15 --T 3600 --threads 1 --time-limit 60 --frontier-intervals 1 --max-nodes 63 --out results/gcap_smoke_v4_m1_frontier.json
./build/ExactEBRP.exe --method gcap-frontier --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 4 --time-limit 180 --frontier-intervals 2 --gcap-seed-cplex --max-nodes 31 --out results/v8_m2_average_gcap_frontier2_seed.json
./build/ExactEBRP.exe --method gcap-frontier --input '..\Hybrid GA\testdata\Smallnetwork2\test_data_V8_M2_average.txt' --lambda 0.15 --T 3600 --threads 8 --time-limit 900 --frontier-intervals 8 --gcap-seed-cplex --max-nodes 255 --out results/v8_m2_average_gcap_frontier8_adaptive_cutoff.json
```

## Historical Compact Portfolio Results

The table below is for the auxiliary `tailored` compact/portfolio method, not the paper BPC algorithm. It is retained for engineering history and incumbent-generation context only. Do not cite these rows as full Gini-frontier route-load BPC speedups. In particular, the V10 ratio is not a certified-optimal speedup because the plain CPLEX run did not certify.

| Instance | Tailored status | Tailored obj | Tailored LB | Tailored UB | Tailored time | Plain CPLEX status | Plain CPLEX LB | Plain CPLEX UB | Plain CPLEX gap | Plain CPLEX time | Speedup |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V8 M2 average | optimal | 0.319087311860 | 0.319087311860 | 0.319087311860 | 2.4877s | optimal | 0.319087311860 | 0.319087311860 | 0 | 5.6400s | 2.267x |
| V8 M2 low | optimal | 2.18621359223 | 2.18621359223 | 2.18621359223 | 0.6107s | optimal | 2.18621359223 | 2.18621359223 | 0 | 0.4491s | 0.735x |
| V8 M2 high | optimal | 0.359576511323 | 0.359576511323 | 0.359576511323 | 1.7932s | optimal | 0.359576511323 | 0.359576511323 | 0 | 1.3301s | 0.742x |
| V8 M1 low | optimal | 1.83063493255 | 1.83063493255 | 1.83063493255 | 0.3467s | optimal | 1.83063493255 | 1.83063493255 | 0 | 0.1823s | 0.526x |
| V8 M1 average | optimal | 0.795767180526 | 0.795767180526 | 0.795767180526 | 0.3021s | optimal | 0.795767180526 | 0.795767180526 | 0 | 0.2858s | 0.946x |
| V8 M1 high | optimal | 0.571697257514 | 0.571697257514 | 0.571697257514 | 4.0204s | optimal | 0.571697257514 | 0.571697257514 | 0 | 51.3916s | 12.783x |
| V10 M2 average | optimal | 0.463263009179 | 0.463263009179 | 0.463263009179 | 55.6407s | not certified | 0.43854431231 | 0.463263009179 | 5.3358% | 120.1633s | 2.16x |

The compact portfolio is faster than plain CPLEX on some V8 rows, but this does not satisfy the paper BPC speedup goal. Across all six V8 checks above, the median compact-portfolio speedup remains below 1 because several small cases are already very easy for the plain compact baseline.

Route-load BPC/frontier certificate status:

| Instance | Method | Status | Objective | Lower bound | Upper bound | Gap | Runtime | Nodes | Columns | Pricing calls |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V8 M2 average | gcap-frontier | optimal | 0.319087311860 | 0.319087311860 | 0.319087311860 | 0 | 648.2557s | 189 | 19,158 | 498 |
| V10 M2 average | gcap-frontier | optimal | 0.463263009179 | 0.463263009179 | 0.463263009179 | 0 | 1006.3825s | 28 | 12,615 | 76 |

Both rows are full Gini-frontier route-load BPC certificates for the original objective. The V8 result uses the current route-mask relaxation run and is exact, but remains slower than the plain compact CPLEX benchmark on that instance (`648.2557s` versus `31.9968s`). On V10 M2 average, BPC certified in `1006.3825s`; the matching plain CPLEX benchmark did not certify within `1200.1490s` and ended with gap `0.0245397104541`. Do not report this as a certified-optimal speedup because CPLEX did not close.

## Logs and Result Files

Key files:

- `results/compare_v8_m2_average.csv`
- `results/compare_v8_m2_average_current.csv`
- `results/compare_v8_m2_low.csv`
- `results/compare_v8_m2_high.csv`
- `results/compare_v8_m1_low.csv`
- `results/compare_v8_m1_average.csv`
- `results/compare_v8_m1_high.csv`
- `results/compare_v10_m2_average.csv`
- `results/paper_bpc_v8_m2_average_frontier_routemask_relax20_900s.json`
- `results/paper_bpc_v10_m2_average_frontier_routemask_relax20_refine18_1200s.json`
- `results/paper_cplex_v10_m2_average_plain_1200s.json`
- `results/v10_m2_average_tailored.json`
- `results/v10_m2_average_cplex_plain.json`
- `logs/v10_m2_average_tailored.log.cplex.log`
- `logs/v10_m2_average_cplex_plain.log`
- `results/v8_m2_average_incumbent_proof2_suffixfeas.json`
- `logs/v8_m2_average_incumbent_proof2_suffixfeas.log`
- `results/v8_m2_average_incumbent_proof2_suffixdp.json`
- `logs/v8_m2_average_incumbent_proof2_suffixdp.log`
- `results/v8_m2_average_incumbent_proof2_parallel.json`
- `logs/v8_m2_average_incumbent_proof2_parallel.log`
- `results/v8_m2_average_incumbent_proof2_widthorder.json`
- `logs/v8_m2_average_incumbent_proof2_widthorder.log`
- `results/v8_m2_average_incumbent_proof2_feasibleS.json`
- `logs/v8_m2_average_incumbent_proof2_feasibleS.log`
- `results/v8_m2_average_incumbent_proof2_budgetinterval.json`
- `logs/v8_m2_average_incumbent_proof2_budgetinterval.log`
- `results/v8_m1_high_inventory_proof30_parallel.json`
- `logs/v8_m1_high_inventory_proof30_parallel.log`
- `results/v8_m1_low_route_enum10.json`
- `logs/v8_m1_low_route_enum10.log`
- `results/v8_m2_average_pricing_diag.json`
- `results/v10_m2_average_pricing_diag.json`
- `results/v8_m2_average_pricing_branch_diag.json`
- `results/v10_m2_average_pricing_branch_diag.json`
- `results/v8_m2_average_cuts_diag.json`
- `results/v10_m2_average_cuts_diag.json`
- `results/v8_m2_average_branching_diag.json`
- `results/v10_m2_average_branching_diag.json`
- `results/v8_m2_average_master_diag.json`
- `results/v10_m2_average_master_diag.json`
- `results/v8_m2_average_cg_diag.json`
- `results/v10_m2_average_cg_diag.json`
- `results/gcap_smoke_v4_m1_gcap_cg.json`
- `results/v8_m2_average_gcap_cg_diag.json`
- `results/v10_m2_average_gcap_cg_diag.json`
- `results/gcap_smoke_v4_m1_gcap_branch.json`
- `results/v8_m2_average_gcap_branch.json`
- `results/gcap_smoke_v4_m1_gcap_tree.json`
- `results/gcap_smoke_v4_m1_gcap_tree_lowcap.json`
- `results/gcap_smoke_v4_m1_gcap_interval_lowcap.json`
- `results/v8_m2_average_gcap_tree15.json`
- `results/v8_m2_average_gcap_interval_optgamma_seed127.json`
- `results/gcap_smoke_v4_m1_frontier.json`
- `results/v8_m2_average_gcap_frontier2_seed.json`
- `results/v8_m2_average_gcap_frontier2_seed127.json`
- `results/v8_m2_average_gcap_frontier4_seed63.json`
- `results/v8_m2_average_gcap_frontier4_seed63_cuts.json`
- `results/v8_m2_average_gcap_frontier8_adaptive_cutoff.json`
- `results/v8_m2_average_gcap_frontier_interval_079_119_cutoff1023.json`
- `results/v8_m2_average_gcap_frontier_interval_119_159_cutoff1023.json`
- `results/v8_m1_high_gcap_frontier8_adaptive_cutoff.json`
- `results/gcap_smoke_v4_m1_frontier_adaptive_regression.json`
- `results/v8_m2_average_gcap_frontier_interval_tiny_open_seed255.json`

Each JSON includes route lists, station operations, final inventories, and an independent verifier block.

## Remaining Bottlenecks and Next Optimization Plan

The route-load BPC/frontier certificate now closes `V8 M2 average`, but it is not yet competitive with the compact fallback. The main unresolved algorithmic requirement is to make the BPC/frontier path fast and robust enough to replace compact CPLEX on V8 and to produce useful V10 certificates.

Next steps:

1. Remove the compact CPLEX seed dependency by adding a non-CPLEX primal heuristic or inventory-frontier incumbent generator.
2. Reduce repeated work in adaptive frontier retries by retaining branch nodes/column pools between passes instead of rerunning an interval from the root.
3. Strengthen pricing under arbitrary inventory duals for V10. The operation DP closes V8 root pricing, but V10 still spends billions of DP states in the first pricing call.
4. Add objective-space cuts over final-inventory boxes so incumbent-neighborhood intervals require fewer branch-price nodes.
5. Parallelize independent interval and branch-node solves while preserving a deterministic incumbent and lower-bound ledger.
6. Keep the strengthened compact CPLEX fallback as a verifier and incumbent source, but do not count it as BPC closure.
