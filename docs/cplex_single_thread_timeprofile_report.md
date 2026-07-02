# Single-Thread CPLEX Time-Profile Report

All controlled plain CPLEX rows in
`results/gf_compact_bc_timeprofile_round/` use `--cplex-threads 1` and emit
`thread_fairness_class=one_thread_fair`.

At 300s, compact-BC substantially outperformed plain CPLEX on some V20 rows:

- `high_imbalance_seed3201`: compact-BC gap `0.0523`, CPLEX gap `0.2259`;
- `high_imbalance_seed3202`: compact-BC 300s gap `0.0219`, CPLEX gap `0.6485`;
- `tight_T_seed3101`: compact-BC certified, CPLEX gap `0.8816`.

CPLEX was stronger than the current compact-BC wrapper rows on
`tight_T_seed3102`, `moderate_seed3301`, and `moderate_seed3302` in this
particular run because those compact-BC rows were interrupted before leaf MIPs
returned useful final bounds.
