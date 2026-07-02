# Large-V Compact-BC Time-Profile Diagnostics

Rows run:

- V50/M3 moderate, 300s;
- V50/M3 high imbalance, 300s;
- V100/M5 moderate, 300s;
- V100/M5 high imbalance, 300s.

Results are diagnostic only. V50 rows hit `model_size_limit` with
`std_bad_alloc`. V100 rows produced wrapper-finalized noncertified rows with
early progress LB/UB/gap. No large-V row certified.

Plain CPLEX benchmark rows with one thread were also run for V50/V100 and are
kept benchmark-only.
