# Diagnostic tight_T_seed3101__ext_grb_warm

Triggered by: `plain_higher_valid_final_lb`. This 300-second replay uses the frozen executable and identical mathematical options and does not replace the official 900-second row.

The 300-second comparison is `EXT-GRB-COLD` (LB `0.052886026602309115`, gap `0.5069027654226236`, AUC `0.47730948728378264`) versus the replay (LB `0.05292500039676334`, gap `0.5065393826634899`, AUC `0.4776793459810228`). Outcome: `performance_ordering_not_reproduced_and_therefore_unstable` (`plain_higher_valid_final_lb`).

Replay status: `external_gini_tree_time_limit`; optimize/model-read/artifact counts: `8/6/6`; fresh/same-leaf/child restarts: `6/2/6`; splits/closures: `2/1`; enhanced trace: `results/gf_solver_backend_validation_round25/runs/diagnostic__tight_T_seed3101__ext_grb_warm__300s/external/enhanced_attempt_trace.csv`.

Bottleneck classifications: performance ordering not reproduced and therefore unstable, repeated presolve/root overhead, excessive native model restarts, weak leaf lower bounds, controlling-leaf or scheduler stagnation, warm-start rejection or overhead.
