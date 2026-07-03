# Tailored BC Callback Status and Remaining Blockers

The original architectural blocker was that the production path invoked `cplex.exe` through command files and did not link the CPLEX API. This has been partially removed by `src/TailoredBCCplexApi.cpp`, which dynamically loads `cplex2211.dll` and registers a generic CPLEX callback.

Implemented:

- dynamic loading of `cplex2211.dll`;
- in-process `CPXreadcopyprob` / `CPXmipopt`;
- generic callback registration;
- relaxation/candidate/branch/progress callback event counters;
- one redundant paper-safe Gini interval cap from the relaxation callback;
- relaxation-point separation hooks for visit-inventory linking rows;
- relaxation-point separation hooks for singleton/pair Gini subset-envelope rows;
- relaxation-point separation hooks for the aggregate low-Gini L1 centering row;
- candidate compact-row consistency checks with safe lazy rejection of numerical Gini interval, visit-inventory, Gini subset-envelope, and low-Gini L1 violations;
- CPLEX branch-order priorities through `CPXcopyorder`;
- a one-shot custom Gini split callback path that is wired but not yet validated on hard leaves.

Remaining blockers:

- verifier-backed route-plan lazy incumbent rejection is not implemented;
- independent route-plan feasibility/objective verification inside the callback is not implemented;
- custom Gini branch creation has no hard-leaf evidence yet;
- hard-leaf callback separation is not performance-validated;
- the problem-specific callback cuts have only smoke/diagnostic evidence and have not yet produced hard-leaf bound improvement.
