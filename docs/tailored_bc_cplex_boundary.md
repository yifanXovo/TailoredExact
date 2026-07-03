# CPLEX Boundary for Tailored BC

`paper-gf-tailored-bc` is intended to be a CPLEX-managed tailored branch-and-cut mode with user-cut, lazy, incumbent, and branching callbacks.

Current repository state:

- The checked-in executable is built with MinGW/g++.
- `src/CplexBaseline.cpp` generates LP/script files and invokes `cplex.exe -f ...` through a command-file process boundary.
- `src/TailoredBCCplexApi.cpp` can now load `cplex2211.dll` dynamically and use the CPLEX C API without linking against MSVC import libraries.

The current callback implementation is intentionally narrow:

- read the existing fixed-interval LP model into an in-process CPLEX environment;
- register a generic callback for relaxation, candidate, branching, and global-progress contexts;
- add one redundant paper-safe user cut `G <= gamma_U` when the `G` column exists;
- retrieve relaxation points through `CPXcallbackgetrelaxationpoint`;
- separate visit-inventory linking rows, singleton/pair Gini subset-envelope rows, and the aggregate low-Gini L1 centering row from relaxation points when violated;
- inspect candidate points and reject only numerical fixed-Gini interval violations through `CPXcallbackrejectcandidate`;
- apply CPLEX branch-order priorities through `CPXcopyorder`;
- wire a one-shot Gini interval split through `CPXcallbackmakebranch` for rows that explicitly request callback Gini branching;
- count callback events and solve the model through `CPXmipopt`.

This proves the callback boundary is now technically open. It does not yet implement the full requested tailored branch-and-cut policy: independent route-plan incumbent verification/rejection, hard-leaf-validated custom Gini branches, and hard-leaf callback cut separation remain incomplete.
