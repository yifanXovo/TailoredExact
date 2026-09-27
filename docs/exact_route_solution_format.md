# Round 56 native route-solution format

Every official row with a verified final incumbent has one authoritative package under `results/gf_paper_benchmark_time_horizon_round56/solutions/<scenario_id>/`:

- `native_solution.json` contains the unchanged native vehicle indices, route order, complete node sequences, station operations, final inventory, objective components, bounds, certificate class, mathematical/run identities, T, M, Q, service times, source commit, executable hash, and separated timing fields;
- `routes.csv` provides one row for every available vehicle, including explicit unused `[0,0]` routes;
- `operations.csv` provides one ordered row per visited station;
- `final_inventory.csv` records depot and station initial, target, and final inventories;
- `solution_verification.json` records the independent disk-level verifier outcome;
- `solution_sha256.txt` hashes the five authoritative data and verification files.

A certified package is an exact optimal witness only when the official result has a strict original-problem certificate, complete valid interval coverage, a closed bound, and a passing original-solution verifier. A capped package is labeled `verified_incumbent_noncertified`; it is feasible evidence but not an exact or optimal solution.

For each vehicle, duration is recomputed as travel time plus pickup/drop service time, including final depot unload service. Loads begin at zero, remain within the vehicle's Q, and the final carried load is unloaded at depot. Every visited station appears at most once across routes and has one nonzero pickup-or-drop operation. Unused vehicles are materialized explicitly for completeness without claiming that the native solver returned a positive route for them.

The independent archive verifier rereads the JSON and expanded CSV files without solver objects. It checks identities, sequence consistency, depot endpoints, loads, capacities, station inventories, travel, service, duration, T feasibility, G, P, objective, solution class, and certificate consistency. It never optimizes or repairs a witness.
