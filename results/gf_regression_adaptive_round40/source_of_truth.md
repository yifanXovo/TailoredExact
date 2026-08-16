# Round 40 source of truth

- Repository: `ExactEBRP` (existing local repository; no clone created).
- Research branch: `codex/round40-regression-adaptive`.
- Stable parent: Round 39 commit `60d1f6e454e0d2b2b1c5c883c3a3d0ae9b5ffd19`.
- Validated default protected throughout: `C6-HGA-FULL`, `K=4`, `rho=0.01`.
- Result root: `results/gf_regression_adaptive_round40/`.
- Part 0: 8 frozen Off/Auto rows in `presolve_fairness_manifest.csv`.
- Part 1: 40 original rows plus 10 iterative decisive rows; both manifests were frozen before their respective results.
- Part 2: 48 rows (24 frozen Round 39 instances x K4/nested-dyadic) in `ub_geometry_manifest.csv`.
- Default equivalence: 6 current-executable rows in `default_c6_equivalence_manifest.csv`.
- Every run directory contains its exact command, executable SHA-256, instance SHA-256, stdout/stderr, result JSON, and native evidence ledgers.
- Gurobi contract after Part 0: Presolve Auto (`-1`), Threads 1, Seed 0, relative/absolute gaps 0.
- Historical Round 39 evidence was read only and remains unchanged.

Part 1's decisive arm was added after the original four-arm manifest; its separate executable hash and freeze record are retained. Later default-off equivalence confirms that adding experimental arms did not alter the frozen K4 path on 25 deterministic fields across three representative instances.
