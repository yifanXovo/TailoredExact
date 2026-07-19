# External-tree certificate policy

An external-tree certificate is engineering-exact only when root coverage and every parent-child coverage identity pass; every relevant leaf is closed; every retained leaf bound is valid and monotone; the aggregated minimum bound is valid and monotone; all native model/optimize/free lifecycles complete; the global incumbent is independently feasible and recomputed; the feasibility-consistency gate passes; and global LB equals verified UB.

Native bounds may enter only from a finalized unchanged leaf model whose canonical fingerprint matches its request. On interruption, a finite native bound is retained only if the adapter’s native call marks it valid. Parent bounds may be inherited by children. Incumbents, cutoffs, starts, and closed siblings never become a lower bound for an open leaf.

Any uncovered interval, partial child replacement, invalid/nonfinite/decreasing bound, reset or lifecycle mismatch, verifier failure, contradicted infeasibility, open relevant leaf, or positive global gap rejects the certificate. The Stage 0 CPLEX smoke is intentionally non-strict (`relevant_leaf_open`). The Gurobi smoke is unavailable and contributes no bound.
