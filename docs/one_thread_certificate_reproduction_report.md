# One-Thread Certificate Reproduction

Round 2 reran key compact-BC rows with one internal compact-BC solver thread.

Results are in
`results/gf_compact_bc_strengthening_round2/certificate_reproduction_summary.csv`.

Certified under one-thread policy:

- `regen_candidate_V12_M1_average.txt`: objective/LB/UB `0.357200583208`.
- `regen_candidate_V12_M2_average.txt`: objective/LB/UB `0.718504070755`.
- `high_imbalance_seed3202.txt`: objective/LB/UB `1.74931345205`.
- `tight_T_seed3101.txt`: objective/LB/UB `0.107252734134`.

All four rows passed certificate audit with no archive, known-UB, external
incumbent, BPC, or route-mask certificate evidence.

