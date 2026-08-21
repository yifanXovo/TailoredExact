# Round 45 research contract

Round 45 has two strictly separated questions. Part I changes only the
mathematical split/retain timing decision while every split is the midpoint.
Part II freezes the selected timing rule and changes only the split location.

The promoted mechanism must be genuinely adaptive: it must issue both split
and retain actions on the frozen development evidence. `no-adaptive` is an
ineligible performance reference. No instance identity, seed, dimensions,
membership, prior winner, telemetry, runtime, Work, node count, memory,
hardware property, or learned/per-instance dispatch may influence a decision.

All exact runs use Gurobi Presolve Auto, Seed 0, Threads 1, zero relative and
absolute gaps, the full original objective, the same independently verified
HGA-FULL incumbent, certificate tolerance 1e-7, complete interval coverage,
monotone valid global lower bounds, and fail-closed lifecycle handling. The
external 3600-second cap is an outcome constraint and never a decision input.
