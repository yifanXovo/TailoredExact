# Tailored BC Callback Status and Remaining Blockers

The original architectural blocker was that the production path invoked `cplex.exe` through command files and did not link the CPLEX API. This has been partially removed by `src/TailoredBCCplexApi.cpp`, which dynamically loads `cplex2211.dll` and registers a generic CPLEX callback.

Implemented:

- dynamic loading of `cplex2211.dll`;
- in-process `CPXreadcopyprob` / `CPXmipopt`;
- generic callback registration;
- relaxation/candidate/branch/progress callback event counters;
- one redundant paper-safe user cut from the relaxation callback.

Remaining blockers:

- lazy incumbent rejection is not implemented;
- independent incumbent verification inside the callback is not implemented;
- custom Gini branch creation is not implemented;
- branch priorities are metadata only;
- hard-leaf callback separation is not performance-validated;
- the callback user cut is currently a redundant interval cap used to prove callback plumbing safely.
