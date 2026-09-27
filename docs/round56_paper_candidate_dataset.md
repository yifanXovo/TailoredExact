# Round 56 paper-candidate screening dataset

Round 56 constructs a deterministic matched screening panel for the frozen corrected `paper-k1-am-sf` mainline. It is not a recovered historical benchmark and is not the final replicated paper dataset.

Five independently generated moderate/average base landscapes cover V in {8, 12, 20, 30, 50}. Each V has one deterministic seed derived from the frozen Round 55 base commit, V, and the string `round56-paper-time-horizon-v1`. M, Q, and T never participate in base-landscape generation. Fleet variants reuse identical station order, capacities, inventories, targets, weights, min-ratio metadata, coordinates, and parser-effective distances.

The primary factorial screen uses Q=30, two M values per V, and operational route horizons T in {1800, 3600, 10800, 18000}, for 40 scenarios. A smaller capacity-transfer sentinel panel uses Q=20, the lower M at each V, and T in {3600, 18000}, for 10 scenarios. No T=21600 scenario is part of Round 56.

All scenario identities, input hashes, output paths, and process caps were frozen before performance execution. The common proof-comparison horizon is 3600 seconds. Exactly nine predeclared V>=20, T=18000 rows have a 7200-second final cap; that extension is used only to inventory additional exact solutions and does not replace the common comparison horizon.

The complete sources of truth are:

- `reference/round56_paper_candidate/` for base landscapes, fleet variants, and mathematical scenario descriptors;
- `results/gf_paper_benchmark_time_horizon_round56/scenario_manifest.csv` for the 50-row matrix;
- `results/gf_paper_benchmark_time_horizon_round56/execution_manifest.json` for exact official commands and run identities;
- `results/gf_paper_benchmark_time_horizon_round56/paper_candidate_instance_table.csv`, `paper_candidate_result_table.csv`, and `paper_candidate_route_table.csv` for direct analysis tables.

One base landscape per V is sufficient for matched engineering and structural screening, but not for statistical generalization. A later final paper dataset should replicate every retained structural cell across multiple independently frozen landscapes and must not select landscapes according to Round 56 certification difficulty or favorable outcomes.
