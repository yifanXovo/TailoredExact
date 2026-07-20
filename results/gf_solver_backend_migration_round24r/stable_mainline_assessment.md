# Stable mainline assessment

Round 24R is qualification evidence only. **Corrected CPLEX S0/F0 remains the stable paper mainline for every observed outcome.** The presolve-on single-tree arm is permanently non-authoritative; its bounds and certificate decisions are excluded from exact claims.

The licensed Gurobi results are strong enough to justify a later, longer migration study: plain Gurobi and both external-Gurobi arms strictly certified V12_M1 and V12_M2, and the external Gurobi variants certified both faster than external CPLEX. Evidence on the two hard cases is mixed, and this round does not justify promotion. Warm-start evidence is also mixed and preliminary: one of six Stage 2 submissions was affirmatively accepted, with small aggregate proof-progress gains but no parent-tree reuse. No solver portfolio or instance-dependent selector was created.
