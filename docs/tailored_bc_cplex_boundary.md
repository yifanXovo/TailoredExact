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
- separate visit-inventory linking rows, singleton/pair Gini subset-envelope rows, the aggregate low-Gini L1 centering row, conservative singleton/pair/triple subset-inventory imbalance rows, basic transfer-cutset rows, and lifted pair/triple/quad support-duration cover rows from relaxation points when violated;
- inspect candidate points and reject fixed-Gini interval, visit-inventory, Gini subset-envelope, low-Gini L1, and subset-inventory numerical violations through `CPXcallbackrejectcandidate` when the corresponding valid row can be re-added safely;
- apply CPLEX branch-order priorities through `CPXcopyorder`;
- wire a one-shot Gini interval split through `CPXcallbackmakebranch` for rows that explicitly request callback Gini branching;
- count callback events and solve the model through `CPXmipopt`.

Separate from the callback-owned mechanisms, `--tailored-bc-benders-inventory-cuts diagnostic` adds aggregate receiver-set inventory capacity rows during LP model generation. That family is deliberately classified as diagnostic static strengthening, not callback evidence and not paper-core certificate evidence.

The callback package includes a diagnostic branch-smoke row that uses a multidimensional binary knapsack to test branch callback reachability.  With current settings, the row applies branch priorities, receives relaxation/candidate callbacks, enters branch context, and creates two one-shot Gini branches through `CPXcallbackmakebranch`.

This proves the callback boundary is now technically open for relaxation, candidate, and diagnostic branching contexts. It does not yet implement the full requested tailored branch-and-cut policy: independent route-plan incumbent verification/rejection, consistently useful custom Gini branches on ExactEBRP hard leaves, and decisive hard-leaf callback cut separation remain incomplete.
