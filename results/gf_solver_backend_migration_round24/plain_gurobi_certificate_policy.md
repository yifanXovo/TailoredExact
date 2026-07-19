# Plain Gurobi engineering-exact certificate policy

A plain Gurobi optimality certificate is accepted only when all gates hold: native status is exactly `OPTIMAL`; optimize and finalization completed; the audited complete original model and lifecycle are valid; executable and canonical/native fingerprints match the frozen manifest; requested and read-back `MIPGap` and `MIPGapAbs` are exactly zero; a finite solution exists; the independent original-problem verifier and objective recomputation pass; and no HGA, Tailored, known-UB, or CPLEX result entered the solve.

`ObjBoundC` is the authoritative raw continuous lower bound. `ObjBound` is retained but never used as silent objective-integrality rounding. Limit, interrupt, numerical, unsupported, unavailable, mismatched, or contradictory states reject strict certification. Native infeasibility additionally requires complete original-model scope and no independently verified feasible witness; a witness contradiction fails closed.

The local Stage 0 P-GRB attempts received error 10009 before optimize. They therefore have zero models, zero optimize calls, no native status/fingerprint, and no certificate.
