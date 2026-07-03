# S-Range Denominator Refinement

S-range refinement is implemented as fixed-interval diagnostic bucket rows. A bucket adds `S_L^b <= sum_i r_i <= S_U^b` and reuses `S_U^b` in the objective-estimator cutoff. It is not enabled as paper-core evidence until the full frontier ledger explicitly partitions every parent leaf over S and checks exact bucket coverage.
