# Round 45 completion contract

- Branch: `codex/round45-adaptive-timing-parametric-partition`
- Starting local commit: `0dbba47a0bf6e909d555cce1af8d9e32c4c7b035`
- Starting tree: `0066f6f306a46c8d0145c2fbe3b8effc8dbe039b`
- Machine: `WIN-3NO58RVQ4VC`
- Frozen rows: 213 total; 48 mandatory complex; 6 D_R43 complex diagnostics.

All official Gurobi rows run sequentially with Presolve Auto, Seed 0, Threads 1,
MIPGap 0, MIPGapAbs 0, certificate tolerance 1e-7, no known/archive optimum
injection, and a 3600-second total-process cap. Unsolved rows must reach the cap
within finalization tolerance and preserve 300/1200/3600 reconstructible traces.

The K4 candidate is frozen at gamma-veto/rho_gamma=0.012/frontier-d2/all
parent-scope facets/midpoint/no MIP starts. D_R43 is frozen at rho_D=0.10.
Thresholds will not be retuned from validation or the consumed holdout.

The finalizer must derive every classification from completed evidence. Missing
rows force `round45_completion_incomplete`; no-adaptive is never promotion
eligible; C6 remains the broad validated mainline until all gates pass.
